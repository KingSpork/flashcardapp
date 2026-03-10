from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk


def show_edit_deck_selection_screen(app) -> None:
    # Render single-deck selection for edit mode.
    app._clear_main_frame()

    ttk.Label(app.main_frame, text="Edit Deck", style="Title.TLabel").pack(pady=(0, 16))

    deck_entries = app.storage.list_deck_entries()

    frame = ttk.Frame(app.main_frame, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Select one deck to edit:", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

    colors = app.theme_colors
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
        app.show_edit_deck_screen(deck_id, deck_name)

    controls = ttk.Frame(frame)
    controls.pack()

    ttk.Button(controls, text="Edit Selected Deck", command=open_edit_screen, width=18).pack(side="left", padx=8)
    ttk.Button(controls, text="Back to Menu", command=app.show_main_menu, width=18).pack(side="left", padx=8)

    if not deck_entries:
        messagebox.showinfo("No Decks", "No decks found. Create cards first.")


def show_edit_deck_screen(app, deck_id: str, deck_name: str) -> None:
    # Render card-by-card deck editor with save and navigation controls.
    try:
        cards = app.storage.load_deck(deck_id)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        messagebox.showerror("Load Error", f"Could not load deck '{deck_name}':\n{exc}")
        return

    if not cards:
        messagebox.showwarning("Empty Deck", "This deck has no cards to edit.")
        return

    app._clear_main_frame()

    ttk.Label(app.main_frame, text=f"Edit Deck: {deck_name}", style="Title.TLabel").pack(pady=(0, 12))

    card_position_label = ttk.Label(app.main_frame, text="", style="Header.TLabel")
    card_position_label.pack(pady=(0, 8))

    form = ttk.Frame(app.main_frame, padding=8)
    form.pack(fill="x", padx=50)

    current_index = 0

    ttk.Label(form, text="Question (max 500 chars):", style="Header.TLabel").grid(row=0, column=0, sticky="nw", pady=6)
    question_entry = app._create_limited_textbox(form)
    question_entry.grid(row=0, column=1, sticky="ew", pady=6)

    ttk.Label(form, text="Answer (max 500 chars):", style="Header.TLabel").grid(row=1, column=0, sticky="nw", pady=6)
    answer_entry = app._create_limited_textbox(form)
    answer_entry.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(form, text="Explanation (optional, max 1000 chars):", style="Header.TLabel").grid(row=2, column=0, sticky="nw", pady=6)
    explanation_entry = app._create_limited_textbox(form, max_chars=1000)
    explanation_entry.grid(row=2, column=1, sticky="ew", pady=6)

    form.columnconfigure(1, weight=1)

    def load_current_card() -> None:
        card = cards[current_index]
        app._set_textbox_value(question_entry, card["question"])
        app._set_textbox_value(answer_entry, card["answer"])
        app._set_textbox_value(explanation_entry, card.get("explanation", ""), max_chars=1000)
        card_position_label.config(text=f"Card {current_index + 1} of {len(cards)}")

    def save_current_card() -> None:
        question = app._textbox_value(question_entry)
        answer = app._textbox_value(answer_entry)
        explanation = app._textbox_value(explanation_entry)

        if not question:
            messagebox.showwarning("Missing Question", "Please enter a question.")
            return
        if not answer:
            messagebox.showwarning("Missing Answer", "Please enter an answer.")
            return
        if not app._validate_card_lengths(question, answer, explanation, explanation_limit=1000):
            return

        cards[current_index] = {"question": question, "answer": answer, "explanation": explanation}

        try:
            app.storage.save_deck_cards(deck_id, cards)
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

    buttons = ttk.Frame(app.main_frame)
    buttons.pack(pady=20)

    ttk.Button(buttons, text="Previous", command=previous_card, width=14).pack(side="left", padx=6)
    ttk.Button(buttons, text="Next", command=next_card, width=14).pack(side="left", padx=6)
    ttk.Button(buttons, text="Save Card", command=save_current_card, width=14).pack(side="left", padx=6)
    ttk.Button(buttons, text="Back to Deck Select", command=app.show_edit_deck_selection_screen, width=18).pack(side="left", padx=6)

    load_current_card()
    question_entry.focus_set()
