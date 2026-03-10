from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from flashcards.screens.create_cards import show_create_cards_screen
from flashcards.screens.edit_deck import show_edit_deck_screen, show_edit_deck_selection_screen
from flashcards.screens.menu import change_decks_folder, show_main_menu
from flashcards.screens.study import (
    load_study_decks,
    refresh_card_display,
    show_study_screen,
    show_study_selection_screen,
)
from flashcards.storage import DeckStorage
from flashcards.study_session import StudySession
from flashcards.ui.theme import LIGHT_THEME, build_styles
from flashcards.ui.widgets import create_limited_textbox, set_textbox_value, textbox_value, validate_card_lengths


class FlashcardApp:
    # Main Tkinter app for creating and studying flashcards.

    LIGHT_THEME = LIGHT_THEME

    def __init__(self, root: tk.Tk, base_dir: Path) -> None:
        self.root = root
        self.root.title("Flashcard App")
        self.root.geometry("760x500")
        self.root.minsize(680, 420)
        self.dark_mode_enabled = False
        self.theme_colors = self.LIGHT_THEME

        self.storage = DeckStorage(base_dir)

        self.main_frame = ttk.Frame(self.root, padding=18)
        self.main_frame.pack(fill="both", expand=True)

        self.study_session = StudySession()

        self._build_styles()
        self.show_main_menu()

    def _build_styles(self) -> None:
        # Configure basic widget styles based on the active theme.
        self.theme_colors = build_styles(self.root, self.dark_mode_enabled)

    def _toggle_dark_mode(self) -> None:
        # Toggle between light and dark color palettes.
        self.dark_mode_enabled = not self.dark_mode_enabled
        self._build_styles()
        self.show_main_menu()

    def _clear_main_frame(self) -> None:
        for child in self.main_frame.winfo_children():
            child.destroy()

    def _create_limited_textbox(self, parent: ttk.Frame, width: int = 60, height: int = 4, max_chars: int = 500) -> tk.Text:
        return create_limited_textbox(parent, self.theme_colors, width=width, height=height, max_chars=max_chars)

    def _textbox_value(self, textbox: tk.Text) -> str:
        return textbox_value(textbox)

    def _validate_card_lengths(self, question: str, answer: str, explanation: str, explanation_limit: int = 500) -> bool:
        return validate_card_lengths(question, answer, explanation, explanation_limit=explanation_limit)

    def _set_textbox_value(self, textbox: tk.Text, value: str, max_chars: int = 500) -> None:
        set_textbox_value(textbox, value, max_chars=max_chars)

    def show_main_menu(self) -> None:
        show_main_menu(self)

    def change_decks_folder(self) -> None:
        change_decks_folder(self)

    def show_create_cards_screen(self) -> None:
        show_create_cards_screen(self)

    def show_study_selection_screen(self) -> None:
        show_study_selection_screen(self)

    def show_edit_deck_selection_screen(self) -> None:
        show_edit_deck_selection_screen(self)

    def show_edit_deck_screen(self, deck_id: str, deck_name: str) -> None:
        show_edit_deck_screen(self, deck_id, deck_name)

    def _load_study_decks(self, selected_decks: list[tuple[str, str]]) -> None:
        load_study_decks(self, selected_decks)

    def show_study_screen(self, topic_name: str) -> None:
        show_study_screen(self, topic_name)

    def _refresh_card_display(self) -> None:
        refresh_card_display(self)

    def _flip_card(self) -> None:
        # Toggle current card between question and answer.
        self.study_session.flip()
        self._refresh_card_display()

    def _next_card(self) -> None:
        # Move to the next card with wrap-around.
        self.study_session.next_card()
        self._refresh_card_display()

    def _previous_card(self) -> None:
        # Move to the previous card with wrap-around.
        self.study_session.previous_card()
        self._refresh_card_display()

    def _random_card(self) -> None:
        # Jump to a random card and show its question.
        self.study_session.random_card()
        self._refresh_card_display()
