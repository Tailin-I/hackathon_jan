import arcade
from .base_state import BaseState
from ..ui.notification_system import notifications as ns
from config import constants as C

class LockPickingState(BaseState):
    """Мини-игра для взлома сундуков"""

    def __init__(self, gsm, asset_loader):
        super().__init__("lock_picking", gsm, asset_loader)
        self.chest_event = None
        self.player = None
        self.current_sequence = ""
        self.status_text = "← / → Для взлома"

    def on_enter(self, **kwargs):
        self.current_sequence = ""
        self.chest_event = kwargs.get("chest_event")
        self.player = kwargs.get("player")

        if self.chest_event:
            self.status_text = "← / → Для взлома"

    def handle_key_press(self, key, modifiers):
        if not self.chest_event:
            return

        # Влево
        if self.gsm.input_manager.get_action("left"):
            success, completed, sequence = self.chest_event.check_lock_attempt("<")
            self._handle_lock_result(success, completed, sequence)

        # Вправо
        elif self.gsm.input_manager.get_action("right"):
            success, completed, sequence = self.chest_event.check_lock_attempt(">")
            self._handle_lock_result(success, completed, sequence)

        # Отмена
        elif self.gsm.input_manager.get_action("escape"):
            ns.notification("Взлом отменен")
            self.gsm.pop_overlay()

    def _handle_lock_result(self, success, completed, sequence):
        """Обрабатывает результат попытки взлома"""
        self.current_sequence = sequence
        if completed:
            if success:
                self.chest_event.open_chest()
                self.status_text = "Замок взломан!"
                # Закрываем через 1 секунду
                arcade.schedule(self._close_overlay, 1.0)
            else:
                self.status_text = "Будь осторожнее"
        else:
            # Показываем прогресс
            progress = len(sequence)
            total = len(self.chest_event.lock_sequence)
            self.status_text = f"{sequence} ({total-progress})"

    def _close_overlay(self, delta_time):
        """Закрывает overlay"""
        arcade.unschedule(self._close_overlay)
        self.gsm.pop_overlay()

    def draw(self):
        """Отрисовка интерфейса взлома"""
        C.draw_dark_background()

        # Окно взлома
        window_x = self.gsm.window.width // 2
        window_y = self.gsm.window.height // 2
        window_w = 400
        window_h = 200

        arcade.draw_rect_filled(
            arcade.rect.XYWH(window_x, window_y, window_w, window_h),
            (40, 40, 60)
        )

        arcade.draw_rect_outline(
            arcade.rect.XYWH(window_x, window_y, window_w, window_h),
            arcade.color.GOLD, 3
        )

        # Текст
        arcade.Text(
            "ВЗЛОМ ЗАМКА",
            window_x, window_y + 60,
            arcade.color.GOLD, 24,
            anchor_x="center", anchor_y="center"
        ).draw()

        arcade.Text(
            self.status_text,
            window_x, window_y,
            arcade.color.WHITE, 25,
            anchor_x="center", anchor_y="center"
        ).draw()
