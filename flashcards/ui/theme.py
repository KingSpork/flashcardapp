from __future__ import annotations

from tkinter import ttk

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


def build_styles(root, dark_mode_enabled: bool) -> dict[str, str]:
    colors = DARK_THEME if dark_mode_enabled else LIGHT_THEME

    root.configure(background=colors["window_bg"])
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
    return colors
