import arcade
import time
from typing import List, Dict

from .base_state import BaseState
from src.core.dialogue_manager import dialogue_manager
from config import constants as C


class DialogueState(BaseState):
    """Диалоговое состояние с одним окном сверху и выбором снизу"""

    def __init__(self, gsm, asset_loader):
        super().__init__("dialogue", gsm, asset_loader)

        # Текущий диалог
        self.current_npc = None  # Текущий объект NPC
        self.current_npc_name = ""  # Имя текущего NPC (для обращения к БД)
        self.current_topic = ""

        # Реплики NPC по теме
        self.dialog_lines: List[Dict] = []
        self.current_line_index = 0
        self.displayed_text = ""

        # Ответы игрока
        self.responses: List[Dict] = []
        self.selected_index = 0

        # Анимация текста
        self.text_speed = 0.05
        self.text_timer = 0
        self.is_text_complete = False

        # Управление
        self.key_cooldown = 0.15
        self.last_key_time = 0

        # Размеры окон
        self.dialog_window_height = C.SCREEN_HEIGHT * 0.3  # Окно диалога сверху
        self.choice_window_height = C.SCREEN_HEIGHT * 0.25  # Окно выбора снизу

        # Состояние
        self.state = "npc_speaking"  # "npc_speaking", "player_choosing"

        # Сбор всех NPC в сцене для переключения
        self.all_npcs = {}  # Будет заполнено при входе

        # Цвета
        self.npc_text_color = C.DEEPSEEK_COLOR
        self.player_text_color = arcade.color.LIGHT_GREEN
        self.selection_color = C.UI_MAIN_COLOR
        self.text_color = C.TEXT_COLOR
        self.window_bg_color = (30, 30, 40, 230)
        self.choice_bg_color = (40, 30, 30, 230)

    def on_enter(self, **kwargs):
        """Начинаем диалог с NPC"""
        self.current_npc = kwargs.get("npc")

        if not self.current_npc:
            self.logger.error("NPC не передан в диалог")
            self.gsm.pop_overlay()
            return

        self.current_npc_name = self.current_npc.name # так удобнее

        # Собираем всех NPC в сцене (для переключения между ними)
        self._collect_all_npcs()

        # Получаем активную тему
        self.current_topic = dialogue_manager.get_active_topic(self.current_npc_name)

        # Загружаем диалог
        self._load_dialog()

        self.logger.debug(f"Начало диалога с {self.current_npc_name}, тема: {self.current_topic}")
        self.state = "npc_speaking"

    def _collect_all_npcs(self):
        """Собирает всех NPC в текущей сцене"""
        self.all_npcs = {}

        # Получаем ссылку на игровое состояние
        game_state = self.gsm.current_state

        if hasattr(game_state, 'mobs'):
            for mob in game_state.mobs:
                if hasattr(mob, 'can_dialogue') and mob.can_dialogue:
                    self.all_npcs[mob.name.lower()] = mob
                    self.logger.debug(f"Найден NPC: {mob.name}")

    def _load_dialog(self):
        """Загружает реплики NPC для текущей темы"""
        self.dialog_lines = dialogue_manager.get_dialog(
            self.current_npc_name,
            self.current_topic
        )

        # Сбрасываем состояние
        self.current_line_index = 0
        self.displayed_text = ""
        self.is_text_complete = False
        self.text_timer = 0

        if not self.dialog_lines:
            self.logger.warning(f"Нет реплик для {self.current_npc_name}.{self.current_topic}")
            self._show_responses()

    def _show_responses(self):
        """Показывает варианты ответов игрока"""
        self.responses = dialogue_manager.get_responses(
            self.current_npc_name,
            self.current_topic
        )

        if self.responses:
            self.state = "player_choosing"
            self.selected_index = 0
        else:
            # Нет ответов - завершаем диалог
            self.logger.warning(f"Нет ответов для {self.current_npc_name}.{self.current_topic} - завершение")
            self.gsm.pop_overlay()

    def _select_response(self):
        """Обрабатывает выбор ответа игроком"""
        if not self.responses or self.selected_index >= len(self.responses):
            return

        response = self.responses[self.selected_index]

        # Обрабатываем через DialogueManager
        next_npc, next_npc_name, next_topic, triggered_events = dialogue_manager.process_player_choice(
            self.current_npc_name,
            self.current_topic,
            self.selected_index,
            self.all_npcs
        )
        # ВЫПОЛНЯЕМ ТРИГГЕРЫ СРАЗУ
        if triggered_events:
            self._execute_trigger_events(triggered_events)

        if next_topic:
            # Переход к новой теме или NPC
            if next_npc and next_npc != self.current_npc:
                self.current_npc = next_npc
                self.current_npc_name = next_npc_name
                self.current_topic = next_topic
                self._load_dialog()
                self.state = "npc_speaking"
            else:
                self.current_topic = next_topic
                self._load_dialog()
                self.state = "npc_speaking"
        else:
            self.gsm.pop_overlay()

    def _execute_trigger_events(self, events: List[Dict]):
        """Выполняет триггерные события"""
        from ..core.game_data import game_data
        from ..ui.notification_system import notifications as ns

        for event in events:


            event_type = event['type']
            params = event['params']
            try:
                if event_type == "give_item":
                    # give_item:apple:1
                    item_id = params[0]
                    count = int(params[1]) if len(params) > 1 else 1
                    game_data.add_item(item_id, count=count)
                    ns.notification(f"Получено: {item_id} x{count}")

                elif event_type == "remove_item":
                    # remove_item:coin:100
                    item_id = params[0]
                    count = int(params[1]) if len(params) > 1 else 1
                    if game_data.remove_item(item_id, count):
                        ns.notification(f"Потрачено: {item_id} x{count}")

                elif event_type == "change_npc_topic":
                    # change_npc_topic:охранник:friendly
                    npc_name = params[0]
                    new_topic = params[1]
                    dialogue_manager.set_active_topic(npc_name, new_topic)

                elif event_type == "change_property":
                    # change_property:артемий:behavior:aggressive

                    npc_name = params[0]
                    property_name = params[1]
                    property_value = params[2]
                    # Ищем NPC в сцене
                    for mob in self.gsm.current_state.mobs:
                        if hasattr(mob, 'name') and mob.name.lower() == npc_name.lower():
                            # Меняем свойство
                            if hasattr(mob, property_name):
                                # Преобразуем значение
                                if property_value.lower() == 'true':
                                    value = True
                                elif property_value.lower() == 'false':
                                    value = False
                                elif property_value.isdigit():
                                    value = int(property_value)
                                else:
                                    value = property_value

                                setattr(mob, property_name, value)
                            break

                elif event_type == "teleport_player":
                    # teleport_player:map_name:x:y
                    map_name = params[0] if len(params) > 0 else None
                    x = int(params[1]) if len(params) > 1 else 0
                    y = int(params[2]) if len(params) > 2 else 0

                    # Вызываем телепорт
                    self.gsm.current_state.teleport_to(x, y, map_name)

                elif event_type == "unlock_door":
                    # unlock_door:door_1
                    door_id = params[0]
                    # TODO: Реализовать открытие дверей
                    ns.notification(f"Дверь {door_id} открыта")

                elif event_type == "start_quest":
                    # start_quest:fix_computer
                    quest_id = params[0]
                    # TODO: Реализовать систему квестов
                    ns.notification(f"Задание получено: {quest_id}")

                elif event_type == "complete_quest":
                    # complete_quest:fix_computer
                    quest_id = params[0]
                    # TODO: Реализовать систему квестов
                    ns.notification(f"Задание завершено: {quest_id}")

                elif event_type == "finishgame":
                    self.gsm.switch_to("finish")

            except Exception as e:
                self.logger.error(f"Ошибка выполнения триггера {event}: {e}")

    def update(self, delta_time: float):
        """Обновление анимации текста"""
        if self.state == "npc_speaking" and not self.is_text_complete:
            if self.current_line_index < len(self.dialog_lines):
                current_line = self.dialog_lines[self.current_line_index]['text']
                self.text_timer += delta_time

                chars_to_show = int(self.text_timer / self.text_speed)
                if chars_to_show > len(current_line):
                    chars_to_show = len(current_line)
                    self.is_text_complete = True

                self.displayed_text = current_line[:chars_to_show]

    def draw(self):
        """Отрисовка диалога"""
        C.draw_dark_background()

        # Окно диалога сверху
        self._draw_dialog_window()

        # Окно выбора снизу (если нужно)
        if self.state == "player_choosing":
            self._draw_choice_window()

    def _draw_dialog_window(self):
        """Окно диалога в верхней части экрана"""
        window_x = C.SCREEN_WIDTH // 2
        window_y = C.SCREEN_HEIGHT - self.dialog_window_height *0.55

        # Фон окна
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                window_x, window_y,
                C.SCREEN_WIDTH * 0.8, self.dialog_window_height
            ),
            self.window_bg_color
        )

        # Рамка
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                window_x, window_y,
                C.SCREEN_WIDTH * 0.8, self.dialog_window_height
            ),
            self.npc_text_color, 2
        )

        # Имя говорящего
        speaker_name = self.current_npc_name if self.state == "npc_speaking" else "Вы"
        speaker_color = self.npc_text_color if self.state == "npc_speaking" else self.player_text_color

        arcade.Text(
            speaker_name,
            window_x,
            window_y + self.dialog_window_height // 2 - 30,
            speaker_color, 24,
            anchor_x="center", anchor_y="center",
            bold=True
        ).draw()

        # Разделительная линия под именем
        line_y = window_y + self.dialog_window_height * 0.2
        arcade.draw_line(
            C.SCREEN_WIDTH * 0.15, line_y,
            C.SCREEN_WIDTH *0.85, line_y,
            speaker_color, 1
        )

        # Текст диалога
        text_to_display = ""
        if self.state == "npc_speaking":
            text_to_display = self.displayed_text
        elif self.state == "player_choosing" and self.responses:
            # Показываем выбранный ответ
            if self.selected_index < len(self.responses):
                text_to_display = self.responses[self.selected_index]['chat_text']

        if text_to_display:
            arcade.Text(
                text_to_display,
                C.SCREEN_WIDTH*0.14,  # Отступ слева
                window_y - 30,
                self.text_color, 20,
                width=C.SCREEN_WIDTH - 120,
                multiline=True
            ).draw()

        # Индикатор продолжения (только при речи NPC)
        if self.state == "npc_speaking" and self.is_text_complete:
            if int(time.time() * 2) % 2 == 0:  # Мигание
                arcade.Text(
                    "► Нажмите ENTER",
                    C.SCREEN_WIDTH *0.85,
                    window_y - self.dialog_window_height // 2 + 30,
                    self.text_color, 14,
                    anchor_x="right"
                ).draw()

    def _draw_choice_window(self):
        """Окно выбора ответов в нижней части экрана"""
        if not self.responses:
            return

        window_x = C.SCREEN_WIDTH // 2
        window_y = self.choice_window_height * 0.55

        # Фон окна
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                window_x, window_y,
                C.SCREEN_WIDTH*0.7, self.choice_window_height
            ),
            self.choice_bg_color
        )

        # Рамка
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                window_x, window_y,
                C.SCREEN_WIDTH*0.7, self.choice_window_height
            ),
            self.player_text_color, 2
        )

        # Заголовок
        arcade.Text(
            "Выберите ответ:",
            window_x,
            window_y + self.choice_window_height // 2 - 25,
            self.player_text_color, 20,
            anchor_x="center", anchor_y="center"
        ).draw()

        # Варианты ответов
        start_y = window_y + self.choice_window_height // 2 - 60
        spacing = 30

        for i, response in enumerate(self.responses):
            color = self.selection_color if i == self.selected_index else self.text_color

            arcade.Text(
                f"{i + 1}. {response['button_text']}",
                C.SCREEN_WIDTH * 0.2,  # Отступ слева
                start_y - i * spacing,
                color, 18,
                width=C.SCREEN_WIDTH - 200,
                multiline=True
            ).draw()

    def handle_key_press(self, key, modifiers):
        """Обработка клавиш в диалоге"""
        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        # ESC для выхода
        if self.gsm.input_manager.get_action("escape"):
            self.gsm.pop_overlay()
            self.last_key_time = current_time
            return

        # Обработка в зависимости от состояния
        if self.state == "npc_speaking":
            self._handle_npc_speaking_state()
        elif self.state == "player_choosing":
            self._handle_player_choosing_state(key)

        self.last_key_time = current_time

    def _handle_npc_speaking_state(self):
        """Обработка ввода при речи NPC"""
        if self.gsm.input_manager.get_action("select"):
            if not self.is_text_complete:
                # Пропустить анимацию текста
                current_line = self.dialog_lines[self.current_line_index]['text']
                self.displayed_text = current_line
                self.is_text_complete = True
            else:
                # Перейти к следующей реплике или ответам
                if self.current_line_index < len(self.dialog_lines) - 1:
                    # Следующая реплика NPC
                    self.current_line_index += 1
                    self.displayed_text = ""
                    self.is_text_complete = False
                    self.text_timer = 0
                else:
                    # Все реплики закончились - показываем ответы
                    self._show_responses()

    def _handle_player_choosing_state(self, key):
        """Обработка ввода при выборе ответа"""
        if self.gsm.input_manager.get_action("up"):
            self.selected_index = max(0, self.selected_index - 1)

        elif self.gsm.input_manager.get_action("down"):
            self.selected_index = min(len(self.responses) - 1, self.selected_index + 1)

        elif self.gsm.input_manager.get_action("select"):
            self._select_response()

    def on_exit(self):
        """Выход из диалога"""
        # Сброс всех данных
        self.current_npc = None
        self.current_npc_name = ""
        self.current_topic = ""
        self.dialog_lines = []
        self.responses = []
        self.state = "npc_speaking"
        self.all_npcs = {}