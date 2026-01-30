from .base_item import Item
from ...core.game_data import game_data
from ...ui.notification_system import notifications as ns

class GoldRing(Item):
    """Золотое Кольцо Сони"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="sonya_ring",
            name="Золотое кольцо",
            texture=texture
        )
        self.additional_health = 50
        self.additional_strength = 2
        self.additional_range = 25
        self.count = count
        self.is_equippable= True
        self.description = "Это золотое кольцо невероятно красиво"

    def use(self, user) -> bool:
        ns.notification("Нужно поспрашивать лицеистов и узнать кому оно принадлежит!")
        return False

class BlueBoots(Item):
    """Голубые ботики"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="blue_boots",
            name="простые ботинки",
            texture=texture
        )

        self.additional_speed = 40
        self.count = count
        self.is_equippable= True
        self.description = "Эти ботинку позволяют ходить чуть быстрее"

    def use(self, user) -> bool:
        return False

class OrcWeapon(Item):
    """Дубина орка"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="orc_weapon",
            name="Тяжёлая дубина орка",
            texture=texture
        )

        self.additional_strength = 10
        self.count = count
        self.is_equippable= True
        self.description = "Если такой огреть..."

    def use(self, user) -> bool:
        return False

class SimpleSword(Item):
    """Простой меч"""

    def __init__(self, texture=None, count: int = 1):
        super().__init__(
            item_id="simple_sword",
            name="Простой меч",
            texture=texture
        )

        self.additional_strength = 500
        self.count = count
        self.is_equippable= True
        self.description = "Делает владельца сильнее"

    def use(self, user) -> bool:
        return False