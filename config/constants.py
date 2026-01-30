import arcade

# РАЗМЕР ТАЙЛОВ
ORIGINAL_TILE_SIZE = 16  # Оригинальный размер тайлов
TILE_SIZE = 64  # Желаемый размер тайлов
SCALE_FACTOR = TILE_SIZE / ORIGINAL_TILE_SIZE

# UI
# полоска здоровья
HEALTH_BAR_X = 150
HEALTH_BAR_Y = 50
HEALTH_BAR_WIDTH = 200
HEALTH_BAR_HEIGHT = 20

health_color = arcade.color.RED

# полоска усталости
FATIGUE_BAR_X = 150
FATIGUE_BAR_Y = 80
FATIGUE_BAR_WIDTH = 200
FATIGUE_BAR_HEIGHT = 16
FATIGUE_BAR_FONT_SIZE = 9



# ПАРАМЕТРЫ ОКНА
SCREEN_WIDTH = 21.5 * TILE_SIZE
SCREEN_HEIGHT = 12* TILE_SIZE

VIEWPORT_WIDTH = SCREEN_WIDTH  # Фиксированная ширина обзора
VIEWPORT_HEIGHT = SCREEN_HEIGHT  # Фиксированная высота обзора

SCREEN_TITLE = "IT-Кубия"

# ЦВЕТА
TEXT_COLOR = arcade.color.LIGHT_GRAY
MENU_BACKGROUND_COLOR = (15,21,65)# Тёмно-синий
MENU_BACKGROUND_COLOR_TRANSLUCENT = (15,21,65, 70)# Тёмно-синий
UI_MAIN_COLOR = arcade.color.ANDROID_GREEN
UI_TITLE_COLOR = arcade.color.CYAN
UI_SUBTITLE_COLOR = arcade.color.LIGHT_BLUE
FOGGING_COLOR = (0, 0, 0, 200)  # Полупрозрачный чёрный

DEEPSEEK_COLOR = (76, 106, 253)
DEEPSEEK_COLOR_TRANSLUCENT = (76, 106, 253, 70)

# читы
cheat_mode = True
debug_mode = False
show_area_mode = False
debug_pause = False

ghost_mode = False
base_color = (255, 255, 255, 255)  # Белый, непрозрачный
ghost_color = (100, 100, 255, 128)  # Синий, полупрозрачный

damaged_color = (200, 10, 10, 255)

def draw_dark_background():
    """Полупрозрачный тёмный фон"""
    arcade.draw_rect_filled(
        arcade.rect.LRBT(
            0,SCREEN_WIDTH,
            0,
            SCREEN_HEIGHT),
        FOGGING_COLOR
    )