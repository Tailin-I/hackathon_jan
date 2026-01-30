import arcade
import random
from typing import Dict, List, Optional
from .resource_manager import resource_manager


class DialogueBackgroundManager:
    """Менеджер для управления фоновыми картинками в диалогах"""

    def __init__(self):
        self.backgrounds: Dict[str, List[arcade.Texture]] = {}
        self.current_backgrounds: Dict[str, dict] = {}  # npc_name -> {images: [], current_index: int}

    def load_backgrounds_for_npc(self, npc_name: str, image_names: List[str]):
        """Загружает фоновые картинки для NPC"""
        textures = []
        for image_name in image_names:
            try:
                path = f"dialogs_bgr/{image_name}.png"
                texture = resource_manager.load_texture(path)
                textures.append(texture)
            except Exception as e:
                print(f"Ошибка загрузки фона {image_name} для NPC {npc_name}: {e}")

        self.backgrounds[npc_name] = textures
        self.current_backgrounds[npc_name] = {
            "images": textures,
            "current_index": 0
        }

    def get_current_background(self, npc_name: str) -> Optional[arcade.Texture]:
        """Получает текущую фоновую картинку для NPC"""
        if npc_name not in self.current_backgrounds:
            return None

        data = self.current_backgrounds[npc_name]
        if not data["images"]:
            return None

        return data["images"][data["current_index"]]

    def next_background(self, npc_name: str):
        """Переключает на следующую фоновую картинку"""
        if npc_name not in self.current_backgrounds:
            return

        data = self.current_backgrounds[npc_name]
        if not data["images"]:
            return

        data["current_index"] = (data["current_index"] + 1) % len(data["images"])

    def random_background(self, npc_name: str):
        """Устанавливает случайный фон"""
        if npc_name not in self.current_backgrounds:
            return

        data = self.current_backgrounds[npc_name]
        if len(data["images"]) > 1:
            data["current_index"] = random.randrange(len(data["images"]))

    def reset_background(self, npc_name: str):
        """Сбрасывает фон на первый"""
        if npc_name in self.current_backgrounds:
            self.current_backgrounds[npc_name]["current_index"] = 0


# Глобальный экземпляр
dialogue_bg_manager = DialogueBackgroundManager()