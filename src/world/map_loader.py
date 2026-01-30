import arcade
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any

from src.core.resource_manager import resource_manager
from src.entities import entity_manager
from src.events.event_manager import EventManager
from config import constants as C
from src.entities.chest import ChestSprite
from src.core.game_data import game_data


class MapLoader:
    """загрузчик карт Tiled."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rm = resource_manager
        self.event_manager = None

        # Загруженная карта
        self.tile_map = None
        self.scene = None

        self.layers: Dict[str, Optional[arcade.SpriteList]] = {
            'ground': None,
            'walls': None,
            'containers': None,
            'top_layer': None,
            'collisions': None

        }

        # Границы карты
        self.bounds = None
        self.current_map_name = None

        # Кэш для загруженных текстур
        self.chest_textures = {
            'closed': None,
            'open': None
        }

    def _preload_common_textures(self):
        """Предзагрузка общих текстур для оптимизации"""
        try:
            self.chest_textures['closed'] = self.rm.load_texture("containers/chest.png")
            self.chest_textures['open'] = self.rm.load_texture("containers/chest_opened.png")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить текстуры сундуков: {e}")

    def load(self, map_file: str, scale: float = C.SCALE_FACTOR) -> bool:
        """Загружает Tiled карту."""
        try:
            self.current_map_name = Path(map_file).stem

            self.event_manager = EventManager()

            # Полный путь к файлу
            project_root = Path(self.rm.get_project_root())
            map_path = project_root / "res" / map_file

            self.logger.debug(f"Загрузка карты: {map_path}")

            if not map_path.exists():
                self.logger.warning(f"Файл не найден: {map_path}")
                return False

            layer_options = {
                "ground": {"use_spatial_hash": False},
                "walls": {"use_spatial_hash": False},
                "containers": {"use_spatial_hash": False},
                "top_layer": {"use_spatial_hash": False},
                "collisions": {"use_spatial_hash": True}
            }

            self.tile_map = arcade.load_tilemap(
                str(map_path),
                scaling=scale,
                layer_options=layer_options
            )

            # Получаем границы
            self._calculate_bounds()

            # Инициализируем все слои из tile_map
            self._initialize_layers()

            # Предзагружаем текстуры
            self._preload_common_textures()

            # Загружаем события
            self._load_events(scale)

            # Создаем сцену
            self.scene = arcade.Scene.from_tilemap(self.tile_map)

            # Скрываем невидимые слои
            self._hide_invisible_layers()

            # Загружаем игровые объекты
            self.load_mob_zones()
            self.load_entities()

            self.logger.debug(f"Карта '{self.current_map_name}' загружена. "
                             f"Слоев: {len(self.layers)}, "
                             f"Размер: {self.bounds['width']}x{self.bounds['height']}")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка загрузки карты: {e}", exc_info=True)
            return False

    def _initialize_layers(self):
        """Инициализирует все слои из загруженной карты"""
        if not self.tile_map or not self.tile_map.sprite_lists:
            return

        # Очищаем слои
        for layer_name in self.layers:
            self.layers[layer_name] = None

        # Заполняем слои из tile_map
        for layer_name, sprite_list in self.tile_map.sprite_lists.items():
            # Нормализуем имя слоя
            normalized_name = layer_name.lower().replace(' ', '_')

            if normalized_name in self.layers:
                self.layers[normalized_name] = sprite_list
            else:
                # Динамически добавляем новый слой
                self.layers[normalized_name] = sprite_list
                self.logger.debug(f"Добавлен динамический слой: {layer_name}")

    def _hide_invisible_layers(self):
        """Скрывает служебные слои"""
        invisible_layers = ['collisions', 'entities', 'zones', 'events']

        for layer_name in invisible_layers:
            if self.layers.get(layer_name):
                for sprite in self.layers[layer_name]:
                    sprite.visible = False

    def _load_events(self, scale: float):
        """Загружает события из слоя events"""
        if 'events' in self.tile_map.object_lists:
            object_list = self.tile_map.object_lists['events']
            self.event_manager.load_events_from_objects(
                object_list,
                scale,
                self.current_map_name
            )

            # Создаем спрайты сундуков если есть слой containers
            if self.layers.get('containers'):
                self._create_chest_sprites_from_layer(scale)

    def _create_chest_sprites_from_layer(self, scale: float):
        """Создает спрайты сундуков из слоя containers"""
        containers_layer = self.layers['containers']
        if not containers_layer:
            return

        for tile_sprite in containers_layer:
            chest_event = self.event_manager.find_nearest_chest_event(
                tile_sprite.center_x,
                tile_sprite.center_y,
                max_distance=self.tile_map.tile_width * 2  # Уменьшен радиус
            )

            if chest_event:
                try:
                    sprite = ChestSprite(
                        texture=self.chest_textures['closed'],
                        texture_open=self.chest_textures['open'],
                        x=tile_sprite.center_x,
                        y=tile_sprite.center_y,
                        event=chest_event,
                        scale=scale
                    )

                    chest_event.set_sprite(sprite)
                    chest_event.map_name = self.current_map_name
                    self.event_manager.chest_sprites.append(sprite)

                    # Восстанавливаем состояние
                    saved_state = self.event_manager.get_event_state(chest_event.event_id)
                    if saved_state.get('is_empty', False) and sprite:
                        sprite.update_visual()

                except Exception as e:
                    self.logger.warning(f"Ошибка создания спрайта сундука: {e}")

    def _calculate_bounds(self):
        """Вычисляет границы карты в пикселях"""
        if not self.tile_map:
            self.bounds = {'left': 0, 'right': 0, 'bottom': 0, 'top': 0, 'width': 0, 'height': 0}
            return

        # В Tiled координаты уже в пикселях после загрузки через arcade
        width_px = self.tile_map.width * C.TILE_SIZE
        height_px = self.tile_map.height * C.TILE_SIZE

        self.bounds = {
            'left': 0,
            'bottom': 0,
            'right': width_px,
            'top': height_px,
            'width': width_px,
            'height': height_px,
        }

    def load_mob_zones(self) -> List[Dict]:
        """Загружает зоны для монстров (прямоугольники)"""
        zones = []

        if not self.tile_map:
            return zones

        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == "zones":
                for i, obj in enumerate(object_list):
                    zone = self._create_zone_from_object(obj, i)
                    if zone:
                        zones.append(zone)
                        game_data.add_mob_zone(zone["id"], zone)

                self.logger.debug(f"Загружено зон для карты '{self.current_map_name}': {len(zones)}")
                break

        return zones

    def _create_zone_from_object(self, obj, index: int) -> Optional[Dict]:
        """Создает зону из прямоугольного объекта Tiled"""
        try:
            points = obj.shape

            left = points[0][0]
            top = points[0][1]
            right = points[1][0]
            bottom = points[3][1]

            width = right - left
            height = bottom - top

            x = left
            y = top

            # Получаем свойства
            properties = {}
            if hasattr(obj, 'properties'):
                props = getattr(obj, 'properties', {})
                if isinstance(props, dict):
                    properties = props.copy()

            zone_id = properties.get('id', f"zone_{index}")

            zone_data = {
                "id": zone_id,
                "rect": (x, y, width, height),
                "properties": properties,
                "map_name": self.current_map_name
            }

            self.logger.debug(f"Зона: {zone_id} ({x}, {y}, {width}, {height})")
            return zone_data

        except Exception as e:
            self.logger.warning(f"Ошибка создания зоны {index}: {e}")
            return None

    def load_entities(self) -> List:
        """Загружает существ (монстры и NPC) для текущей карты"""
        mob_list = []

        if not self.tile_map:
            return mob_list

        # Загружаем существ
        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == 'entities':
                for index, obj in enumerate(object_list):
                    mob = self._create_entity_from_object(obj, index)
                    if mob:
                        mob_list.append(mob)

                self.logger.debug(f"Загружено существ для карты '{self.current_map_name}': {len(mob_list)}")
                break

        return mob_list

    def _create_entity_from_object(self, obj, index: int):
        """Создает сущность из точечного объекта Tiled"""
        try:
            # Точечные объекты в Tiled хранят координаты в shape
            if not hasattr(obj, 'shape'):
                return None

            # shape обычно это tuple (x, y) для точек
            shape = obj.shape
            if isinstance(shape, tuple) and len(shape) == 2:
                x, y = shape
            elif isinstance(shape, list) and len(shape) > 0:
                if isinstance(shape[0], (list, tuple)):
                    x, y = shape[0]
                else:
                    x, y = shape[0], shape[1]
            else:
                return None

            # Тип монстра
            mob_type = getattr(obj, 'type').lower()
            mob_name = getattr(obj, 'name').lower()

            # Свойства из Tiled
            properties = {}
            if hasattr(obj, 'properties'):
                props = getattr(obj, 'properties', {})
                if isinstance(props, dict):
                    properties = props.copy()

            monster_id = f"creature_{mob_type}_{index}_{self.current_map_name}"

            # ПРОВЕРЯЕМ: если монстр уже есть в game_data и он мертв - не создаем
            from src.core.game_data import game_data
            existing_data = game_data.get_entity_data(monster_id)
            if existing_data and not existing_data.get("is_alive", True):
                self.logger.debug(f"Монстр {monster_id} уже мертв, пропускаем создание")
                return None

            monster = entity_manager.spawn_monster(
                mob_id=monster_id,
                mob_name=mob_name,
                mob_type=mob_type,
                position=(x, y),
                properties=properties,
                map_name=self.current_map_name
            )

            if monster:
                self.logger.debug(f"Создан {mob_type} на ({x}, {y})")
                return monster

        except Exception as e:
            self.logger.warning(f"Ошибка создания сущности {index}: {e}")

        return None

    def get_layer(self, layer_name: str) -> Optional[arcade.SpriteList]:
        """Безопасно получает слой по имени"""
        return self.layers.get(layer_name.lower())

    def add_top_layer_overlay(self, sprite_list: arcade.SpriteList):
        """Добавляет динамический контент в top_layer"""
        if not self.layers.get('top_layer'):
            self.layers['top_layer'] = sprite_list
        else:
            # Добавляем к существующему
            for sprite in sprite_list:
                self.layers['top_layer'].append(sprite)

    def clear_top_layer(self):
        """Очищает top_layer (кроме оригинальных тайлов)"""
        # Сохраняем только оригинальные тайлы из tile_map
        if self.tile_map and 'top_layer' in self.tile_map.sprite_lists:
            original_sprites = self.tile_map.sprite_lists['top_layer']
            self.layers['top_layer'] = arcade.SpriteList()

            # Копируем оригинальные спрайты
            for sprite in original_sprites:
                self.layers['top_layer'].append(sprite)
        else:
            self.layers['top_layer'] = arcade.SpriteList()

    def get_collision_layer(self) -> Optional[arcade.SpriteList]:
        """Возвращает слой коллизий"""
        return self.layers.get('collisions')

    def get_bounds(self) -> Dict[str, float]:
        """Возвращает границы карты"""
        return self.bounds.copy() if self.bounds else {
            'left': 0, 'right': 0, 'bottom': 0, 'top': 0, 'width': 0, 'height': 0
        }

    def draw(self):
        """Отрисовывает карту в правильном порядке"""
        if not self.scene:
            return

        # Определяем порядок отрисовки слоев
        draw_order = [
            'ground',
            'walls',
            'decorations',
            'containers',
            'top_layer'  # Самый верхний
        ]

        # Рисуем слои по порядку
        for layer_name in draw_order:
            layer = self.layers.get(layer_name)
            if layer:
                layer.draw()

        # Рисуем события (сундуки и т.д.)
        if self.event_manager:
            self.event_manager.draw()

    def update_events(self, delta_time: float, player, game_state):
        """Обновляет события"""
        if self.event_manager:
            self.event_manager.update(delta_time)
            self.event_manager.check_collisions(player, game_state)

    def draw_events(self):
        """Отрисовывает события"""
        if self.event_manager:
            self.event_manager.draw()

    def unload(self):
        """Выгружает текущую карту и освобождает ресурсы"""
        self.logger.debug(f"Выгрузка карты: {self.current_map_name}")

        # Очищаем слои
        for layer_name, sprite_list in self.layers.items():
            if sprite_list:
                sprite_list.clear()
        self.layers.clear()

        # Очищаем сцену
        self.scene = None
        self.tile_map = None

        # Очищаем события
        if self.event_manager:
            self.event_manager.events.clear()
            self.event_manager.chest_sprites.clear()

        self.current_map_name = None
        self.bounds = None

    def get_map_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущей карте"""
        return {
            'name': self.current_map_name,
            'bounds': self.bounds.copy() if self.bounds else None,
            'layers': list(self.layers.keys()),
            'has_events': bool(self.event_manager and self.event_manager.events),
            'has_collisions': bool(self.layers.get('collisions'))
        }

    def get_entity_at_position(self, x: float, y: float, max_distance: float = 64.0):
        """Находит сущность (монстр/NPC) в указанной позиции"""
        if not self.tile_map or 'entities' not in self.tile_map.object_lists:
            return None

        for obj in self.tile_map.object_lists['entities']:
            try:
                shape = obj.shape
                if isinstance(shape, tuple) and len(shape) == 2:
                    obj_x, obj_y = shape
                elif isinstance(shape, list) and len(shape) > 0:
                    if isinstance(shape[0], (list, tuple)):
                        obj_x, obj_y = shape[0]
                    else:
                        obj_x, obj_y = shape[0], shape[1]
                else:
                    continue

                # Проверяем расстояние
                distance = ((x - obj_x) ** 2 + (y - obj_y) ** 2) ** 0.5
                if distance <= max_distance:
                    return obj
            except:
                continue

        return None