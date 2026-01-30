import logging
import json
import os
import arcade
from typing import Dict, List, Set

from src.core.resource_manager import resource_manager


class InputManager:
    """Простой и надежный менеджер ввода"""

    def __init__(self, config_file=resource_manager.get_full_path("settings/key_bindings.json")):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file

        # Состояние
        self.keys_pressed: Set[int] = set()  # Нажатые клавиши (коды)
        self.actions: Dict[str, bool] = {}  # Состояния действий

        # Привязки клавиш
        self._key_bindings: Dict[str, List[str]] = {}  # Действие -> [ключи как строки]
        self._key_codes: Dict[str, List[int]] = {}  # Действие -> [коды клавиш]

        # Маппинг строк->коды и коды->строки
        self._init_key_mapping()

        # Дефолтные привязки
        self._default_bindings = {
            'up': ["W", "UP"],
            'down': ["S", "DOWN"],
            'left': ["A", "LEFT"],
            'right': ["D", "RIGHT"],

            'attack': ["C"],

            'select': ["ENTER"],
            'escape': ["ESCAPE"],
            'stats': ["B"],
            'inventory': ["I", "TAB"],
            'heal': ["H"],


            # читы
            'cheat_console': ["F2"],
            'ghost_mode': ["NUM_0"],
            'debug_mode': ["NUM_1"],
            'show_area_mode': ["NUM_3"],
            'debug_pause': ["NUM_9"],

            'tp_up': ["NUM_8"],
            'tp_down': ["NUM_5"],
            'tp_left': ["NUM_4"],
            'tp_right': ["NUM_6"],

        }

        # Загружаем настройки
        self._load_config()

        # Инициализируем состояния действий
        for action in self._key_bindings:
            self.actions[action] = False

    # ==================== ОСНОВНОЙ ИНТЕРФЕЙС ====================

    def get_action(self, action_name: str) -> bool:
        """Проверяет, активно ли действие"""
        return self.actions.get(action_name, False)

    def reset_action(self, action_name: str):
        """Сбрасывает действие (принудительно отключает)"""
        if action_name in self.actions:
            self.actions[action_name] = False

            # Удаляем связанные клавиши из нажатых
            if action_name in self._key_codes:
                for key_code in self._key_codes[action_name]:
                    self.keys_pressed.discard(key_code)

    # ==================== ОБРАБОТКА СОБЫТИЙ ====================

    def on_key_press(self, key: int, modifiers: int):
        """Обработка нажатия клавиши"""
        self.keys_pressed.add(key)

        # Для направлений - эксклюзивный режим (только одно направление)
        direction = self._get_direction_for_key(key)
        if direction:
            self._handle_direction_press(direction)
        else:
            # Для остальных действий - просто обновляем состояние
            self._update_actions()

    def on_key_release(self, key: int, modifiers: int):
        """Обработка отпускания клавиши"""
        self.keys_pressed.discard(key)

        # Для направлений - особая логика
        direction = self._get_direction_for_key(key)
        if direction:
            self._handle_direction_release(direction)

        # Всегда обновляем состояния после отпускания
        self._update_actions()

    # ==================== ПРИВЯЗКА КЛАВИШ ====================

    def rebind_action(self, action_name: str, new_key: int) -> bool:
        """Переназначает клавишу для действия"""
        if action_name not in self._key_bindings:
            return False

        key_string = self._code_to_string.get(new_key)
        if not key_string:
            return False

        # Удаляем старые привязки этой клавиши у других действий
        for other_action in self._key_bindings:
            if key_string in self._key_bindings[other_action] and other_action != action_name:
                self._key_bindings[other_action].remove(key_string)
                self._key_codes[other_action] = [
                    code for code in self._key_codes[other_action]
                    if code != new_key
                ]

        # Добавляем новую привязку
        if key_string not in self._key_bindings[action_name]:
            self._key_bindings[action_name].append(key_string)
            self._key_codes[action_name].append(new_key)

        return self._save_config()

    def reset_to_defaults(self):
        """Сброс к настройкам по умолчанию"""
        self._key_bindings = {k: v.copy() for k, v in self._default_bindings.items()}
        self._key_codes = self._strings_to_codes(self._key_bindings)
        self._save_config()

    def get_action_info(self) -> Dict[str, Dict]:
        """Информация о всех привязках (для настроек)"""
        return {
            action: {
                'keys': codes,
                'key_names': self._key_bindings[action]
            }
            for action, codes in self._key_codes.items()
        }

    def clear_state(self):
        """Полностью очищает состояние ввода"""
        self.keys_pressed.clear()
        for action in self.actions:
            self.actions[action] = False
        self.logger.debug("Состояние ввода очищено")
        # ==================== ТИПИНГ (для текстового ввода) ====================

    def typing(self, key: int, first_part: str, second_part: str) -> str:
        """
        Обработка ввода текста. Возвращает новую строку с курсором.

        Args:
            key: Код клавиши
            first_part: Текст до курсора
            second_part: Текст после курсора

        Returns:
            Строка с обновленной позицией курсора
        """
        key_string = self.get_key_string_for_code(key)

        # Обработка цифр с NUM_ префиксом
        if key_string.startswith("NUM_"):
            key_string = key_string[-1]

        # Буквы и цифры
        if (key_string.isalpha() or key_string.isdigit()) and len(key_string) == 1:
            return f"{first_part}{key_string}|{second_part}"

        # Специальные клавиши
        handlers = {
            "SPACE": lambda: f"{first_part}_|{second_part}",
            "BACKSPACE": lambda: f"{first_part[:-1]}|{second_part}" if first_part else f"|{second_part}",
            "DELETE": lambda: f"{first_part}|{second_part[1:]}" if second_part else f"{first_part}|{second_part}",
            "LEFT": lambda: f"{first_part[:-1]}|{first_part[-1:]}{second_part}" if first_part else f"|{second_part}",
            "RIGHT": lambda: f"{first_part}{second_part[:1]}|{second_part[1:]}" if second_part else f"{first_part}|",
            "HOME": lambda: f"|{first_part}{second_part}",
            "END": lambda: f"{first_part}{second_part}|",
        }

        if key_string in handlers:
            return handlers[key_string]()

        # Для остальных клавиш - без изменений
        return f"{first_part}|{second_part}"

    def get_key_string_for_code(self, key_code: int) -> str:
        """Возвращает строковое представление клавиши по коду"""
        return self._code_to_string.get(key_code, f"Key_{key_code}")

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _init_key_mapping(self):
        """Инициализация маппинга клавиш"""
        # Строка -> код
        self._string_to_code = {
            # Буквы
            "A": arcade.key.A, "B": arcade.key.B, "C": arcade.key.C,
            "D": arcade.key.D, "E": arcade.key.E, "F": arcade.key.F,
            "G": arcade.key.G, "H": arcade.key.H, "I": arcade.key.I,
            "J": arcade.key.J, "K": arcade.key.K, "L": arcade.key.L,
            "M": arcade.key.M, "N": arcade.key.N, "O": arcade.key.O,
            "P": arcade.key.P, "Q": arcade.key.Q, "R": arcade.key.R,
            "S": arcade.key.S, "T": arcade.key.T, "U": arcade.key.U,
            "V": arcade.key.V, "W": arcade.key.W, "X": arcade.key.X,
            "Y": arcade.key.Y, "Z": arcade.key.Z,

            # Цифры
            "0": arcade.key.KEY_0, "1": arcade.key.KEY_1, "2": arcade.key.KEY_2,
            "3": arcade.key.KEY_3, "4": arcade.key.KEY_4, "5": arcade.key.KEY_5,
            "6": arcade.key.KEY_6, "7": arcade.key.KEY_7, "8": arcade.key.KEY_8,
            "9": arcade.key.KEY_9,

            "NUM_0": arcade.key.NUM_0, "NUM_1": arcade.key.NUM_1, "NUM_2": arcade.key.NUM_2,
            "NUM_3": arcade.key.NUM_3, "NUM_4": arcade.key.NUM_4, "NUM_5": arcade.key.NUM_5,
            "NUM_6": arcade.key.NUM_6, "NUM_7": arcade.key.NUM_7, "NUM_8": arcade.key.NUM_8,
            "NUM_9": arcade.key.NUM_9,

            # Функциональные
            "F1": arcade.key.F1, "F2": arcade.key.F2, "F3": arcade.key.F3,
            "F4": arcade.key.F4, "F5": arcade.key.F5, "F6": arcade.key.F6,
            "F7": arcade.key.F7, "F8": arcade.key.F8, "F9": arcade.key.F9,
            "F10": arcade.key.F10, "F11": arcade.key.F11, "F12": arcade.key.F12,

            # Специальные
            "SPACE": arcade.key.SPACE, "ENTER": arcade.key.ENTER,
            "ESCAPE": arcade.key.ESCAPE, "TAB": arcade.key.TAB,
            "BACKSPACE": arcade.key.BACKSPACE, "DELETE": arcade.key.DELETE,

            # Стрелки
            "UP": arcade.key.UP, "DOWN": arcade.key.DOWN,
            "LEFT": arcade.key.LEFT, "RIGHT": arcade.key.RIGHT,

            # Модификаторы
            "LSHIFT": arcade.key.LSHIFT, "RSHIFT": arcade.key.RSHIFT,
            "LCTRL": arcade.key.LCTRL, "RCTRL": arcade.key.RCTRL,
        }

        # Код -> строка (обратный маппинг)
        self._code_to_string = {v: k for k, v in self._string_to_code.items()}

    def _load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)

                # Загружаем или используем дефолты
                self._key_bindings = {}
                for action, default_keys in self._default_bindings.items():
                    if action in saved and isinstance(saved[action], list):
                        self._key_bindings[action] = saved[action]
                    else:
                        self._key_bindings[action] = default_keys.copy()
            else:
                # Используем дефолты и создаем файл
                self._key_bindings = {k: v.copy() for k, v in self._default_bindings.items()}
                self._save_config()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфига: {e}, используем дефолты")
            self._key_bindings = {k: v.copy() for k, v in self._default_bindings.items()}

        # Конвертируем строки в коды
        self._key_codes = self._strings_to_codes(self._key_bindings)

    def _save_config(self) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._key_bindings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфига: {e}")
            return False

    def _strings_to_codes(self, bindings: Dict[str, List[str]]) -> Dict[str, List[int]]:
        """Конвертация строк в коды клавиш"""
        result = {}
        for action, key_strings in bindings.items():
            codes = []
            for key_str in key_strings:
                code = self._string_to_code.get(key_str)
                if code is not None:
                    codes.append(code)
            result[action] = codes
        return result


    def _get_direction_for_key(self, key: int) -> str:
        """Определяет, является ли клавиша направлением"""
        if key in self._key_codes.get('up', []):
            return 'up'
        if key in self._key_codes.get('down', []):
            return 'down'
        if key in self._key_codes.get('left', []):
            return 'left'
        if key in self._key_codes.get('right', []):
            return 'right'
        return ''

    def _handle_direction_press(self, direction: str):
        """Обработка нажатия направления"""
        # Сбрасываем все направления
        for dir_name in ['up', 'down', 'left', 'right']:
            self.actions[dir_name] = False

        # Активируем только новое направление
        self.actions[direction] = True

    def _handle_direction_release(self, released_direction: str):
        """Обработка отпускания направления"""
        # Сбрасываем отпущенное направление
        self.actions[released_direction] = False

        # Проверяем, остались ли другие нажатые направления
        for direction in ['up', 'down', 'left', 'right']:
            if direction != released_direction:
                for key_code in self._key_codes.get(direction, []):
                    if key_code in self.keys_pressed:
                        self.actions[direction] = True
                        return  # Нашли другое нажатое направление

    def _update_actions(self):
        """Обновление состояний всех не-направленных действий"""
        for action, codes in self._key_codes.items():
            if action not in ['up', 'down', 'left', 'right']:
                # Проверяем, нажата ли хоть одна из связанных клавиш
                self.actions[action] = any(
                    key_code in self.keys_pressed
                    for key_code in codes
                )

