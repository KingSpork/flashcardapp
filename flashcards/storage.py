from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Card = dict[str, str]


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

    def load_deck(self, deck_id: str) -> list[Card]:
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

        cards: list[Card] = []
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

    def _write_deck(self, deck_id: str, deck_name: str, cards: list[Card]) -> None:
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
            cards: list[Card] = []
        else:
            cards = self.load_deck(deck_id)

        cards.append({'question': question, 'answer': answer, 'explanation': explanation})
        self._write_deck(deck_id, normalized_name, cards)
        self.deck_index[deck_id] = normalized_name
        return normalized_name

    def save_deck_cards(self, deck_id: str, cards: list[Card]) -> str:
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
