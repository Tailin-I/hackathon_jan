import arcade
import random
from typing import Tuple




class Particle(arcade.Sprite):
    """Одна частица"""

    def __init__(self, x: float, y: float,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 size: int = 4,
                 lifetime: float = 1.0):
        if len(color) == 3:
            color_with_alpha = color + (255,)
        else:
            color_with_alpha = color

        texture = arcade.Texture.create_empty(
            f"particle_{color}",
            (size, size),
            color=color_with_alpha
        )

        super().__init__(texture)

        self.center_x = x
        self.center_y = y
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime

        # Случайное направление
        self.velocity_x = random.uniform(-5, 5)
        self.velocity_y = random.uniform(-5, 5)

        # Гравитация
        # self.gravity = -50

        # Исчезание
        self.fade_out = True

    def update_particle(self, delta_time: float) -> bool:
        """Обновление частицы."""
        # Движение через change_x/change_y (совместимо с arcade.Sprite)
        self.change_x = self.velocity_x
        self.change_y = self.velocity_y
        # Вызываем родительский update для движения
        super().update(delta_time)

        # Гравитация
        # self.velocity_y += self.gravity * delta_time

        # Уменьшение времени жизни
        self.lifetime -= delta_time


        # Прозрачность при исчезанииy
        if self.fade_out:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            self.alpha = max(0, min(255, alpha))

        # Уменьшение размера
        scale = self.lifetime / self.max_lifetime
        self.scale = max(0.1, scale)

        return self.lifetime <= 0