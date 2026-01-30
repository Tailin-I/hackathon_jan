import logging
from config import  constants as C
from src.core.game_data import game_data
from src.core.resource_manager import resource_manager
from src.core.sound_manager import sound_manager
from src.effects.particle_manager import particle_manager


class BaseState:
    """
    Базовый класс для всех состояний.
    """

    def __init__(self, state_id: str, gsm, asset_loader=None):
        self.player = None
        self.logger = logging.getLogger(self.__class__.__name__)

        self.game_data = game_data
        self.rm = resource_manager
        self.asset_loader = asset_loader
        self.sound_manager = sound_manager
        self.particle_manager = particle_manager


        self.state_id = state_id
        self.gsm = gsm
        self.is_active = False

        # РАЗМЕРЫ:
        self.tile_size = C.TILE_SIZE
        self.scale_factor = C.SCALE_FACTOR

    def on_enter(self, **kwargs):
        """Вход в состояние"""
        pass

    def on_exit(self):
        """Выход из состояния"""
        pass

    def update(self, delta_time: float):
        """Обновление"""
        pass

    def draw(self):
        """Отрисовка"""
        pass

    def on_pause(self):
        """Пауза"""
        pass

    def on_resume(self):
        """Возобновление"""
        pass

    def handle_key_press(self, key: int, modifiers: int):
        """Обработка клавиш"""
        pass

    def handle_key_release(self, key: int, modifiers: int):
        """Обработка отпускания"""
        pass