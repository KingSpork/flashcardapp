from __future__ import annotations

import random

Card = dict[str, str]


class StudySession:
    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.current_index = 0
        self.showing_answer = False

    def set_cards(self, cards: list[Card]) -> None:
        self.cards = cards
        self.current_index = 0
        self.showing_answer = False

    def current_card(self) -> Card | None:
        if not self.cards:
            return None
        return self.cards[self.current_index]

    def flip(self) -> None:
        if not self.cards:
            return
        self.showing_answer = not self.showing_answer

    def next_card(self) -> None:
        if not self.cards:
            return
        self.current_index = (self.current_index + 1) % len(self.cards)
        self.showing_answer = False

    def previous_card(self) -> None:
        if not self.cards:
            return
        self.current_index = (self.current_index - 1) % len(self.cards)
        self.showing_answer = False

    def random_card(self) -> None:
        if not self.cards:
            return
        if len(self.cards) == 1:
            self.current_index = 0
        else:
            available_indices = [index for index in range(len(self.cards)) if index != self.current_index]
            self.current_index = random.choice(available_indices)
        self.showing_answer = False
