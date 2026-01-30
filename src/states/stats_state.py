import arcade
from .base_state import BaseState
from config import constants as C


class StatsState(BaseState):
    """Меню характеристик """

    def __init__(self, gsm, asset_loader):
        super().__init__("stats", gsm, asset_loader)

        self.level = None
        self.exp = None
        self.req_exp = None
        self.speed = None
        self.strength = None

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.title_color = C.UI_TITLE_COLOR
        self.menu_background_color = C.MENU_BACKGROUND_COLOR_TRANSLUCENT

        # Размеры окна меню
        self.window_width = self.gsm.window.width // 2
        self.window_height = self.gsm.window.height // 2

    def on_enter(self, **kwargs):
        self.level = self._get_player("level")
        self.exp = self._get_player("exp")
        self.req_exp = self._get_player("req_exp")
        self.speed = self._get_player("speed")
        self.strength = self._get_player("strength")

    def _get_player(self, arg):
        return str(self.game_data.get_player(arg))

    def on_exit(self):
        """Выход из меню паузы"""

    def update(self, delta_time):
        pass

    def draw(self):
        """Отрисовка меню паузы ПОВЕРХ игры"""
        C.draw_dark_background()

        # Окно меню (в центре экрана)
        window_x = self.gsm.window.width // 2
        window_y = self.gsm.window.height // 2

        # Фон окна
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                window_x, window_y,
                self.window_width, self.window_height),
            self.menu_background_color
        )

        # Рамка окна
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                window_x, window_y,
                self.window_width, self.window_height),
            self.main_color, 3
        )

        # Заголовок
        arcade.Text(
            "Характеристики",
            window_x, window_y * 1.45,
            self.main_color,
            30,
            align="center",
            anchor_x="center",
            anchor_y="center",
            bold=True
        ).draw()

        arcade.Text(
            f"Уровень: {self.level}",
            window_x * 0.55, window_y * 1.34,
            self.text_color,
            20
        ).draw()

        arcade.Text(
            f"Опыт: {self.exp}/{self.req_exp}",
            window_x * 0.55, window_y * 1.25,
            self.text_color,
            20
        ).draw()

        self._draw_current_bonuses(window_x, window_y)

    def _draw_current_bonuses(self, window_x, window_y):
        """Отрисовывает текущие бонусы от экипированных предметов."""

        # Считаем суммарные бонусы
        total_health = 0
        total_strength = 0
        total_speed = 0
        total_range = 0

        for slot in ["accessory_1", "accessory_2", "accessory_3"]:
            item_id = self.game_data.player_data["equipment"][slot]
            if item_id:
                from src.entities.items.item_factory import ItemFactory
                item_obj = ItemFactory.create(item_id, 1)
                if hasattr(item_obj, 'additional_health'):
                    total_health += item_obj.additional_health
                if hasattr(item_obj, 'additional_strength'):
                    total_strength += item_obj.additional_strength
                if hasattr(item_obj, 'additional_speed'):
                    total_speed += item_obj.additional_speed
                if hasattr(item_obj, 'additional_range'):
                    total_range += item_obj.additional_range

        bonus_text = "Бонусы от экипировки:."
        if total_health > 0:
            bonus_text += f"+{total_health} здоровья."
        if total_strength > 0:
            bonus_text += f"+{total_strength} силы."
        if total_speed > 0:
            bonus_text += f"+{total_speed} скорости."
        if total_range > 0:
            bonus_text += f"+{total_range} к обзору."

        bufs = bonus_text.split(".")
        print(bufs)
        for i ,text in enumerate(bufs):
            arcade.Text(f"{text}",
                        window_x * 1.1,
                        window_y *1.3 - i *0.07 * window_y,
                        arcade.color.LIGHT_GREEN, 14).draw()

    def handle_key_press(self, key, modifiers):
        """Обработка клавиш в меню паузы"""

        if self.gsm.input_manager.get_action("stats"):
            self.gsm.pop_overlay()

        elif self.gsm.input_manager.get_action("escape"):
            self.gsm.pop_overlay()
