from .consumables import HealingPotion, FatigueKiller, QuestFlash
from .equippables import GoldRing, BlueBoots, OrcWeapon, SimpleSword
from .keys import Key
from .base_item import Item
from ...core.resource_manager import resource_manager as rm


class ItemFactory:
    """Создает предметы по ID"""

    @staticmethod
    def create(item_id: str, count: int = 1, **kwargs) -> Item:
        """Создает предмет по его ID"""
        texture = kwargs.get("texture")
        if not texture:

            try:
                # Для consumables проверяем другую папку
                if item_id.startswith("key_"):
                    texture = rm.load_item("key","consumables")
                else:
                    if item_id == "healing_potion":
                        texture = rm.load_item("potion_red", "consumables")
                    elif item_id == "fatigue_killer":
                        texture = rm.load_item("manacrystal_full", "consumables")
                    elif item_id == "flash_quest":
                        texture = rm.load_item("flash", "consumables")

                    elif item_id == "sonya_ring":
                        texture = rm.load_item("gold_ring", "equippables")
                    elif item_id == "blue_boots":
                        texture = rm.load_item("blue_boots", "equippables")
                    elif item_id == "orc_weapon":
                        texture = rm.load_item("orc_weapon", "equippables")
                    elif item_id == "simple_sword":
                        texture = rm.load_item("simple_sword", "equippables")

            except Exception as e:
                print(e)
                from arcade import Texture
                texture = Texture.create_empty(f"default_{item_id}", (32, 32), (128, 128, 128, 255))

        # Консумаблы
        if item_id == "healing_potion":
            return HealingPotion(texture=texture, count=count)
        elif item_id == "fatigue_killer":
            return FatigueKiller(texture=texture, count=count)
        elif item_id == "flash_quest":
            return QuestFlash(texture=texture, count=count)

        # Аксессуары
        elif item_id == "sonya_ring":
            return GoldRing(texture=texture, count=count)
        elif item_id == "blue_boots":
            return BlueBoots(texture=texture, count=count)
        elif item_id == "orc_weapon":
            return OrcWeapon(texture=texture, count=count)
        elif item_id == "simple_sword":
            return SimpleSword(texture=texture, count=count)

        # Ключи
        elif item_id.startswith("key_"):
            key_type = item_id[4:] if "_" in item_id else "basic"
            name = kwargs.get("name", f"Ключ {key_type}")
            return Key(key_id=key_type, name=name, texture=texture)

        else:
            return Item(
                item_id=item_id,
                name=kwargs.get("name", item_id),
                texture=texture
            )

    @staticmethod
    def parse_loot_string(loot_str: str) -> list:
        """
        Парсит строку лута из Tiled: "healing_potion:3,key_door1:1,gold:50"
        Возвращает список предметов
        """
        items = []
        if not loot_str:
            return items

        for item_part in loot_str.split(','):
            item_part = item_part.strip()
            if ':' in item_part:
                item_id, count_str = item_part.split(':')
                try:
                    count = int(count_str)
                    item = ItemFactory.create(item_id.strip(), count)
                    if item:
                        items.append(item)
                except ValueError:
                    print(f"Неверный формат количества: {item_part}")
            else:
                # Если нет количества - 1
                item = ItemFactory.create(item_part.strip(), 1)
                if item:
                    items.append(item)

        return items
