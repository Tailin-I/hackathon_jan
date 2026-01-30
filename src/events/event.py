import logging
from typing import Dict, Any
from config import constants as C

import arcade


class GameEvent:
    """Базовый класс для игровых событий"""

    def __init__(self, event_id: str, name: str, event_type: str, rect: tuple, properties: Dict[str, Any] = None):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.show_text_description = False
        self.tileSize = 64

        self.event_id = event_id
        self.name = name
        self.type = event_type  # "chest", "teleport", "dialogue"
        self.rect = rect  # (x, y, width, height)
        self.properties = properties or {}
        self.activated = False
        self.cooldown = 0
        self.max_cooldown = 30  # 0.5 секунды при 60 FPS

        # координаты события
        self.x, self.y, self.width, self.height = self.rect
        self.center_x = self.x + self.width / 2
        self.center_y = self.y + self.height / 2

    def check_collision(self, player_rect) -> bool:
        """Проверяет пересечение с игроком"""
        px, py, pw, ph = player_rect

        # Простая проверка прямоугольников
        collision = (px < self.x + self.width and
                     px + pw > self.x and
                     py < self.y + self.height and
                     py + ph > self.y)

        if collision and hasattr(self, 'logger'):
            self.logger.debug(f"Коллизия с {self.event_id}")

        return collision

    def activate(self, player, game_state):
        """Активировать событие - будет переопределено"""
        pass

    def update(self, delta_time: float):
        """Обновление кулдауна"""
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.cooldown <= 0:
            self.activated = False

    def draw_names(self):
        pass
    def draw_debug(self):
        """визуализация события"""

        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.center_x, self.center_y, self.width, self.height),
            C.DEEPSEEK_COLOR_TRANSLUCENT
        )

        arcade.Text(
            self.name,
            self.x,
            self.center_y ,
            C.DEEPSEEK_COLOR,
            20
        ).draw()

    def set_sprite(self, sprite):
        pass
