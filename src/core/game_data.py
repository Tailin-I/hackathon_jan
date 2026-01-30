import logging
import os
import pickle
from typing import Dict

from .resource_manager import resource_manager
from ..ui.notification_system import notifications as ns
from config import constants as C


class GameData:
    """центр всех данных игры"""

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.base_req_exp = 500

        # Данные игрока
        self.player_data = {
            "id": "player",
            "name": "Игрок",
            "type": "player",
            "position": {"x": 3, "y": 7, "map": "house"},
            # "position": {"x": 93, "y": 35, "map": "itcube1floor"},
            # "position": {"x": 10, "y": 35, "map": "itcube2floor"},
            "level": 1,
            "exp": 0,
            "req_exp": self.base_req_exp,
            "health": 224,
            "max_health": 400,

            "fatigue": 0,
            "max_fatigue": 200,
            "restoration_speed": 1,
            # TODO реализовать скорость атаки

            "strength": 48,
            "speed": 5,
            "vision_range": 200,
            # Инвентарь
            "inventory": [
                {'id': 'healing_potion', 'name': 'Целебное зелье', 'count': 1, 'stackable': True},
                {'id': 'simple_sword', 'name': 'Простой меч', 'count': 1, 'stackable': False}
            ],
            "equipment": {
                "accessory_1": None,
                "accessory_2": None,
                "accessory_3": None
            }
        }

        # Данные снарядов
        self.projectiles_data = {}

        # Таймеры перезарядки атаки (для игрока)
        self.attack_cooldown = 0
        self.attack_cooldown_max = 0.5  # Полсекунды между выстрелами

        # Шаблоны снарядов
        self.projectile_templates = {
            "default": {
                "speed": 250,
                "damage_multiplier": 1.0,  # Множитель урона игрока
                "max_lifetime": 4.0,
                "fatigue_cost": 25,
                "sprite_size": (16, 16),
                "animation_speed": 0.3,
                "tile_count": 3,
                "texture_name": "fireball"
            }
        }

        # Данные монстров (загружаются из Tiled)
        self.mobs_data = {}

        # Данные зон для монстров
        self.mob_zones = {}

        # Шаблоны монстров (дефолтные значения)
        self.mob_templates = {
            "bug": {
                "health": 20,
                "max_health": 20,
                "exp": 25,
                "damage": 25,
                "speed": 1,
                "vision_range": 200,
                "behavior": "aggressive",
                "chase_speed": 3,
                "loot": [],
                "scale": 1,
                "imp": False,
            },
            "npc": {
                "health": 100,
                "max_health": 100,
                "exp": 100,
                "damage": 25,
                "speed": 1,
                "vision_range": 500,
                "behavior": "passive",
                "chase_speed": 2,
                "loot": [],
                "scale": 0.8,
                "imp": True,
                "can_dialogue": True,  # <-- может разговаривать
                "active_topic": "greeting",
            }
        }

        self._projectile_counter = 0

    def get_entity_data(self, entity_id):
        """Получить данные любой сущности"""
        if entity_id == "player":
            return self.player_data
        elif entity_id in self.mobs_data:
            return self.mobs_data[entity_id]

    def update_entity_data(self, entity_id, updates):
        """Обновить данные сущности"""
        data = self.get_entity_data(entity_id)
        if data:
            data.update(updates)
            # Здесь можно триггерить события

    def add_mob(self, mob_id, monster_data):
        """Добавить монстра"""
        self.mobs_data[mob_id] = monster_data

    def remove_mob(self, mob_id):
        """Удалить монстра"""
        if mob_id in self.mobs_data:

            del self.mobs_data[mob_id]



    def save_to_file(self, file="savegame"):
        """Сохраняем в бинарный файл"""
        os.makedirs(resource_manager.get_full_path("saves"), exist_ok=True)
        with open(resource_manager.get_save_path(file), 'wb') as f:
            pickle.dump(self.__dict__, f)  # Сохраняем ВСЕ данные класса
            ns.notification(f"Сохранено ({file})")

    def load_from_file(self, file="savegame"):
        """Загружаем из файла"""

        try:
            with open(resource_manager.get_save_path(file), 'rb') as f:
                data = pickle.load(f)
                self.__dict__.update(data)  # Обновляем все данные
                ns.notification(f"Загружено ({file})")

        except FileNotFoundError:
            self.logger.warning("Файл сохранения не найден, используем значения по умолчанию")

    # Удобные методы для доступа
    def get_player_position(self):
        return (self.player_data["position"]["x"] * C.TILE_SIZE,
                self.player_data["position"]["y"] * C.TILE_SIZE,
                self.player_data["position"]["map"]
                )

    def get_player(self, arg):
        if arg in self.player_data:
            return self.player_data[arg]
        return None

    def set_player_position(self, x, y, map_name=None):
        self.player_data["position"]["x"] = x
        self.player_data["position"]["y"] = y
        if map_name:
            self.player_data["position"]["map"] = map_name

    def change_player_stat(self, stat_name: str, operation: str, value: int):
        """
        Изменяет характеристику игрока с различными операциями.

        Args:
            stat_name: Название характеристики ('health', 'strength', 'exp', и т.д.)
            operation: Операция ('set', 'add', 'subtract', 'multiply', 'divide')
            value: Значение для операции
        """
        if stat_name not in self.player_data:
            self.logger.warning(f"Характеристика '{stat_name}' не найдена")
            return False

        current = self.player_data[stat_name]

        try:
            if operation == "set":
                new_value = value
            elif operation == "add":
                new_value = current + value
            elif operation == "subtract":
                new_value = current - value
            elif operation == "multiply":
                new_value = current * value
            elif operation == "divide":
                new_value = current / value if value != 0 else current
            else:
                self.logger.warning(f"Неизвестная операция: {operation}")
                return False

            # Применяем ограничения для разных характеристик
            new_value = self._apply_stat_limits(stat_name, new_value)

            self.player_data[stat_name] = new_value
            self.logger.debug(f"{stat_name}: {current} -> {new_value} ({operation} {value})")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка изменения {stat_name}: {e}")
            return False

    def _apply_stat_limits(self, stat_name: str, value):
        """Применяет ограничения для характеристик"""
        if stat_name == "health":
            return max(0, min(value, self.player_data["max_health"]))
        elif stat_name == "max_health":
            return max(1, value)
        elif stat_name in ["strength", "speed", "level"]:
            return max(1, value)
        elif stat_name == "exp":
            # Автоматический уровень при накоплении опыта
            new_exp = max(0, value)
            if new_exp >= self.player_data["req_exp"]:
                self._level_up()
            return new_exp
        return value

    def _level_up(self):
        """Повышение уровня"""
        self.player_data["level"] += 1
        self.player_data["exp"] = self.player_data["exp"] - self.player_data["req_exp"]
        self.player_data["req_exp"] = int(self.player_data["req_exp"] * 1.5)  # Увеличиваем требуемый опыт

        # Улучшаем характеристики при повышении уровня
        self.player_data["max_health"] += 12
        self.player_data["health"] += 12
        self.player_data["strength"] += 1

        ns.notification("Новый уровень")
        self.logger.info(f"Уровень повышен! Теперь уровень {self.player_data['level']}")

    def heal(self, amount: int):
        """Восстановление здоровья"""
        ns.health_changes(amount)

        return self.change_player_stat("health", "add", amount)

    def take_damage(self, amount: int):
        """Получение урона"""
        ns.health_changes(-amount)
        return self.change_player_stat("health", "subtract", amount)

    def add_exp(self, amount: int):
        """Добавление опыта"""
        ns.notification(f"+{amount} exp")
        return self.change_player_stat("exp", "add", amount)

    def increase_strength(self, amount: int = 1):
        """Увеличение силы"""
        return self.change_player_stat("strength", "add", amount)

    def increase_max_health(self, amount: int):
        """Увеличение максимального здоровья"""
        success = self.change_player_stat("max_health", "add", amount)
        if success:
            # Также увеличиваем текущее здоровье
            self.change_player_stat("health", "add", amount)
        return success

    def add_mob_zone(self, zone_id, zone_data):
        """Добавить зону для монстров"""
        self.mob_zones[zone_id] = zone_data

    def get_monster_zone(self, zone_id):
        """Получить зону по ID"""
        return self.mob_zones.get(zone_id)

    def find_nearest_zone(self, x, y, max_distance=1000):
        """Находит ближайшую зону к точке"""
        nearest_zone = None
        min_distance = float('inf')

        for zone_id, zone in self.mob_zones.items():
            zone_x, zone_y, zone_w, zone_h = zone["rect"]

            # Центр зоны
            center_x = zone_x + zone_w / 2
            center_y = zone_y + zone_h / 2

            # Расстояние до центра зоны
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_zone = zone.copy()
                nearest_zone["id"] = zone_id

        return nearest_zone

    def create_monster_data(self, monster_id, mob_name, monster_type, position, custom_props: Dict=None,  map_name=None, scale=1):
        """Создать данные монстра с учетом дефолтных и кастомных свойств"""
        # Копируем шаблон для этого типа
        monster_data = self.mob_templates[monster_type].copy()

        # Добавляем обязательные поля
        monster_data.update({
            "id": monster_id,
            "type": monster_type,
            "name": mob_name,
            "position": {"x": position[0], "y": position[1]},
            "is_alive": True,
            "zone_id": None,  # Будет установлено позже
            "custom_properties": custom_props or {},
            "map_name": map_name
        })

        # Перезаписываем свойствами из Tiled
        if custom_props:
            for key, value in custom_props.items():
                if key in monster_data:
                    monster_data[key] = value

            if "health" not in custom_props.keys():
                monster_data["health"] = monster_data["max_health"]

        return monster_data

    def add_item(self, item_id: str, name: str = None, count: int = 1, stackable: bool = True):
        """Добавляет предмет в инвентарь игрока"""
        inventory = self.player_data["inventory"]
        ns.notification(f"+{count} {name}")
        # Ищем уже существующий предмет
        if stackable:
            for item in inventory:
                if item["id"] == item_id:
                    item["count"] += count
                    return True

        # Если предмет не найден или не стакаемый - добавляем новый
        inventory.append({
            "id": item_id,
            "name": name or item_id,
            "count": count,
            "stackable": stackable,
            "type": "item"  # Тип для категоризации
        })


        return True

    def remove_item(self, item_id: str, count: int = 1):
        """Удаляет предмет из инвентаря"""
        inventory = self.player_data["inventory"]

        for i, item in enumerate(inventory):
            if item["id"] == item_id:
                if item["stackable"]:
                    item["count"] -= count
                    if item["count"] <= 0:
                        inventory.pop(i)
                else:
                    inventory.pop(i)
                return True
        return False

    def get_item_count(self, item_id: str) -> int:
        """Возвращает количество предметов в инвентаре"""
        for item in self.player_data["inventory"]:
            if item["id"] == item_id:
                return item["count"]
        return 0

    def has_item(self, item_id: str, min_count: int = 1) -> bool:
        """Проверяет наличие предмета в инвентаре"""
        return self.get_item_count(item_id) >= min_count

    def get_inventory_size(self) -> int:
        """Возвращает текущее количество занятых слотов"""
        return len(self.player_data["inventory"])



    def get_fatigue(self):
        return self.player_data.get("fatigue", 0)

    def get_max_fatigue(self):
        return self.player_data.get("max_fatigue", 100)

    def add_fatigue(self, amount: int):
        """Увеличивает усталость"""
        current = self.player_data.get("fatigue", 0)
        max_fatigue = self.player_data.get("max_fatigue", 100)
        new_fatigue = min(max_fatigue, current + amount)
        self.player_data["fatigue"] = new_fatigue
        return new_fatigue

    def can_use_fatigue(self, amount: int) -> bool:
        """Проверяет, достаточно ли усталости для действия"""
        return self.player_data.get("fatigue") < self.player_data.get("max_fatigue") - amount

        # Методы для снарядов

    def add_projectile(self, projectile_id: str, projectile_data: dict):
        """Добавляет снаряд"""
        self.projectiles_data[projectile_id] = projectile_data

    def get_projectile_data(self, projectile_id: str):
        """Получает данные снаряда"""
        return self.projectiles_data.get(projectile_id)

    def create_projectile_data(self, projectile_type: str, position: tuple, direction: tuple, owner_id: str = "player"):
        """Создаёт данные снаряда на основе шаблона"""
        template = self.projectile_templates.get(projectile_type, self.projectile_templates["default"]).copy()

        # Рассчитываем урон на основе силы игрока
        player_damage = self.player_data.get("strength", 10)
        damage = int(player_damage * template["damage_multiplier"])

        # Уникальный ID на основе счетчика
        self._projectile_counter += 1
        projectile_id = f"projectile_{self._projectile_counter}_{owner_id}"

        projectile_data = {
            "id": projectile_id,
            "type": projectile_type,
            "position": {"x": position[0], "y": position[1]},
            "direction": {"x": direction[0], "y": direction[1]},
            "speed": template["speed"],
            "damage": damage,
            "max_lifetime": template["max_lifetime"],
            "current_lifetime": 0,
            "fatigue_cost": template["fatigue_cost"],
            "owner_id": owner_id,
            "sprite_params": {
                "texture_name": template["texture_name"],
                "sprite_size": template["sprite_size"],
                "animation_speed": template["animation_speed"],
                "tile_count": template["tile_count"]
            }
        }

        return projectile_data

    def remove_projectile(self, projectile_id: str):
        """Удаляет снаряд из хранилища"""
        if projectile_id in self.projectiles_data:
            del self.projectiles_data[projectile_id]

    def reset_to_defaults(self):
        """Сбрасывает все данные к значениям по умолчанию"""
        self.__init__()
        self.logger.info("Данные игры сброшены к значениям по умолчанию")

    def equip_item(self, item_id: str) -> bool:
        """Экипирует предмет. Возвращает True если успешно."""
        # Проверяем, есть ли предмет в инвентаре
        if not self.has_item(item_id):
            return False

        # Получаем информацию о предмете
        from src.entities.items.item_factory import ItemFactory
        item_obj = ItemFactory.create(item_id, 1)

        if not item_obj or not hasattr(item_obj, 'is_equippable') or not item_obj.is_equippable:
            return False

        # Ищем свободный слот
        equipment = self.player_data["equipment"]
        slot_to_use = None

        # Проверяем свободные слоты
        for slot in ["accessory_1", "accessory_2", "accessory_3"]:
            if equipment[slot] is None:
                slot_to_use = slot
                break

        # Если нет свободных слотов, используем первый слот (по принципу FIFO)
        if slot_to_use is None:
            slot_to_use = "accessory_1"

            # Снимаем предмет из первого слота
            unequipped_item_id = equipment[slot_to_use]
            if unequipped_item_id:
                self.unequip_item(slot_to_use)

        # Экипируем предмет (сохраняем только ID)
        equipment[slot_to_use] = item_id

        # Применяем бонусы предмета
        self._apply_item_bonuses(item_obj)

        # НЕ удаляем предмет из инвентаря - он остается там, но отмечен как экипированный
        # Просто обновляем счетчик в инвентаре, чтобы показать, что предмет экипирован

        return True

    def unequip_item(self, slot: str) -> bool:
        """Снимает предмет из указанного слота."""
        if slot not in self.player_data["equipment"]:
            return False

        item_id = self.player_data["equipment"][slot]
        if not item_id:
            return False

        # Убираем бонусы предмета
        from src.entities.items.item_factory import ItemFactory
        item_obj = ItemFactory.create(item_id, 1)
        self._remove_item_bonuses(item_obj)

        # Очищаем слот
        self.player_data["equipment"][slot] = None

        return True

    def get_equipped_item_info(self, slot: str):
        """Возвращает информацию об экипированном предмете в слоте."""
        item_id = self.player_data["equipment"].get(slot)
        if not item_id:
            return None

        # Находим предмет в инвентаре
        for item in self.player_data["inventory"]:
            if item["id"] == item_id:
                return item.copy()

        return None

    def is_item_equipped(self, item_id: str) -> bool:
        """Проверяет, экипирован ли предмет."""
        for slot, equipped_id in self.player_data["equipment"].items():
            if equipped_id == item_id:
                return True
        return False

    def get_item_equipment_slot(self, item_id: str):
        """Возвращает слот, в котором экипирован предмет, или None."""
        for slot, equipped_id in self.player_data["equipment"].items():
            if equipped_id == item_id:
                return slot
        return None

    def _apply_item_bonuses(self, item_obj):
        """Применяет бонусы предмета к игроку."""
        # Здоровье
        if hasattr(item_obj, 'additional_health'):
            self.player_data["max_health"] += item_obj.additional_health
            self.player_data["health"] += item_obj.additional_health

        # Сила
        if hasattr(item_obj, 'additional_strength'):
            self.player_data["strength"] += item_obj.additional_strength

        # Дистанция видения
        if hasattr(item_obj, 'additional_range'):
            self.player_data["vision_range"] += item_obj.additional_range

        # Скорость
        if hasattr(item_obj, 'additional_speed'):
            self.player_data["speed"] += item_obj.additional_speed

    def _remove_item_bonuses(self, item_obj):
        """Убирает бонусы предмета с игрока."""
        # Здоровье
        if hasattr(item_obj, 'additional_health'):
            self.player_data["max_health"] -= item_obj.additional_health
            self.player_data["health"] = min(self.player_data["health"], self.player_data["max_health"])

        # Сила
        if hasattr(item_obj, 'additional_strength'):
            self.player_data["strength"] -= item_obj.additional_strength

        # Дистанция видения
        if hasattr(item_obj, 'additional_range'):
            self.player_data["vision_range"] -= item_obj.additional_range

        # Скорость
        if hasattr(item_obj, 'additional_speed'):
            self.player_data["speed"] -= item_obj.additional_speed

    def get_equipped_items(self) -> dict:
        """Возвращает словарь с экипированными предметами."""
        return self.player_data["equipment"].copy()

# Глобальный экземпляр (будет один на всю игру)
game_data = GameData()
