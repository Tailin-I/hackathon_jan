import logging

import arcade
from typing import List
from .event import GameEvent
from .chest_event import ChestEvent
from .notification_event import NotificationEvent
from .teleport_event import TeleportEvent
from config import constants as C
from ..core.game_data import game_data
from ..core.resource_manager import resource_manager


# from ..ui.notification_system import notifications as ns


class EventManager:
    def __init__(self):
        """Инициализация менеджера событий."""
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.rm = resource_manager
        self.tile_size = C.TILE_SIZE

        # Логика событий (зоны взаимодействия из event Layer)
        self.events: List[GameEvent] = []

        # Визуальные спрайты (будут созданы из Tile Layer "chests_visual")
        self.chest_sprites = arcade.SpriteList()

        # Словарь для сохранения состояния событий (можно сохранять в GameData или в файл)
        self.event_states = {}  # {event_id: {"is_empty": bool, ...}}

    def save_event_state(self, event_id: str, state_data: dict):
        """Сохраняет состояние события"""
        self.event_states[event_id] = state_data.copy()
        self.logger.debug(f"Сохранено состояние для события {event_id}: {state_data}")

    def get_event_state(self, event_id: str) -> dict:
        """Возвращает сохраненное состояние события"""
        return self.event_states.get(event_id, {})

    def load_events_from_objects(self, object_list, scale: float = 1.0, map_name: str = None):
        """Загружает события (зоны взаимодействия) из events"""
        for i, obj in enumerate(object_list):
            event = self._create_event_from_object(obj, scale, i, map_name)
            if event:
                # Восстанавливаем состояние из сохраненного
                saved_state = self.get_event_state(event.event_id)
                if saved_state:
                    event.is_empty = saved_state.get("is_empty", False)
                    event.logger.info(f"Восстановлено состояние для {event.event_id}: is_empty={event.is_empty}")

                self.events.append(event)

    def _create_event_from_object(self, obj, scale: float, index: int, map_name: str = None):
        """Создаёт события"""
        try:
            points = obj.shape

            left = points[0][0]
            top = points[0][1]
            right = points[1][0]
            bottom = points[3][1]

            width = right - left
            height = bottom - top

            x = left
            y = top

            if height < 0:
                height = abs(height)
                y = bottom

            # Получаем свойства
            properties = getattr(obj, 'properties', {})
            event_type = getattr(obj, 'type', 'trigger').lower()
            name = getattr(obj, 'name', '!')
            event_id = properties.get('id', f"{event_type}_{index}_{map_name or 'unknown'}")

            # Создаем событие
            if event_type == "chest":
                event = ChestEvent(event_id, name, (x, y, width, height), properties)
                event.map_name = map_name
                # Восстанавливаем состояние из game_data
                saved_data = game_data.mobs_data.get(event_id)
                if saved_data and saved_data.get("is_empty", False):
                    event.is_empty = True
                    if event.sprite:
                        event.sprite.update_visual()

                return event
            elif event_type == "teleport":
                event = TeleportEvent(event_id, name, (x, y, width, height), properties)
                return event
            elif event_type == "notification":
                event = NotificationEvent(event_id, name, (x, y, width, height), properties)
                return event
            else:
                event = GameEvent(event_id, name, event_type, (x, y, width, height), properties)
                return event

        except Exception as e:
            self.logger.warning(f"Ошибка создания события {index}({name}): {e}")
            return None

    def find_nearest_chest_event(self, x: float, y: float, max_distance: float = None):
        """Находит ближайшее событие сундука к координатам."""
        if max_distance is None:
            max_distance = self.tile_size * 3

        nearest_event = None
        min_distance = float('inf')

        for event in self.events:
            if event.type == "chest":

                # Вычисляем расстояние
                distance = ((x - event.center_x) ** 2 + (y - event.center_y) ** 2) ** 0.5

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_event = event

        return nearest_event

    def update(self, delta_time: float):
        """Обновляет логику событий"""
        for event in self.events:
            event.update(delta_time)

        # Обновляем визуалы сундуков
        for sprite in self.chest_sprites:
            if hasattr(sprite, 'update_visual'):
                sprite.update_visual()

    def check_collisions(self, player, game_state):
        """Проверяет коллизии игрока с событиями"""
        if not player:
            return

        player_rect = (
            player.center_x - player.width / 2,
            player.center_y - player.height / 2,
            player.width,
            player.height
        )

        for event in self.events:
            if event.check_collision(player_rect):

                # ДЛЯ ВСЕХ СОБЫТИЙ проверяем дистанцию через общий метод
                if self._is_player_close_enough(player, event):
                    # Для сундуков проверяем кнопку взаимодействия
                    if event.type == "chest":
                        event.show_text_description = True
                        if hasattr(player, 'input_manager') and player.input_manager:
                            if player.input_manager.get_action('select'):
                                event.activate(player, game_state)
                                player.input_manager.reset_action("select")
                    else:
                        # Для других событий (телепортов) активируем сразу
                        event.activate(player, game_state)

    def _is_player_close_enough(self, player, event) -> bool:
        """Проверяет, достаточно ли близко игрок к событию."""

        # Дистанция
        distance = ((player.center_x - event.center_x) ** 2 +
                    (player.center_y - event.center_y) ** 2) ** 0.5

        # Максимальная дистанция для взаимодействия
        max_distance = self.tile_size * 1.5

        return distance <= max_distance

    def draw(self):
        """Отрисовывает визуальные элементы событий"""
        self.chest_sprites.draw()

        for i in self.events:
            if i.type == "chest":
                i.draw_names()

        if C.show_area_mode:
            for i in self.events:
                i.draw_debug()
