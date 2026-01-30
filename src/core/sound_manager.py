import logging
import arcade

from .resource_manager import resource_manager


class SoundManager:
    """менеджер звуков"""

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # Текущая музыка
        self.current_music = None
        self.music_player = None

        # Громкости
        self.music_volume = 0.6
        self.sounds_volume = 0.8

    def play_music(self, music_name: str):
        """
        Включает фоновую музыку.
        Останавливает предыдущую музыку перед запуском новой.
        """
        try:
            if self.music_player:
                arcade.stop_sound(self.music_player)

            sound = resource_manager.load_sound(f"sounds/background/{music_name}.wav")
            self.music_player = sound.play(volume=self.music_volume, loop=True)
            self.current_music = music_name

            self.logger.debug(f"Запущена музыка: {music_name}")

        except Exception as e:
            self.logger.warning(f"Не смог включить музыку '{music_name}': {e}")

    def play_effect(self, effect_name: str):
        """Проигрывает звуковой эффект"""
        try:
            sound = resource_manager.load_sound(f"sounds/effects/{effect_name}.wav")
            sound.play(volume=self.sounds_volume)
        except Exception as e:
            self.logger.debug(f"Не смог проиграть эффект '{effect_name}': {e}")

    def play_ui(self, ui_name: str):
        """Проигрывает звук интерфейса"""
        try:
            sound = resource_manager.load_sound(f"sounds/ui/{ui_name}.wav")
            sound.play(volume=self.sounds_volume)
        except Exception as e:
            self.logger.debug(f"Не смог проиграть UI звук '{ui_name}': {e}")

    def stop_music(self):
        """Останавливает музыку"""
        if self.music_player:
            try:
                arcade.stop_sound(self.music_player)
            except Exception as e:
                self.logger.debug(f"Не удалось остановить музыку: {e}")

        self.current_music = None
        self.music_player = None

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        # Если музыка играет, перезапускаем с новой громкостью
        if self.current_music:
            self.play_music(self.current_music)

    def set_effects_volume(self, volume: float):
        self.sounds_volume = max(0.0, min(1.0, volume))


# Глобальный экземпляр
sound_manager = SoundManager()
