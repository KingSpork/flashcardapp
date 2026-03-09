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

from __future__ import annotations

import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any


class DeckStorage:
    # Manage deck file persistence using JSON files.

    SCHEMA_VERSION = 2

    def __init__(self, base_dir: Path) -> None:
        self.deck_index: dict[str, str] = {}
        self.set_decks_dir(base_dir / "decks")

    def set_decks_dir(self, decks_dir: Path) -> None:
        self.decks_dir = decks_dir
        self.decks_dir.mkdir(parents=True, exist_ok=True)
        self._load_deck_index()

    def _normalize_topic_name(self, topic_name: str) -> str:
        normalized = topic_name.strip()
        if normalized.lower().endswith(".json"):
            normalized = normalized[:-5]
        return normalized

    def _sanitize_topic_name_for_filename(self, topic_name: str) -> str:
        invalid_chars = set('<>:"/\\|?*')
        sanitized = ''.join(character for character in topic_name.strip() if character not in invalid_chars and ord(character) >= 32)
        sanitized = sanitized.strip().strip('.')
        return sanitized or 'deck'

    def _load_deck_index(self) -> None:
        self.deck_index = {}
        for path in sorted(self.decks_dir.glob('*.json')):
            if not path.is_file():
                continue
            stem = path.stem
            deck_name = stem
            try:
                with path.open('r', encoding='utf-8') as file:
                    data: Any = json.load(file)
                if isinstance(data, dict):
                    maybe_name = data.get('deck_name')
                    if isinstance(maybe_name, str) and maybe_name.strip():
                        deck_name = maybe_name.strip()
            except (OSError, json.JSONDecodeError, ValueError):
                deck_name = stem
            self.deck_index[stem] = deck_name

    def list_deck_entries(self) -> list[tuple[str, str]]:
        # Return deck entries as (deck_id, display_name), sorted by display name.
        return sorted(self.deck_index.items(), key=lambda item: item[1].lower())

    def refresh_decks(self) -> None:
        # Reload deck metadata from disk.
        self._load_deck_index()

    def _deck_path(self, deck_id: str) -> Path:
        normalized_topic = self._normalize_topic_name(deck_id)
        return self.decks_dir / f"{normalized_topic}.json"

    def _ensure_unique_deck_id(self, deck_name: str, existing_deck_id: str | None = None) -> str:
        candidate = self._sanitize_topic_name_for_filename(deck_name)
        while True:
            path = self._deck_path(candidate)
            if not path.exists() or candidate == existing_deck_id:
                return candidate
            candidate += '_'

    def find_deck_id_by_name(self, deck_name: str) -> str | None:
        normalized_name = deck_name.strip()
        for deck_id, display_name in self.deck_index.items():
            if display_name == normalized_name:
                return deck_id
        return None

    def load_deck(self, deck_id: str) -> list[dict[str, str]]:
        # Load and validate a deck's cards.
        deck_path = self._deck_path(deck_id)
        if not deck_path.exists():
            return []

        with deck_path.open('r', encoding='utf-8') as file:
            data: Any = json.load(file)

        if isinstance(data, list):
            raw_cards = data
        elif isinstance(data, dict):
            schema_version = data.get('schema_version')
            if schema_version not in {1, self.SCHEMA_VERSION}:
                raise ValueError(
                    f"Unsupported deck schema_version: {schema_version}. "
                    f"Expected 1 or {self.SCHEMA_VERSION}."
                )
            raw_cards = data.get('cards')
            if not isinstance(raw_cards, list):
                raise ValueError("Deck JSON field 'cards' must be a list.")
        else:
            raise ValueError("Deck JSON must be an object with deck metadata and cards.")

        cards: list[dict[str, str]] = []
        for item in raw_cards:
            if not isinstance(item, dict):
                raise ValueError('Each card must be an object.')
            allowed_keys = {'question', 'answer', 'explanation'}
            if not {'question', 'answer'}.issubset(item.keys()) or not set(item.keys()).issubset(allowed_keys):
                raise ValueError("Each card must contain 'question' and 'answer', with optional 'explanation'.")
            question = item.get('question')
            answer = item.get('answer')
            explanation = item.get('explanation', '')
            if not isinstance(question, str) or not isinstance(answer, str):
                raise ValueError('Card question and answer must be strings.')
            if not isinstance(explanation, str):
                raise ValueError('Card explanation must be a string when provided.')
            cards.append({'question': question, 'answer': answer, 'explanation': explanation})

        return cards

    def _write_deck(self, deck_id: str, deck_name: str, cards: list[dict[str, str]]) -> None:
        deck_path = self._deck_path(deck_id)
        with deck_path.open('w', encoding='utf-8') as file:
            json.dump(
                {'schema_version': self.SCHEMA_VERSION, 'deck_name': deck_name, 'cards': cards},
                file,
                ensure_ascii=False,
                indent=2,
            )

    def append_card(self, deck_name: str, question: str, answer: str, explanation: str = '') -> str:
        # Append a card to a deck, creating a new file when deck name is new.
        normalized_name = deck_name.strip()
        if not normalized_name:
            raise ValueError('Deck name cannot be empty.')

        deck_id = self.find_deck_id_by_name(normalized_name)
        if deck_id is None:
            deck_id = self._ensure_unique_deck_id(normalized_name)
            cards: list[dict[str, str]] = []
        else:
            cards = self.load_deck(deck_id)

        cards.append({'question': question, 'answer': answer, 'explanation': explanation})
        self._write_deck(deck_id, normalized_name, cards)
        self.deck_index[deck_id] = normalized_name
        return normalized_name

    def rename_deck(self, deck_id: str, new_name: str) -> tuple[str, str]:
        # Rename a deck display name and update filename based on sanitized deck name.
        current_path = self._deck_path(deck_id)
        if not current_path.exists():
            raise FileNotFoundError(f"Deck '{deck_id}' was not found.")

        normalized_name = new_name.strip()
        if not normalized_name:
            raise ValueError('Deck name cannot be empty.')

        cards = self.load_deck(deck_id)
        new_deck_id = self._ensure_unique_deck_id(normalized_name, existing_deck_id=deck_id)
        self._write_deck(new_deck_id, normalized_name, cards)

        if new_deck_id != deck_id and current_path.exists():
            current_path.unlink()
            self.deck_index.pop(deck_id, None)

        self.deck_index[new_deck_id] = normalized_name
        return new_deck_id, normalized_name


class FlashcardApp:
    # Main Tkinter app for creating and studying flashcards.

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Flashcard App")
        self.root.geometry("760x500")
        self.root.minsize(680, 420)

        self.storage = DeckStorage(Path(__file__).resolve().parent)

        self.main_frame = ttk.Frame(self.root, padding=18)
        self.main_frame.pack(fill="both", expand=True)

        self.current_cards: list[dict[str, str]] = []
        self.current_index = 0
        self.showing_answer = False

        self._build_styles()
        self.show_main_menu()

    def _build_styles(self) -> None:
        # Configure basic widget styles.
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("CardText.TLabel", font=("Segoe UI", 16), padding=16)
        style.configure("QuestionTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground="#cc0000")
        style.configure("AnswerTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground="#228b22")
        style.configure("ExplanationTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground="#b8860b")

    def _clear_main_frame(self) -> None:
        for child in self.main_frame.winfo_children():
            child.destroy()

    def show_main_menu(self) -> None:
        # Render the main menu screen.
        self._clear_main_frame()

        container = ttk.Frame(self.main_frame)
        container.pack(expand=True)

        ttk.Label(container, text="Flashcard App", style="Title.TLabel").pack(pady=(0, 24))
        ttk.Label(container, text=f"Decks folder: {self.storage.decks_dir}", wraplength=640).pack(pady=(0, 12))
        ttk.Button(container, text="Create Cards", command=self.show_create_cards_screen, width=24).pack(pady=8)
        ttk.Button(container, text="Study", command=self.show_study_selection_screen, width=24).pack(pady=8)
        ttk.Button(container, text="Change Decks Folder", command=self.change_decks_folder, width=24).pack(pady=8)
        ttk.Button(container, text="Exit", command=self.root.destroy, width=24).pack(pady=8)

    def change_decks_folder(self) -> None:
        # Allow the user to choose a different folder for deck files.
        selected_dir = filedialog.askdirectory(
            title="Choose Decks Folder",
            initialdir=str(self.storage.decks_dir),
            mustexist=True,
        )
        if not selected_dir:
            return

        try:
            self.storage.set_decks_dir(Path(selected_dir))
        except OSError as exc:
            messagebox.showerror("Folder Error", f"Could not use selected folder:\n{exc}")
            return

        messagebox.showinfo("Decks Folder Updated", f"Deck files will now be stored in:\n{self.storage.decks_dir}")
        self.show_main_menu()

    def show_create_cards_screen(self) -> None:
        # Render the create-cards screen.
        self._clear_main_frame()

        ttk.Label(self.main_frame, text="Create Cards", style="Title.TLabel").pack(pady=(0, 18))

        form = ttk.Frame(self.main_frame, padding=8)
        form.pack(fill="x", padx=50)

        ttk.Label(form, text="Topic Name:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        topic_var = tk.StringVar()
        question_var = tk.StringVar()
        answer_var = tk.StringVar()
        explanation_var = tk.StringVar()

        topic_entry = ttk.Entry(form, textvariable=topic_var, width=60)
        topic_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Question:", style="Header.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        question_entry = ttk.Entry(form, textvariable=question_var, width=60)
        question_entry.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Answer:", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        answer_entry = ttk.Entry(form, textvariable=answer_var, width=60)
        answer_entry.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Explanation (optional):", style="Header.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        explanation_entry = ttk.Entry(form, textvariable=explanation_var, width=60)
        explanation_entry.grid(row=3, column=1, sticky="ew", pady=6)

        form.columnconfigure(1, weight=1)

        def save_card() -> None:
            topic = topic_var.get().strip()
            question = question_var.get().strip()
            answer = answer_var.get().strip()
            explanation = explanation_var.get().strip()

            if not topic:
                messagebox.showwarning("Missing Topic", "Please enter a topic name.")
                return
            if not question:
                messagebox.showwarning("Missing Question", "Please enter a question.")
                return
            if not answer:
                messagebox.showwarning("Missing Answer", "Please enter an answer.")
                return

            try:
                saved_deck_name = self.storage.append_card(deck_name=topic, question=question, answer=answer, explanation=explanation)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                messagebox.showerror("Save Error", f"Could not save card:\n{exc}")
                return

            question_var.set("")
            answer_var.set("")
            explanation_var.set("")
            question_entry.focus_set()
            messagebox.showinfo("Saved", f"Card saved to deck '{saved_deck_name}'.")

        buttons = ttk.Frame(self.main_frame)
        buttons.pack(pady=20)

        ttk.Button(buttons, text="Save Card", command=save_card, width=18).pack(side="left", padx=8)
        ttk.Button(buttons, text="Back to Menu", command=self.show_main_menu, width=18).pack(side="left", padx=8)

        topic_entry.focus_set()

    def show_study_selection_screen(self) -> None:
        # Render deck selection for study mode.
        self._clear_main_frame()

        ttk.Label(self.main_frame, text="Study", style="Title.TLabel").pack(pady=(0, 16))

        deck_entries = self.storage.list_deck_entries()

        frame = ttk.Frame(self.main_frame, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select one or more decks:", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        listbox = tk.Listbox(frame, height=12, selectmode=tk.EXTENDED)
        listbox.pack(fill="both", expand=True, pady=(0, 10))

        for deck_id, deck_name in deck_entries:
            listbox.insert(tk.END, deck_name)

        if deck_entries:
            listbox.selection_set(0)

        def start_study() -> None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Deck Selected", "Please select a deck to study.")
                return
            selected_decks = [deck_entries[index] for index in selection]
            self._load_study_decks(selected_decks)

        def rename_deck() -> None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Deck Selected", "Please select a deck to rename.")
                return

            selected_deck_id, selected_deck_name = deck_entries[selection[0]]
            renamed_deck = simpledialog.askstring(
                "Rename Deck",
                "Enter a new name for the selected deck:",
                initialvalue=selected_deck_name,
                parent=self.root,
            )
            if renamed_deck is None:
                return

            renamed_deck = renamed_deck.strip()
            if not renamed_deck:
                messagebox.showwarning("Invalid Name", "Deck name cannot be empty.")
                return

            try:
                _, final_deck_name = self.storage.rename_deck(selected_deck_id, renamed_deck)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Rename Error", f"Could not rename deck:\n{exc}")
                return

            messagebox.showinfo("Deck Renamed", f"Deck '{selected_deck_name}' was renamed to '{final_deck_name}'.")
            self.show_study_selection_screen()

        def reload_decks() -> None:
            self.storage.refresh_decks()
            self.show_study_selection_screen()

        controls = ttk.Frame(frame)
        controls.pack()

        ttk.Button(controls, text="Start Study", command=start_study, width=18).pack(side="left", padx=8)
        ttk.Button(controls, text="Rename Deck", command=rename_deck, width=18).pack(side="left", padx=8)
        ttk.Button(controls, text="Reload Decks", command=reload_decks, width=18).pack(side="left", padx=8)
        ttk.Button(controls, text="Back to Menu", command=self.show_main_menu, width=18).pack(side="left", padx=8)

        ttk.Label(
            self.main_frame,
            text=f"App schema version: {self.storage.SCHEMA_VERSION}",
            font=("Segoe UI", 9),
        ).pack(anchor="se", pady=(8, 0))

        if not deck_entries:
            messagebox.showinfo("No Decks", "No decks found. Create cards first.")

    def _load_study_decks(self, selected_decks: list[tuple[str, str]]) -> None:
        # Load selected decks and open the study screen.
        combined_cards: list[dict[str, str]] = []
        for deck_id, deck_name in selected_decks:
            try:
                cards = self.storage.load_deck(deck_id)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                messagebox.showerror("Load Error", f"Could not load deck '{deck_name}':\n{exc}")
                return
            combined_cards.extend(
                {
                    "question": card["question"],
                    "answer": card["answer"],
                    "explanation": card.get("explanation", ""),
                    "topic_name": deck_name,
                }
                for card in cards
            )

        self.current_cards = combined_cards
        self.current_index = 0
        self.showing_answer = False

        if not self.current_cards:
            messagebox.showwarning("Empty Selection", "The selected decks do not contain any cards.")
            return

        study_label = selected_decks[0][1] if len(selected_decks) == 1 else ""
        self.show_study_screen(study_label)

    def show_study_screen(self, topic_name: str) -> None:
        # Render flashcard study controls and card display.
        self._clear_main_frame()

        self.study_title_label = ttk.Label(self.main_frame, text=f"Studying: {topic_name}", style="Title.TLabel")
        self.study_title_label.pack(pady=(0, 14))

        self.card_position_label = ttk.Label(self.main_frame, text="", style="Header.TLabel")
        self.card_position_label.pack(pady=(0, 8))

        card_frame = ttk.Frame(self.main_frame, relief="solid", borderwidth=1)
        card_frame.pack(fill="both", expand=True, padx=30, pady=8)

        self.card_content_frame = ttk.Frame(card_frame, padding=16)
        self.card_content_frame.pack(fill="both", expand=True)

        self.card_title_label = ttk.Label(
            self.card_content_frame,
            text="",
            style="QuestionTitle.TLabel",
            anchor="center",
            justify="center",
            wraplength=640,
        )
        self.card_title_label.pack(fill="x", pady=(0, 8))

        self.card_body_label = ttk.Label(
            self.card_content_frame,
            text="",
            style="CardText.TLabel",
            anchor="center",
            justify="center",
            wraplength=640,
        )
        self.card_body_label.pack(fill="both", expand=True)

        self.card_explanation_title_label = ttk.Label(
            self.card_content_frame,
            text="",
            style="ExplanationTitle.TLabel",
            anchor="center",
            justify="center",
            wraplength=640,
        )

        self.card_explanation_body_label = ttk.Label(
            self.card_content_frame,
            text="",
            style="CardText.TLabel",
            anchor="center",
            justify="center",
            wraplength=640,
        )

        controls = ttk.Frame(self.main_frame)
        controls.pack(pady=12)

        top_controls = ttk.Frame(controls)
        top_controls.pack(pady=(0, 8))
        ttk.Button(top_controls, text="Flip", command=self._flip_card, width=12).pack()

        bottom_controls = ttk.Frame(controls)
        bottom_controls.pack()
        ttk.Button(bottom_controls, text="Back to Menu", command=self.show_main_menu, width=12).pack(side="left", padx=6)
        ttk.Button(bottom_controls, text="Previous", command=self._previous_card, width=12).pack(side="left", padx=6)
        ttk.Button(bottom_controls, text="Next", command=self._next_card, width=12).pack(side="left", padx=6)
        ttk.Button(bottom_controls, text="Random", command=self._random_card, width=12).pack(side="left", padx=6)

        self._refresh_card_display()

    def _refresh_card_display(self) -> None:
        # Update labels to display current card state.
        if not self.current_cards:
            self.card_title_label.config(text="")
            self.card_body_label.config(text="No cards to display.")
            self.card_explanation_title_label.pack_forget()
            self.card_explanation_body_label.pack_forget()
            self.card_position_label.config(text="")
            return

        card = self.current_cards[self.current_index]
        self.study_title_label.config(text=f"Studying: {card.get('topic_name', '')}")
        explanation = card.get("explanation", "").strip()

        if self.showing_answer:
            side = "Answer"
            body_text = card["answer"]
            side_style = "AnswerTitle.TLabel"
        else:
            side = "Question"
            body_text = card["question"]
            side_style = "QuestionTitle.TLabel"

        self.card_title_label.config(text=f"{side}:", style=side_style)
        self.card_body_label.config(text=body_text)

        if self.showing_answer and explanation:
            self.card_explanation_title_label.config(text="Explanation:")
            self.card_explanation_title_label.pack(fill="x", pady=(12, 8))
            self.card_explanation_body_label.config(text=explanation)
            self.card_explanation_body_label.pack(fill="both", expand=True)
        else:
            self.card_explanation_title_label.pack_forget()
            self.card_explanation_body_label.pack_forget()

        total = len(self.current_cards)
        self.card_position_label.config(text=f"Card {self.current_index + 1} of {total}")

    def _flip_card(self) -> None:
        # Toggle current card between question and answer.
        if not self.current_cards:
            return
        self.showing_answer = not self.showing_answer
        self._refresh_card_display()

    def _next_card(self) -> None:
        # Move to the next card with wrap-around.
        if not self.current_cards:
            return
        self.current_index = (self.current_index + 1) % len(self.current_cards)
        self.showing_answer = False
        self._refresh_card_display()

    def _previous_card(self) -> None:
        # Move to the previous card with wrap-around.
        if not self.current_cards:
            return
        self.current_index = (self.current_index - 1) % len(self.current_cards)
        self.showing_answer = False
        self._refresh_card_display()

    def _random_card(self) -> None:
        # Jump to a random card and show its question.
        if not self.current_cards:
            return
        if len(self.current_cards) == 1:
            self.current_index = 0
        else:
            available_indices = [index for index in range(len(self.current_cards)) if index != self.current_index]
            self.current_index = random.choice(available_indices)
        self.showing_answer = False
        self._refresh_card_display()


def main() -> None:
    # Run the flashcard desktop application.
    root = tk.Tk()
    FlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
