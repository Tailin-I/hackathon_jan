import arcade

from .ui_component import UIComponent


class FatigueBar(UIComponent):
    """Горизонтальная шкала здоровья"""

    def __init__(self, entity, x, y, width=200, height=20, font_size=12, border=2, icon_texture=None):
        super().__init__(x, y, width, height)
        self.entity = entity  # Сущность, за которой следим
        self.icon_texture = icon_texture
        # Цвета
        self.bg_color = arcade.color.BEIGE
        self.fill_color = arcade.color.FRENCH_BEIGE
        self.border_color = arcade.color.GOLD
        self.border_width = border
        self.font_size = font_size

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

        # Заполнение (процент здоровья)
        fill_width = max(0, (int(self.entity.fatigue) / max(int(self.entity.fatigue),
                                                            int(self.entity.max_fatigue))) * self.width)
        if fill_width > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                    self.x - self.width / 2 + fill_width / 2, self.y,
                    fill_width, self.height),
                self.fill_color
            )

        # Рамка
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.x, self.y,
                self.width, self.height),
            self.border_color, self.border_width
        )

        # Текст (опционально)
        arcade.Text(
            f"{self.entity.fatigue}/{self.entity.max_fatigue}",
            self.x, self.y,
            arcade.color.BEIGE,
            self.font_size,
            anchor_x="center", anchor_y="center"
        ).draw()

        # Иконка сверху (если есть)
        if self.icon_texture:
            icon_y = self.y + self.height *1.15  # Чуть выше полоски
            arcade.draw_texture_rect(
                self.icon_texture,
                arcade.rect.XYWH(
                    self.x, icon_y,
                    32, 32))


