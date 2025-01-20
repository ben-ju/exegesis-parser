import re
import sqlite3
import os
from .epub_parser import parse_epub_generic
from dotenv import load_dotenv
load_dotenv()

def parse_commentary(epub_path, book_id):
    db_path = os.environ["DATABASE_FILE"]
    """
    Parse un EPUB de type 'Commentaire' et insère les textes par bloc (par plage de versets).
    - epub_path: chemin vers l'EPUB
    - db_path: chemin vers la base SQLite
    - book_id: ID de la table 'books' correspondant au commentaire
    """
    result = parse_epub_generic(epub_path)
    metadata = result["metadata"]
    sections = result["sections"]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Repère ex: "Col 3:16-20" ou "Mat 5:1–12" => \1= "Col" / \2= "3" / \3="16" / \4="20"
    ref_range_pattern = re.compile(r"([1-3]?\s?[A-Z][a-z]+)\s+(\d+):(\d+)(?:–|-)(\d+)")

    for section_title, text_content in sections:
        # Logique : repérer chaque mention de "Col 3:16-20" puis associer le bloc de commentaire qui suit
        matches = ref_range_pattern.finditer(text_content)
        for match in matches:
            # Ex: "Col", "3", "16", "20"
            book_abbrev = match.group(1)
            chap_num = int(match.group(2))
            start_v = int(match.group(3))
            end_v = int(match.group(4))

            # Récupérer l'ID du verset start, l'ID du verset end
            # => Sur base du livre biblique (table bible_books), du chapitre, etc.
            # Ici c'est purement indicatif :
            # 1) Trouver le bible_books.id correspondant à "Col" (ou "Colossiens" dans ta DB)
            # 2) Trouver chapters.id où (bible_book_id=?), number=chap_num
            # 3) Trouver verses.id pour le verset start_v
            # 4) Trouver verses.id pour end_v

            # Ensuite, extraire le "bloc" de commentaire.
            # => Dans la pratique, tu devras parser plus finement
            #    ou décider que tout le paragraphe est rattaché à la plage de versets.

            # Pour l'exemple, on insère juste un record minimal:
            cursor.execute("""
                INSERT INTO contents (book_id, start_verse_id, end_verse_id, text)
                VALUES (?, ?, ?, ?)
            """, (book_id, 999, 1000, f"Commentaire pour {book_abbrev} {chap_num}:{start_v}-{end_v}..."))

    conn.commit()
    conn.close()
    print(f"[INFO] Commentary parsed and inserted into DB. Book ID: {book_id}")
