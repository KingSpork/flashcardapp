# Flashcards App (Tkinter, standard library only).
#
# How to run:
#     python flashcards_app.py
#
# Deck storage:
#     Deck files are stored in a folder named "decks" located next to this script.
#     Each deck is saved as: <topic_name>.json
#
# JSON format:
#     Each deck file contains a JSON object with:
#     {
#         "schema_version": <integer>,
#         "deck_name": "<string>",
#         "cards": [
#             {
#                 "question": "<string>",
#                 "answer": "<string>",
#                 "explanation": "<string, optional>"
#             }
#         ]
#     }

from flashcards.main import main


if __name__ == "__main__":
    main()
