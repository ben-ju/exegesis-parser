import re
import sqlite3
import os
from .epub_parser import parse_epub_generic
from dotenv import load_dotenv
from ebooklib import epub
from bs4 import BeautifulSoup
from enums.books import BOOKS_FR, BOOKS_EN, END_BOOKS, START_BOOKS
load_dotenv()
ALL_BOOKS = BOOKS_FR + BOOKS_EN

def flatten_epub(epub_path, output_path=None):
    """
    Lit un fichier EPUB et crée un unique fichier texte
    contenant le contenu brut de tous les documents dans l'ordre de lecture,
    SANS balises HTML (uniquement le texte).
    """
    # Déterminer le chemin de sortie si non fourni
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(epub_path))[0]
        output_path = f"{base_name}_flattened.txt"

    # 1. Lire l'EPUB
    book = epub.read_epub(epub_path)

    # 2. Parcourir les éléments dans l'ordre du "spine"
    #    (c'est la table qui définit l'ordre logique de lecture)
    all_text_parts = []

    for itemref in book.spine:
        item_id = itemref[0]  # l'ID de l'item dans la liste spine
        item = book.get_item_with_id(item_id)

        # Vérifier qu'il s'agit bien d'un document (HTML/XHTML)
        if item is not None:
            # 3. Décoder le contenu HTML
            html_content = item.get_content().decode("utf-8", errors="ignore")

            # Parser avec BeautifulSoup pour extraire uniquement le texte
            soup = BeautifulSoup(html_content, "html.parser")
            text_content = soup.get_text(separator="\n")

            # Ajouter des délimiteurs pour repérer l'origine du fichier (optionnel)
            all_text_parts.append(text_content)

    # 4. Écrire dans le fichier de sortie (pur texte ou .html sans balises)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text_parts))
        f.write("\n")

    print(f"[INFO] EPUB aplati (texte brut) et enregistré dans : {output_path}")
    return output_path  # On retourne le chemin pour une utilisation ultérieure

def clean_text(file_path):
    """
    Ouvre le fichier texte `file_path`, effectue deux opérations :
      1. Retire toutes les occurrences de type [n] (chiffres entre crochets).
      2. Supprime les retours à la ligne sauf si la ligne suivante débute par un chiffre.
         Dans ce dernier cas, on conserve un seul \n.
    Puis réécrit le fichier nettoyé dans file_path.
    """

    # 1. Lire tout le contenu du fichier
    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    # 2. Supprimer les motifs [nombre]
    #    Regex : \[\d+\] => correspond à [123], [4], etc.
    text_content = re.sub(r"\[\d+\]", "", text_content)

    # 3. Gérer les retours à la ligne
    #    - On veut conserver le \n si le caractère suivant est un digit (ex. 12),
    #      et supprimer tous les \n sinon.
    #
    #    Explication de la regex :
    #      \n+(?!\d)
    #      - \n+ : une ou plusieurs fins de ligne
    #      - (?!\d) : si le prochain caractère n'est PAS un chiffre
    #
    #    On remplace cela par "" (pas d'espace) pour coller les lignes.
    text_content = re.sub(r"\n+(?!\d)", "", text_content)

    # 4. Réécrire dans le fichier (en écrasant l’ancien contenu)
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
        # On autorise 0 espace => \s*
        # Ex.  "Jericho.Deutéronome 1"
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


def parse_bible(epub_path, book_id):
    """
    1) Flatten => un fichier .txt
    2) Nettoyer => retire [n], etc.
    3) Parcourt le fichier.
       - Ignore tout avant Genèse 1:1 (ou Genesis 1:1).
       - Stocke (livre, chapitre, verset, texte).
       - S'arrête après Apocalypse 22:21 (ou Revelation 22:21).
    """

    flatten_epub_path = flatten_epub(epub_path)
    clean_text(flatten_epub_path)

    verses = []
    current_book = None
    current_chapter = None

    # Flags pour savoir si on a commencé / fini
    has_started = False
    has_finished = False

    with open(flatten_epub_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 1) Détecter s'il y a un "Livre Chapitre"
            b, c = detect_book_chapter_in_line(line, ALL_BOOKS)
            if b and c:
                current_book = b
                current_chapter = c
                # On continue la boucle pour vérifier si la ligne contient AUSSI un verset
                # => si c'est rare, on peut ignorer. Si c'est fréquent, on peut re-check
                #   la même line, mais passons.

            # 2) Détecter verset => ^(\d+)(.*)
            match_verse = re.match(r'^(\d+)(.*)', line)
            if match_verse:
                verse_num_str = match_verse.group(1)
                verse_text = match_verse.group(2).strip()
                try:
                    verse_num = int(verse_num_str)
                except ValueError:
                    verse_num = None

                if current_book and current_chapter and verse_num is not None:
                    # ----- Vérifier si on doit "start" -----
                    # On démarre la collecte dès qu'on voit (Genèse/Genesis, 1, 1)
                    if not has_started:
                        if (current_book in START_BOOKS) and (current_chapter == 1) and (verse_num == 1):
                            has_started = True
                        else:
                            # Pas encore commencé
                            continue

                    # ----- Vérifier si on doit "stop" -----
                    # On arrête si on voit (Apocalypse/Revelation, 22, 21)
                    if has_started and not has_finished:
                        if (current_book in END_BOOKS) and (current_chapter == 22) and (verse_num == 21):
                            # On ajoute ce dernier verset, puis on arrête
                            verses.append((current_book, current_chapter, verse_num, verse_text))
                            has_finished = True
                            break  # sortir du for

                    # Si on est "en cours"
                    if has_started and not has_finished:
                        verses.append((current_book, current_chapter, verse_num, verse_text))

            # fin du for line

    # Debug ou usage
    print("[INFO] Nombre de versets extraits :", len(verses))
    if verses:
        print("Premier verset:", verses[0])
        print("Dernier verset:", verses[-1])

    return verses



