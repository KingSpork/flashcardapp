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
        self.outdated_deck_ids: set[str] = set()
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
        self.outdated_deck_ids = set()
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
                    schema_version = data.get('schema_version')
                    if isinstance(schema_version, int) and schema_version < self.SCHEMA_VERSION:
                        self.outdated_deck_ids.add(stem)
            except (OSError, json.JSONDecodeError, ValueError):
                deck_name = stem
            self.deck_index[stem] = deck_name

    def list_deck_entries(self) -> list[tuple[str, str]]:
        # Return deck entries as (deck_id, display_name), sorted by display name.
        return sorted(self.deck_index.items(), key=lambda item: item[1].lower())

    def is_outdated_schema(self, deck_id: str) -> bool:
        # Return True when a deck file declares an older schema version than the app supports.
        return deck_id in self.outdated_deck_ids

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

    def save_deck_cards(self, deck_id: str, cards: list[dict[str, str]]) -> str:
        # Replace all cards in a deck with provided cards.
        if deck_id not in self.deck_index:
            raise FileNotFoundError(f"Deck '{deck_id}' was not found.")

        deck_name = self.deck_index[deck_id]
        self._write_deck(deck_id, deck_name, cards)
        return deck_name

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

    LIGHT_THEME = {
        "window_bg": "#f7f7f7",
        "surface_bg": "#ffffff",
        "text_primary": "#1c1c1c",
        "text_secondary": "#4a4a4a",
        "accent": "#2f6feb",
        "question": "#cc0000",
        "answer": "#228b22",
        "explanation": "#b8860b",
        "entry_bg": "#ffffff",
        "entry_fg": "#1c1c1c",
        "selection_bg": "#dce8ff",
        "selection_fg": "#1c1c1c",
        "button_bg": "#e9e9e9",
        "button_active_bg": "#dddddd",
        "button_fg": "#1c1c1c",
        "danger": "#cc0000",
    }

    DARK_THEME = {
        "window_bg": "#101215",
        "surface_bg": "#1a1f26",
        "text_primary": "#e8edf2",
        "text_secondary": "#b4beca",
        "accent": "#8ab4ff",
        "question": "#ff8e8e",
        "answer": "#7ee787",
        "explanation": "#f2cc74",
        "entry_bg": "#242b35",
        "entry_fg": "#e8edf2",
        "selection_bg": "#3a4b63",
        "selection_fg": "#f4f8ff",
        "button_bg": "#2c3440",
        "button_active_bg": "#394454",
        "button_fg": "#e8edf2",
        "danger": "#ff8e8e",
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Flashcard App")
        self.root.geometry("760x500")
        self.root.minsize(680, 420)
        self.dark_mode_enabled = False
        self.theme_colors = self.LIGHT_THEME

        self.storage = DeckStorage(Path(__file__).resolve().parent)

        self.main_frame = ttk.Frame(self.root, padding=18)
        self.main_frame.pack(fill="both", expand=True)

        self.current_cards: list[dict[str, str]] = []
        self.current_index = 0
        self.showing_answer = False

        self._build_styles()
        self.show_main_menu()

    def _build_styles(self) -> None:
        # Configure basic widget styles based on the active theme.
        self.theme_colors = self.DARK_THEME if self.dark_mode_enabled else self.LIGHT_THEME
        colors = self.theme_colors

        self.root.configure(background=colors["window_bg"])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=colors["window_bg"], foreground=colors["text_primary"])
        style.configure("TFrame", background=colors["window_bg"])
        style.configure("Surface.TFrame", background=colors["surface_bg"])
        style.configure("TLabel", background=colors["window_bg"], foreground=colors["text_primary"])
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=colors["text_secondary"])
        style.configure("CardText.TLabel", font=("Segoe UI", 16), padding=16, background=colors["surface_bg"])
        style.configure("QuestionTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground=colors["question"], background=colors["surface_bg"])
        style.configure("AnswerTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground=colors["answer"], background=colors["surface_bg"])
        style.configure("ExplanationTitle.TLabel", font=("Segoe UI", 16, "bold"), foreground=colors["explanation"], background=colors["surface_bg"])

        style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"], borderwidth=1)
        style.map("TButton", background=[("active", colors["button_active_bg"])])

        style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
        style.map("TEntry", fieldbackground=[("readonly", colors["entry_bg"])])

    def _toggle_dark_mode(self) -> None:
        # Toggle between light and dark color palettes.
        self.dark_mode_enabled = not self.dark_mode_enabled
        self._build_styles()
        self.show_main_menu()

    def _clear_main_frame(self) -> None:
        for child in self.main_frame.winfo_children():
            child.destroy()

    def _create_limited_textbox(self, parent: ttk.Frame, width: int = 60, height: int = 4, max_chars: int = 500) -> tk.Text:
        # Create a multiline textbox that wraps words.
        # Character limits are validated when the user submits the card.
        _ = max_chars
        colors = self.theme_colors
        textbox = tk.Text(
            parent,
            width=width,
            height=height,
            wrap="word",
            undo=True,
            bg=colors["entry_bg"],
            fg=colors["entry_fg"],
            insertbackground=colors["entry_fg"],
            selectbackground=colors["selection_bg"],
            selectforeground=colors["selection_fg"],
            highlightbackground=colors["window_bg"],
            highlightcolor=colors["accent"],
            relief="solid",
            borderwidth=1,
        )
        return textbox

    def _textbox_value(self, textbox: tk.Text) -> str:
        return textbox.get("1.0", "end-1c").strip()

    def _validate_card_lengths(self, question: str, answer: str, explanation: str, explanation_limit: int = 500) -> bool:
        if len(question) > 500:
            messagebox.showwarning("Question Too Long", "Question cannot exceed 500 characters.")
            return False
        if len(answer) > 500:
            messagebox.showwarning("Answer Too Long", "Answer cannot exceed 500 characters.")
            return False
        if len(explanation) > explanation_limit:
            messagebox.showwarning("Explanation Too Long", f"Explanation cannot exceed {explanation_limit} characters.")
            return False
        return True

    def _set_textbox_value(self, textbox: tk.Text, value: str, max_chars: int = 500) -> None:
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value[:max_chars])

    def show_main_menu(self) -> None:
        # Render the main menu screen.
        self._clear_main_frame()

        container = ttk.Frame(self.main_frame)
        container.pack(expand=True)

        ttk.Label(container, text="Flashcard App", style="Title.TLabel").pack(pady=(0, 24))
        mode_text = "On" if self.dark_mode_enabled else "Off"
        ttk.Label(container, text=f"Dark mode: {mode_text}", style="Header.TLabel").pack(pady=(0, 12))
        ttk.Label(container, text=f"Decks folder: {self.storage.decks_dir}", wraplength=640).pack(pady=(0, 12))
        ttk.Button(container, text="Create Cards", command=self.show_create_cards_screen, width=24).pack(pady=8)
        ttk.Button(container, text="Edit Deck", command=self.show_edit_deck_selection_screen, width=24).pack(pady=8)
        ttk.Button(container, text="Study", command=self.show_study_selection_screen, width=24).pack(pady=8)
        ttk.Button(container, text="Toggle Dark Mode", command=self._toggle_dark_mode, width=24).pack(pady=8)
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

        topic_entry = ttk.Entry(form, textvariable=topic_var, width=60)
        topic_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Question (max 500 chars):", style="Header.TLabel").grid(row=1, column=0, sticky="nw", pady=6)
        question_entry = self._create_limited_textbox(form)
        question_entry.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Answer (max 500 chars):", style="Header.TLabel").grid(row=2, column=0, sticky="nw", pady=6)
        answer_entry = self._create_limited_textbox(form)
        answer_entry.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Explanation (optional, max 1000 chars):", style="Header.TLabel").grid(row=3, column=0, sticky="nw", pady=6)
        explanation_entry = self._create_limited_textbox(form, max_chars=1000)
        explanation_entry.grid(row=3, column=1, sticky="ew", pady=6)

        form.columnconfigure(1, weight=1)

        def save_card() -> None:
            topic = topic_var.get().strip()
            question = self._textbox_value(question_entry)
            answer = self._textbox_value(answer_entry)
            explanation = self._textbox_value(explanation_entry)

            if not topic:
                messagebox.showwarning("Missing Topic", "Please enter a topic name.")
                return
            if not question:
                messagebox.showwarning("Missing Question", "Please enter a question.")
                return
            if not answer:
                messagebox.showwarning("Missing Answer", "Please enter an answer.")
                return
            if not self._validate_card_lengths(question, answer, explanation, explanation_limit=1000):
                return

            try:
                saved_deck_name = self.storage.append_card(deck_name=topic, question=question, answer=answer, explanation=explanation)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                messagebox.showerror("Save Error", f"Could not save card:\n{exc}")
                return

            self._set_textbox_value(question_entry, "")
            self._set_textbox_value(answer_entry, "")
            self._set_textbox_value(explanation_entry, "")
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

        colors = self.theme_colors
        listbox = tk.Listbox(
            frame,
            height=12,
            selectmode=tk.EXTENDED,
            bg=colors["entry_bg"],
            fg=colors["text_primary"],
            selectbackground=colors["selection_bg"],
            selectforeground=colors["selection_fg"],
            highlightbackground=colors["window_bg"],
            highlightcolor=colors["accent"],
        )
        listbox.pack(fill="both", expand=True, pady=(0, 10))

        for deck_id, deck_name in deck_entries:
            listbox.insert(tk.END, deck_name)
            if self.storage.is_outdated_schema(deck_id):
                listbox.itemconfig(tk.END, foreground=colors["danger"])

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

    def show_edit_deck_selection_screen(self) -> None:
        # Render single-deck selection for edit mode.
        self._clear_main_frame()

        ttk.Label(self.main_frame, text="Edit Deck", style="Title.TLabel").pack(pady=(0, 16))

        deck_entries = self.storage.list_deck_entries()

        frame = ttk.Frame(self.main_frame, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select one deck to edit:", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        colors = self.theme_colors
        listbox = tk.Listbox(
            frame,
            height=12,
            selectmode=tk.SINGLE,
            bg=colors["entry_bg"],
            fg=colors["text_primary"],
            selectbackground=colors["selection_bg"],
            selectforeground=colors["selection_fg"],
            highlightbackground=colors["window_bg"],
            highlightcolor=colors["accent"],
        )
        listbox.pack(fill="both", expand=True, pady=(0, 10))

        for _deck_id, deck_name in deck_entries:
            listbox.insert(tk.END, deck_name)

        if deck_entries:
            listbox.selection_set(0)

        def open_edit_screen() -> None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Deck Selected", "Please select a deck to edit.")
                return
            deck_id, deck_name = deck_entries[selection[0]]
            self.show_edit_deck_screen(deck_id, deck_name)

        controls = ttk.Frame(frame)
        controls.pack()

        ttk.Button(controls, text="Edit Selected Deck", command=open_edit_screen, width=18).pack(side="left", padx=8)
        ttk.Button(controls, text="Back to Menu", command=self.show_main_menu, width=18).pack(side="left", padx=8)

        if not deck_entries:
            messagebox.showinfo("No Decks", "No decks found. Create cards first.")

    def show_edit_deck_screen(self, deck_id: str, deck_name: str) -> None:
        # Render card-by-card deck editor with save and navigation controls.
        try:
            cards = self.storage.load_deck(deck_id)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Load Error", f"Could not load deck '{deck_name}':\n{exc}")
            return

        if not cards:
            messagebox.showwarning("Empty Deck", "This deck has no cards to edit.")
            return

        self._clear_main_frame()

        ttk.Label(self.main_frame, text=f"Edit Deck: {deck_name}", style="Title.TLabel").pack(pady=(0, 12))

        card_position_label = ttk.Label(self.main_frame, text="", style="Header.TLabel")
        card_position_label.pack(pady=(0, 8))

        form = ttk.Frame(self.main_frame, padding=8)
        form.pack(fill="x", padx=50)

        current_index = 0

        ttk.Label(form, text="Question (max 500 chars):", style="Header.TLabel").grid(row=0, column=0, sticky="nw", pady=6)
        question_entry = self._create_limited_textbox(form)
        question_entry.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Answer (max 500 chars):", style="Header.TLabel").grid(row=1, column=0, sticky="nw", pady=6)
        answer_entry = self._create_limited_textbox(form)
        answer_entry.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Explanation (optional, max 1000 chars):", style="Header.TLabel").grid(row=2, column=0, sticky="nw", pady=6)
        explanation_entry = self._create_limited_textbox(form, max_chars=1000)
        explanation_entry.grid(row=2, column=1, sticky="ew", pady=6)

        form.columnconfigure(1, weight=1)

        def load_current_card() -> None:
            card = cards[current_index]
            self._set_textbox_value(question_entry, card["question"])
            self._set_textbox_value(answer_entry, card["answer"])
            self._set_textbox_value(explanation_entry, card.get("explanation", ""), max_chars=1000)
            card_position_label.config(text=f"Card {current_index + 1} of {len(cards)}")

        def save_current_card() -> None:
            question = self._textbox_value(question_entry)
            answer = self._textbox_value(answer_entry)
            explanation = self._textbox_value(explanation_entry)

            if not question:
                messagebox.showwarning("Missing Question", "Please enter a question.")
                return
            if not answer:
                messagebox.showwarning("Missing Answer", "Please enter an answer.")
                return
            if not self._validate_card_lengths(question, answer, explanation, explanation_limit=1000):
                return

            cards[current_index] = {"question": question, "answer": answer, "explanation": explanation}

            try:
                self.storage.save_deck_cards(deck_id, cards)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Save Error", f"Could not save card:\n{exc}")
                return

            messagebox.showinfo("Saved", f"Card {current_index + 1} saved.")

        def next_card() -> None:
            nonlocal current_index
            current_index = (current_index + 1) % len(cards)
            load_current_card()

        def previous_card() -> None:
            nonlocal current_index
            current_index = (current_index - 1) % len(cards)
            load_current_card()

        buttons = ttk.Frame(self.main_frame)
        buttons.pack(pady=20)

        ttk.Button(buttons, text="Previous", command=previous_card, width=14).pack(side="left", padx=6)
        ttk.Button(buttons, text="Next", command=next_card, width=14).pack(side="left", padx=6)
        ttk.Button(buttons, text="Save Card", command=save_current_card, width=14).pack(side="left", padx=6)
        ttk.Button(buttons, text="Back to Deck Select", command=self.show_edit_deck_selection_screen, width=18).pack(side="left", padx=6)

        load_current_card()
        question_entry.focus_set()

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

        card_frame = ttk.Frame(self.main_frame, relief="solid", borderwidth=1, style="Surface.TFrame")
        card_frame.pack(fill="both", expand=True, padx=30, pady=8)

        self.card_content_frame = ttk.Frame(card_frame, padding=16, style="Surface.TFrame")
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
