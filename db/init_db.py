
import sqlite3

def init_db(db_path="db/database.db"):
    """Initialise la base de données SQLite avec le schéma défini."""
    # Connexion à la base de données SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Création des tables
    cursor.executescript("""
    -- Table Category
    CREATE TABLE IF NOT EXISTS category (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        title         TEXT    NOT NULL,
        desc          TEXT,
        abbreviation  TEXT
    );

    -- Table bible_books
    CREATE TABLE IF NOT EXISTS bible_books (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        title               TEXT NOT NULL,
        abbreviation        TEXT NOT NULL,
        is_deuterocanonical BOOLEAN DEFAULT 0,
        is_old_testament    BOOLEAN DEFAULT 0,
        is_new_testament    BOOLEAN DEFAULT 0
    );

    -- Table books
    CREATE TABLE IF NOT EXISTS books (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        abbreviation TEXT,
        language     TEXT,
        authors      TEXT,
        cover        TEXT,
        category_id  INTEGER,
        FOREIGN KEY (category_id) REFERENCES category(id)
    );

    -- Table chapters
    CREATE TABLE IF NOT EXISTS chapters (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        bible_book_id   INTEGER NOT NULL,
        number          INTEGER NOT NULL,
        is_ambiguous    BOOLEAN DEFAULT 0,
        FOREIGN KEY (bible_book_id) REFERENCES bible_books(id)
    );

    -- Table verses
    CREATE TABLE IF NOT EXISTS verses (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_id   INTEGER NOT NULL,
        number       INTEGER NOT NULL,
        is_ambiguous BOOLEAN DEFAULT 0,
        FOREIGN KEY (chapter_id) REFERENCES chapters(id)
    );

    -- Table contents
    CREATE TABLE IF NOT EXISTS contents (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id        INTEGER NOT NULL,
        start_verse_id INTEGER,
        end_verse_id   INTEGER,
        text           TEXT,
        FOREIGN KEY (book_id)        REFERENCES books(id),
        FOREIGN KEY (start_verse_id) REFERENCES verses(id),
        FOREIGN KEY (end_verse_id)   REFERENCES verses(id)
    );
    """)

    # Insertion des données de base
    cursor.executemany("""
    INSERT INTO category (title, desc, abbreviation) VALUES (?, ?, ?);
    """, [
        ("Bible", "Texte biblique", "BIB"),
        ("Commentaire", "Commentaires sur les livres bibliques", "COM"),
        ("Introduction", "Présentation générale ou préface", "INTRO")
    ])

    cursor.executemany("""
    INSERT INTO bible_books (title, abbreviation, is_old_testament, is_new_testament) VALUES (?, ?, ?, ?);
    """, [
        ("Genèse", "Gen", 1, 0),
        ("Exode", "Ex", 1, 0),
        ("Matthieu", "Mt", 0, 1)
    ])

    # Exemple d'insertion de livres
    cursor.executemany("""
    INSERT INTO books (title, abbreviation, language, authors, cover, category_id) VALUES (?, ?, ?, ?, ?, ?);
    """, [
        ("Treaduction Oecuménique de la Bible", "TOB", "fr", "Coll. Oecuménique", "genese_cover.jpg", 1),
        ("Commentaire sur Genèse", "Com-Gen", "fr", "Auteur X", None, 2),
        ("Introduction au NT", "Intro-NT", "fr", "Auteur Y", None, 3)
    ])

    # Exemple d'insertion de chapitres pour Genèse
    cursor.executemany("""
    INSERT INTO chapters (bible_book_id, number) VALUES (?, ?);
    """, [
        (1, 1),
        (1, 2),
        (1, 3)
    ])

    # Exemple d'insertion de versets pour Genèse chapitre 1
    cursor.executemany("""
    INSERT INTO verses (chapter_id, number) VALUES (?, ?);
    """, [
        (1, 1),
        (1, 2),
        (1, 3)
    ])

    # Exemple d'insertion de contenu
    cursor.executemany("""
    INSERT INTO contents (book_id, start_verse_id, end_verse_id, text) VALUES (?, ?, ?, ?);
    """, [
        (1, 1, 1, "Au commencement, Dieu créa le ciel et la terre..."),  # Bible TOB - Genèse 1:1
        (2, 1, 3, "Commentaire sur Genèse 1:1 à 1:3..."),  # Commentaire sur Genèse
        (3, None, None, "Introduction au NT : contexte historique, auteurs...")  # Introduction
    ])

    # Valider les changements et fermer la connexion
    conn.commit()
    conn.close()
    print(f"Base de données initialisée avec succès dans {db_path}")

if __name__ == "__main__":
    init_db()
