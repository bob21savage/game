from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    characters = db.relationship('Character', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Character(UserMixin, db.Model):
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
    gold = db.Column(db.Integer, default=0)
    inventory = db.Column(db.JSON, default=list)
    equipment = db.Column(db.JSON, default=dict)
    abilities = db.Column(db.JSON, default=list)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100), default=None)
    item_effect = db.Column(db.String(100), default=None)
    in_inventory = db.Column(db.Boolean, default=False)
    in_use = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Character {self.name}>'