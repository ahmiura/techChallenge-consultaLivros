import logging
from typing import Any, Dict, Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Constantes para seletores, melhorando a manutenibilidade
class BookSelectors:
    TITLE = (By.CSS_SELECTOR, "h3 > a")
    PRICE = (By.CSS_SELECTOR, "p.price_color")
    RATING = (By.CSS_SELECTOR, "p.star-rating")
    AVAILABILITY = (By.CSS_SELECTOR, "p.instock.availability")
    IMAGE = (By.CSS_SELECTOR, "div.image_container img")

# Mapeamento de rating de texto para valor numérico
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def extrair_dados_livro(
    elemento_html: WebElement, nome_categoria: str
) -> Optional[Dict[str, Any]]:
    """
    Extrai informações detalhadas de um único livro a partir de seu elemento HTML.

    Args:
        elemento_html: O WebElement do Selenium que contém o contêiner do livro.
        nome_categoria: A categoria do livro, passada como contexto.

    Returns:
        Um dicionário com os dados do livro ou None se ocorrer um erro na extração.
    """
    try:
        # Título
        titulo_element = elemento_html.find_element(*BookSelectors.TITLE)
        titulo = titulo_element.get_attribute("title")

        # Preço
        preco_element = elemento_html.find_element(*BookSelectors.PRICE)
        # Remove o símbolo da moeda e converte para float
        preco = float(preco_element.text.replace("£", ""))

        # Rating
        rating_element = elemento_html.find_element(*BookSelectors.RATING)
        # A classe do rating é a última na lista de classes do elemento
        rating_texto = rating_element.get_attribute("class").split()[-1]
        rating_numero = RATING_MAP.get(rating_texto, 0)

        # Disponibilidade
        disponibilidade_element = elemento_html.find_element(*BookSelectors.AVAILABILITY)
        disponibilidade = "In stock" in disponibilidade_element.text

        # Imagem
        imagem_element = elemento_html.find_element(*BookSelectors.IMAGE)
        imagem_url = imagem_element.get_attribute("src")

        return {
            "titulo": titulo,
            "preco": preco,
            "rating": rating_numero,
            "disponibilidade": disponibilidade,
            "imagem": imagem_url,
            "categoria": nome_categoria,
        }

    except NoSuchElementException as e:
        logging.warning(f"Seletor não encontrado durante extração: {e.msg}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao extrair dados do livro: {e}", exc_info=True)
        return None