import logging
import arcade

from config import  constants as C
from src.core.dialogue_manager import dialogue_manager
from src.core.game_state_manager import GameStateManager
from src.core.input_manager import InputManager
from src.core.resource_manager import resource_manager
from src.core.asset_loader import AssetLoader
from src.states.cheat_console_state import CheatConsoleState
from src.states.death_state import DeathState
from src.states.dialogue_state import DialogueState
from src.states.finish_state import FinishState
from src.states.inventory_state import InventoryState
from src.states.lobby_state import LobbyState
from src.states.game_state import GameplayState
from src.states.lock_picking_state import LockPickingState
from src.states.pause_menu_state import PauseMenuState
from src.states.settings_state import SettingsState
from src.states.stats_state import StatsState


class MainWindow(arcade.Window):
    """
    Главное окно игры.
    (Вся логика делегируется GameStateManager)
    """

    def __init__(self):

        # КОНСТАНТЫ
        self.screen_title = C.SCREEN_TITLE

        self.screen_width = C.SCREEN_WIDTH
        self.screen_height = C.SCREEN_HEIGHT

        self.viewport_width = C.VIEWPORT_WIDTH
        self.viewport_height = C.VIEWPORT_HEIGHT

        super().__init__(
            width=self.screen_width,
            height=self.screen_height,
            title=self.screen_title,
            update_rate=1 / 60
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Создано окно: {self.screen_width}x{self.screen_height}")

        # Устанавливаем цвет фона
        arcade.set_background_color(arcade.color.ASH_GREY)

        # СОЗДАЕМ МЕНЕДЖЕРЫ
        self.resource_manager = resource_manager
        self.asset_loader = AssetLoader()
        self.input_manager = InputManager()

        # СОЗДАЕМ ЦЕНТРАЛЬНЫЙ МЕНЕДЖЕР СОСТОЯНИЙ
        self.gsm = GameStateManager(self)
        self.gsm.input_manager = self.input_manager
        self.gsm.asset_loader = self.asset_loader

        # РЕГИСТРИРУЕМ ВСЕ СОСТОЯНИЯ
        self._register_states()

        # НАЧИНАЕМ С ЛОББИ
        self.gsm.switch_to("lobby")

    def _register_states(self):
        """Регистрирует все состояния игры"""
        lobby_state = LobbyState(self.gsm, self.asset_loader)
        self.game_state = GameplayState(self.gsm, self.asset_loader)
        pause_state = PauseMenuState(self.gsm, self.asset_loader)
        settings_state = SettingsState(self.gsm, self.asset_loader)
        self.cheat_state = CheatConsoleState(self.gsm, self.asset_loader)
        lock_state = LockPickingState(self.gsm, self.asset_loader)
        stats_state = StatsState(self.gsm, self.asset_loader)
        dialogue_state = DialogueState(self.gsm, self.asset_loader)
        inventory_state = InventoryState(self.gsm, self.asset_loader)
        finish_state = FinishState(self.gsm, self.asset_loader)
        death_state = DeathState(self.gsm, self.asset_loader)

        # Регистрация состояний
        self.gsm.register_state("lobby", lobby_state)
        self.gsm.register_state("game", self.game_state)
        self.gsm.register_state("pause_menu", pause_state)
        self.gsm.register_state("settings", settings_state)
        self.gsm.register_state("cheat_console", self.cheat_state)
        self.gsm.register_state("lock_picking", lock_state)
        self.gsm.register_state("stats", stats_state)
        self.gsm.register_state("dialogue", dialogue_state)
        self.gsm.register_state("inventory", inventory_state)
        self.gsm.register_state("finish", finish_state)
        self.gsm.register_state("death", death_state)

        self.logger.debug(f"Зарегистрировано состояний: {len(self.gsm.states)}")

    def on_draw(self):
        """Отрисовка - делегируем GameStateManager"""
        self.clear()
        self.gsm.draw()

    def on_update(self, delta_time: float):
        """Обновление - делегируем GameStateManager"""
        self.gsm.update(delta_time)

    def on_key_press(self, key: int, modifiers: int):
        """Нажатие клавиши"""
        self.input_manager.on_key_press(key, modifiers)
        self.gsm.handle_key_press(key, modifiers)

    def on_key_release(self, key: int, modifiers: int):
        """Отпускание клавиши"""
        self.input_manager.on_key_release(key, modifiers)
        self.gsm.handle_key_release(key, modifiers)

    def on_close(self):
        """Закрытие окна"""
        dialogue_manager.close()
        super().on_close()
