import logging
import math
import arcade
from ..core.game_data import game_data
from ..effects.particle_manager import particle_manager

from ..ui.notification_system import notifications as ns

class Projectile(arcade.Sprite):
    """Класс снаряда"""

    def __init__(self, projectile_id: str, texture_list, scale=4.0):
        # Убедимся, что texture_list не пустой
        if not texture_list:
            # Создаём тестовую текстуру
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
            self.logger.warning(f"Пустой список текстур для снаряда {projectile_id}")

            # Создаём цветную текстуру
            texture = arcade.Texture.create_empty(
                f"debug_{projectile_id}",
                (32, 32),
                color=(255, 0, 0, 255)  # Красный
            )
            texture_list = [texture]

        # Передаём первую текстуру в родительский конструктор КАК ПОЗИЦИОННЫЙ АРГУМЕНТ
        super().__init__(texture_list[0], scale=scale)

        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # Сохраняем все текстуры
        self.texture_list = texture_list
        self.entity_id = projectile_id

        # Добавляем все текстуры в self.textures (наследуемое от arcade.Sprite)
        for texture in texture_list[1:]:  # Первая уже добавлена в super().__init__
            self.append_texture(texture)

        # Загружаем данные снаряда
        self.data = game_data.get_projectile_data(projectile_id)

        # Анимация
        self.animation_speed = self.data.get("sprite_params", {}).get("animation_speed", 0.1)
        self.tile_count = self.data.get("sprite_params", {}).get("tile_count", 1)
        self.cur_texture_index = 0
        self.time_elapsed = 0

        # Устанавливаем начальную позицию
        pos = self.data.get("position", {"x": 0, "y": 0})
        self.center_x = pos.get("x", 0)
        self.center_y = pos.get("y", 0)

        # Направление движения
        direction = self.data.get("direction", {"x": 0, "y": 0})
        self.direction_x = direction.get("x", 0)
        self.direction_y = direction.get("y", 0)

        # Нормализуем вектор направления
        length = math.sqrt(self.direction_x ** 2 + self.direction_y ** 2)
        if length > 0:
            self.direction_x /= length
            self.direction_y /= length

        self._update_sprite_angle()

        # Скорость
        self.speed = self.data.get("speed")

        # Урон
        self.damage = self.data.get("damage")

        # Время жизни
        self.max_lifetime = self.data.get("max_lifetime", 3.0)
        self.current_lifetime = 0

        # Владелец (чтобы снаряд не попадал в себя)
        self.owner_id = self.data.get("owner_id", "player")

        # Флаг активного состояния
        self.is_active = True


    def _update_sprite_angle(self):
        """Обновляет угол спрайта в зависимости от направления атаки"""
        math_angle = math.degrees(math.atan2(self.direction_y, self.direction_x))
        arcade_angle = -math_angle
        self.angle = (arcade_angle - 270) % 360

    def update(self, delta_time: float = 1 / 60, collision_layer=None, monsters=None):
        """Обновление снаряда"""

        if not self.is_active:
            return

        # Обновляем время жизни
        self.current_lifetime += delta_time
        if self.current_lifetime >= self.max_lifetime:
            self.is_active = False
            return

        # Обновляем анимацию
        self._update_animation(delta_time)
        start_x = self.center_x
        start_y = self.center_y
        particle_manager.create_explosion(
            start_x,
            start_y,
            color=arcade.color.ORANGE,
            size=5,
            count=4
        )

        # Движение
        move_x = self.direction_x * self.speed * delta_time
        move_y = self.direction_y * self.speed * delta_time

        self.center_x += move_x
        self.center_y += move_y

        # Проверяем коллизии со стенами
        if collision_layer and arcade.check_for_collision_with_list(self, collision_layer):
            self.is_active = False
            return

        # Проверяем коллизии с монстрами
        if monsters:
            for monster in monsters:



                if monster.is_alive and arcade.check_for_collision(self, monster):
                    # Наносим урон
                    if monster.imp and monster.behavior == "passive":
                        self.is_active = False
                        ns.notification(f"{monster.name} не может получить от вас урон")
                        return
                    monster.health = max(0, int(monster.health) - self.damage)
                    monster.behavior = "aggressive"
                    self.is_active = False

                    # Проверяем, не убит ли монстр
                    if monster.health <= 0:
                        monster.if_alive()
                    return

    def _update_animation(self, delta_time: float):
        """Обновляет анимацию снаряда"""
        if self.tile_count <= 1 or len(self.textures) <= 1:
            return  # Нет анимации

        self.time_elapsed += delta_time

        if self.time_elapsed >= self.animation_speed:
            self.time_elapsed = 0
            self.cur_texture_index = (self.cur_texture_index + 1) % len(self.textures)
            self.set_texture(self.cur_texture_index)

    def get_debug_info(self):
        """Возвращает отладочную информацию для рисования"""
        if not self.is_active:
            return None

        return {
            "position": (self.center_x, self.center_y),
            "direction": (self.direction_x, self.direction_y),
            "id": self.entity_id,
            "lifetime": f"{self.current_lifetime:.1f}/{self.max_lifetime:.1f}"
        }