import logging
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from ..db.database import SessionLocal
from ..repositorios.livros_repositorio import salva_dados_livros
from ..repositorios.tarefas_repositorio import atualiza_tarefa, busca_tarefa_por_id
from .book_scraper import extrair_dados_livro
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _setup_driver() -> webdriver.Chrome:
    """Configura e inicializa o driver do Selenium Chrome."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    logging.info("Instalando e configurando o ChromeDriver...")
    driver = webdriver.Chrome(options=chrome_options)
    logging.info("Driver do Chrome inicializado com sucesso.")
    return driver


def raspa_livros_categoria(driver: webdriver.Chrome, url_categoria: str, nome_categoria: str) -> list[dict]:
    """Realiza a raspagem de todos os livros de uma categoria, percorrendo a paginação."""
    dados_livros = []
    url_atual = url_categoria
 
    while True:
        logging.info(f"Acessando página da categoria '{nome_categoria}': {url_atual}")
        driver.get(url_atual)

        livros_elements = driver.find_elements(By.CLASS_NAME, "product_pod")

        for livro_element in livros_elements:
            data = extrair_dados_livro(livro_element, nome_categoria)
            if data:
                dados_livros.append(data)

        try:
            next_page_element = driver.find_element(By.CLASS_NAME, "next")
            prox_pag_link_relativo = next_page_element.find_element(By.TAG_NAME, "a").get_attribute("href")
            url_atual = urljoin(url_atual, prox_pag_link_relativo)
        except NoSuchElementException:
            logging.info(f"Não há mais páginas para raspar na categoria '{nome_categoria}'.")
            break

    return dados_livros


def _worker_raspa_lote_de_categorias(lote_categorias: list[dict]) -> list[dict]:
    """
    Função de trabalho para raspar um LOTE de categorias.
    Inicia um único driver e o reutiliza para todas as categorias no lote.
    """
    driver = None
    todos_os_livros_do_lote = []
    try:
        driver = _setup_driver()
        logging.info(f"Worker iniciando raspagem para um lote de {len(lote_categorias)} categorias.")
        
        for categoria in lote_categorias:
            livros = raspa_livros_categoria(driver, categoria['url'], categoria['nome'])
            if livros:
                todos_os_livros_do_lote.extend(livros)
        
        logging.info(f"Worker finalizou seu lote, encontrou {len(todos_os_livros_do_lote)} livros no total.")
        return todos_os_livros_do_lote
    except Exception as e:
        logging.error(f"Worker falhou ao processar seu lote de categorias: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()
            logging.info("Worker fechou seu driver.")


def rodar_scraper_completo(id_tarefa: str | None = None):
    """
    Função principal que busca categorias e dispara workers para processar
    LOTES de categorias concorrentemente. 
    Atualiza o status da tarefa.
    """
    # Este driver inicial é usado apenas para buscar a lista de categorias.
    driver = _setup_driver()

    try:
        # 1. ATUALIZAR STATUS DA TAREFA PARA "EXECUTANDO"
        with SessionLocal() as db:
            if id_tarefa:
                tarefa = busca_tarefa_por_id(db, id_tarefa)
                if not tarefa:
                    logging.error(f"Tarefa com ID {id_tarefa} não encontrada.")
                    return {"error": "Tarefa não encontrada"}

                logging.info(f"Iniciando raspagem para a tarefa: {tarefa.id}")
                atualiza_tarefa(db, tarefa.id, estado="EXECUTANDO", resultado={"mensagem": "Raspagem iniciada"})
                db.commit()  # Garante que o estado seja salvo imediatamente

            # 2. BUSCAR CATEGORIAS (usando o driver principal)
            base_url = "https://books.toscrape.com/"
            driver.get(base_url)

            logging.info("Buscando lista de categorias...")
            categoria_elements = driver.find_elements(By.XPATH, "//div[@class='side_categories']//ul/li/ul/li/a")

            categorias_para_raspar = [
                {
                    'nome': cat_el.text, 
                    'url': urljoin(base_url, cat_el.get_attribute('href'))
                }
                for cat_el in categoria_elements
            ]
            logging.info(f"Encontradas {len(categorias_para_raspar)} categorias para raspar.")

        # O driver principal não é mais necessário, pode ser fechado.
        driver.quit()
        driver = None  # Garante que não será fechado de novo no finally

        # 3. PREPARAÇÃO E EXECUÇÃO DOS LOTES
        NUMERO_DE_WORKERS = 2
        # Divide a lista de categorias em N lotes para os N workers
        lotes_de_categorias = np.array_split(categorias_para_raspar, NUMERO_DE_WORKERS)
        
        todos_os_livros = []
        with ThreadPoolExecutor(max_workers=NUMERO_DE_WORKERS) as executor:
            # executor.map agora passa cada LOTE para a função do worker
            resultados_por_lote = executor.map(_worker_raspa_lote_de_categorias, lotes_de_categorias)
            
            for lista_livros in resultados_por_lote:
                if lista_livros:
                    todos_os_livros.extend(lista_livros)

        total_livros_encontrados = len(todos_os_livros)
        logging.info(f"Raspagem paralela em lotes finalizada. Total de {total_livros_encontrados} livros encontrados.")

        # 4. SALVAR DADOS EM MASSA E ATUALIZAR TAREFA
        with SessionLocal() as db:
            if todos_os_livros:
                logging.info(f"Salvando {total_livros_encontrados} livros no banco de dados em uma única transação.")
                salva_dados_livros(db, todos_os_livros)

            if id_tarefa:
                atualiza_tarefa(db, id_tarefa, estado="CONCLUIDA", resultado={"total_encontrado": total_livros_encontrados})
                logging.info(f"Tarefa {id_tarefa} concluída com sucesso.")

        return {"total_encontrado": total_livros_encontrados}

    except Exception as e:
        logging.error(f"Erro ao rodar o scraper: {e}", exc_info=True)
        # 5. ATUALIZAR TAREFA PARA "ERRO"
        if id_tarefa:
            try:
                with SessionLocal() as db_erro:
                    atualiza_tarefa(db_erro, id_tarefa, estado="ERRO", resultado={"erro": str(e)})
                    db_erro.commit()
                    logging.info(f"Tarefa {id_tarefa} marcada como ERRO.")
            except Exception as db_exc:
                logging.error(f"Falha ao atualizar status da tarefa para ERRO: {db_exc}")

        return {"error": str(e)}
    finally:
        if driver:  # Apenas se o driver principal ainda estiver ativo (em caso de erro inicial)
            logging.info("Fechando o driver do Chrome principal.")
            driver.quit()

if __name__ == "__main__":
    logging.info("Executando o scraper em modo standalone...")
    resultado = rodar_scraper_completo()
    logging.info(f"Resultado: {resultado}")
