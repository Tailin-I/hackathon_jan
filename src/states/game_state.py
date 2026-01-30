import math
import time

import arcade
from arcade import SpriteList, Camera2D

from .base_state import BaseState
from ..entities import Player
from ..ui.FatigueBar import FatigueBar
from ..ui.health_bar import HealthBar
from ..ui.notification_system import notifications as ns
from ..world.map_loader import MapLoader
from config import constants as C
from src.entities.entity_manager import entity_manager


class GameplayState(BaseState):
    """
    Состояние основной игры.
    Здесь происходит вся игровая логика.
    """

    def __init__(self, gsm, asset_loader):
        super().__init__("game", gsm, asset_loader)

        self.is_paused = False
        self.entity_manager = entity_manager

        # Для FPS
        self.frame_count = 0
        self.fps = 0
        self.fps_timer = time.time()

        self.viewport_width = C.VIEWPORT_WIDTH
        self.viewport_height = C.VIEWPORT_HEIGHT
        self.input_manager = self.gsm.input_manager

        self.default_camera = Camera2D()
        self.default_camera.viewport = (
            arcade.rect.XYWH(self.gsm.window.width // 2, self.gsm.window.height // 2, self.gsm.window.width,
                             self.gsm.window.height))

        player_textures = self.asset_loader.load_player_sprites()
        self.player = Player(player_textures, self.input_manager)
        self.player_list = SpriteList()
        self.player_list.append(self.player)

        self.map_loader = MapLoader()

        self.mobs = arcade.SpriteList()

        # Устанавливаем начальные значения (будут обновлены в on_enter)
        self.map_left = 0
        self.map_bottom = 0
        self.map_right = 0
        self.map_top = 0

        self.collision_layer = None  # Будет установлен при загрузке карты
        self.camera = arcade.camera.Camera2D()
        self.ui_elements = []

        self.fatigue_bar = FatigueBar(
            self.player,
            x=C.FATIGUE_BAR_X,
            y=C.FATIGUE_BAR_Y,
            width=C.FATIGUE_BAR_WIDTH,
            height=C.FATIGUE_BAR_HEIGHT,
            font_size=C.FATIGUE_BAR_FONT_SIZE,
            icon_texture=asset_loader.load_ui_texture("fatigue")
        )
        self.gsm.ui_elements.append(self.fatigue_bar)

        self.health_bar = HealthBar(
            self.player,
            x=C.HEALTH_BAR_X,
            y=C.HEALTH_BAR_Y,
            width=C.HEALTH_BAR_WIDTH,
            height=C.HEALTH_BAR_HEIGHT
        )
        self.gsm.ui_elements.append(self.health_bar)

        self.select_pressed = False

        self.mob_under_focus = None

        # Режим прицеливания
        self.is_aiming = False
        self.aim_angle = 0  # Угол в радианах
        self.aim_rotation_speed = 6.0  # Радиан в секунду

        # Таймер перезарядки атаки
        self.attack_cooldown = 0
        self.attack_cooldown_max = 0.4  # Полсекунды между выстрелами

        # Полоска прицела
        self.aim_line_width = 4
        self.aim_line_color = arcade.color.RED

        self.projectile_list = arcade.SpriteList()



    def setup_map_limits(self, left, bottom, width, height):
        self.map_left = left
        self.map_bottom = bottom
        self.map_right = left + width
        self.map_top = bottom + height

    def teleport_to(self, x: int, y: int, map: str = None):
        """
        Телепортирует игрока в указанные координаты.
        """
        # Если нужно сменить карту
        if map:
            self._load_map(map)

        # Устанавливаем позицию игрока
        self.player.center_x = x * self.tile_size
        self.player.center_y = y * self.tile_size

        # Обновляем данные игрока
        self.game_data.set_player_position(x, y, map or self.entity_manager.current_map_name)

        self._update_cam()
        ns.notification(f"Телепорт в ({x}, {y}). карта: {map or 'текущая'}")
        return True

    def on_enter(self, **kwargs):
        self.is_paused = False

        # Очищаем снаряды
        self.projectile_list.clear()

        # Получаем позицию игрока
        pos_x, pos_y, map_name = self.game_data.get_player_position()

        # ОЧИЩАЕМ все сущности перед загрузкой новой карты
        self.entity_manager.clear_all()
        self.mobs.clear()

        # Загружаем карту
        self._load_map(map_name)

        # Ставим игрока на сохраненную позицию
        self.player.center_x = pos_x
        self.player.center_y = pos_y

        # Обновляем камеру
        self._update_cam()

        self._init_ui()
        self.sound_manager.play_music("game_music")

    def _load_map(self, map_name: str):
        """Загружает карту и обновляет все связанные данные"""
        path = f"maps/{map_name}.tmx"

        if not self.map_loader.load(path):
            # Если карта не загрузилась - загружаем дефолтную
            self.logger.error(f"Не удалось загрузить карту {map_name}, загружаем polygon")

        # Устанавливаем текущую карту
        self.entity_manager.set_current_map(map_name)

        # Обновляем слой коллизий
        self.collision_layer = self.map_loader.get_collision_layer()


        # это костыль ! для защиты
        if self.collision_layer:
            self.player.physics_engine = arcade.PhysicsEngineSimple(
                self.player,
                self.collision_layer
            )

        # Обновляем границы карты
        bounds = self.map_loader.get_bounds()
        self.setup_map_limits(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])

        # Загружаем монстров из map_loader
        self.mobs.clear()
        loaded_mobs = self.map_loader.load_entities()

        # Добавляем загруженных монстров в список
        for monster in loaded_mobs:
            if monster and monster.is_alive:
                self.mobs.append(monster)
            elif monster and not monster.is_alive:
                # Монстр мертв, пропускаем
                self.logger.debug(f"Пропускаем мертвого монстра: {monster.entity_id}")

        self.logger.info(f"Карта {map_name} загружена, монстров: {len(self.mobs)}")

    def on_exit(self):
        """Вызывается при выходе из состояния"""
        # Сбрасываем флаги
        self.is_paused = False
        self.is_initialized = False

        # Сохраняем прогресс, освобождаем ресурсы...

    def on_pause(self):
        """Вызывается при постановке игры на паузу (для overlay)"""
        self.is_paused = True

    def on_resume(self):
        """Вызывается при возобновлении игры"""
        self.is_paused = False

    def _update_cam(self):
        target_x = self.player.center_x
        target_y = self.player.center_y

        # Учитываем половину размера экрана, чтобы камера не показывала пустоту за краем
        half_screen_w = self.gsm.window.width / 2
        half_screen_h = self.gsm.window.height / 2

        # Зажимаем камеру между границами карты
        final_x = max(self.map_left + half_screen_w, min(target_x, self.map_right - half_screen_w))
        final_y = max(self.map_bottom + half_screen_h, min(target_y, self.map_top - half_screen_h))

        # ПРИМЕНЕНИЕ (Для мгновенного следования)
        self.camera.position = (final_x, final_y)

    def update(self, delta_time: float):
        """Обновление игровой логики"""
        if self.is_paused:
            return

        if C.debug_pause:
            self.player.update(delta_time, collision_layer=self.collision_layer, monster=self.mobs)
            self._update_camera()
            self._update_ui(delta_time)
            self._update_debug()
            return

        # Обновляем таймер перезарядки
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time

        # Обновляем угол прицеливания
        if self.is_aiming:
            self.aim_angle += self.aim_rotation_speed * delta_time
            # Нормализуем угол в диапазоне 0-2π
            self.aim_angle %= (2 * 3.14159)

        # Обновляем снаряды
        self.entity_manager.update_projectiles(
            delta_time,
            collision_layer=self.collision_layer,
            monsters=self.mobs
        )

        # Удаляем неактивные снаряды
        projectiles_to_remove = []
        for projectile in self.projectile_list:
            if hasattr(projectile, 'is_active') and not projectile.is_active:
                projectiles_to_remove.append(projectile)

        for projectile in projectiles_to_remove:
            # Удаляем из SpriteList
            self.projectile_list.remove(projectile)

            # Удаляем из EntityManager и GameData
            self.entity_manager.remove_projectile(projectile.entity_id)

        # Обновляем монстров
        self.mob_under_focus = None
        for mob in self.mobs:
            if mob.is_alive:
                mob.update(delta_time, self.player, self.collision_layer, self.mobs)

                if mob.is_nearby:

                    self.mob_under_focus = mob
                    if not self.is_aiming:
                        if mob.can_dialogue and mob.behavior == "passive":
                            if self.input_manager.get_action("select"):
                                self.gsm.push_overlay("dialogue", npc=mob)
                                mob.can_start_dialogue = False

                                # self.input_manager.reset_action("select")
                                break



        self.entity_manager.update_all(delta_time, self.player, self.collision_layer)

        # Обновляем игрока
        self.player.update(delta_time, collision_layer=self.collision_layer, monster=self.mobs)

        # Обновляем и проверяем события
        if hasattr(self.map_loader, 'event_manager') and self.map_loader.event_manager:
            self.map_loader.event_manager.update(delta_time)
            self.map_loader.event_manager.check_collisions(self.player, self)

        self._update_camera()

        self._update_battle_music()

        self._update_ui(delta_time)

        self._update_debug()

        # Обновляем снаряды через entity_manager
        self.entity_manager.update_projectiles(
            delta_time,
            collision_layer=self.collision_layer,
            monsters=self.mobs
        )
        self.particle_manager.update(delta_time)

        if self.player.health == 0:
            self.gsm.switch_to("death")

    def draw(self):
        """Отрисовка игры"""
        # Активируем камеру для игрового мира
        self.camera.use()

        # Рисуем карту
        self.map_loader.draw()
        
        self.projectile_list.draw()



        self.entity_manager.draw_debug()

        if self.is_aiming:
            self._draw_aiming_line()


        self.mobs.draw()
        for mob in self.mobs:
            mob.draw()


        self.player_list.draw()
        self.player.draw()
        self.particle_manager.draw()

        # Переключаемся на UI камеру (полный экран)
        self.default_camera.use()

        if C.debug_mode:
            # FPS и координаты

            text = f"x:{int(self.player.center_x // self.tile_size)} y:{int(self.player.center_y // self.tile_size)}"
            arcade.Text(text,
                        self.gsm.window.width - 3 * self.tile_size,
                        self.gsm.window.height - self.tile_size,
                        C.DEEPSEEK_COLOR, 18).draw()

            arcade.Text(f"FPS: {self.fps}",
                        self.gsm.window.width - 3 * self.tile_size,
                        self.gsm.window.height - 0.5 * self.tile_size,
                        C.DEEPSEEK_COLOR, 18).draw()

        # Рисуем UI элементы
        for ui_element in self.ui_elements:
            ui_element.draw()

        for ui_element in self.gsm.ui_elements:
            ui_element.entity = self.player

    def _draw_aiming_line(self):
        """Рисует вращающуюся полоску прицела"""
        # Рассчитываем конечную точку полоски
        end_x = self.player.center_x + math.cos(self.aim_angle) * self.player.vision_range
        end_y = self.player.center_y + math.sin(self.aim_angle) * self.player.vision_range

        # Рисуем полоску
        arcade.draw_line(
            self.player.center_x, self.player.center_y,
            end_x, end_y,
            self.aim_line_color, self.aim_line_width
        )

        # Рисуем круг радиуса видимости (опционально)
        arcade.draw_circle_outline(
            self.player.center_x, self.player.center_y,
            self.player.vision_range,
            arcade.color.RED, 1
        )

    def in_battle(self):
        for mob in self.mobs:
            if mob.behavior == "aggressive" and mob.current_state == "chase":
                return True
        return False

    def _update_battle_music(self):
        if self.in_battle() and self.sound_manager.current_music != "fighting_music":
            self.sound_manager.play_music("fighting_music")
        elif not self.in_battle() and self.sound_manager.current_music != "game_music":
            self.sound_manager.play_music("game_music")

    def _update_camera(self):
        # Учитываем половину размера экрана, чтобы камера не показывала пустоту за краем
        half_screen_w = self.gsm.window.width / 2
        half_screen_h = self.gsm.window.height / 2

        # Зажимаем камеру между границами карты
        final_x = max(self.map_left + half_screen_w, min(self.player.center_x, self.map_right - half_screen_w))
        final_y = max(self.map_bottom + half_screen_h, min(self.player.center_y, self.map_top - half_screen_h))

        self.camera.position = arcade.math.lerp_2d(self.camera.position, (final_x, final_y), 0.3)

    def _update_debug(self):
        # Счет FPS
        if C.debug_mode:
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.fps_timer >= 1.0:  # Каждую секунду
                self.fps = self.frame_count
                self.frame_count = 0
                self.fps_timer = current_time

    def _update_ui(self, delta_time):
        """Обновляение UI"""
        for ui_element in self.ui_elements:
            ui_element.update(delta_time)

    def handle_key_press(self, key: int, modifiers: int):
        if not self.input_manager:
            return

        # Включение/выключение режима прицеливания
        if self.input_manager.get_action("attack"):
            self.is_aiming = not self.is_aiming
            if not self.is_aiming:
                # При выходе из режима сбрасываем угол
                self.aim_angle = 0

        # Выстрел (только в режиме прицеливания)
        if self.is_aiming and self.input_manager.get_action("select"):
            self._fire_projectile()

        # ESC - открыть меню паузы
        if self.input_manager.get_action("escape"):
            self._open_pause_menu()

        if self.input_manager.get_action("select"):
            self.select_pressed = True

        if self.input_manager.get_action("stats"):
            self.gsm.push_overlay("stats")

        if self.input_manager.get_action("inventory"):
            self.gsm.push_overlay("inventory")

        if C.cheat_mode:
            # F2 - чит-консоль
            if self.input_manager.get_action("cheat_console"):
                self.gsm.push_overlay("cheat_console")

            if self.input_manager.get_action("ghost_mode"):
                self.fast_cheat_execute("GHOST")
            if self.input_manager.get_action("debug_mode"):
                self.fast_cheat_execute("DEBUG")
            if self.input_manager.get_action("show_area_mode"):
                self.fast_cheat_execute("AREAS")
            if self.input_manager.get_action("debug_pause"):
                self.fast_cheat_execute("STOP")

            if self.input_manager.get_action("heal"):
                if self.game_data.has_item("healing_potion"):
                    from src.entities.items.consumables import HealingPotion
                    potion = HealingPotion()
                    if potion.use(self.player):
                        self.game_data.remove_item("healing_potion", 1)
                        ns.notification("Зелье лечения использовано")
                else:
                    ns.notification("Нет зелий лечения")

    def fast_cheat_execute(self, command):
        self.gsm.window.cheat_state.execute_command(command)

    def _fire_projectile(self):
        """Создаёт и запускает снаряд"""
        # Проверяем перезарядку
        if self.attack_cooldown > 0 and not C.debug_pause:
            return

        # Проверяем усталость
        projectile_cost = self.game_data.projectile_templates["default"]["fatigue_cost"]

        if not self.game_data.can_use_fatigue(projectile_cost) and not C.debug_pause:
            from ..ui.notification_system import notifications as ns
            ns.notification("Слишком устал для атаки!")
            return

        # Создаём данные снаряда
        direction = (
            math.cos(self.aim_angle),
            math.sin(self.aim_angle)
        )


        start_x = self.player.center_x - self.player.width//2
        start_y = self.player.center_y - self.player.height//2

        projectile_data = self.game_data.create_projectile_data(
            projectile_type="default",
            position=(start_x, start_y),  # Используем смещенную позицию
            direction=direction,
            owner_id="player"
        )

        # Добавляем снаряд в GameData
        self.game_data.add_projectile(projectile_data["id"], projectile_data)

        # Загружаем текстуры для снаряда
        sprite_params = projectile_data["sprite_params"]
        textures = self.asset_loader.load_projectile_sprites(
            texture_name=sprite_params["texture_name"],
            sprite_size=sprite_params["sprite_size"],
            tile_count=sprite_params["tile_count"],
            animation_speed=sprite_params["animation_speed"]
        )

        # Создаём визуальный объект снаряда
        projectile = self.entity_manager.spawn_projectile(
            projectile_data["id"],
            texture_list=textures
        )

        if projectile:
            # Проверяем, не добавлен ли уже снаряд в SpriteList
            if projectile not in self.projectile_list:
                self.projectile_list.append(projectile)

            # self.particle_manager.create_explosion(
            #     start_x,
            #     start_y,
            #     color= arcade.color.ORANGE,
            #     size=30,
            #     count=15
            # )
            # Добавляем усталость
            self.game_data.add_fatigue(projectile_data["fatigue_cost"])

            # Устанавливаем перезарядку
            self.attack_cooldown = self.attack_cooldown_max

    def _init_ui(self):
        """Инициализирует UI элементы"""
        # Пока пусто - добавим позже
        pass

    def _open_pause_menu(self):
        """Открывает меню паузы поверх игры"""
        self.gsm.push_overlay("pause_menu", )
