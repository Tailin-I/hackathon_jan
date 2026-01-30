import sqlite3
from typing import List, Dict, Optional, Tuple

from src.core.resource_manager import resource_manager


class DialogueManager:
    """Менеджер для работы с диалогами из базы данных"""

    def __init__(self, db_path: str = resource_manager.get_resource_path("db/dialogues.db")):
        self.db_path = db_path
        self.connection = None

        # Кеши для ускорения
        self.dialog_cache: Dict[Tuple[str, str], List[Dict]] = {}  # (npc_name, topic) -> диалоги
        self.response_cache: Dict[Tuple[str, str], List[Dict]] = {}  # (npc_name, topic) -> ответы

        # Подключаемся к БД
        self._connect()

    def _connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Для доступа по именам колонок
            print(f"Подключено к базе данных: {self.db_path}")

        except sqlite3.Error as e:
            print(f"Ошибка подключения к БД: {e}")
            raise

    def get_dialog(self, npc_name: str, topic: str) -> List[Dict]:
        """
        Получает все реплики диалога для указанного NPC и темы

        Args:
            npc_name: Имя NPC (например, 'алина')
            topic: Тема диалога (например, 'greeting')

        Returns:
            Список словарей с репликами, отсортированный по order_index
        """
        cache_key = (npc_name, topic)

        # Проверяем кеш
        if cache_key in self.dialog_cache:
            print()
            return self.dialog_cache[cache_key]

        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id, npc_name, topic, text, order_index 
                FROM dialog 
                WHERE npc_name = ? AND topic = ? 
                ORDER BY order_index
            ''', (npc_name, topic))

            # Конвертируем в список словарей
            rows = cursor.fetchall()
            dialogs = []

            for row in rows:
                dialogs.append({
                    'id': row['id'],
                    'npc_name': row['npc_name'],
                    'topic': row['topic'],
                    'text': row['text'],
                    'order_index': row['order_index']
                })

            # Сохраняем в кеш
            self.dialog_cache[cache_key] = dialogs

            return dialogs

        except sqlite3.Error as e:
            print(f"Ошибка получения диалога {npc_name}.{topic}: {e}")
            return []

    def get_responses(self, npc_name: str, topic: str) -> List[Dict]:
        """
        Получает все варианты ответов игрока для указанного NPC и темы
        """
        cache_key = (npc_name, topic)

        try:
            # Проверяем кеш всех ответов (без фильтрации)
            if cache_key not in self.response_cache:
                # Загружаем ВСЕ ответы из БД (без проверки условий)
                cursor = self.connection.cursor()
                cursor.execute('''
                    SELECT id, npc_name, topic, button_text, chat_text, 
                           target_npc, next_topic, order_index, 
                           condition, condition_fail_topic, trigger_event
                    FROM player_response 
                    WHERE npc_name = ? AND topic = ? 
                    ORDER BY order_index
                ''', (npc_name, topic))

                # Сохраняем ВСЕ строки в кеш (как они есть в БД)
                rows = cursor.fetchall()
                all_responses = []
                for row in rows:
                    all_responses.append({
                        'id': row['id'],
                        'npc_name': row['npc_name'],
                        'topic': row['topic'],
                        'button_text': row['button_text'],
                        'chat_text': row['chat_text'],
                        'target_npc': row['target_npc'],
                        'next_topic': row['next_topic'],
                        'order_index': row['order_index'],
                        'condition': row['condition'],
                        'condition_fail_topic': row['condition_fail_topic'],
                        'trigger_event': row['trigger_event']
                    })
                self.response_cache[cache_key] = all_responses

            # Теперь фильтруем ответы с проверкой условий КАЖДЫЙ РАЗ
            filtered_responses = []
            for response in self.response_cache[cache_key]:
                if self._check_condition(response['condition']):
                    filtered_responses.append(response)
                elif response['condition_fail_topic']:
                    # Если условие не выполнено, но есть альтернативная тема
                    alt_response = response.copy()
                    alt_response['next_topic'] = response['condition_fail_topic']
                    filtered_responses.append(alt_response)

            return filtered_responses

        except sqlite3.Error as e:
            print(f"Ошибка получения ответов {npc_name}.{topic}: {e}")
            return []
    def _check_condition(self, condition: Optional[str]) -> bool:
        """
        Проверяет условие для ответа

        Форматы условий:
        - "has_item:item_id:count" - наличие предмета
        - "stat_min:stat_name:value" - минимальное значение характеристики
        - "quest_completed:quest_id" - завершение квеста
        """
        if not condition:
            return True  # Нет условия - всегда доступно

        try:
            parts = condition.split(':')
            cond_type = parts[0]
            if cond_type == "has_item":
                # Проверка наличия предмета в инвентаре
                item_id = parts[1]
                required_count = int(parts[2]) if len(parts) > 2 else 1
                # Используем game_data для проверки
                from ..core.game_data import game_data
                current_count = game_data.get_item_count(item_id)
                return current_count >= required_count

            elif cond_type == "stat_min":
                # Проверка характеристики игрока
                stat_name = parts[1]
                min_value = int(parts[2])

                from ..core.game_data import game_data
                current_value = game_data.player_data.get(stat_name, 0)
                return current_value >= min_value

            elif cond_type == "quest_completed":
                # Проверка завершения квеста
                quest_id = parts[1]
                # TODO: Реализовать систему квестов
                # Пока возвращаем True
                return True

            else:
                print(f"Неизвестный тип условия: {cond_type}")
                return True

        except Exception as e:
            print(f"Ошибка проверки условия {condition}: {e}")
            return True
    def set_active_topic(self, npc_name: str, topic: str):
        """
        Устанавливает активную тему для NPC (сохраняет в game_data)

        Args:
            npc_name: Имя NPC
            topic: Новая активная тема
        """
        from ..core.game_data import game_data
        # Ищем NPC в монстрах
        for monster_id, mob_data in game_data.mobs_data.items():
            if mob_data.get("name") == npc_name:
                mob_data["active_topic"] = topic
                return

        # Если NPC не найден в монстрах, создаем запись
        game_data.mobs_data[f"npc_{npc_name}"] = {
            "name": npc_name,
            "active_topic": topic,
            "type": "npc"
        }

    def get_active_topic(self, npc_name: str) -> str:
        """
        Получает активную тему NPC из game_data

        Args:
            npc_name: Имя NPC

        Returns:
            Активная тема или "greeting" по умолчанию
        """
        from ..core.game_data import game_data
        # Ищем NPC в монстрах
        for monster_id, monster_data in (game_data.mobs_data
                .items()):
            if monster_data.get("name") == npc_name:
                return monster_data.get("active_topic", "greeting")

        return "greeting"  # Тема по умолчанию

    def process_player_choice(self, npc_name: str, topic: str, response_index: int,
                              all_npcs: dict = None):
        """
        Обрабатывает выбор игрока

        Returns:
            Кортеж (next_npc_object, next_npc_name, next_topic, triggered_events)
        """
        responses = self.get_responses(npc_name, topic)

        if not responses or response_index >= len(responses):
            return None, None, None, []

        response = responses[response_index]

        # Получаем триггеры событий
        trigger_events = []
        if 'trigger_event' in response and response['trigger_event']:
            events = self._parse_trigger_events(response['trigger_event'])
            trigger_events.extend(events)

        # Определяем следующего NPC
        next_npc_name = response['target_npc'] if response['target_npc'] else npc_name
        next_topic = response['next_topic']

        # Находим объект NPC
        next_npc = None
        if next_npc_name and all_npcs:
            next_npc = all_npcs.get(next_npc_name)

        if next_topic:
            self.set_active_topic(next_npc_name, next_topic)
            return next_npc, next_npc_name, next_topic, trigger_events
        else:
            return None, None, None, trigger_events

    def _parse_trigger_events(self, event_string: str) -> List[Dict]:
        """
        Парсит строку триггеров: "give_item:apple:1;change_npc_topic:охранник:friendly"

        Форматы:
        - give_item:item_id:count
        - remove_item:item_id:count
        - change_npc_topic:npc_name:new_topic
        - change_npc_property:npc_name:property:value
        - unlock_door:door_id
        - start_quest:quest_id
        - complete_quest:quest_id
        - spawn_monster:monster_type:x:y
        - teleport_player:map_name:x:y
        - finishgame:0:0
        """
        events = []
        if not event_string:
            return events

        # Разделяем по точке с запятой
        event_parts = event_string.split(';')

        for event_part in event_parts:
            event_part = event_part.strip()
            if not event_part:
                continue

            # Разбираем на компоненты
            parts = event_part.split(':')
            if len(parts) < 2:
                continue

            event_type = parts[0]
            event_data = {
                'type': event_type,
                'params': parts[1:]
            }
            events.append(event_data)

        return events
    def clear_cache(self):
        """Очищает кеш диалогов и ответов"""
        self.dialog_cache.clear()
        self.response_cache.clear()

    def close(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Соединение с БД закрыто")


# Глобальный экземпляр менеджера
dialogue_manager = DialogueManager()