import os
import sqlite3
from utils.epub_parser import parse_epub_generic
from utils.bible_parser import parse_bible
from utils.commentary_parser import parse_commentary
from utils.introduction_parser import parse_introduction
from dotenv import load_dotenv
import warnings

# Ignorer les UserWarnings spécifiques d'ebooklib
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib.epub")

# Ignorer les FutureWarnings spécifiques d'ebooklib
warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib.epub")

# Ignorer les warnings XML/HTML de BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module="html.parser")

def parse_directory():

    load_dotenv()
    db_path = os.environ["DATABASE_FILE"]
    directory_path = os.environ["RESOURCES_PATH"]
    """
    Boucle sur tous les EPUB de 'directory_path'.
    Si le livre n'existe pas déjà dans la DB, on l'insère et on parse le fichier.
    """
    # Connexion DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Récupérer la liste des fichiers EPUB
    epub_files = [f for f in os.listdir(directory_path) if f.lower().endswith(".epub")]

    for filename in epub_files:
        epub_path = os.path.join(directory_path, filename)
        print(f"[INFO] Found EPUB: {epub_path}")

        # 2. On peut extraire des infos de base (titre, auteur...) via parse_epub_generic
        #    juste pour check la présence en DB
        result = parse_epub_generic(epub_path)
        metadata = result.get("metadata", {})
        epub_title = metadata.get("title") or filename  # Si l'EPUB n'a pas de titre, fallback sur filename
        author = metadata.get("authors") or "unknown"  # Si l'EPUB n'a pas de titre, fallback sur filename
        epub_title = next(iter(epub_title), (None,))[0]
        author = next(iter(author), (None,))[0]
            # 3. Vérifier si le titre existe dans la base
        cursor.execute("SELECT id FROM books WHERE title = ?", (epub_title,))
        row = cursor.fetchone()

        if row:
            # Livre déjà existant
            print(f"[INFO] Book '{epub_title}' already in DB (id={row[0]}). Skipping parse.")
        else:
            print(f"[INFO] Book '{epub_title}' not found in DB. Parsing & inserting.")

            # 4. Déterminer la catégorie (ex. via un paramètre, un champ metadata,
            #    ou un prompt à l'utilisateur)
            #    Ci-dessous, on suppose un prompt (très simplifié) :
            cat_input = input(f"Catégorie pour '{epub_title}'? (bible/commentary/intro/skip) : ").strip().lower()

            if cat_input == "skip":
                print("[INFO] Skipped by user request.")
                continue

            # 5. Insérer le nouveau livre dans la table 'books'
            #    Il faudra associer un category_id en fonction de la catégorie
            category_id = get_category_id(cursor, cat_input)
            cursor.execute(
                """INSERT INTO books (title, abbreviation, language, authors, cover, category_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    epub_title,
                    metadata.get("abbreviation"),
                    metadata.get("language", "unknown"),
                    author,
                    None,  # cover
                    category_id
                )
            )
            new_book_id = cursor.lastrowid
            # TODO REMOVE COMMENT TO ADD BOOK
            # conn.commit()

            # 6. Appeler le parseur adapté
            if cat_input == "bible":
                parse_bible(epub_path, new_book_id)
            elif cat_input == "commentary":
                parse_commentary(epub_path, new_book_id)
            elif cat_input == "intro":
                parse_introduction(epub_path, new_book_id)
            else:
                print("[WARN] Unknown category. Skipping parser.")

    conn.close()
    print("[INFO] Finished parsing directory.")

def get_category_id(cursor, cat_input):
    """
    Récupère l'id de la table category pour 'bible', 'commentary', etc.
    À adapter selon ta table category.
    """
    cat_mapping = {
        "bible": "Bible",
        "commentary": "Commentaire",
        "intro": "Introduction",
    }
    cat_title = cat_mapping.get(cat_input, None)
    if cat_title is None:
        return None

    cursor.execute("SELECT id FROM category WHERE title = ?", (cat_title,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None


