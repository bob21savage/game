class ItemModel:
    def __init__(self, item_name, item_effect):
        self.item_name = item_name
        self.item_effect = item_effect

items = [
    ItemModel('Small Shield', '10% HP boost'),
    ItemModel('Healing Potion', '20 HP heal'),
    ItemModel('Gold Amulet', '10 gold gain'),
    ItemModel('Strength Potion', '50 damage boost'),
]