import logging
import arcade
from typing import Dict, List
from .base_entity import Entity
from .creatures import Creature
from .projectile import Projectile
from ..core.game_data import game_data


class EntityManager:
    """Простой менеджер сущностей"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.entities: Dict[str, Entity] = {}  # Все сущности по ID
        self.mob: List[Creature] = []  # Только монстры
        self.current_map_name = None
        self.projectiles: List[Projectile] = []

    def update_projectiles(self, delta_time: float, collision_layer=None, monsters=None):
        """Обновляет все снаряды"""
        for projectile in self.projectiles[:]:  # Копия списка для безопасного удаления
            if projectile.is_active:
                projectile.update(delta_time, collision_layer, monsters)
            else:
                # Удаляем неактивные снаряды
                self.remove_projectile(projectile.entity_id)

    def remove_projectile(self, projectile_id: str):
        """Удаляет снаряд"""
        # Удаляем из GameData
        game_data.remove_projectile(projectile_id)

        # Удаляем из списка снарядов
        for i, proj in enumerate(self.projectiles):
            if proj.entity_id == projectile_id:
                # Важно: вызываем remove_from_sprite_lists() перед удалением
                proj.remove_from_sprite_lists()
                self.projectiles.pop(i)
                break

        # Удаляем из общего словаря
        if projectile_id in self.entities:
            del self.entities[projectile_id]

    def spawn_projectile(self, projectile_id: str, texture_list=None):
        """
        Создаёт визуальный объект снаряда.

        Returns:
            Projectile или None, если снаряд уже существует
        """
        if projectile_id in self.entities:
            return self.entities[projectile_id]

        # Получаем данные снаряда
        projectile_data = game_data.get_projectile_data(projectile_id)
        if not projectile_data:
            self.logger.warning(f"Данные снаряда {projectile_id} не найдены")
            return None

        # Создаём снаряд
        projectile = Projectile(projectile_id, texture_list or [])

        # Добавляем в менеджер
        self.projectiles.append(projectile)
        self.entities[projectile_id] = projectile

        self.logger.debug(f"Создан снаряд: {projectile_id}")
        return projectile

    def set_current_map(self, map_name: str):
        """Устанавливает текущую карту и очищает визуальные монстры"""
        self.current_map_name = map_name
        self.logger.debug(f"Установлена карта: {map_name}")

    def spawn_monster(self, mob_id: str, mob_name: str, mob_type: str, position, properties=None, map_name: str = None):
        """Создает монстра"""

        # Проверяем данные в game_data
        data = game_data.get_entity_data(mob_id)
        if data and not data.get("is_alive", True):
            self.logger.debug(f"Монстр {mob_id} уже мертв, пропускаем создание")
            return None

        # если монстр уже существует - возвращаем его
        if mob_id in self.entities.keys():
            existing = self.entities[mob_id]
            self.logger.debug(f"Монстр {mob_id} уже существует")
            return existing

        # Создаем данные (если их еще нет)
        if data is None:
            monster_data = game_data.create_monster_data(
                monster_id=mob_id,
                mob_name=mob_name,
                monster_type=mob_type,
                position=position,
                custom_props=properties,
                map_name=map_name
            )
            game_data.add_mob(mob_id, monster_data)
        else:
            monster_data = data

        monster_data["position"] = {"x": position[0], "y": position[1]}
        if map_name:
            monster_data["map_name"] = map_name

        # Находим ближайшую зону
        nearest_zone = game_data.find_nearest_zone(position[0], position[1])
        if nearest_zone:
            monster_data["zone_id"] = nearest_zone["id"]
            monster_data["zone_rect"] = nearest_zone["rect"]

        # Создаем визуальный объект
        monster = Creature(
            creature_id=mob_id,
            mob_name=mob_name,
            creature_type=mob_type,
            position=position,
            properties=properties
        )

        # Привязываем к зоне
        if nearest_zone:
            monster.zone_id = nearest_zone["id"]
            monster.zone_rect = nearest_zone["rect"]

        # Добавляем в менеджер
        self.entities[mob_id] = monster
        self.mob.append(monster)

        self.logger.debug(f"{mob_name} создан: {mob_id} на ({position[0]:.0f}, {position[1]:.0f})")
        return monster
    def update_all(self, delta_time: float, player=None, collision_layer=None):
        """Обновляет всех монстров"""
        for monster in self.mob[:]:
            if monster.is_alive:
                monster.update(delta_time, player, collision_layer)
            else:
                self.remove_entity(monster.entity_id)

    def clear_all(self):
        """Полностью очищает все сущности"""
        # Удаляем все сущности
        for entity_id in list(self.entities.keys()):
            self.remove_entity(entity_id)

        # Очищаем списки
        self.entities.clear()
        self.mob.clear()
        self.projectiles.clear()

        # Сбрасываем карту
        self.current_map_name = None

        self.logger.debug("Все сущности очищены")

    def sync_mob_positions_from_game_data(self):
        """Синхронизирует позиции монстров из GameData с визуальными объектами"""
        for mob_id, mob_data in game_data.mobs_data.items():
            if mob_id in self.entities:
                monster = self.entities[mob_id]
                if isinstance(monster, Creature):
                    # Обновляем позицию из сохраненных данных
                    pos_data = mob_data.get("position", {})
                    if pos_data:
                        monster.center_x = pos_data.get("x", monster.center_x)
                        monster.center_y = pos_data.get("y", monster.center_y)

                        # Обновляем состояние жизни
                        monster.is_alive = mob_data.get("is_alive", True)
                        monster.visible = monster.is_alive

                        # Обновляем здоровье
                        monster.health = mob_data.get("health", monster.health)
                        monster.max_health = mob_data.get("max_health", monster.max_health)

                        self.logger.debug(f"Синхронизирован монстр {mob_id}: "
                                          f"({monster.center_x}, {monster.center_y}), "
                                          f"жив: {monster.is_alive}")


    def remove_entity(self, entity_id: str):
        """Удаляет сущность"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]

            # Удаляем из списков
            if isinstance(entity, Creature) and entity in self.mob:
                self.mob.remove(entity)

            # Удаляем спрайт
            entity.remove_from_sprite_lists()

            # Удаляем из словаря
            del self.entities[entity_id]

    def draw_debug(self):
        """Отрисовывает отладочную информацию (зоны и радиусы)"""
        from config import constants as C

        if not C.show_area_mode:
            return

        # Рисуем зоны
        for zone_id, zone in game_data.mob_zones.items():
            if zone.get("map_name") != self.current_map_name:
                continue
            x, y, w, h = zone["rect"]
            arcade.draw_rect_filled(
                arcade.rect.XYWH(x + w / 2, y + h / 2, w, h),
                C.MENU_BACKGROUND_COLOR_TRANSLUCENT
            )

            # Название зоны
            arcade.Text(
                f"Zone: {zone_id}",
                x + w / 2, y + h / 2,
                arcade.color.YELLOW, 15,
                anchor_x="center", anchor_y="center"
            ).draw()

        # Рисуем информацию о монстрах
        for monster in self.mob:

            if game_data.get_entity_data(monster.entity_id)["map_name"] != self.current_map_name:
                continue

            if monster.is_alive:
                data = game_data.get_entity_data(monster.entity_id)
                # Радиус агрессии
                if hasattr(monster, 'vision_range'):
                    arcade.draw_circle_outline(
                        monster.center_x, monster.center_y,
                        monster.vision_range,
                        arcade.color.RED, 1
                    )

                # ID и координаты
                arcade.Text(
                    f"{data['id']} (x: {int(monster.center_x / C.TILE_SIZE)} y:{int(monster.center_y / C.TILE_SIZE)})",
                    monster.center_x, monster.center_y + monster.height * 1.4,
                    arcade.color.WHITE, 15,
                    anchor_x="center"
                ).draw()

# Глобальный экземпляр
entity_manager = EntityManager()
