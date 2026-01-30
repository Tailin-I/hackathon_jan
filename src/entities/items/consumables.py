from .base_item import Item
from ...core.game_data import game_data
from ...ui.notification_system import notifications as ns


class HealingPotion(Item):
    """Целебное зелье"""

    def __init__(self, texture=None, count: int = 1):
        # Используем переданную текстуру
        super().__init__(
            item_id="healing_potion",
            name="Целебное зелье",
            texture=texture
        )
        self.count = count
        self.is_consumable = True
        self.heal_amount = 45
        self.description = f"Восстанавливает {self.heal_amount} здоровья"

    def use(self, user) -> bool:
        if user.health < user.max_health:
            heal_amount = min(self.heal_amount, user.max_health - user.health)
            game_data.heal(heal_amount)
            self.count -= 1
            print(user.health)
            ns.notification(f"+{heal_amount} HP")
            return True  # Предмет израсходован
        ns.notification(f"И так полное здоровье")
        return False


class FatigueKiller(Item):
    """Зелье восстановления усталости"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="fatigue_killer",
            name="Кристал духа",
            texture=texture
        )
        self.count = count
        self.is_consumable = True
        self.restore_amount = 30  # Сколько восстанавливает
        self.description = f"Восстанавливает {self.restore_amount} духа"

    def use(self, user) -> bool:
        if user.fatigue > 0:
            current_fatigue = user.fatigue

            # Минимум из того, сколько нужно и сколько можем восстановить
            restore = min(self.restore_amount, current_fatigue)

            user.fatigue -= restore

            self.count -= 1

            ns.notification(f"Восстановлено {restore} духа")
            return True
        else:
            ns.notification("И так полон сил")
            return False

class QuestFlash(Item):
    """Флешка с данными пентагона для задания"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="flash_quest",
            name="Флешка с данными пентагона",
            texture=texture
        )
        self.count = count
        self.is_consumable = True
        self.description = "Хранит суперсекретные данные"

    def use(self, user) -> bool:
        ns.notification("C этим нужно быть аккуратнее")
        return False

