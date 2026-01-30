class UIComponent:
    """Базовый класс для UI элементов без мыши"""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.enabled = True

        # Сохраняем оригинальные размеры для масштабирования
        self.original_x = x
        self.original_y = y
        self.original_width = width
        self.original_height = height

    def on_resize(self, offset_x: int, offset_y: int, width: int, height: int, scale: float):
        """Обновляет позицию и размер при изменении окна"""
        # Восстанавливаем оригинальные координаты (относительно 1280x768)
        orig_x = getattr(self, 'original_x', self.x)
        orig_y = getattr(self, 'original_y', self.y)
        orig_width = getattr(self, 'original_width', self.width)
        orig_height = getattr(self, 'original_height', self.height)

        # Пересчитываем с учетом масштаба и смещения
        self.x = offset_x + (orig_x * scale)
        self.y = offset_y + (orig_y * scale)
        self.width = orig_width * scale
        self.height = orig_height * scale

    def update(self, delta_time):
        """Обновление анимаций и логики"""
        pass

    def draw(self):
        """Отрисовка элемента"""
        pass

    def is_point_inside(self, px, py):
        """Проверяет, находится ли точка внутри элемента"""
        return (self.x - self.width / 2 <= px <= self.x + self.width / 2 and
                self.y - self.height / 2 <= py <= self.y + self.height / 2)