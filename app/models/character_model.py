from .. import db

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    char_class = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    hp = db.Column(db.Integer, nullable=False)
    max_hp = db.Column(db.Integer, nullable=False)
    strength = db.Column(db.Integer, nullable=False)
    dexterity = db.Column(db.Integer, nullable=False)
    constitution = db.Column(db.Integer, nullable=False)
    intelligence = db.Column(db.Integer, nullable=False)
    wisdom = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    inventory = db.Column(db.JSON, default=list)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    def level_up(self):
        self.level += 1
        # Increase HP based on class and constitution modifier
        con_mod = (self.constitution - 10) // 2
        if self.char_class == 'warrior':
            hp_increase = 10 + con_mod
        elif self.char_class == 'mage':
            hp_increase = 6 + con_mod
        else:  # rogue
            hp_increase = 8 + con_mod
        self.max_hp += max(1, hp_increase)  # Minimum 1 HP per level
        self.hp = self.max_hp

    def add_to_inventory(self, item):
        if self.inventory is None:
            self.inventory = []
        self.inventory.append(item)

    def remove_from_inventory(self, item):
        if self.inventory and item in self.inventory:
            self.inventory.remove(item)

    def __repr__(self):
        return f'<Character {self.name}>'
