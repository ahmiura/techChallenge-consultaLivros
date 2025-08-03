from selenium.webdriver.common.by import By

def extrair_dados_livro(elemento_html, nome_categoria):
    try:
        # Título
        titulo_element = elemento_html.find_element(By.XPATH, ".//h3/a")
        titulo = titulo_element.get_attribute("title")

        # Preço
        preco_element = elemento_html.find_element(By.CLASS_NAME, "price_color")
        preco = float(preco_element.text.replace("£", ""))

        # Dicionário para o mapeamento de rating de texto para número
        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }

        # Rating
        rating_element = elemento_html.find_element(By.XPATH, ".//p[contains(@class, 'star-rating')]")
        rating_class = rating_element.get_attribute("class")
        rating_texto = rating_class.split(" ")[-1]  # Pega a última classe (e.g., "One", "Two", etc.)
        rating_numero = rating_map.get(rating_texto, 0)  # Mapeia o texto para número, padrão é 0 se não encontrado


        # Disponibilidade
        disponibilidade_element = elemento_html.find_element(By.CLASS_NAME, "instock.availability")
        disponibilidade = "In stock" in disponibilidade_element.text

        # Imagem
        imagem_element = elemento_html.find_element(By.XPATH, ".//div[@class='image_container']/a/img")
        imagem = imagem_element.get_attribute("src")

        return {
            "titulo": titulo,
            "preco": preco,
            "rating": rating_numero,
            "disponibilidade": disponibilidade,
            "imagem": imagem,
            "categoria": nome_categoria 
        }

    except Exception as e:
        print(f"Erro ao extrair dados do livro: {e}")
        return None