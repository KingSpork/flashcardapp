from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk


def show_create_cards_screen(app) -> None:
    # Render the create-cards screen.
    app._clear_main_frame()

    ttk.Label(app.main_frame, text="Create Cards", style="Title.TLabel").pack(pady=(0, 18))

    form = ttk.Frame(app.main_frame, padding=8)
    form.pack(fill="x", padx=50)

    ttk.Label(form, text="Topic Name:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=6)
    topic_var = tk.StringVar()

    topic_entry = ttk.Entry(form, textvariable=topic_var, width=60)
    topic_entry.grid(row=0, column=1, sticky="ew", pady=6)

    ttk.Label(form, text="Question (max 500 chars):", style="Header.TLabel").grid(row=1, column=0, sticky="nw", pady=6)
    question_entry = app._create_limited_textbox(form)
    question_entry.grid(row=1, column=1, sticky="ew", pady=6)

    ttk.Label(form, text="Answer (max 500 chars):", style="Header.TLabel").grid(row=2, column=0, sticky="nw", pady=6)
    answer_entry = app._create_limited_textbox(form)
    answer_entry.grid(row=2, column=1, sticky="ew", pady=6)

    ttk.Label(form, text="Explanation (optional, max 1000 chars):", style="Header.TLabel").grid(row=3, column=0, sticky="nw", pady=6)
    explanation_entry = app._create_limited_textbox(form, max_chars=1000)
    explanation_entry.grid(row=3, column=1, sticky="ew", pady=6)

    form.columnconfigure(1, weight=1)

    def save_card() -> None:
        topic = topic_var.get().strip()
        question = app._textbox_value(question_entry)
        answer = app._textbox_value(answer_entry)
        explanation = app._textbox_value(explanation_entry)

        if not topic:
            messagebox.showwarning("Missing Topic", "Please enter a topic name.")
            return
        if not question:
            messagebox.showwarning("Missing Question", "Please enter a question.")
            return
        if not answer:
            messagebox.showwarning("Missing Answer", "Please enter an answer.")
            return
        if not app._validate_card_lengths(question, answer, explanation, explanation_limit=1000):
            return

        try:
            saved_deck_name = app.storage.append_card(deck_name=topic, question=question, answer=answer, explanation=explanation)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Save Error", f"Could not save card:\n{exc}")
            return

        app._set_textbox_value(question_entry, "")
        app._set_textbox_value(answer_entry, "")
        app._set_textbox_value(explanation_entry, "")
        question_entry.focus_set()
        messagebox.showinfo("Saved", f"Card saved to deck '{saved_deck_name}'.")

    buttons = ttk.Frame(app.main_frame)
    buttons.pack(pady=20)

    ttk.Button(buttons, text="Save Card", command=save_card, width=18).pack(side="left", padx=8)
    ttk.Button(buttons, text="Back to Menu", command=app.show_main_menu, width=18).pack(side="left", padx=8)

    topic_entry.focus_set()
