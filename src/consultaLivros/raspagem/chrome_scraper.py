from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin 
from .book_scraper import extrair_dados_livro
from ..repositorios.livros_repositorio import salva_dados_livros
from ..repositorios.tarefas_repositorio import busca_tarefa_por_id, atualiza_tarefa
from sqlalchemy.orm import Session
from ..db.database import SessionLocal



# Função para raspar todos os livros de uma página de uma categoria
def raspa_livros_categoria(driver, url_categoria, nome_categoria):
    """
    Realiza a raspagem de todos os livros, percorrendo todas as páginas.
    """
    dados_livros = []
    url_atual = url_categoria
 
    while True:
        print(f"Acessando página: {url_atual}")
        driver.get(url_atual)

        # Encontre todos os elementos <article class="product_pod"> na página atual
        livros_elements = driver.find_elements(By.CLASS_NAME, "product_pod")

        # Extraia os dados de cada livro na página atual
        for livro_element in livros_elements:
            data = extrair_dados_livro(livro_element, nome_categoria)
            if data:
                dados_livros.append(data)

        # Tenta encontrar o botão "next" para paginar dentro da categoria
        try:
            next_page_element = driver.find_element(By.CLASS_NAME, "next")
            prox_pag_link_relativo = next_page_element.find_element(By.TAG_NAME, "a").get_attribute("href")
            # Constrói a URL completa para a próxima página
            url_atual = urljoin(url_atual, prox_pag_link_relativo)

        except:
            # Se não encontrar o botão "next", significa que chegamos à última página
            print(f"Não ha mais página para raspar na categoria '{nome_categoria}'.")
            break

    return dados_livros


def rodar_scraper_completo(id_tarefa: str):
    """
    Função principal para rodar o scraper completo.
    Configura o Selenium, raspa os dados e salva no banco de dados.
    """
    # Configuração do Selenium para usar o Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa o Chrome em modo headless (sem interface gráfica)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") 

    # Inicializando o driver do Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    dados_todos_os_livros = []
    try:
        
        # Busca a tarefa pelo ID
        if id_tarefa:
            with SessionLocal() as db:
                tarefa = busca_tarefa_por_id(db, id_tarefa)
                if not tarefa:
                    print(f"Tarefa com ID {id_tarefa} não encontrada.")
                    return {"error": "Tarefa não encontrada"}
                print(f"Iniciando raspagem para a tarefa: {tarefa.id}")
                atualiza_tarefa(db, tarefa.id, estado="EXECUTANDO", resultado={"mensagem": "Raspagem iniciada"})

        base_url = "https://books.toscrape.com/"
        driver.get(base_url)

        # 1. ENCONTRAR TODOS OS LINKS DAS CATEGORIAS NO MENU LATERAL
        print("Buscando lista de categorias...")
        categoria_elements = driver.find_elements(By.XPATH, "//div[@class='side_categories']//ul/li/ul/li/a")

        # Extraímos o texto (nome) e o href (link) de cada categoria
        categorias_para_raspar = []
        for cat_el in categoria_elements:
            categorias_para_raspar.append({
                'nome': cat_el.text,
                'url': cat_el.get_attribute('href')
            })
        print(f"Encontradas {len(categorias_para_raspar)} categorias para raspar.")


        # 2. ITERAR SOBRE CADA CATEGORIA E RASPAR OS LIVROS
        for categoria in categorias_para_raspar:
            print(f"\n--- INICIANDO RASPAGEM DA CATEGORIA: {categoria['nome']} ---")
            livros_da_categoria = raspa_livros_categoria(driver, categoria['url'], categoria['nome'])
            dados_todos_os_livros.extend(livros_da_categoria)
            print(f"Total de {len(livros_da_categoria)} livros encontrados em '{categoria['nome']}'.")


        print(f"\nRaspagem finalizada. Total de {len(dados_todos_os_livros)} livros encontrados em todas as categorias.")

        if dados_todos_os_livros:
            print("Iniciando o salvamento dos dados no banco de dados...")
            with SessionLocal() as db:
                try:
                    # Salva os dados dos livros no banco de dados SQLite
                    salva_dados_livros(db, dados_todos_os_livros)
                    print("Dados salvos com sucesso no banco de dados.")
                except Exception as e:
                    print(f"Ocorreu um erro ao salvar os dados no banco de dados: {e}")
                    db.rollback()
        
        # Atualiza o estado da tarefa para concluída
        if id_tarefa:
            with SessionLocal() as db:
                atualiza_tarefa(db, tarefa.id, estado="CONCLUIDA", resultado={"total_encontrado": len(dados_todos_os_livros)})
                print(f"Tarefa {tarefa.id} concluída com sucesso.")

        return {"total_encontrado": len(dados_todos_os_livros)}
    
    except Exception as e:
        # Atualiza o estado da tarefa para erro
        if id_tarefa:
            with SessionLocal() as db:
                atualiza_tarefa(db, tarefa.id, estado="ERRO", resultado={"erro": str(e)})
                print(f"Tarefa {tarefa.id} finalizada com erro: {e}")
                
        print(f"Erro ao rodar o scraper: {e}")
        return {"error": str(e)}
    finally:
        # Fechando o driver
        driver.quit()

if __name__ == "__main__":
    print("Executando o scraper em modo standalone...")
    resultado = rodar_scraper_completo()
    print(resultado)
