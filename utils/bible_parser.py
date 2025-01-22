
import re
from dotenv import load_dotenv
from enums.books import BOOKS_FR, BOOKS_EN
from utils.epub_parser import flatten_epub
from tests.bible_tests import test_book_coverage

load_dotenv()
ALL_BOOKS = BOOKS_FR + BOOKS_EN

def clean_bible_text(file_path):
    """
    Recupère la version "flattened" de la bible et supprime les élements non désirés pour récupérer uniquement le texte à parser.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    # Supprimer les motifs [nombre] qui sont en général des références à d'autres versets (souvent présents dans les bible avec annotations).  [12], [1]
    text_content = re.sub(r"\[\d+\]", "", text_content)

    # Supprimer les retours à la ligne sauf devant un chiffre
    text_content = re.sub(r"\n+(?!\d)", "", text_content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    print(f"[INFO] Fichier nettoyé et réécrit : {file_path}")
    print("  - [chiffres] supprimés")
    print("  - Retours à la ligne supprimés sauf devant un chiffre.")

def detect_book_chapter_in_line(line, books_list):
    """
    Extrait (book, chapter) s'il existe ex. "Deutéronome 1" n'importe où dans la ligne.
    Return (None, None) si pas trouvé.
    """
    for book in books_list:
        # Vérfie dans la liste des livres si la ligne contient le nom d'un livre
        pattern = rf"{re.escape(book)}\s*(\d+)"
        found = re.search(pattern, line)
        if found:
            chap_str = found.group(1)
            try:
                chap_num = int(chap_str)
            except ValueError:
                continue
            return (book, chap_num)
    return (None, None)

def parse_bible(epub_path):
    """
    Lance les différentes fonctions afin de parser et insérer dans la base de données les informations du de la bible.
    """
    current_book = None
    current_chapter = None
    verses = []

    flatten_epub_path = flatten_epub(epub_path)
    clean_bible_text(flatten_epub_path)


    with open(flatten_epub_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            book, chapter = detect_book_chapter_in_line(line, ALL_BOOKS)
            if book and chapter:
                current_book = book
                current_chapter = chapter

            # Detecte un verset sur la ligne
            match_verse = re.match(r'^(\d+)(.*)', line)
            if match_verse:
                verse_num_str = match_verse.group(1)
                verse_text = match_verse.group(2).strip()
                try:
                    verse_num = int(verse_num_str)
                except ValueError:
                    verse_num = None
                verses.append((current_book, current_chapter, verse_num, verse_text))

    if verses:
        print("Premier verset:", verses[0])
        print("Dernier verset:", verses[-1])
    test_book_coverage(verses)
    return verses





