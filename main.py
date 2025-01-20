import sys
import os
import sqlite3

# Import du script qui va gérer la mise à jour des ressources
from utils.check_resources_update import parse_directory

def parse_reference(ref_str):
    """
    Convertit 'Colossians 3.16' en (book_name, chapitre, verset).
    Exemples de formats attendus :
      - 'Colossians 3.16'
      - 'Gen 1.1'
    On peut ajuster la logique selon tes besoins (regex, etc.).
    """
    # Séparation (simplifiée) sur l'espace pour livre + la partie chap.verset
    # ex: "Colossians 3.16" => ["Colossians", "3.16"]
    parts = ref_str.split(" ", 1)
    if len(parts) < 2:
        return None, None, None

    book_name = parts[0]
    chap_verse = parts[1]

    # Séparation du chapitre et verset par le point "."
    cv_parts = chap_verse.split(".")
    if len(cv_parts) < 2:
        return book_name, None, None

    try:
        chapter = int(cv_parts[0])
        verse = int(cv_parts[1])
        return book_name, chapter, verse
    except ValueError:
        # Si le parsing échoue, on renvoie None
        return book_name, None, None

def search_contents_for_verse(db_path, book_name, chapter, verse):
    """
    Recherche tout ce qui concerne 'book_name chapter:verse'
    dans la DB.
    - Retrouve d'abord l'ID du livre biblique (bible_books)
    - Puis l'ID du chapitre, l'ID du verset
    - Enfin, récupère tous les contenus (bible, commentaire, intro)
      dont la plage [start_verse_id, end_verse_id] inclut ce verset
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Trouver le livre biblique correspondant au 'book_name'
    #    Ici on suppose que bible_books.title ou abbreviation match "Colossians", "Genèse", etc.
    #    Ajuste selon ta table. On utilise un LIKE pour être souple.
    cursor.execute("""
        SELECT id FROM bible_books
        WHERE title LIKE ? OR abbreviation LIKE ?
        LIMIT 1
    """, (f"%{book_name}%", f"%{book_name}%"))
    row_bible_book = cursor.fetchone()
    if not row_bible_book:
        conn.close()
        return [], f"[WARN] Aucune correspondance pour le livre '{book_name}' dans bible_books."

    bible_book_id = row_bible_book[0]

    # 2. Trouver le chapter_id correspondant
    cursor.execute("""
        SELECT id FROM chapters
        WHERE bible_book_id = ?
          AND number = ?
        LIMIT 1
    """, (bible_book_id, chapter))
    row_chapter = cursor.fetchone()
    if not row_chapter:
        conn.close()
        return [], f"[WARN] Aucune correspondance pour le chapitre {chapter} du livre {book_name}."

    chapter_id = row_chapter[0]

    # 3. Trouver le verse_id
    cursor.execute("""
        SELECT id FROM verses
        WHERE chapter_id = ?
          AND number = ?
        LIMIT 1
    """, (chapter_id, verse))
    row_verse = cursor.fetchone()
    if not row_verse:
        conn.close()
        return [], f"[WARN] Aucune correspondance pour le verset {chapter}.{verse} du livre {book_name}."

    verse_id = row_verse[0]

    # 4. Maintenant, on récupère tous les contenus (table 'contents')
    #    dont la plage [start_verse_id, end_verse_id] inclut verse_id.
    #    start_verse_id <= verse_id <= end_verse_id
    #    On gère aussi le cas où start_verse_id = end_verse_id = verse_id
    #    Ou le cas où start_verse_id ou end_verse_id est NULL => on l’ignore
    #    ou on considère autrement (ex. contenu global). Adaptation selon besoin.
    cursor.execute("""
        SELECT c.id, c.book_id, c.start_verse_id, c.end_verse_id, c.text,
               b.title AS book_title
        FROM contents c
        JOIN books b ON b.id = c.book_id
        WHERE (c.start_verse_id IS NOT NULL AND c.end_verse_id IS NOT NULL
               AND c.start_verse_id <= ?
               AND c.end_verse_id >= ?)
           OR (c.start_verse_id = ? AND c.end_verse_id = ?) -- si les deux identiques
    """, (verse_id, verse_id, verse_id, verse_id))

    results = cursor.fetchall()

    conn.close()

    return results, None

def main():
    # Exemple d’utilisation :
    # python main.py "Colossians 3.16"
    # 1) Lance check_and_update_resources() pour mettre la DB à jour
    # 2) Cherche la référence dans la DB

    if len(sys.argv) < 2:
        print("Usage: python main.py \"Colossians 3.16\"")
        return

    reference_str = sys.argv[1]

    # 1. Lancer la mise à jour des ressources
    parse_directory()
    # 2. Extraire "book_name", "chapitre", "verset" de la référence
    book_name, chapter, verse = parse_reference(reference_str)
    if not book_name or not chapter or not verse:
        print(f"[ERROR] Impossible de parser la référence '{reference_str}' (format attendu: 'BookName X.Y').")
        return

    # 3. Ouvrir la DB et chercher tout ce qui concerne la référence
    db_path = os.path.join("data", "bible_database.db")
    results, warning = search_contents_for_verse(db_path, book_name, chapter, verse)

    if warning:
        print(warning)
    if results:
        for row in results:
            content_id, book_id, start_v, end_v, text, book_title = row
            print("-----")
            print(f"Source Book: {book_title} (ID: {book_id})")
            print(f"Verses Range: {start_v} -> {end_v}")
            print("Content:")
            print(text[:300], "..." if len(text) > 300 else "")  # on affiche les 300 premiers caractères
    else:
        print(f"Aucun contenu trouvé pour {reference_str}.")

if __name__ == "__main__":
    main()
