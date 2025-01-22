from enums.books import BOOKS_EN, BOOKS_FR
def test_book_coverage(test_verses):
    """Test l'exhaustivité des livres détectés selon la langue choisie"""
    # Sélection de la langue
    lang = input("Choisir la langue [fr/en] (défaut=en): ").strip().lower() or 'en'
    book_list = BOOKS_EN if lang == 'en' else BOOKS_FR
    start_books = ["Genesis", "Genèse"] if lang == 'en' else ["Genèse"]
    end_books = ["Revelation", "Apocalypse"] if lang == 'en' else ["Apocalypse"]


    # Collecte des livres détectés
    detected_books = {v[0] for v in test_verses}

    # Vérification du début et fin
    first_book = test_verses[0][0] if test_verses else None
    last_book = test_verses[-1][0] if test_verses else None

    # Analyse des résultats
    missing_books = set(book_list) - detected_books
    valid_start = first_book in start_books
    valid_end = last_book in end_books

    # Affichage des résultats
    print(f"\n=== TEST COMPLET ({lang.upper()}) ===")
    print(f"Livres détectés ({len(detected_books)}/{len(book_list)}) :")
    print(", ".join(sorted(detected_books)))

    print(f"\nLivres manquants ({len(missing_books)}) :")
    if missing_books:
        print("⚠️ " + ", ".join(sorted(missing_books)))
    else:
        print("✅ Aucun livre manquant !")

    print(f"\nValidation du début : {'✅' if valid_start else '❌'} {first_book}")
    print(f"Validation de la fin : {'✅' if valid_end else '❌'} {last_book}")

    # Assertions pour test unitaire
    assert len(missing_books) == 0, f"Livres manquants : {missing_books}"
    assert valid_start, f"Livre de début invalide : {first_book}"
    assert valid_end, f"Livre de fin invalide : {last_book}"

if __name__ == "__main__":
    test_book_coverage()
