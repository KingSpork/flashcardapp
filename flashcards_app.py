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
#     Each deck file contains a JSON list of flashcard objects with:
#     {
#         "question": "<string>",
#         "answer": "<string>",
#         "explanation": "<string, optional>"
#     }

from __future__ import annotations

import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any


class DeckStorage:
    # Manage deck file persistence using JSON files.

    def __init__(self, base_dir: Path) -> None:
        self.set_decks_dir(base_dir / "decks")

    def set_decks_dir(self, decks_dir: Path) -> None:
        self.decks_dir = decks_dir
        self.decks_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_topic_name(self, topic_name: str) -> str:
        normalized = topic_name.strip()
        if normalized.lower().endswith(".json"):
            normalized = normalized[:-5]
        return normalized

    def list_decks(self) -> list[str]:
        # Return deck names (without .json extension), sorted alphabetically.
        return sorted(path.stem for path in self.decks_dir.glob("*.json") if path.is_file())

    def _deck_path(self, topic_name: str) -> Path:
        normalized_topic = self._normalize_topic_name(topic_name)
        return self.decks_dir / f"{normalized_topic}.json"

    def load_deck(self, topic_name: str) -> list[dict[str, str]]:
        # Load and validate a deck's cards.
        # Returns an empty list when file does not exist.
        # Raises OSError/ValueError on file/read/format errors.
        deck_path = self._deck_path(topic_name)
        if not deck_path.exists():
            return []

        with deck_path.open("r", encoding="utf-8") as file:
            data: Any = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Deck JSON must be a list.")

        cards: list[dict[str, str]] = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each card must be an object.")
            allowed_keys = {"question", "answer", "explanation"}
            if not {"question", "answer"}.issubset(item.keys()) or not set(item.keys()).issubset(allowed_keys):
                raise ValueError("Each card must contain 'question' and 'answer', with optional 'explanation'.")
            question = item.get("question")
            answer = item.get("answer")
            explanation = item.get("explanation", "")
            if not isinstance(question, str) or not isinstance(answer, str):
                raise ValueError("Card question and answer must be strings.")
            if not isinstance(explanation, str):
                raise ValueError("Card explanation must be a string when provided.")
            cards.append({"question": question, "answer": answer, "explanation": explanation})

        return cards

    def append_card(self, topic_name: str, question: str, answer: str, explanation: str = "") -> None:
        # Append a card to a deck file, creating the file if needed.
        cards = self.load_deck(topic_name)
        cards.append({"question": question, "answer": answer, "explanation": explanation})
        deck_path = self._deck_path(topic_name)
        with deck_path.open("w", encoding="utf-8") as file:
            json.dump(cards, file, ensure_ascii=False, indent=2)


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
                self.storage.append_card(topic_name=topic, question=question, answer=answer, explanation=explanation)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                messagebox.showerror("Save Error", f"Could not save card:\n{exc}")
                return

            question_var.set("")
            answer_var.set("")
            explanation_var.set("")
            question_entry.focus_set()
            messagebox.showinfo("Saved", f"Card saved to deck '{topic}'.")

        buttons = ttk.Frame(self.main_frame)
        buttons.pack(pady=20)

        ttk.Button(buttons, text="Save Card", command=save_card, width=18).pack(side="left", padx=8)
        ttk.Button(buttons, text="Back to Menu", command=self.show_main_menu, width=18).pack(side="left", padx=8)

        topic_entry.focus_set()

    def show_study_selection_screen(self) -> None:
        # Render deck selection for study mode.
        self._clear_main_frame()

        ttk.Label(self.main_frame, text="Study", style="Title.TLabel").pack(pady=(0, 16))

        deck_names = self.storage.list_decks()

        frame = ttk.Frame(self.main_frame, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select a Deck:", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        listbox = tk.Listbox(frame, height=12)
        listbox.pack(fill="both", expand=True, pady=(0, 10))

        for name in deck_names:
            listbox.insert(tk.END, name)

        if deck_names:
            listbox.selection_set(0)

        def start_study() -> None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Deck Selected", "Please select a deck to study.")
                return
            selected_deck = listbox.get(selection[0])
            self._load_study_deck(selected_deck)

        controls = ttk.Frame(frame)
        controls.pack()

        ttk.Button(controls, text="Start Study", command=start_study, width=18).pack(side="left", padx=8)
        ttk.Button(controls, text="Back to Menu", command=self.show_main_menu, width=18).pack(side="left", padx=8)

        if not deck_names:
            messagebox.showinfo("No Decks", "No decks found. Create cards first.")

    def _load_study_deck(self, topic_name: str) -> None:
        # Load selected deck and open the study screen.
        try:
            cards = self.storage.load_deck(topic_name)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Load Error", f"Could not load deck:\n{exc}")
            return

        self.current_cards = cards
        self.current_index = 0
        self.showing_answer = False

        if not self.current_cards:
            messagebox.showwarning("Empty Deck", f"Deck '{topic_name}' is empty.")
            return

        self.show_study_screen(topic_name)

    def show_study_screen(self, topic_name: str) -> None:
        # Render flashcard study controls and card display.
        self._clear_main_frame()

        ttk.Label(self.main_frame, text=f"Studying: {topic_name}", style="Title.TLabel").pack(pady=(0, 14))

        self.card_position_label = ttk.Label(self.main_frame, text="", style="Header.TLabel")
        self.card_position_label.pack(pady=(0, 8))

        card_frame = ttk.Frame(self.main_frame, relief="solid", borderwidth=1)
        card_frame.pack(fill="both", expand=True, padx=30, pady=8)

        self.card_text_label = ttk.Label(
            card_frame,
            text="",
            style="CardText.TLabel",
            anchor="center",
            justify="center",
            wraplength=640,
        )
        self.card_text_label.pack(fill="both", expand=True)

        controls = ttk.Frame(self.main_frame)
        controls.pack(pady=12)

        ttk.Button(controls, text="Flip", command=self._flip_card, width=12).pack(side="left", padx=6)
        ttk.Button(controls, text="Previous", command=self._previous_card, width=12).pack(side="left", padx=6)
        ttk.Button(controls, text="Next", command=self._next_card, width=12).pack(side="left", padx=6)
        ttk.Button(controls, text="Random", command=self._random_card, width=12).pack(side="left", padx=6)
        ttk.Button(controls, text="Back to Menu", command=self.show_main_menu, width=12).pack(side="left", padx=6)

        self._refresh_card_display()

    def _refresh_card_display(self) -> None:
        # Update labels to display current card state.
        if not self.current_cards:
            self.card_text_label.config(text="No cards to display.")
            self.card_position_label.config(text="")
            return

        card = self.current_cards[self.current_index]
        if self.showing_answer:
            explanation = card.get("explanation", "").strip()
            text = card["answer"]
            if explanation:
                text = f"{text}\n\nExplanation:\n{explanation}"
        else:
            text = card["question"]
        side = "Answer" if self.showing_answer else "Question"
        total = len(self.current_cards)
        self.card_text_label.config(text=f"{side}:\n\n{text}")
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
