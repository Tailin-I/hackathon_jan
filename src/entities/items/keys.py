from .base_item import Item


class Key(Item):
    """Ключ для открытия дверей/сундуков"""

    def __init__(self, key_id: str = "basic_key", name: str = "Старый ключ", texture=None):
        super().__init__(
            item_id=f"key_{key_id}",
            name=name,
            texture=texture
        )
        self.is_stackable = False
        self.is_key_item = True
        self.key_id = key_id  # Какой замок открывает
        self.description = f"Ключ для замка '{key_id}'"

    def use(self, user) -> bool:
        # Ключи не расходуются при использовании
        return False