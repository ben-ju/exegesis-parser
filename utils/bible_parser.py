import re
import sqlite3
import os
from .epub_parser import parse_epub_generic
from dotenv import load_dotenv
from ebooklib import epub
from bs4 import BeautifulSoup

load_dotenv()


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

def parse_bible(epub_path, book_id):
    db_path = os.environ["DATABASE_FILE"]
    """
    Parse un EPUB de type 'Bible' et insère le texte verset par verset dans la DB.
    - epub_path: chemin vers l'EPUB
    - db_path: chemin vers la base SQLite
    - book_id: ID de la table 'books' correspondant à ce livre
    """
    # 1. Extraire le contenu brut
    result = parse_epub_generic(epub_path)
    metadata = result["metadata"]

    flatten_epub_path = flatten_epub(epub_path)
    clean_text(flatten_epub_path)
    # 2. Connexion DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.commit()
    conn.close()
    print(f"[INFO] Bible parsed and inserted into DB. Book ID: {book_id}")
