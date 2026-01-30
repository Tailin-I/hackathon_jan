import arcade
import time
from .base_state import BaseState
from config import constants as C
from ..ui.notification_system import notifications as ns



class LobbyState(BaseState):
    """
    Игровое лобби, первое окно которое встречает пользователя
    """

    def __init__(self, gsm, asset_loader):
        super().__init__("lobby", gsm, asset_loader)
        ns.notification("Добро пожаловать в первую версию игры ITcubia!")
        # Пункты меню
        self.menu_items = [
            {"text": "НОВАЯ ИГРА", "action": "new_game"},
            {"text": "ЗАГРУЗИТЬ", "action": "load"},
            {"text": "НАСТРОЙКИ", "action": "settings"},
            {"text": "ВЫХОД", "action": "exit"}
        ]

        # Выбранный пункт
        self.selected_index = 0
        self.last_selected_index = self.selected_index

        # Для предотвращения быстрых повторных нажатий
        self.key_cooldown = 0.15  # секунд
        self.last_key_time = 0

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.selected_color = C.UI_MAIN_COLOR
        self.title_color = C.UI_TITLE_COLOR
        self.subtitle_color = C.UI_SUBTITLE_COLOR

        # Звуки
        self.has_sounds = False

    def on_enter(self, **kwargs):
        """Вход в лобби"""
        # Сбрасываем таймеры
        self.last_key_time = time.time()
        # Запускаем фоновую музыку для лобби
        self.sound_manager.play_music("menu_music")

    def on_exit(self):
        """Выход из лобби"""


    def on_pause(self):
        """Пауза (не используется в лобби)"""
        pass

    def on_resume(self):
        """Возобновление (не используется в лобби)"""
        pass

    def update(self, delta_time: float):
        pass

    def draw(self):
        """Отрисовка лобби"""
        # Очищаем экран красивым градиентом
        arcade.draw_texture_rect(
            self.asset_loader.load_background("lobby_background")
            , arcade.rect.XYWH(
            self.gsm.window.width // 2,
            self.gsm.window.height // 2,
            self.gsm.window.width,
            self.gsm.window.height,
        ))

        arcade.draw_rect_filled(arcade.rect.XYWH(
            x=self.gsm.window.width//2,
            y=self.gsm.window.height//2,
            width=self.gsm.window.width,
            height=self.gsm.window.height),
            color=(0, 0, 0, 200))

        # Заголовок игры (с тенью)
        title_x = self.gsm.window.width // 2
        title_y = self.gsm.window.height * 0.75

        # Тень
        arcade.Text(
            "Россия многонациональна страна",
            title_x + 5, title_y - 5,
            arcade.color.BLACK,
            font_size=40,
            anchor_x="center",
            anchor_y="center",
            bold=True
        ).draw()

        # Основной текст
        arcade.Text(
            "Россия многонациональна страна",
            title_x, title_y,
            self.title_color,
            font_size=40,
            anchor_x="center",
            anchor_y="center",
            bold=True
        ).draw()

        # Подзаголовок
        arcade.Text(
            "Основано на реальных событиях",
            title_x, title_y - 80,
            self.subtitle_color,
            font_size=24,
            anchor_x="center",
            anchor_y="center"
        ).draw()

        # Подзаголовок
        arcade.Text(
            "Все совпадения НЕ случайны",
            title_x, title_y * 0.80,
            self.subtitle_color,
            font_size=24,
            anchor_x="center",
            anchor_y="center"
        ).draw()

        # Рисуем меню
        self._draw_menu()

    def _draw_menu(self):
        """Рисует пункты меню"""
        start_x = self.gsm.window.width // 2
        start_y = self.gsm.window.height * 0.5
        spacing = 70

        for i, item in enumerate(self.menu_items):
            # Выбираем цвет
            if i == self.selected_index:
                color = self.selected_color
                font_size = 42
                is_bold = True
            else:
                color = self.text_color
                font_size = 36
                is_bold = False

            # Рисуем текст пункта
            text = arcade.Text(
                item["text"],
                start_x,
                start_y - i * spacing,
                color,
                font_size=font_size,
                anchor_x="center",
                anchor_y="center",
                bold=is_bold
            )
            text.draw()

    def handle_key_press(self, key: int, modifiers: int):
        """Обработка нажатия клавиш"""
        if not self.gsm.input_manager:
            return

        # Проверяем кд (чтобы не было слишком быстрых нажатий)
        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        # Навигация ВВЕРХ
        if self.gsm.input_manager.get_action("up"):
            self.sound_manager.play_ui("menu_navigation")
            self.last_selected_index = self.selected_index
            self.selected_index = max(0, self.selected_index - 1)
            if self.last_selected_index == self.selected_index:
                self.selected_index = len(self.menu_items)-1

            self.last_key_time = current_time

        # Навигация ВНИЗ
        elif self.gsm.input_manager.get_action("down"):
            self.sound_manager.play_ui("menu_navigation")
            self.last_selected_index = self.selected_index
            self.selected_index = min(len(self.menu_items) - 1, self.selected_index + 1)
            if self.last_selected_index == self.selected_index:
                self.selected_index = 0
            self.last_key_time = current_time

        # Выбор пункта (ENTER/E)
        elif self.gsm.input_manager.get_action("select"):
            self._select_menu_item()
            self.last_key_time = current_time

        # Выход (ESC)
        elif self.gsm.input_manager.get_action("escape"):
            self._confirm_exit()
            self.last_key_time = current_time

    def _select_menu_item(self):
        """Обрабатывает выбор пункта меню"""
        selected = self.menu_items[self.selected_index]
        # Воспроизводим звук
        self.sound_manager.play_ui("menu_select")

        if selected["action"] == "new_game":
            # Полностью сбрасываем game_data
            self.game_data.reset_to_defaults()

            # Очищаем entity_manager
            from src.entities.entity_manager import entity_manager
            entity_manager.clear_all()

            # Переключаемся на игру
            self.gsm.switch_to("game")

        if selected["action"] == "load":
            self.game_data.load_from_file()
            self.gsm.switch_to("game")

        elif selected["action"] == "settings":
            self.gsm.switch_to("settings")

        elif selected["action"] == "exit":
            self._confirm_exit()

    def _confirm_exit(self):
        """Подтверждение выхода"""
        # Можно добавить диалог подтверждения
        # Пока просто закрываем
        self.gsm.window.close()
