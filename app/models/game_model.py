from .. import db
from datetime import datetime

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active_character_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_played = db.Column(db.DateTime, default=datetime.utcnow)
    game_state = db.Column(db.JSON, default=dict)  # Store current game state
    is_completed = db.Column(db.Boolean, default=False)
    
    characters = db.relationship('Character', backref='game', lazy=True)

    def update_last_played(self):
        self.last_played = datetime.utcnow()

    def save_game_state(self, state):
        self.game_state = state
        self.update_last_played()

    def __repr__(self):
        return f'<Game {self.id}>'