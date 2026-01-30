import arcade
import random
from typing import List, Tuple
from .particle import Particle


class ParticleManager:
    """Управляет всеми частицами"""

    def __init__(self):
        self.particles: List[Particle] = []
        self.particle_list = arcade.SpriteList()

    def create_explosion(self, x: float, y: float,
                         color: arcade.color.ORANGE,
                         count: int = 20,
                         size: int = 10):
        """Создает взрыв частиц"""
        for _ in range(count):
            particle = Particle(x, y, color, size, lifetime=random.uniform(0.5, 1.5))
            self.particles.append(particle)
            self.particle_list.append(particle)

    def create_blood(self, x: float, y: float,
                         color: Tuple[int, int, int] = (255, 0, 0),
                         count: int = 20,
                         size: int = 10):
        """Эффект крови"""
        for _ in range(count):


            particle = Particle(x, y, color, size,
                                lifetime=random.uniform(1.0, 2.5))

            self.particles.append(particle)
            self.particle_list.append(particle)




    def update(self, delta_time: float):
        """Обновляет все частицы"""
        dead_particles = []

        for particle in self.particles:
            if particle.update_particle(delta_time):
                dead_particles.append(particle)

        # Удаляем мертвые частицы
        for particle in dead_particles:
            self.particles.remove(particle)
            self.particle_list.remove(particle)

    def draw(self):
        """Рисует все частицы"""
        self.particle_list.draw()



    def clear(self):
        """Очищает все частицы"""
        self.particles.clear()
        self.particle_list.clear()

particle_manager = ParticleManager()