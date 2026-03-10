from __future__ import annotations

import tkinter as tk
from pathlib import Path

from flashcards.app import FlashcardApp


def main() -> None:
    # Run the flashcard desktop application.
    root = tk.Tk()
    base_dir = Path(__file__).resolve().parent.parent
    FlashcardApp(root, base_dir=base_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
