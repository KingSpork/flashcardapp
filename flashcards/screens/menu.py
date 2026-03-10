from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def show_main_menu(app) -> None:
    # Render the main menu screen.
    app._clear_main_frame()

    container = ttk.Frame(app.main_frame)
    container.pack(expand=True)

    ttk.Label(container, text="Flashcard App", style="Title.TLabel").pack(pady=(0, 24))
    mode_text = "On" if app.dark_mode_enabled else "Off"
    ttk.Label(container, text=f"Dark mode: {mode_text}", style="Header.TLabel").pack(pady=(0, 12))
    ttk.Label(container, text=f"Decks folder: {app.storage.decks_dir}", wraplength=640).pack(pady=(0, 12))
    ttk.Button(container, text="Create Cards", command=app.show_create_cards_screen, width=24).pack(pady=8)
    ttk.Button(container, text="Edit Deck", command=app.show_edit_deck_selection_screen, width=24).pack(pady=8)
    ttk.Button(container, text="Study", command=app.show_study_selection_screen, width=24).pack(pady=8)
    ttk.Button(container, text="Toggle Dark Mode", command=app._toggle_dark_mode, width=24).pack(pady=8)
    ttk.Button(container, text="Change Decks Folder", command=app.change_decks_folder, width=24).pack(pady=8)
    ttk.Button(container, text="Exit", command=app.root.destroy, width=24).pack(pady=8)


def change_decks_folder(app) -> None:
    # Allow the user to choose a different folder for deck files.
    selected_dir = filedialog.askdirectory(
        title="Choose Decks Folder",
        initialdir=str(app.storage.decks_dir),
        mustexist=True,
    )
    if not selected_dir:
        return

    try:
        app.storage.set_decks_dir(Path(selected_dir))
    except OSError as exc:
        messagebox.showerror("Folder Error", f"Could not use selected folder:\n{exc}")
        return

    messagebox.showinfo("Decks Folder Updated", f"Deck files will now be stored in:\n{app.storage.decks_dir}")
    app.show_main_menu()
