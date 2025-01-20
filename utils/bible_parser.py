import re
import sqlite3
import os
from .epub_parser import parse_epub_generic
from dotenv import load_dotenv

load_dotenv()

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

    # 2. Connexion DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 3. Parcourir chaque section, repérer les références (selon la structure de l’EPUB)
    #    Ici, c'est un exemple simplifié : on suppose qu'il existe des marqueurs "Gen 1:1" ...
    reference_pattern = re.compile(r"([1-3]?\s?[A-Z][a-z]+)\s+(\d+):(\d+)")
    # => Simpliste : repère "Gen 1:1" ou "Col 3:16", etc.

    for section_title, text_content in sections:
        # 4. Découper le contenu par référence (dans la pratique, c'est rarement aussi simple)
        #    Ex: "Gen 1:1 Au commencement ... Gen 1:2 La terre était ..."
        #    Il faudra affiner selon la structure de l'EPUB
        matches = reference_pattern.finditer(text_content)
        # TODO: Logique plus avancée pour segmenter réellement le texte verset par verset

        # Ici, on illustre juste comment on pourrait insérer
        # un bloc correspondant à un verset dans la table contents
        # (start_verse_id = end_verse_id).
        # => Voir comment tu "récupères" chap/vers pour faire le lien sur 'verses.id'

        # Exemple (très simplifié): on suppose qu'on a un chap/vers en cours
        # et on insère un record dans contents. Dans la réalité, tu devras
        # segmenter le texte selon ces matches et lier au bon ID dans 'verses'.
        pass

    conn.commit()
    conn.close()
    print(f"[INFO] Bible parsed and inserted into DB. Book ID: {book_id}")
