from ebooklib import epub
from bs4 import BeautifulSoup

def open_epub(epub_path):
    """Charge et retourne l'objet ebooklib du fichier EPUB."""
    book = epub.read_epub(epub_path)
    return book

def extract_sections(book):
    """
    Extrait tous les items textuels de l'EPUB.
    Retourne une liste de tuples (titre_section, contenu_texte).
    """
    sections = []
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            # HTML brut
            html_content = item.get_content().decode("utf-8", errors="ignore")
            # Si besoin, on peut récupérer un titre depuis la table des matières (metadata),
            # mais ici on se contente du nom du fichier
            title = item.get_name()

            # Convertir en texte brut + possible usage de BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator="\n")
            sections.append((title, text_content))
    return sections

def parse_epub_generic(epub_path):
    """
    Exemple d'usage: ouvre l'EPUB, récupère les sections,
    renvoie une structure de base (metadata + list de (title, text)).
    """
    book = open_epub(epub_path)
    # sections = extract_sections(book)


    # Métadonnées (titre, auteurs...) si l'EPUB les fournit
    title = book.get_metadata('DC', 'title')
    authors = book.get_metadata('DC', 'creator')

    metadata = {}
    if title:
        metadata["title"] = title
    if authors:
        metadata["authors"] = authors

    return {
        "metadata": metadata,
    }
