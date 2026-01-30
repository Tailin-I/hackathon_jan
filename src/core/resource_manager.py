import os
from pathlib import Path

import arcade
from typing import Dict


class ResourceManager:
    """Менеджер для загрузки и кэширования ресурсов"""

    def __init__(self):
        self._textures: Dict[str, arcade.Texture] = {}
        self._project_root = None

    def get_project_root(self) -> str:
        """загрузка корня проекта"""
        if self._project_root is None:
            current_file = Path(__file__).resolve()
            core_dir = current_file.parent
            src_dir = core_dir.parent
            self._project_root = str(src_dir.parent)  # Преобразуем в строку

        # Убедимся, что путь нормализован для текущей ОС
        return os.path.normpath(self._project_root)

    def get_resource_path(self, relative_path: str) -> str:
        """Получить абсолютный путь к ресурсу"""
        return os.path.join(self.get_project_root(), "res", relative_path)

    def get_full_path(self, relative_path: str) -> str:
        """Получить абсолютный путь к ресурсу"""
        return os.path.join(self.get_project_root(), relative_path)

    def get_save_path(self, file):
        return os.path.join(self.get_project_root(), "saves", f"{file}.dat")

    def load_texture(self, relative_path: str) -> arcade.Texture:
        """Загрузить текстуру с кэшированием"""

        if relative_path in self._textures:
            return self._textures[relative_path]

        path = self.get_resource_path(relative_path)
        texture = arcade.load_texture(path)
        self._textures[relative_path] = texture
        return texture

    def load_item(self, name, folder):
        path = os.path.join(self.get_project_root(), "res", "items", folder, f"{name}.png")
        return self.load_texture(path)

    def load_spritesheet(self, relative_path: str, size=(16, 16), columns=8, count=8):
        """Загрузить spritesheet"""
        path = self.get_resource_path(relative_path)
        grid = arcade.load_spritesheet(path)
        return grid.get_texture_grid(size=size, columns=columns, count=count)

    def load_sound(self, relative_path: str) -> arcade.Sound:
        """Загрузить звук с кэшированием"""
        path = self.get_resource_path(relative_path)
        sound = arcade.load_sound(path)
        return sound

    def clear_cache(self):
        """Очистить кэш ресурсов"""
        self._textures.clear()


# Глобальный экземпляр менеджера
resource_manager = ResourceManager()
