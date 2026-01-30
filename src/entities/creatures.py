import random
from typing import Tuple
import arcade

from config.creature_config import CreatureConfig as MC
from .base_entity import Entity
from .items.item_factory import ItemFactory
from ..core.asset_loader import AssetLoader
from ..core.game_data import game_data
from ..effects.particle_manager import particle_manager
from ..ui.health_bar import HealthBar
from ..ui.notification_system import notifications as ns
from config import constants as C


class Creature(Entity):
    """Простой монстр"""

    def __init__(self, creature_id: str, mob_name: str, creature_type: str, position: list[float], properties=None,
                 scale=1.0):
        # Получаем имя существа (есть дублирование, оставляю как в оригинале)
        self.creature_name = mob_name
        self.wander_direction = (0, 0)

        # Определяем, является ли существо NPC (по типу)
        is_npc = creature_type == "npc"

        # Для NPC используем имя, для остальных - тип существа
        texture_to_load = mob_name if is_npc else creature_type

        # Загружаем спрайты через AssetLoader
        asset_loader = AssetLoader()

        try:
            sprite_size = MC.get_sprite_size(texture_to_load)
            texture_dict = asset_loader.load_creature_sprites(texture_to_load, sprite_size)
        except:
            # Fallback на дефолт
            sprite_size = MC.get_sprite_size("default")
            texture_dict = asset_loader.load_creature_sprites("default", sprite_size)

        # Собираем все текстуры в один список для Entity
        all_textures = []
        for direction in ["up", "down", "left", "right"]:
            if direction in texture_dict:
                all_textures.extend(texture_dict[direction])
            else:
                all_textures.extend([texture_dict.get("down", [None])[0]] * 2)

        # Сохраняем texture_dict для анимации
        self.texture_dict = texture_dict
        self.animation_speed = MC.get_animation_speed(self.creature_name)

        # Создаём Entity
        super().__init__(
            entity_id=creature_id,
            texture_list=all_textures,
            scale=scale
        )

        # Инициализация анимации
        self.texture_indexes = {
            "up": 0,
            "down": 2,
            "left": 4,
            "right": 6
        }
        self.last_direction = "down"
        self.cur_texture_index = self.texture_indexes["down"]
        self.is_moving = False

        self.return_timer = 0
        self.wander_timer = 0

        # Таймеры для диалогов
        self.dialogue_said = False
        self.last_dialogue_time = 0
        self.dialogue_cooldown = 3.0

        # Позиция
        self.center_x, self.center_y = position
        self.creature_type = creature_type

        # Свойства зоны
        self.zone_id = None
        self.zone_rect: Tuple[float, float, float, float] = (0, 0, 0, 0)

        # Состояние поведения
        self.current_state = "idle"
        self.current_action = None
        self.action_timer = 0

        # Для возврата в зону
        self.return_target = None

        # Загружаем свойства из GameData
        self._load_properties_from_data()

        self.health_bar = HealthBar(
            self,
            x=position[0],
            y=position[1] + self.height,
            width=100,
            height=10,
            font_size=8,
            border=1
        )

        if not self.is_alive:
            self.visible = False
            self.logger.info(f"Монстр {creature_id} уже мертв")

        self.is_nearby = False

        # для отбрасывания
        self.last_x = self.center_x
        self.last_y = self.center_y
        self.push_back_might = 75
        self.current_direction = "down"
        self.set_texture(self.cur_texture_index)

    def _load_properties_from_data(self):
        """Загружает свойства из GameData"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data:
            # Устанавливаем свойства как атрибуты
            for key, value in data.items():
                if key not in ["id", "type", "position"]:
                    setattr(self, key, value)

            # Если монстр мертв - скрываем
            if not data.get("is_alive", True):
                self.visible = False

    def _combat_interaction(self, player, collision_layer, mobs):
        """Взаимодействие с игроком - двусторонний урон"""
        if self.is_alive:
            # Монстр наносит урон игроку
            game_data.take_damage(self.damage)
            self.push_back(player, collision_layer, mobs)
            self.if_alive()

    def push_back(self, player, collision_layer, mobs):
        """Отбрасывает игрока, но не в стену"""
        dx = self.center_x - self.last_x
        dy = self.center_y - self.last_y

        if dx == 0 and dy == 0:
            return

        # Направление толчка
        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "up" if dy > 0 else "down"

        # Пробуем толкнуть по одному пикселю до стены
        push_distance = self.push_back_might

        for i in range(push_distance):
            old_x, old_y = player.center_x, player.center_y

            # Двигаем на 1 пиксель
            if direction == "right":
                player.center_x += 1
            elif direction == "left":
                player.center_x -= 1
            elif direction == "up":
                player.center_y += 1
            elif direction == "down":
                player.center_y -= 1

            # Если уперлись в стену - останавливаемся
            if collision_layer and arcade.check_for_collision_with_list(player, collision_layer):
                player.center_x = old_x
                player.center_y = old_y
                break
    def _drop_loot(self):
        """Выпадение лута из монстра"""
        loot_items = ItemFactory.parse_loot_string(self.loot)

        for item in loot_items:
            game_data.add_item(
                item_id=item.item_id,
                name=item.name,
                count=item.count,
                stackable=item.is_stackable
            )

    def interact(self, player, collision_layer, mobs):
        """Взаимодействие с существом"""
        if not self.is_alive:
            return False

        # Если существо агрессивное - бой
        if self.behavior == "aggressive" and player.immortality < 0:
            self._combat_interaction(player, collision_layer, mobs)
            return True

        return False

    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None, mobs=None):
        """Обновление с поддержкой поведения"""
        super().update(delta_time)

        # Сохраняем предыдущую позицию для отбрасывания
        self.last_x = self.center_x
        self.last_y = self.center_y

        # Определяем текущее направление для анимации
        if self.wander_direction != (0,0):
            dx, dy = self.wander_direction
            if abs(dx) > abs(dy):
                self.current_direction = "right" if dx > 0 else "left"
            elif dy != 0:
                self.current_direction = "up" if dy > 0 else "down"

            # Обновляем анимацию
            self._update_animation(delta_time, self.current_direction)

        # Обновляем полоску здоровья
        self.health_bar.x = self.center_x
        self.health_bar.y = self.center_y + self.height

        # Проверяем близость к игроку
        self.is_nearby = self.in_players_range(player)

        # Основная логика поведения
        if self.can_see_player(player):
            if self.behavior == "aggressive":
                self.current_state = "chase"
                self._chase_player(player, delta_time, collision_layer, mobs)
            elif self.behavior == "passive":
                self.current_state = "idle"
                self._wander_behavior(delta_time, collision_layer, player, mobs)
        elif not self._is_point_in_zone():
            self.current_state = "return"
            self._return_to_zone(delta_time, player, collision_layer, mobs)
        else:
            self.current_state = "idle"
            self._wander_behavior(delta_time, collision_layer, player, mobs)

        # Обновляем таймеры
        self.wander_timer -= delta_time
        if self.return_timer > 0:
            self.return_timer -= delta_time

    def draw(self):
        self._draw_debug()

        if self.is_nearby:
            self.health_bar.draw()
            color = C.DEEPSEEK_COLOR
            if self.behavior == "aggressive":
                color = arcade.color.RED
            arcade.Text(
                self.name,
                x=self.center_x,
                y=self.center_y + self.height * 1.2,
                color=color,
                anchor_x="center",
                align="center",
                font_size=15

            ).draw()

    def _draw_debug(self):
        if C.debug_mode:
            arcade.Text(
                f"{self.behavior} {self.name}({self.zone_id}): {self.current_state}",
                x=self.center_x,
                y=self.center_y - self.height,
                anchor_x="center",
                align="center",
                font_size=15
            ).draw()

    def _chase_player(self, player, delta_time, collision_layer=None, mobs=None):
        """Преследование игрока с коллизиями"""
        if not hasattr(self, 'chase_speed') or not player:
            self.chase_speed = self.speed
            return

        player.under_chase = True



        direction = self._get_cardinal_direction_to_player(player)
        if not direction:
            return

        # Вычисляем смещение
        speed = self.chase_speed * delta_time * 60
        dx, dy = 0, 0

        if direction == "up":
            dy = speed
        elif direction == "down":
            dy = -speed
        elif direction == "left":
            dx = -speed
        elif direction == "right":
            dx = speed

        # Перемещаемся с проверкой коллизий
        self._move_with_collision(dx, dy, collision_layer, player, mobs)

        # Обновляем направление для анимации
        self.wander_direction = (dx, dy)

    def _move_with_collision(self, dx, dy, collision_layer, player, mobs):
        """Перемещение с проверкой коллизий"""
        old_x, old_y = self.center_x, self.center_y
        self.center_x += dx
        self.center_y += dy

        if arcade.check_for_collision_with_list(self, collision_layer):
            self.center_x = old_x
            self.center_y = old_y
            return False
        if self.collides_with_sprite(player):
            self.interact(player, collision_layer, mobs)

            self.center_x = old_x
            self.center_y = old_y
            return False
        return True

    def _get_cardinal_direction_to_player(self, player):
        """Определяет направление к игроку по 4 сторонам"""
        if not player:
            return None

        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y

        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "up" if dy > 0 else "down"

    def _return_to_zone(self, delta_time, player=None, collision_layer=None, mobs=None):
        """Возврат в свою зону с коллизиями"""
        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        target_x = zone_x + zone_w / 2
        target_y = zone_y + zone_h / 2

        dx = target_x - self.center_x
        dy = target_y - self.center_y

        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "up" if dy > 0 else "down"

        return_speed = getattr(self, 'chase_speed')
        speed = return_speed * delta_time * 60
        dx_move, dy_move = 0, 0

        if direction == "up":
            dy_move = speed
        elif direction == "down":
            dy_move = -speed
        elif direction == "left":
            dx_move = -speed
        elif direction == "right":
            dx_move = speed

        # Перемещаемся
        moved = self._move_with_collision(dx_move, dy_move, collision_layer, player, mobs)
        self.wander_direction = (dx_move, dy_move)

        # Если вернулись в зону, сбрасываем состояние
        if self._is_point_in_zone():
            self.current_state = "idle"

    def _wander_behavior(self, delta_time, collision_layer=None, player=None, mobs=None):
        """Случайное блуждание в зоне"""
        if self.wander_timer <= 0:
            directions = ["up", "down", "left", "right", None]
            direction = random.choice(directions)

            if direction:
                if direction == "up":
                    self.wander_direction = (0, self.speed)
                elif direction == "down":
                    self.wander_direction = (0, -self.speed)
                elif direction == "left":
                    self.wander_direction = (-self.speed, 0)
                elif direction == "right":
                    self.wander_direction = (self.speed, 0)
            else:
                self.wander_direction = (0, 0)

            self.wander_timer = random.uniform(1.0, 3.0)

        # Двигаемся в выбранном направлении
        dx = self.wander_direction[0] * delta_time * 60
        dy = self.wander_direction[1] * delta_time * 60

        if dx != 0 or dy != 0:
            self._move_with_collision(dx, dy, collision_layer, player, mobs)

            # Проверяем, не вышел ли за зону
            if not self._is_point_in_zone():
                self.current_state = "return"

    def _is_point_in_zone(self):
        """Проверяет, находится ли точка в зоне монстра"""
        if not self.zone_rect:
            return True

        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        zone_h = abs(zone_h)
        zone_y -= zone_h

        return (zone_x <= self.center_x <= zone_x + zone_w and
                zone_y <= self.center_y <= zone_y + zone_h)

    def can_see_player(self, player) -> bool:
        """Может ли монстр видеть игрока"""
        distance = self._get_distance_to_player(player)
        return distance <= self.vision_range

    def in_players_range(self, player) -> bool:
        """Находится ли в радиусе видимости игрока"""
        if not player:
            return False
        distance = self._get_distance_to_player(player)
        return distance <= player.vision_range

    def _get_distance_to_player(self, player):
        """Расстояние до игрока"""
        if not player:
            return float('inf')
        return ((self.center_x - player.center_x) ** 2 +
                (self.center_y - player.center_y) ** 2) ** 0.5

    def _update_animation(self, delta_time: float, current_direction: str = None):
        """Обновляет анимацию ходьбы"""
        if current_direction and current_direction != self.last_direction:
            self._set_direction_texture(current_direction)
            self.time_elapsed = 0
            self.last_direction = current_direction
            self.is_moving = True
        elif current_direction and self.time_elapsed > self.animation_speed:
            self._animate_direction(current_direction)
            self.time_elapsed = 0
            self.is_moving = True
        elif not current_direction:
            self._set_idle_texture()
            self.is_moving = False

    def _set_direction_texture(self, direction):
        """Сразу устанавливает первую текстуру направления"""
        if direction in self.texture_indexes:
            self.cur_texture_index = self.texture_indexes[direction]
            self.set_texture(self.cur_texture_index)

    def _animate_direction(self, direction):
        """Анимирует движение в указанном направлении"""
        if direction not in self.texture_indexes:
            return

        start_index = self.texture_indexes[direction]

        if self.cur_texture_index == start_index:
            self.cur_texture_index = start_index + 1
            self.set_texture(self.cur_texture_index)
        else:
            self.cur_texture_index = start_index
            self.set_texture(self.cur_texture_index)

    def _set_idle_texture(self):
        """Устанавливает статичную текстуру для стояния"""
        if self.last_direction in self.texture_indexes:
            self.cur_texture_index = self.texture_indexes[self.last_direction]
            self.set_texture(self.cur_texture_index)

    @property
    def exp(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("exp")

    @exp.setter
    def exp(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["exp"] = value



    @property
    def loot(self):
        """Читаем из GameData"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("loot")

    @loot.setter
    def loot(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["loot"] = value

    @property
    def chase_speed(self):
        """Читаем из GameData"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("chase_speed")

    @chase_speed.setter
    def chase_speed(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["chase_speed"] = value

    def if_alive(self):
        """Если здоровье закончилось - монстр умирает"""
        if self.health <= 0:
            self.logger.debug(
                f"Монстр {self.name} умирает на позиции {self.center_x // C.TILE_SIZE}, {self.center_y // C.TILE_SIZE}")
            particle_manager.create_blood(
                self.center_x,
                self.center_y,
                color=C.DEEPSEEK_COLOR,
                size=25,
                count=20
            )

            self.is_alive = False
            self.visible = False
            ns.notification(f"Монстр побежден!")

            # Добавляем опыт
            game_data.add_exp(self.exp)
            self._drop_loot()



