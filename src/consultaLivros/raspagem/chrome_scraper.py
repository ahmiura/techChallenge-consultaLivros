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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _setup_driver() -> webdriver.Chrome:
    """Configura e inicializa o driver do Selenium Chrome."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    logging.info("Instalando e configurando o ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
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


def _worker_raspa_categoria(categoria: dict) -> list[dict]:
    """
    Função de trabalho para raspar uma única categoria.
    Cada worker inicializa seu próprio driver para garantir o paralelismo seguro.
    """
    driver = None
    try:
        driver = _setup_driver()
        logging.info(f"Worker iniciando raspagem para a categoria: {categoria['nome']}")
        livros = raspa_livros_categoria(driver, categoria['url'], categoria['nome'])
        logging.info(f"Worker finalizou a categoria '{categoria['nome']}', encontrou {len(livros)} livros.")
        return livros
    except Exception as e:
        logging.error(f"Worker falhou ao raspar a categoria '{categoria['nome']}': {e}", exc_info=True)
        return []  # Retorna lista vazia em caso de erro para não quebrar o processo
    finally:
        if driver:
            driver.quit()


def rodar_scraper_completo(id_tarefa: str | None = None):
    """
    Função principal para rodar o scraper de forma paralela.
    Configura o Selenium, busca as categorias, e dispara workers para raspar
    cada categoria concorrentemente. Salva os dados no banco e atualiza o status da tarefa.
    """
    # Este driver inicial é usado apenas para buscar a lista de categorias.
    driver = _setup_driver()
    total_livros_encontrados = 0

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
                {'nome': cat_el.text, 'url': cat_el.get_attribute('href')}
                for cat_el in categoria_elements
            ]
            logging.info(f"Encontradas {len(categorias_para_raspar)} categorias para raspar em paralelo.")

        # O driver principal não é mais necessário, pode ser fechado.
        driver.quit()
        driver = None  # Garante que não será fechado de novo no finally

        # 3. RASPAGEM PARALELA
        todos_os_livros = []
        # O número de workers pode ser ajustado conforme os recursos da máquina.
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados_por_categoria = executor.map(_worker_raspa_categoria, categorias_para_raspar)
            for lista_livros in resultados_por_categoria:
                if lista_livros:
                    todos_os_livros.extend(lista_livros)

        total_livros_encontrados = len(todos_os_livros)
        logging.info(f"Raspagem paralela finalizada. Total de {total_livros_encontrados} livros encontrados.")

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
