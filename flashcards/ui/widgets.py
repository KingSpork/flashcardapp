from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


def create_limited_textbox(parent, colors: dict[str, str], width: int = 60, height: int = 4, max_chars: int = 500) -> tk.Text:
    # Create a multiline textbox that wraps words.
    # Character limits are validated when the user submits the card.
    _ = max_chars
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


def textbox_value(textbox: tk.Text) -> str:
    return textbox.get("1.0", "end-1c").strip()


def validate_card_lengths(question: str, answer: str, explanation: str, explanation_limit: int = 500) -> bool:
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


def set_textbox_value(textbox: tk.Text, value: str, max_chars: int = 500) -> None:
    textbox.delete("1.0", "end")
    textbox.insert("1.0", value[:max_chars])
