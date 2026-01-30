class CreatureConfig:
    """Конфигурация для всех существ"""

    # Размеры спрайтов для каждого типа существ
    SPRITE_SIZES = {
        "лукашенко": (63, 63),
        "валентина степановна":(63,63),
        "автор": (63, 63),
        "виктор": (63, 63),
        "людмила": (63, 63),
        "default": (63, 63),
        "дух": (16, 16)
    }

    # Скорость анимации для каждого типа
    ANIMATION_SPEEDS = {
        "лукашенко": 0.4,
        "валентина степановна": 0.4,
        "автор": 0.4,
        "виктор": 0.4,
        "людмила":0.4,
        "default": 0.4,
        "дух": 0.4
    }

    @classmethod
    def get_sprite_size(cls, creature_name: str):
        """Получить размер спрайта для существа"""
        return cls.SPRITE_SIZES.get(creature_name, cls.SPRITE_SIZES["default"])

    @classmethod
    def get_animation_speed(cls, creature_name: str):
        """Получить скорость анимации"""
        return cls.ANIMATION_SPEEDS.get(creature_name, cls.ANIMATION_SPEEDS["default"])