import arcade
from config import constants as C


class NotificationSystem:
    """система оповещений"""

    def __init__(self, max_messages=6):
        self.messages = []  # список сообщений
        self.timers = []  # таймеры для каждого сообщения
        self.max_messages = max_messages

        self.health_change = None
        self.health_timer = 4

    def notification(self, text: str, duration: float = 4.0):
        """Добавить новое оповещение"""
        self.messages.append(text)
        self.timers.append(duration)

        # Удаляем старые если слишком много
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            self.timers.pop(0)

    def health_changes(self, value: int):
        """Добавить новое оповещение"""
        self.health_change = value
        self.health_timer = 4

    def update(self, delta_time: float):
        """Обновить таймеры"""
        for i in range(len(self.timers) - 1, -1, -1):
            self.timers[i] -= delta_time
            if self.timers[i] <= 0:
                self.messages.pop(i)
                self.timers.pop(i)

        self.health_timer -= delta_time
        if self.health_timer <= 0:
            self.health_change = None

    def draw_message(self, x: int, y: int):
        """Нарисовать все оповещения"""
        for i, text in enumerate(self.messages):
            # Прозрачность при исчезновении
            alpha = min(255, int(self.timers[i] * 255))
            color = (*C.DEEPSEEK_COLOR, alpha)

            arcade.Text(
                text,
                x,
                y - i * 17,
                color,
                15
            ).draw()

    def draw_health_changes(self, x: int, y: int):
        if self.health_change:
            alpha = min(255, int(self.health_timer * 255))

            # Выбираем цвет в зависимости от значения
            if self.health_change > 0:
                color = (0, 255, 0, alpha)  # Зеленый для лечения
            else:
                color = (255, 0, 0, alpha)  # Красный для урона

            arcade.Text(
                text=f"{self.health_change:+}",
                x=x-self.health_timer * 10,
                y=y,
                color=color,
                bold=True,
                font_size=15
            ).draw()

    def clear(self):
        """Очистить все оповещения"""
        self.messages.clear()
        self.timers.clear()

notifications = NotificationSystem()