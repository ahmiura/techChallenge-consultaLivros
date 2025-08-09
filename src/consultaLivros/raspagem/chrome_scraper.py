import logging
from urllib.parse import urljoin

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


def rodar_scraper_completo(id_tarefa: str | None = None):
    """
    Função principal para rodar o scraper.
    Configura o Selenium, raspa os dados, salva no banco e atualiza o status da tarefa.
    """
    driver = _setup_driver()
    dados_todos_os_livros = []

    try:
        with SessionLocal() as db:
            # 1. ATUALIZAR STATUS DA TAREFA PARA "EXECUTANDO"
            if id_tarefa:
                tarefa = busca_tarefa_por_id(db, id_tarefa)
                if not tarefa:
                    logging.error(f"Tarefa com ID {id_tarefa} não encontrada.")
                    return {"error": "Tarefa não encontrada"}
                
                logging.info(f"Iniciando raspagem para a tarefa: {tarefa.id}")
                atualiza_tarefa(db, tarefa.id, estado="EXECUTANDO", resultado={"mensagem": "Raspagem iniciada"})
                db.commit() # Garante que o estado seja salvo imediatamente

            # 2. LÓGICA DE RASPAGEM
            base_url = "https://books.toscrape.com/"
            driver.get(base_url)

            logging.info("Buscando lista de categorias...")
            categoria_elements = driver.find_elements(By.XPATH, "//div[@class='side_categories']//ul/li/ul/li/a")
            
            categorias_para_raspar = [
                {'nome': cat_el.text, 'url': cat_el.get_attribute('href')}
                for cat_el in categoria_elements
            ]
            logging.info(f"Encontradas {len(categorias_para_raspar)} categorias para raspar.")

            for categoria in categorias_para_raspar:
                logging.info(f"--- INICIANDO RASPAGEM DA CATEGORIA: {categoria['nome']} ---")
                livros_da_categoria = raspa_livros_categoria(driver, categoria['url'], categoria['nome'])
                dados_todos_os_livros.extend(livros_da_categoria)
                logging.info(f"Total de {len(livros_da_categoria)} livros encontrados em '{categoria['nome']}'.")

            logging.info(f"Raspagem finalizada. Total de {len(dados_todos_os_livros)} livros encontrados.")

            # 3. SALVAR DADOS E ATUALIZAR TAREFA PARA "CONCLUÍDA"
            if dados_todos_os_livros:
                logging.info("Iniciando o salvamento dos dados no banco de dados...")
                salva_dados_livros(db, dados_todos_os_livros)
                logging.info("Dados salvos com sucesso no banco de dados.")
            
            if id_tarefa:
                atualiza_tarefa(db, id_tarefa, estado="CONCLUIDA", resultado={"total_encontrado": len(dados_todos_os_livros)})
                logging.info(f"Tarefa {id_tarefa} concluída com sucesso.")
            
            db.commit()

        return {"total_encontrado": len(dados_todos_os_livros)}
    
    except Exception as e:
        logging.error(f"Erro ao rodar o scraper: {e}", exc_info=True)
        # 4. ATUALIZAR TAREFA PARA "ERRO"
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
        logging.info("Fechando o driver do Chrome.")
        driver.quit()

if __name__ == "__main__":
    logging.info("Executando o scraper em modo standalone...")
    resultado = rodar_scraper_completo()
    logging.info(f"Resultado: {resultado}")
