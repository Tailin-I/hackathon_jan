class CreatureConfig:
    """Конфигурация для всех существ"""

    # Размеры спрайтов для каждого типа существ
    SPRITE_SIZES = {
        "алина": (63, 63),
        "соня": (63, 63),
        "марк": (63, 63),
        "артемий": (63, 63),
        "dobro": (63, 63),
        "миша": (16, 16),
        "bug": (16, 16),  # Или какой размер у жука?
        "default": (63, 63),
        "олег": (16, 16)
    }

    # Скорость анимации для каждого типа
    ANIMATION_SPEEDS = {
        "алина": 0.4,
        "соня": 0.4,
        "марк": 0.4,
        "артемий": 0.5,
        "dobroa": 0.6,
        "миша": 0.2,
        "bug": 0.6,
        "default": 0.4,
        "олег": 0.4
    }

    @classmethod
    def get_sprite_size(cls, creature_name: str):
        """Получить размер спрайта для существа"""
        return cls.SPRITE_SIZES.get(creature_name, cls.SPRITE_SIZES["default"])

    @classmethod
    def get_animation_speed(cls, creature_name: str):
        """Получить скорость анимации"""
        return cls.ANIMATION_SPEEDS.get(creature_name, cls.ANIMATION_SPEEDS["default"])