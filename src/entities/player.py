import arcade

from .base_entity import Entity
from config import constants as C
from ..core.game_data import game_data


class Player(Entity):
    def __init__(self, texture_dict, input_manager, scale=1):
        # Собираем все текстуры в один список
        all_textures = []
        for direction in ["up", "down", "left", "right"]:
            all_textures.extend(texture_dict[direction])

        # Важно: entity_id = "player"
        super().__init__(entity_id="player", texture_list=all_textures, scale=scale)

        self.texture_dict = texture_dict
        self.input_manager = input_manager


        # Маппинг направлений
        self.texture_indexes = {
            "up": 0,  # текстуры 0 и 1
            "down": 2,  # текстуры 2 и 3
            "left": 4,  # текстуры 4 и 5
            "right": 6  # текстуры 6 и 7
        }
        self.last_direction = "down"
        self.cur_texture_index = self.texture_indexes["down"]

        # Позиция из GameData
        self.center_x, self.center_y, _ = game_data.get_player_position()

        # Инициализируем текстуру
        self.set_texture(self.cur_texture_index)

        self.fatigue_timer = 0

        self.physics_engine = None # для коллизий(для защиты)



    @property
    def speed(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("speed")

    @property
    def inventory(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("inventory")

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        super().update(delta_time)

        self.fatigue_timer += delta_time
        if self.fatigue_timer >= delta_time * 10 and self.fatigue > 0:
            self.fatigue = max(0, self.fatigue - self.restoration_speed)
            self.fatigue_timer = 0

        dx, dy = 0, 0
        current_direction = None

        # Обработка ввода
        if self.input_manager.get_action('up'):
            current_direction = "up"
            dy += self.speed * delta_time * 60
        if self.input_manager.get_action('down'):
            current_direction = "down"
            dy -= self.speed * delta_time * 60
        if self.input_manager.get_action('left'):
            current_direction = "left"
            dx -= self.speed * delta_time * 60
        if self.input_manager.get_action('right'):
            current_direction = "right"
            dx += self.speed * delta_time * 60


        if self.input_manager.get_action('tp_up'):
            self.center_y += 100
        if self.input_manager.get_action('tp_down'):
            self.center_y -= 100
        if self.input_manager.get_action('tp_left'):
            self.center_x -= 100
        if self.input_manager.get_action('tp_right'):
            self.center_x += 100

        # Обработка анимации
        if current_direction and current_direction != self.last_direction:
            self._set_direction_texture(current_direction)
            self.time_elapsed = 0

        if current_direction and self.time_elapsed > 0.3:
            self._animate_direction(current_direction)
            self.time_elapsed = 0
        elif not current_direction:
            self._set_idle_texture()

        # Обновляем последнее направление
        if current_direction:
            self.last_direction = current_direction

        # Перемещение с учетом коллизий
        collision_layer = kwargs.get('collision_layer')
        monster = kwargs.get('monster')

        old_x, old_y = self.center_x, self.center_y
        self.move_with_tiled_collision(collision_layer, monster, dx, dy)

        # Если позиция изменилась - сохраняем в GameData
        if self.center_x != old_x or self.center_y != old_y:
            x_tiles = int(self.center_x / C.TILE_SIZE)
            y_tiles = int(self.center_y / C.TILE_SIZE)
            self.data_source.player_data["position"]["x"] = x_tiles
            self.data_source.player_data["position"]["y"] = y_tiles

        if not self.damaged_state:
            self._update_ghost_appearance()
    def draw(self):
        if C.debug_mode:
            arcade.draw_circle_outline(
                self.center_x, self.center_y,
                self.vision_range,
                arcade.color.GREEN, 1
            )

    def move_with_tiled_collision(self, collision_layer, monster=None, dx=0, dy=0):
        """
        метод коллизий.
        """
        # Если режим призрака
        if C.ghost_mode:
            self.center_x += dx
            self.center_y += dy
            return

        # Создаем временную копию позиции
        target_x = self.center_x + dx
        target_y = self.center_y + dy

        # Сохраняем реальную позицию
        original_x, original_y = self.center_x, self.center_y

        # Телепортируем игрока к позиции
        self.center_x = target_x
        self.center_y = target_y

        # Проверяем коллизии через физический движок
        if hasattr(self, 'physics_engine') and self.physics_engine:
            self.physics_engine.update()

            if self.center_x == original_x and self.center_y == original_y:
                # Коллизия со стенами
                return

        # Проверяем коллизии с монстрами
        if monster and arcade.check_for_collision_with_list(self, monster):
            self.center_x = original_x
            self.center_y = original_y

    def _set_direction_texture(self, direction):
        """Сразу устанавливает первую текстуру направления"""
        if direction == "up":
            self.cur_texture_index = 0
        elif direction == "down":
            self.cur_texture_index = 2
        elif direction == "left":
            self.cur_texture_index = 4
        elif direction == "right":
            self.cur_texture_index = 6

        self.set_texture(self.cur_texture_index)

    def _animate_direction(self, direction):
        """Анимирует движение в указанном направлении"""
        direction_map = {
            "up": (0, 1),  # текстуры 0 и 1
            "down": (2, 3),  # текстуры 2 и 3
            "left": (4, 5),  # текстуры 4 и 5
            "right": (6, 7)  # текстуры 6 и 7
        }

        tex1, tex2 = direction_map[direction]

        # Переключаем между двумя текстурами
        if self.cur_texture_index == tex1:
            self.cur_texture_index = tex2
            self.set_texture(tex2)
        else:
            self.cur_texture_index = tex1
            self.set_texture(tex1)

    def _set_idle_texture(self):
        """Устанавливает статичную текстуру для стояния"""
        # Определяем последнее направление для idle-позы
        if self.last_direction == "up":
            self.cur_texture_index = 0
            self.set_texture(0)
        elif self.last_direction == "down":
            self.cur_texture_index = 2
            self.set_texture(2)
        elif self.last_direction == "left":
            self.cur_texture_index = 4
            self.set_texture(4)
        elif self.last_direction == "right":
            self.cur_texture_index = 6
            self.set_texture(6)

    def _update_ghost_appearance(self):
        """Обновляет внешний вид в режиме призрака"""
        if C.ghost_mode and self.color != C.ghost_color:
            # Устанавливаем синий полупрозрачный цвет
            self.color = C.ghost_color
        elif not C.ghost_mode and self.color != C.base_color:
            # Возвращаем нормальный цвет
            self.color = C.base_color


    @property
    def damage(self):
        return self.strength

    @property
    def max_fatigue(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("max_fatigue")

    @max_fatigue.setter
    def max_fatigue(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["max_fatigue"] = value

    @property
    def fatigue(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("fatigue")

    @fatigue.setter
    def fatigue(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["fatigue"] = value

    @property
    def restoration_speed(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("restoration_speed")

    @restoration_speed.setter
    def restoration_speed(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["restoration_speed"] = value

    @property
    def strength(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("strength", 0)

    @strength.setter
    def strength(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["strength"] = value