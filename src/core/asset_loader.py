import logging

import arcade

from .sound_manager import sound_manager
from ..core.resource_manager import resource_manager


class AssetLoader:
    """Загружает игровые ресурсы"""

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.rm = resource_manager
        self.sound_manager = sound_manager

    def load_creature_sprites(self, creature_name: str, texture_size: tuple = None):
        """
        Загружает спрайты для существа.
        Пытается загрузить по имени, если не находит - использует стандартную текстуру.

        Args:
            creature_name: Имя существа ("Алина", "Артемий", "bug")
            texture_size: Размер одного спрайта (width, height). Если None - определяется автоматически.
        """
        # Пробуем загрузить как спрайтлист
        spritesheet_path = f"mobs/{creature_name}.png"

        try:
            if texture_size:
                # Если указан размер - загружаем как спрайтлист
                textures = self.rm.load_spritesheet(
                    spritesheet_path,
                    size=texture_size,
                    columns=8,  # Всегда 8 спрайтов
                    count=8,
                )
            else:
                # Загружаем текстуру и проверяем размер
                texture = self.rm.load_texture(spritesheet_path)
                img_width = texture.width
                img_height = texture.height

                if img_width >= img_height * 8:
                    # Вероятно, это спрайтлист
                    sprite_height = img_height
                    sprite_width = img_width // 8
                    textures = self.rm.load_spritesheet(
                        spritesheet_path,
                        size=(sprite_width, sprite_height),
                        columns=8,
                        count=8,
                    )
                else:
                    # Одиночная текстура - дублируем её для всех направлений
                    textures = [texture] * 8

        except Exception as e:
            self.logger.warning(f"Не удалось загрузить текстуру {creature_name}: {e}")
            # Fallback на стандартную
            texture = self.rm.load_texture("mobs/default.png")
            textures = [texture] * 8

        # Группируем по направлениям
        return {
            "up": [textures[0], textures[1]],
            "down": [textures[2], textures[3]],
            "left": [textures[4], textures[5]],
            "right": [textures[6], textures[7]]
        }

    def load_player_sprites(self):
        """Загружает спрайты игрока (специальный случай)"""
        return self.load_creature_sprites("default", (63, 63))

    def load_background(self, name):
        """Загружает фоновую текстуру"""
        path = f"backgrounds/{name}.png"
        return self.rm.load_texture(path)

    def load_ui_texture(self, name):
        """Загружает текстуру для UI - используем кеш ResourceManager"""
        path = f"ui/{name}.png"
        return self.rm.load_texture(path)

    def load_background_music(self, name: str) -> arcade.Sound:
        """Загружает фоновую музыку через SoundManager"""
        return self.sound_manager.load_background_music(name)

    def load_effect_sound(self, name: str) -> arcade.Sound:
        """Загружает звуковой эффект через SoundManager"""
        return self.sound_manager.load_effect_sound(name)

    def load_ui_sound(self, name: str) -> arcade.Sound:
        """Загружает звук интерфейса через SoundManager"""
        return self.sound_manager.load_ui_sound(name)

    def load_projectile_sprites(self, texture_name: str, sprite_size: tuple = None,
                                tile_count: int = 1, animation_speed: float = 0.1):
        """
        Загружает спрайты для снаряда.

        Args:
            texture_name: Имя текстуры (например, "projectiles/fireball")
            sprite_size: Размер одного спрайта (width, height). Если None - определяется из текстуры.
            tile_count: Количество тайлов в спрайтлисте (по горизонтали)
            animation_speed: Скорость анимации (секунды на кадр)
        """
        spritesheet_path = f"projectiles/{texture_name}.png"
        if sprite_size:
            # Если указан размер - загружаем как спрайтлист
            textures = self.rm.load_spritesheet(
                spritesheet_path,
                size=sprite_size,
                columns=tile_count,
                count=tile_count,
            )
        else:
            # Пробуем загрузить как одиночную текстуру
            texture = self.rm.load_texture(spritesheet_path)
            textures = [texture]

        return textures
