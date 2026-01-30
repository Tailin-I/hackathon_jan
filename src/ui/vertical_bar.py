import arcade

from .ui_component import UIComponent


class VerticalBar(UIComponent):
    """Вертикальная полоска с иконкой"""

    def __init__(self, x, y, width=15, height=150,
                 bg_color=arcade.color.PURPLE_NAVY, fill_color=arcade.color.PURPLE, icon_texture=None):
        super().__init__(x, y, width, height)
        self.bg_color = bg_color

        self.fill_color = fill_color
        self.icon_texture = icon_texture
        self.fill_percentage = 0.0  # 0.0 - 1.0
        self.value = 0
        self.max_value = 100

    def set_value(self, value, max_value=100):
        """Устанавливает значение полоски"""
        self.value = value
        self.max_value = max_value
        self.fill_percentage = value / max_value

    def draw(self):
        if not self.visible:
            return

        # Фон
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.x, self.y,
                self.width, self.height),
            self.bg_color
        )

        # Заполнение (снизу вверх)
        fill_height = self.height * self.fill_percentage
        if fill_height > 0:
            fill_y = self.y - self.height / 2 + fill_height / 2
            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                    self.x, fill_y,
                    self.width, fill_height),
                self.fill_color
            )

        # Рамка
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.x, self.y,
                self.width, self.height),
            arcade.color.GOLD, 1
        )
        # Иконка сверху (если есть)
        if self.icon_texture:
            icon_y = self.y + self.height / 2 + 5  # Чуть выше полоски
            arcade.draw_texture_rect(
                self.icon_texture,
                arcade.rect.XYWH(
                    self.x, icon_y,
                    32, 32)

            )