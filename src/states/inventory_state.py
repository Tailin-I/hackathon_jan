import arcade
import time
from .base_state import BaseState
from config import constants as C
from src.entities.items.item_factory import ItemFactory
from ..ui.notification_system import notifications as ns


class InventoryState(BaseState):
    """Инвентарь игрока"""

    def __init__(self, gsm, asset_loader):
        super().__init__("inventory", gsm, asset_loader)

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.cell_color = (50, 50, 80, 200)
        self.cell_selected_color = (100, 100, 150, 200)
        self.menu_background_color = C.MENU_BACKGROUND_COLOR_TRANSLUCENT

        # Параметры сетки
        self.grid_cols = 6
        self.grid_rows = 5
        self.cell_size = 70
        self.cell_spacing = 10

        # Навигация
        self.selected_index = 0
        self.key_cooldown = 0.15
        self.last_key_time = 0

        # Кэш текстур
        self.texture_cache = {}

    def on_enter(self, **kwargs):
        """Вход в инвентарь"""
        self.selected_index = 0

    def update(self, delta_time):
        pass

    def _get_selected_item(self):
        """Получить выбранный предмет"""
        inventory = self.game_data.player_data["inventory"]
        if 0 <= self.selected_index < len(inventory):
            return inventory[self.selected_index]
        return None

    def _draw_grid(self):
        """Отрисовка сетки инвентаря с учетом экипированных предметов."""
        inventory = self.game_data.player_data["inventory"]

        # Позиции для отрисовки
        start_x = self.gsm.window.width * 0.80 - self.window_width / 2 + self.cell_spacing
        start_y = self.gsm.window.height * 0.61+ self.window_height / 2 - self.cell_spacing - self.cell_size * 1.5

        # Рисуем все ячейки
        for i in range(self.grid_rows * self.grid_cols):
            row = i // self.grid_cols
            col = i % self.grid_cols

            x = start_x + col * (self.cell_size + self.cell_spacing) + self.cell_size / 2
            y = start_y - row * (self.cell_size + self.cell_spacing) - self.cell_size / 2

            # Цвет ячейки
            is_selected = (i == self.selected_index)
            has_item = (i < len(inventory))

            # Проверяем, экипирован ли предмет
            is_equipped = False
            if has_item:
                item = inventory[i]
                is_equipped = self.game_data.is_item_equipped(item["id"])

            if is_selected and has_item:
                color = self.cell_selected_color
            elif has_item:
                if is_equipped:
                    color = (70, 100, 70, 200)  # Зеленоватый для экипированных
                else:
                    color = self.cell_color
            else:
                color = (30, 30, 50, 100)  # Пустая ячейка

            # Рисуем ячейку
            arcade.draw_rect_filled(arcade.rect.XYWH(x, y, self.cell_size, self.cell_size), color)
            arcade.draw_rect_outline(arcade.rect.XYWH(x, y, self.cell_size, self.cell_size),
                                     self.main_color, 1)

            # Рисуем предмет, если он есть
            if has_item:
                item = inventory[i]
                texture = self._get_item_texture(item["id"])
                if texture:
                    # Немного затемняем экипированные предметы
                    alpha = 180 if is_equipped else 255
                    arcade.draw_texture_rect(texture,
                                             arcade.rect.XYWH(x, y, self.cell_size - 10, self.cell_size - 10),
                                             alpha=alpha)

                # Количество
                if item["count"] > 1:
                    arcade.Text(str(item["count"]), x + self.cell_size / 2 - 5, y - self.cell_size / 2 + 10,
                                arcade.color.WHITE, 14, anchor_x="right").draw()



    def _draw_item_info(self):
        """Отрисовка информации о предмете с учетом экипировки."""
        item = self._get_selected_item()
        if not item:
            return

        # Позиция для отображения
        info_y = self.gsm.window.height * 0.15
        center_x = self.gsm.window.width * 0.80

        # Фон
        arcade.draw_rect_filled(arcade.rect.XYWH(center_x, info_y,
                                                 self.window_width+20, self.cell_size*2), (40, 40, 60, 200))

        # Название
        arcade.Text(item["name"], center_x, self.gsm.window.height * 0.2 ,
                    self.main_color, 18, anchor_x="center", anchor_y="center").draw()

        # Статус экипировки
        is_equipped = self.game_data.is_item_equipped(item["id"])
        if is_equipped:
            slot = self.game_data.get_item_equipment_slot(item["id"])
            arcade.Text(f"Экипирован ({slot})", center_x, info_y - 5,
                        arcade.color.GREEN, 14, anchor_x="center", anchor_y="center").draw()

        # Описание
        item_obj = ItemFactory.create(item["id"], 1)
        description = getattr(item_obj, 'description', "Нет описания")

        # Показываем бонусы
        bonus_text = ""
        if hasattr(item_obj, 'additional_health') and item_obj.additional_health > 0:
            bonus_text += f"+{item_obj.additional_health} здоровья "
        if hasattr(item_obj, 'additional_strength') and item_obj.additional_strength > 0:
            bonus_text += f"+{item_obj.additional_strength} силы "
        if hasattr(item_obj, 'additional_speed') and item_obj.additional_speed > 0:
            bonus_text += f"+{item_obj.additional_speed} скорости "
        if hasattr(item_obj, 'additional_range') and item_obj.additional_range > 0:
            bonus_text += f"+{item_obj.additional_range} радиуса "

        if bonus_text:
            arcade.Text(bonus_text.strip(), center_x, self.gsm.window.height * 0.12,
                        arcade.color.LIGHT_GREEN, 12, anchor_x="center", anchor_y="center").draw()

        arcade.Text(description, center_x, self.gsm.window.height * 0.17,
                        self.text_color, 12, anchor_x="center", anchor_y="center").draw()

    @property
    def window_width(self):
        """Ширина окна"""
        return self.grid_cols * (self.cell_size + self.cell_spacing) + self.cell_spacing * 2

    @property
    def window_height(self):
        """Высота окна"""
        return self.grid_rows * (self.cell_size + self.cell_spacing) + self.cell_size * 1.5

    def draw(self):
        """Основная отрисовка"""
        C.draw_dark_background()

        # Центр окна
        center_x = self.gsm.window.width * 0.8
        center_y = self.gsm.window.height * 0.6

        # Фон окна
        arcade.draw_rect_filled(arcade.rect.XYWH(center_x, center_y,
                                                 self.window_width, self.window_height), self.menu_background_color)
        arcade.draw_rect_outline(arcade.rect.XYWH(center_x, center_y,
                                                  self.window_width, self.window_height), self.main_color, 3)

        # Заголовок
        arcade.Text("ИНВЕНТАРЬ", center_x, center_y + self.window_height * 0.55,
                    self.main_color, 24, anchor_x="center", align="center").draw()

        # Сетка и информация
        self._draw_grid()
        self._draw_item_info()
        self._draw_equipment_slots()



    def _draw_equipment_slots(self):
        """Отрисовывает слоты экипировки."""
        center_x = self.gsm.window.width * 0.80
        center_y = self.gsm.window.height *0.6 + self.window_height * 0.4

        # Получаем экипированные предметы
        equipment = self.game_data.player_data["equipment"]

        slots = [
            ("accessory_1", "Слот 1", center_x - 100, center_y),
            ("accessory_2", "Слот 2", center_x, center_y),
            ("accessory_3", "Слот 3", center_x + 100, center_y)
        ]

        for slot_id, slot_name, x, y in slots:
            # Рамка слота
            slot_color = (50, 50, 80, 200) if equipment[slot_id] else (30, 30, 50, 100)
            arcade.draw_rect_filled(arcade.rect.XYWH(x, y, 70, 70), slot_color)
            arcade.draw_rect_outline(arcade.rect.XYWH(x, y, 70, 70),
                                     self.main_color, 2)

            # Предмет в слоте (если есть)
            item_id = equipment.get(slot_id)
            if item_id:
                texture = self._get_item_texture(item_id)
                if texture:
                    arcade.draw_texture_rect(texture,
                                             arcade.rect.XYWH(x, y, 60, 60))
    def handle_key_press(self, key, modifiers):
        """Управление инвентарем"""
        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        # Закрытие
        if (self.gsm.input_manager.get_action("inventory") or
                self.gsm.input_manager.get_action("escape")):
            self.gsm.pop_overlay()
            self.last_key_time = current_time
            return

        inventory = self.game_data.player_data["inventory"]
        if not inventory:
            return  # Пустой инвентарь

        # Использование предмета
        if self.gsm.input_manager.get_action("select"):
            self._use_item()
            self._equip_selected_item()
            self.last_key_time = current_time
            return


        # Навигация
        total_items = len(inventory)

        if self.gsm.input_manager.get_action("up"):
            new_index = self.selected_index - self.grid_cols
            if new_index >= 0:
                self.selected_index = new_index

        elif self.gsm.input_manager.get_action("down"):
            new_index = self.selected_index + self.grid_cols
            if new_index < total_items:
                self.selected_index = new_index

        elif self.gsm.input_manager.get_action("left"):
            if self.selected_index > 0:
                self.selected_index -= 1

        elif self.gsm.input_manager.get_action("right"):
            if self.selected_index < total_items - 1:
                self.selected_index += 1

        # Корректируем, если вышли за границы
        if self.selected_index >= total_items:
            self.selected_index = max(0, total_items - 1)

        self.last_key_time = current_time

    def _use_item(self):
        """Использовать выбранный предмет"""
        item = self._get_selected_item()
        if not item:
            ns.notification("Нет предмета для использования")
            return

        # Создаем объект предмета через фабрику
        try:
            item_obj = ItemFactory.create(item["id"], item["count"])

            # Пробуем использовать
            if item_obj.use(self.gsm.current_state.player):
                # Успешное использование - удаляем из инвентаря
                self.game_data.remove_item(item["id"], 1)
                ns.notification(f"Использовано: {item['name']}")

        except Exception as e:
            ns.notification(f"Ошибка: {str(e)[:30]}...")

    def _get_item_texture(self, item_id):
        """Получить текстуру предмета"""
        if item_id in self.texture_cache:
            return self.texture_cache[item_id]

        try:
            item = ItemFactory.create(item_id, 1)
            self.texture_cache[item_id] = item.texture
            return item.texture
        except:
            return None

    def _equip_selected_item(self):
        """Экипирует или снимает выбранный предмет."""
        item = self._get_selected_item()
        if not item:
            ns.notification("Нет предмета для экипировки")
            return

        from src.entities.items.item_factory import ItemFactory
        item_obj = ItemFactory.create(item["id"], 1)

        if not hasattr(item_obj, 'is_equippable') or not item_obj.is_equippable:
            ns.notification("Этот предмет нельзя экипировать")
            return

        # Если предмет уже экипирован - снимаем его
        if self.game_data.is_item_equipped(item["id"]):
            slot = self.game_data.get_item_equipment_slot(item["id"])
            if self.game_data.unequip_item(slot):
                ns.notification(f"Снят: {item['name']}")
        else:
            # Экипируем предмет
            if self.game_data.equip_item(item["id"]):
                ns.notification(f"Экипирован: {item['name']}")
            else:
                ns.notification("Не удалось экипировать предмет")

    def _unequip_item_from_slot(self, slot: str):
        """Снимает предмет из указанного слота."""
        if self.game_data.unequip_item(slot):
            ns.notification("Предмет снят")