from typing import Dict, Any
from .event import GameEvent
from ..ui.notification_system import notifications as ns
from src.core.dialogue_manager import dialogue_manager


class NotificationEvent(GameEvent):
    def __init__(self, event_id: str, name: str, rect: tuple, properties: Dict[str, Any]):
        super().__init__(event_id, name, "notification", rect, properties)

        self.text = properties.get("text", "Уведомление")
        self.condition = properties.get("condition", "").split(":") if properties.get("condition") else []
        self.max_cooldown = 120  # 2 секунды при 60 FPS

        self.logger.debug(f"Создано событие уведомления: {event_id}, условие: {self.condition}")

    def check_condition(self, game_state):
        """Проверяет условие для активации события"""
        if not self.condition:
            return True  # Нет условия - всегда можно активировать

        try:
            cond_type = self.condition[0].lower()

            if cond_type == "dialog":
                # Формат: dialog:npc_name:topic
                if len(self.condition) < 3:
                    return True

                npc_name = self.condition[1].strip()
                required_topic = self.condition[2].strip()

                # Получаем активную тему NPC через dialogue_manager
                current_topic = dialogue_manager.get_active_topic(npc_name)

                self.logger.debug(
                    f"Проверка диалога NPC '{npc_name}': текущая тема='{current_topic}', требуемая='{required_topic}'")

                # Проверяем совпадение
                return current_topic == required_topic

            elif cond_type == "has_item":
                # Формат: has_item:item_id:count
                if len(self.condition) < 2:
                    return True

                from ..core.game_data import game_data
                item_id = self.condition[1].strip()
                required_count = int(self.condition[2]) if len(self.condition) > 2 else 1

                current_count = game_data.get_item_count(item_id)
                return current_count >= required_count

            elif cond_type == "quest":
                # Формат: quest:quest_id:state
                if len(self.condition) < 3:
                    return True

                quest_id = self.condition[1].strip()
                required_state = self.condition[2].strip()

                # TODO: Реализовать проверку состояния квеста
                # Пока возвращаем True для разработки
                return True

            else:
                self.logger.warning(f"Неизвестный тип условия: {cond_type}")
                return True

        except Exception as e:
            self.logger.error(f"Ошибка проверки условия {self.condition}: {e}")
            return True

    def activate(self, player, game_state):
        if self.activated and self.cooldown > 0:
            return

        # Проверяем условие
        if not self.check_condition(game_state):
            self.logger.debug(f"Условие не выполнено для события {self.event_id}")
            return

        # Показываем уведомление
        ns.notification(self.text)
        self.logger.debug(f"Уведомление показано: {self.text}")

        # Устанавливаем таймер
        self.activated = True
        self.cooldown = self.max_cooldown
