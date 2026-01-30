import logging
import arcade

from ..core.game_data import game_data
from config import constants as C
from ..effects.particle_manager import particle_manager


class Entity(arcade.Sprite):
    """Главный класс для всех сущностей"""

    def __init__(self, entity_id, texture_list, scale=1, angle=0):

        super().__init__(texture_list=texture_list[0], angle=angle, scale=scale)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.data_source = game_data

        self.entity_id = entity_id
        # Сохраняем текстуры для анимации
        self.textures = texture_list
        self.cur_texture_index = 0
        self.time_elapsed = 0

        # self.last_health = self.health
        self.immortality = 1

        self.damaged_state = False
        self.last_health = self.health

    @property
    def name(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("name")

    @name.setter
    def name(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["name"] = value

    @property
    def health(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return int(data.get("health"))

    @health.setter
    def health(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["health"] = value

    @property
    def max_health(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("max_health", 100)

    @max_health.setter
    def max_health(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["max_health"] = value

    @property
    def damage(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("damage", 0)

    @damage.setter
    def damage(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["damage"] = value

    @property
    def behavior(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("behavior", "passive")

    @behavior.setter
    def behavior(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["behavior"] = value

    @property
    def is_alive(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("is_alive", True)

    @is_alive.setter
    def is_alive(self, value: bool):
        data = self.data_source.get_entity_data(self.entity_id)
        data["is_alive"] = value

    @property
    def active_topic(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("active_topic", "greeting")

    @active_topic.setter
    def active_topic(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["active_topic"] = value

    @property
    def can_dialogue(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("can_dialogue", False)

    @can_dialogue.setter
    def can_dialogue(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["can_dialogue"] = value

    @property
    def speed(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("speed")

    @speed.setter
    def speed(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["speed"] = value

    @property
    def vision_range(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("vision_range")

    @vision_range.setter
    def vision_range(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["vision_range"] = value

    @property
    def imp(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("imp")

    @imp.setter
    def imp(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["imp"] = value


    def damage_creature(self, delta_time):
        old_health = self.last_health
        new_health = self.health

        # Проверяем изменение здоровья
        if new_health != old_health:
            self.immortality = 0.9
            self.last_health = new_health
            self.damaged_state = True

        # таймер неуязвимости
        if self.immortality > 0:
            self.immortality -= delta_time
            if self.immortality <= 0:
                self.damaged_state = False

        # Цвет в зависимости от состояния
        if self.damaged_state and self.immortality > 0.3:
            self.color = C.damaged_color
        else:
            self.color = C.base_color



    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """Базовое обновление"""
        self.time_elapsed += delta_time

        self.damage_creature(delta_time)

