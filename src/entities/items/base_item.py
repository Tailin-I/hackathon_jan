from typing import Dict, Any


class Item:
    """Базовый класс для всех предметов"""

    def __init__(self, item_id: str, name: str, texture=None, scale: float = 1.0):
        # Сохраняем текстуру для UI
        self._texture = texture
        self.scale = scale

        self.item_id = item_id
        self.name = name
        self.description = ""
        self.is_stackable = True
        self.max_stack = 99
        self.count = 1

        self.additional_health = 0
        self.additional_strength = 0
        self.additional_speed = 0
        self.additional_range = 0

        # Флаги
        self.is_equippable = False
        self.is_consumable = False
        self.is_quest_item = False # пока не буду усложнять (нет времени реализовывать квестовую систему)

    def use(self, player):
        """Использовать предмет"""

    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о предмете для UI"""
        return {
            "id": self.item_id,
            "name": self.name,
            "description": self.description,
            "count": self.count,
            "stackable": self.is_stackable,
            "texture": self._texture
        }

    def __str__(self):
        return f"{self.name} (x{self.count})"

    @property
    def texture(self):
        return self._texture