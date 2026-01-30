import arcade
from config import constants as C


class ChestSprite(arcade.Sprite):
    """Визуальное представление сундука"""

    def __init__(self, texture, texture_open, x: float, y: float, event=None, scale=C.SCALE_FACTOR):
        super().__init__(texture, scale=scale)

        self.center_x = x
        self.center_y = y

        # Связь с событием
        self.event = event
        self.is_opened = False

        # Текстуры для разных состояний
        self.texture_closed = texture
        self.texture_open = texture_open

    def update_visual(self):
        """Обновляет визуал в зависимости от состояния"""
        if self.event and self.event.is_empty:
            self.is_opened = True
            if self.texture_open:
                self.texture = self.texture_open
            else:
                # Делаем полупрозрачным
                self.alpha = 128

    def draw_debug(self):
        """Отладочная отрисовка"""
        # Хитбокс
        color = arcade.color.RED
        if self.event:
            if self.event.is_empty:
                color = arcade.color.GRAY
            elif self.event.is_locked:
                color = arcade.color.ORANGE
            else:
                color = arcade.color.GREEN

        arcade.draw_rect_outline(
            arcade.rect.XYWH(self.center_x, self.center_y, self.width, self.height),
            color, 2
        )
