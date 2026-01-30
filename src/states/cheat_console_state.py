import arcade
from config.creature_config import CreatureConfig as MC
from src.states.base_state import BaseState
from src.world.map_loader import MapLoader
from config import constants as C


class CheatConsoleState(BaseState):
    """Чит-консоль поверх игры"""

    def __init__(self, gsm, asset_loader):
        super().__init__("cheat_console", gsm, asset_loader)
        self.map_loader = MapLoader()

        self.input_buffer = "|"  # Введенный текст
        self.cursor_visible = True
        self.can_close = False
        self.history = ["TP_15_10_moscow"]  # История команд

        self.count_to_text = 0

        self.back_color = (68, 71, 78, 180)
        self.main_color = C.DEEPSEEK_COLOR
        self.text_color = (240, 240, 240)

        # речь дип сика
        self.deep_seek_speech = []
        self.text_to_draw = []
        self.current_line = ""

        # история команд
        self.history_cursor = 0

    def handle_key_press(self, key, modifiers):
        if "|" in self.input_buffer:
            first_part, second_part = self.input_buffer.split("|")
            if self.gsm.input_manager.get_action("select") and first_part+second_part!="":
                self.execute_command(first_part + second_part)
                self._add_to_list(first_part + second_part)
                self.input_buffer = "|"
                self.can_close = True

            elif self.gsm.input_manager.get_action("left") and self.input_buffer.startswith("|") and len(
                    self.gsm.input_manager.get_key_string_for_code(key)) != 1 and len(self.history) > 0:
                self.input_buffer = self.input_buffer[1:]
            else:
                self.input_buffer = self.gsm.input_manager.typing(key, first_part, second_part)
        else:
            if self.gsm.input_manager.get_action("select"):
                self.input_buffer = self.history[self.history_cursor] + "|"
            elif self.gsm.input_manager.get_action("right"):
                self.input_buffer = "|" + self.input_buffer
            elif self.gsm.input_manager.get_action("up"):
                if self.history_cursor > 0:
                    self.history_cursor -= 1
            elif self.gsm.input_manager.get_action("down"):
                if self.history_cursor < len(self.history) - 1:
                    self.history_cursor += 1

        if self.gsm.input_manager.get_action("cheat_console") or self.gsm.input_manager.get_action("escape"):
            self.gsm.pop_overlay()

    def _add_to_list(self, text):
        """Добавляет в список и ограничивает его"""
        if self.history[0] != text:
            self.history.insert(0, text)
        if len(self.history) > 32:
            self.history = self.history[:-1]

    def draw(self):
        """Отрисовка консоли в своем стиле"""
        C.draw_dark_background()

        # ---ПАНЕЛЬ КОНСОЛИ---
        panel_width = self.gsm.window.width // 2
        panel_height = 2 * self.tile_size
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.gsm.window.width // 2 - self.tile_size, self.gsm.window.height - self.tile_size,
                panel_width, panel_height),
            self.back_color  # Темно-синий
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.gsm.window.width // 2 - self.tile_size, self.gsm.window.height - self.tile_size,
                panel_width, panel_height),
            self.main_color, 2
        )

        # ---РЕЧЬ ДИП СИКА---
        text = self.current_line
        if not self.text_to_draw:
            text = "..."
        arcade.Text(
            text,
            self.gsm.window.width // 2 - self.tile_size, self.gsm.window.height - self.tile_size,
            self.main_color, 24,
            anchor_x="center"
        ).draw()

        # ---ПОЛЕ ДЛЯ ВВОДА---
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.gsm.window.width // 2 - self.tile_size, self.gsm.window.height - 2 * self.tile_size,
                self.gsm.window.width // 2 - self.tile_size, self.tile_size),
            (0, 0, 0)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.gsm.window.width // 2 - self.tile_size, self.gsm.window.height - 2 * self.tile_size,
                self.gsm.window.width // 2 - self.tile_size, self.tile_size),
            self.back_color, 1
        )

        # ---ТЕКСТ---
        arcade.Text(
            self.input_buffer,
            5.2 * self.tile_size, self.gsm.window.height - 2 * self.tile_size,
            self.main_color, 20
        ).draw()

        # ---ИСТОРИЯ КОМАНД---
        panel_width = self.tile_size * 3.2
        panel_height = self.gsm.window.height - self.tile_size
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                2.2 * self.tile_size, self.gsm.window.height // 2,
                panel_width, panel_height),
            self.back_color  # Темно-синий
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                2.2 * self.tile_size,
                self.gsm.window.height // 2,
                panel_width,
                panel_height
            ), self.main_color, 2
        )

        for i in range(len(self.history) - 1, -1, -1):
            color = self.text_color
            if self.history_cursor == i and "|" not in self.input_buffer:
                color = self.main_color
            text = self.history[i]
            if len(text) > 10:
                text = text[:15] + "..."
            arcade.Text(
                text,
                0.7 * self.tile_size, self.gsm.window.height - self.tile_size - self.tile_size // 3 * i,
                color, 9
            ).draw()

        # ---РЕЧЬ ДИП СИКА---
        panel_width = self.tile_size * 5
        panel_height = self.gsm.window.height - self.tile_size
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.gsm.window.width * 0.85, self.gsm.window.height // 2,
                panel_width, panel_height),
            self.back_color  # Темно-синий
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.gsm.window.width * 0.85, self.gsm.window.height // 2,
                panel_width, panel_height),
            self.main_color, 2
        )

        for i in range(len(self.deep_seek_speech)):
            arcade.Text(
                self.deep_seek_speech[i],
                self.gsm.window.width * 0.75,
                self.gsm.window.height * 0.93 - self.tile_size // 3 * i,
                self.text_color, 14
            ).draw()

    def on_enter(self, **kwargs):
        self.text_to_draw = [" ", "Бог, слушает тебя..."]
        self.can_close = False

    def on_exit(self):
        pass

    def update(self, delta_time: float):
        self.count_to_text += delta_time
        if len(self.text_to_draw) == 0 and self.can_close:
            self.deep_seek_speech.append(" ")
            self.deep_seek_speech.append("Бог, слушает тебя...")
            self.gsm.pop_overlay()
            self.can_close = False

        if self.count_to_text > 0.035:
            # Если есть текст для отображения и мы еще не вывели все строки
            if self.text_to_draw and len(self.current_line) < len(self.text_to_draw[0]):
                # Добавляем следующий символ к текущей строке
                self.current_line += self.text_to_draw[0][len(self.current_line)]
                self.count_to_text = 0
            elif self.text_to_draw and len(self.current_line) >= len(self.text_to_draw[0]):
                # Если строка полностью выведена, добавляем ее в историю речи
                self.deep_seek_speech.append(self.current_line)
                self.text_to_draw.pop(0)  # Удаляем выведенную строку
                self.current_line = ""  # Сбрасываем текущую строку
                self.count_to_text = 0

                # Ограничиваем историю речи
                if len(self.deep_seek_speech) > 26:
                    self.deep_seek_speech = self.deep_seek_speech[10:]

    def execute_command(self, command):
        if command == "GODMOD":
            health_to_add = 9999
            self.gsm.current_state.player.max_health = health_to_add
            self.gsm.current_state.player.health = health_to_add
            self.text_to_draw = [
                "Помни кто здесь бог!",
                f"ОЗ = {health_to_add}",
                "Теперь тебя тоже не убить"
            ]
        elif command == "KILL":
            mob = self.gsm.current_state.mob_under_focus

            if mob:
                mob.health = 0
                mob.if_alive()
                self.gsm.current_state.mob_under_focus = None

                self.text_to_draw = [
                    "АРХИВИРУЮ",
                    f"прощай {mob.name}"
                ]
            else:
                self.text_to_draw = [
                    "Кровожадное чудовище..."

                ]
        elif command == "SAVE":
            self.game_data.save_to_file()

            self.text_to_draw = ["Сохраняю..."]


        elif command == "LOAD":

            self.game_data.load_from_file()

            self.text_to_draw = ["Загружаю..."]

        elif command.startswith("TP_"):
            parts = command.split("_")

            try:
                # Проверка количества аргументов
                if len(parts) not in (3, 4):
                    self.text_to_draw = ["и куда мне тебя переносить?", "..."]
                    return

                x = int(parts[1])
                y = int(parts[2])
                mp = parts[3].lower() if len(parts) == 4 else None

                # Телепорт игрока
                self.gsm.current_state.teleport_to(x, y, mp)

                # Обновляем данные
                if mp is None:

                    self.text_to_draw = [
                        "Дарую новые координаты!",
                        f"x:{x}, y:{y}",
                        "Бессмысленная трата ресурсов..."
                    ]
                else:
                    self.map_loader.load(
                        f"maps/{mp}.tmx"
                    )
                    self.text_to_draw = [
                        "Дарую новые координаты!",
                        f"x:{x}, y:{y}, map:{mp}",
                        "Совсем лицеисты обленились"
                    ]

            except ValueError:
                self.text_to_draw = [
                    "Чего ты пытаешься добиться?",
                    "Я не понимаю",
                    "..."
                ]

        elif command == "DEBUG":
            C.debug_mode = not C.debug_mode

            if C.debug_mode:
                self.text_to_draw = ["Хммммм",
                                     "И правда что-то барахлит..",
                                     "Смотри!.",
                                     "Но не везде..."]
            else:
                self.text_to_draw = ["Ок",
                                     "Хватит с тебя!"]

        elif command == "GHOST":
            C.ghost_mode = not C.ghost_mode

            if C.ghost_mode:
                self.text_to_draw = ["Ты прав!",
                                     "Зачем нужны стены?",
                                     "Теперь ты призрак"]
            else:
                self.text_to_draw = ["Нагулялся?)",
                                     "..."]
        elif command == "AREAS":
            C.show_area_mode = not C.show_area_mode

            if C.show_area_mode:
                self.text_to_draw = ["Не забывай кто здесь бог!",
                                     "АБРАКАДАБРА",
                                     "Загляни в неизведанное.",
                                     "Но не везде..."]
            else:
                self.text_to_draw = ["ТРАХ-ТИБИДОХ",
                                     "теперь...",
                                     "Ты нормальный человек"]
        elif command == "STOP":
            C.debug_pause = not C.debug_pause

            if C.debug_pause:
                self.text_to_draw = ["ПАУЗА!",
                                     "Изучай...",
                                     "Тебе никто не помешает",
                                     "(кроме багов)"]
            else:
                self.text_to_draw = ["Продолжим..."]

        elif command == "GOODBYE":
            C.cheat_mode = False

            self.text_to_draw = ["Нагулялся?",
                                 "Ну пока.."]
        elif command == "END":
            self.gsm.switch_to("finish")

