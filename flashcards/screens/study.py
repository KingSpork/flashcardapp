from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


def show_study_selection_screen(app) -> None:
    # Render deck selection for study mode.
    app._clear_main_frame()

    ttk.Label(app.main_frame, text="Study", style="Title.TLabel").pack(pady=(0, 16))

    deck_entries = app.storage.list_deck_entries()

    frame = ttk.Frame(app.main_frame, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Select one or more decks:", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

    colors = app.theme_colors
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
        if app.storage.is_outdated_schema(deck_id):
            listbox.itemconfig(tk.END, foreground=colors["danger"])

    if deck_entries:
        listbox.selection_set(0)

    def start_study() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No Deck Selected", "Please select a deck to study.")
            return
        selected_decks = [deck_entries[index] for index in selection]
        app._load_study_decks(selected_decks)

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
            parent=app.root,
        )
        if renamed_deck is None:
            return

        renamed_deck = renamed_deck.strip()
        if not renamed_deck:
            messagebox.showwarning("Invalid Name", "Deck name cannot be empty.")
            return

        try:
            _, final_deck_name = app.storage.rename_deck(selected_deck_id, renamed_deck)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Rename Error", f"Could not rename deck:\n{exc}")
            return

        messagebox.showinfo("Deck Renamed", f"Deck '{selected_deck_name}' was renamed to '{final_deck_name}'.")
        app.show_study_selection_screen()

    def reload_decks() -> None:
        app.storage.refresh_decks()
        app.show_study_selection_screen()

    controls = ttk.Frame(frame)
    controls.pack()

    ttk.Button(controls, text="Start Study", command=start_study, width=18).pack(side="left", padx=8)
    ttk.Button(controls, text="Rename Deck", command=rename_deck, width=18).pack(side="left", padx=8)
    ttk.Button(controls, text="Reload Decks", command=reload_decks, width=18).pack(side="left", padx=8)
    ttk.Button(controls, text="Back to Menu", command=app.show_main_menu, width=18).pack(side="left", padx=8)

    ttk.Label(
        app.main_frame,
        text=f"App schema version: {app.storage.SCHEMA_VERSION}",
        font=("Segoe UI", 9),
    ).pack(anchor="se", pady=(8, 0))

    if not deck_entries:
        messagebox.showinfo("No Decks", "No decks found. Create cards first.")


def load_study_decks(app, selected_decks: list[tuple[str, str]]) -> None:
    # Load selected decks and open the study screen.
    combined_cards: list[dict[str, str]] = []
    for deck_id, deck_name in selected_decks:
        try:
            cards = app.storage.load_deck(deck_id)
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

    app.study_session.set_cards(combined_cards)

    if not app.study_session.cards:
        messagebox.showwarning("Empty Selection", "The selected decks do not contain any cards.")
        return

    study_label = selected_decks[0][1] if len(selected_decks) == 1 else ""
    app.show_study_screen(study_label)


def show_study_screen(app, topic_name: str) -> None:
    # Render flashcard study controls and card display.
    app._clear_main_frame()

    app.study_title_label = ttk.Label(app.main_frame, text=f"Studying: {topic_name}", style="Title.TLabel")
    app.study_title_label.pack(pady=(0, 14))

    app.card_position_label = ttk.Label(app.main_frame, text="", style="Header.TLabel")
    app.card_position_label.pack(pady=(0, 8))

    card_frame = ttk.Frame(app.main_frame, relief="solid", borderwidth=1, style="Surface.TFrame")
    card_frame.pack(fill="both", expand=True, padx=30, pady=8)

    app.card_content_frame = ttk.Frame(card_frame, padding=16, style="Surface.TFrame")
    app.card_content_frame.pack(fill="both", expand=True)

    app.card_title_label = ttk.Label(
        app.card_content_frame,
        text="",
        style="QuestionTitle.TLabel",
        anchor="center",
        justify="center",
        wraplength=640,
    )
    app.card_title_label.pack(fill="x", pady=(0, 8))

    app.card_body_label = ttk.Label(
        app.card_content_frame,
        text="",
        style="CardText.TLabel",
        anchor="center",
        justify="center",
        wraplength=640,
    )
    app.card_body_label.pack(fill="both", expand=True)

    app.card_explanation_title_label = ttk.Label(
        app.card_content_frame,
        text="",
        style="ExplanationTitle.TLabel",
        anchor="center",
        justify="center",
        wraplength=640,
    )

    app.card_explanation_body_label = ttk.Label(
        app.card_content_frame,
        text="",
        style="CardText.TLabel",
        anchor="center",
        justify="center",
        wraplength=640,
    )

    controls = ttk.Frame(app.main_frame)
    controls.pack(pady=12)

    top_controls = ttk.Frame(controls)
    top_controls.pack(pady=(0, 8))
    ttk.Button(top_controls, text="Flip", command=app._flip_card, width=12).pack()

    bottom_controls = ttk.Frame(controls)
    bottom_controls.pack()
    ttk.Button(bottom_controls, text="Back to Menu", command=app.show_main_menu, width=12).pack(side="left", padx=6)
    ttk.Button(bottom_controls, text="Previous", command=app._previous_card, width=12).pack(side="left", padx=6)
    ttk.Button(bottom_controls, text="Next", command=app._next_card, width=12).pack(side="left", padx=6)
    ttk.Button(bottom_controls, text="Random", command=app._random_card, width=12).pack(side="left", padx=6)

    app._refresh_card_display()


def refresh_card_display(app) -> None:
    # Update labels to display current card state.
    if not app.study_session.cards:
        app.card_title_label.config(text="")
        app.card_body_label.config(text="No cards to display.")
        app.card_explanation_title_label.pack_forget()
        app.card_explanation_body_label.pack_forget()
        app.card_position_label.config(text="")
        return

    card = app.study_session.current_card()
    if card is None:
        return
    app.study_title_label.config(text=f"Studying: {card.get('topic_name', '')}")
    explanation = card.get("explanation", "").strip()

    if app.study_session.showing_answer:
        side = "Answer"
        body_text = card["answer"]
        side_style = "AnswerTitle.TLabel"
    else:
        side = "Question"
        body_text = card["question"]
        side_style = "QuestionTitle.TLabel"

    app.card_title_label.config(text=f"{side}:", style=side_style)
    app.card_body_label.config(text=body_text)

    if app.study_session.showing_answer and explanation:
        app.card_explanation_title_label.config(text="Explanation:")
        app.card_explanation_title_label.pack(fill="x", pady=(12, 8))
        app.card_explanation_body_label.config(text=explanation)
        app.card_explanation_body_label.pack(fill="both", expand=True)
    else:
        app.card_explanation_title_label.pack_forget()
        app.card_explanation_body_label.pack_forget()

    total = len(app.study_session.cards)
    app.card_position_label.config(text=f"Card {app.study_session.current_index + 1} of {total}")
