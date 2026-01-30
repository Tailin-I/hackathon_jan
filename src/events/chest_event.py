from typing import Dict, Any

import arcade

from ..core.game_data import game_data
from ..ui.notification_system import notifications as ns

from .event import GameEvent
from src.entities.items.item_factory import ItemFactory

class ChestEvent(GameEvent):
    """Событие сундука"""

    def __init__(self, event_id: str, name: str, rect: tuple, properties: Dict[str, Any]):
        super().__init__(event_id, name,"chest", rect, properties)
        # Ссылка на спайт
        self.sprite = None
        self.sprite_center_x = 0
        self.sprite_center_y = 0
        self.sprite_height = 0
        # Парсим свойства
        self.lock_sequence = properties.get("lock", "")
        self.is_locked = len(self.lock_sequence) > 0
        self.is_empty = False
        self.player_sequence = ""

        self.map_name = None

        # Добыча
        loot_str = properties.get("loot", "")
        self.loot_items = ItemFactory.parse_loot_string(loot_str)

        self.logger.debug(f"Создан сундук: id={event_id}, loot='{loot_str}', items={len(self.loot_items)}")


    def activate(self, player, game_state):
        """Игрок взаимодействует с сундуком"""
        if self.activated and self.cooldown > 0:
            return
        if self.is_empty:
            ns.notification("Сундук пуст!")
            return
        self.logger.info(f" Взаимодействие с сундуком '{self.event_id}'")

        if self.is_locked:
            self.player_sequence = ""
            self.logger.info(f"Заперт! Комбинация: {self.lock_sequence}")
            # Открываем мини-игру взлома
            game_state.gsm.push_overlay("lock_picking",
                                        chest_event=self,
                                        player=player)
        else:
            self.open_chest()
        self.activated = True
        self.cooldown = self.max_cooldown


    def draw_names(self):
        if self.show_text_description:
            color = arcade.color.GOLD
            text = "сундук"
            if self.is_empty:
                color = arcade.color.TAN
            """"""
            arcade.Text(
                text,
                self.sprite_center_x,
                self.sprite_center_y+  self.sprite_height*0.8,
                color,
                18,
                align="center",
                anchor_x="center",
                anchor_y="center",
                bold=True
            ).draw()
            self.show_text_description = False



    def set_sprite(self, sprite):
        """Устанавливает связь с визуальным спрайтом"""
        self.sprite = sprite
        self.sprite_center_x = self.sprite.center_x
        self.sprite_center_y = self.sprite.center_y
        self.sprite_height = self.sprite.height
        if sprite:
            sprite.event = self  # Двусторонняя связь

    def open_chest(self):
        """Открыть сундук и выдать добычу"""

        for item in self.loot_items:
            self._add_to_inventory(item)

        self.is_empty = True

        # Обновляем визуал если есть спрайт
        if self.sprite:
            self.sprite.update_visual()

        # Сохраняем состояние
        self._save_state()

    def _save_state(self):
        """Сохраняет состояние сундука"""

        # Создаем или обновляем данные о сундуке
        chest_data = {
                "id": self.event_id,
                "type": "chest",
                "is_empty": self.is_empty,
                "map_name": self.map_name
            }
            # Можно сохранить в monsters_data или создать отдельное хранилище
        game_data.mobs_data[self.event_id] = chest_data #TODO

    def _add_to_inventory(self, item):
        """Добавляет предмет в инвентарь игрока через GameData"""
        game_data.add_item(
            item_id=item.item_id,
            name=item.name,
            count=item.count,
            stackable=item.is_stackable
        )


    def check_lock_attempt(self, direction: str) -> tuple:
        """
        Проверяет попытку взлома.
        Возвращает: (успех, завершено, текущая_последовательность)
        """
        self.player_sequence += direction
        if not self.lock_sequence.startswith(self.player_sequence):
            self.player_sequence = ""
            return None, True, ""

        # Если ввели достаточно символов
        if self.player_sequence == self.lock_sequence:
            return True, True, self.player_sequence  # Успех!

        # Еще вводим
        return None, False, self.player_sequence


