import sqlite3
import os
from .epub_parser import parse_epub_generic
from dotenv import load_dotenv

load_dotenv()

def parse_introduction(epub_path, book_id):
    db_path = os.environ["DATABASE_FILE"]
    """
    Parse un EPUB de type 'Introduction' : pas de lien spécifique vers des versets,
    insertion en un ou plusieurs blocs dans la table contents.
    """
    result = parse_epub_generic(epub_path)
    sections = result["sections"]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insertion simplifiée : chaque section de l'EPUB => un bloc dans contents
    for section_title, text_content in sections:
        cursor.execute("""
            INSERT INTO contents (book_id, start_verse_id, end_verse_id, text)
            VALUES (?, NULL, NULL, ?)
        """, (book_id, text_content))

    conn.commit()
    conn.close()
    print(f"[INFO] Introduction parsed. Book ID: {book_id}")
