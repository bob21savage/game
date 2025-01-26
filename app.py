import random
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = '666'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnd_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    characters = db.relationship('Character', backref='user', lazy=True)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    char_class = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Integer, default=1)
    hp = db.Column(db.Integer, default=70)
    max_hp = db.Column(db.Integer, default=70)
    strength = db.Column(db.Integer, default=10)
    dexterity = db.Column(db.Integer, default=10)
    constitution = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    wisdom = db.Column(db.Integer, default=10)
    charisma = db.Column(db.Integer, default=10)
    gold = db.Column(db.Integer, default=0)
    experience = db.Column(db.Integer, default=0)
    inventory = db.Column(db.String(500), default='[]')
    equipment = db.Column(db.String(500), default='{"weapon": "Fists", "armor": "Clothes"}')
    abilities = db.Column(db.String(500), default='[]')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    version = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<Character {self.name}>'

# Class definitions with starting stats and abilities
CLASS_STATS = {
    'warrior': {
        'hp': 80,
        'strength': 14,
        'dexterity': 12,
        'constitution': 14,
        'intelligence': 8,
        'wisdom': 10,
        'charisma': 10,
        'equipment': {
            'weapon': 'Longsword',
            'armor': 'Chain Mail'
        },
        'abilities': ['Cleave', 'Second Wind']
    },
    'mage': {
        'hp': 60,
        'strength': 8,
        'dexterity': 10,
        'constitution': 10,
        'intelligence': 16,
        'wisdom': 14,
        'charisma': 12,
        'equipment': {
            'weapon': 'Staff',
            'armor': 'Robes'
        },
        'abilities': ['Fireball', 'Divine Shield']
    },
    'rogue': {
        'hp': 70,
        'strength': 10,
        'dexterity': 16,
        'constitution': 12,
        'intelligence': 12,
        'wisdom': 10,
        'charisma': 14,
        'equipment': {
            'weapon': 'Dagger',
            'armor': 'Leather Armor'
        },
        'abilities': ['Backstab', 'Evasion']
    }
}

class PlayForm(FlaskForm):
    choice = RadioField('Make your choice', 
                        choices=[
                            (1, 'Explore the forest'), 
                            (2, 'Enter the dungeon'), 
                            (3, 'Visit the town')
                        ], 
                        coerce=int,
                        validators=[DataRequired()])
    submit = SubmitField('Adventure!')

class CharacterForm(FlaskForm):
    name = StringField('Character Name', validators=[DataRequired(), Length(min=2, max=80)])
    char_class = RadioField('Character Class', 
                           choices=[('warrior', 'Warrior'), 
                                  ('mage', 'Mage'), 
                                  ('rogue', 'Rogue')],
                           validators=[DataRequired()])
    submit = SubmitField('Create Character')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SelectCharacterForm(FlaskForm):
    submit = SubmitField('Select Character')

class GameForm(FlaskForm):
    action = SelectField('Choose your action', 
                      choices=[
                          ('explore', 'Explore the area'),
                          ('fight', 'Look for enemies'),
                          ('rest', 'Rest and heal'),
                          ('inventory', 'Check inventory')
                      ],
                      validators=[DataRequired()])
    submit = SubmitField('Take Action')

class CombatForm(FlaskForm):
    action = SelectField('Choose your action', validators=[DataRequired()])
    target = SelectField('Choose your target', validators=[DataRequired()])
    submit = SubmitField('Execute Action')

ABILITIES = {
    'Cleave': {
        'damage': 12,
        'description': 'A powerful swing that hits all enemies',
        'type': 'attack_all'
    },
    'Second Wind': {
        'heal': 20,
        'description': 'Recover some health',
        'type': 'heal'
    },
    'Fireball': {
        'damage': 15,
        'description': 'Launch a powerful fireball at all enemies',
        'type': 'attack_all'
    },
    'Magic Shield': {
        'shield': 15,
        'description': 'Create a magical shield to absorb damage',
        'type': 'shield'
    },
    'Divine Shield': {
        'shield': 20,
        'description': 'Create a divine shield to absorb damage',
        'type': 'shield'
    },
    'Backstab': {
        'damage': 20,
        'description': 'A precise strike that deals heavy damage to one enemy',
        'type': 'attack_single'
    },
    'Evasion': {
        'dodge': 0.5,
        'description': 'Increase dodge chance for one turn',
        'type': 'buff'
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        
        if user and password == user.password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('character_select'))
            
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if User.query.filter_by(username=username).first():
            return "Username already exists"
            
        user = User(username=username, password=password)  # In production, hash the password
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register.html', form=form)

@app.route('/character/create', methods=['GET', 'POST'])
@login_required
def create_character():
    form = CharacterForm()
    if form.validate_on_submit():
        char_class = form.char_class.data
        stats = CLASS_STATS[char_class]
        
        character = Character(
            name=form.name.data,
            char_class=char_class,
            user_id=current_user.id,
            hp=stats['hp'],
            max_hp=stats['hp'],
            strength=stats['strength'],
            dexterity=stats['dexterity'],
            constitution=stats['constitution'],
            intelligence=stats['intelligence'],
            wisdom=stats['wisdom'],
            charisma=stats['charisma'],
            equipment=json.dumps(stats['equipment']),
            abilities=json.dumps(stats['abilities'])
        )
        
        db.session.add(character)
        db.session.commit()
        
        return redirect(url_for('character_select'))
        
    return render_template('create_character.html', form=form)

@app.route('/character/select')
@login_required
def character_select():
    characters = Character.query.filter_by(user_id=current_user.id).all()
    forms = {char.id: SelectCharacterForm() for char in characters}
    return render_template('character_select.html', characters=characters, forms=forms)

@app.route('/character/select/choose', methods=['POST'])
@login_required
def select_character():
    form = SelectCharacterForm()
    if form.validate_on_submit():
        character_id = request.args.get('character_id')
        character = Character.query.get_or_404(character_id)
        
        if character.user_id != current_user.id:
            return "Unauthorized", 403
            
        session['current_character_id'] = character_id
        return redirect(url_for('game', character_id=character_id))
    return redirect(url_for('character_select'))

@app.route('/game/<int:character_id>', methods=['GET', 'POST'])
@login_required
def game(character_id):
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        return "Unauthorized", 403

    form = GameForm()
    
    if form.validate_on_submit():
        action = form.action.data
        if action == 'explore':
            # Random exploration outcomes with varied events
            outcomes = [
                {
                    'text': "You find a hidden treasure chest! Inside you find some gold and a healing potion.",
                    'effect': {'gold': 50, 'hp': 5, 'item': 'Healing Potion'},
                    'rarity': 'rare'
                },
                {
                    'text': "You discover an ancient shrine. Praying here restores your health and grants a blessing.",
                    'effect': {'hp': 15, 'ability': 'Divine Shield'},
                    'rarity': 'rare'
                },
                {
                    'text': "You stumble upon a merchant's abandoned cart. You find some useful items.",
                    'effect': {'gold': 30, 'item': 'Magic Scroll'},
                    'rarity': 'uncommon'
                },
                {
                    'text': "You find a peaceful grove and take a short rest.",
                    'effect': {'hp': 10},
                    'rarity': 'common'
                },
                {
                    'text': "You discover a trap the hard way! You take some damage.",
                    'effect': {'hp': -8},
                    'rarity': 'common'
                },
                {
                    'text': "You find an ancient training dummy and practice your combat skills.",
                    'effect': {'strength': 1},
                    'rarity': 'uncommon'
                },
                {
                    'text': "You discover a mystical fountain. Drinking from it enhances your abilities.",
                    'effect': {'max_hp': 5, 'hp': 5},
                    'rarity': 'rare'
                },
                {
                    'text': "You find a merchant willing to trade.",
                    'effect': {'shop': True},
                    'rarity': 'uncommon'
                }
            ]
            
            # Weight outcomes by rarity
            weights = {'common': 0.5, 'uncommon': 0.3, 'rare': 0.2}
            weighted_outcomes = []
            for outcome in outcomes:
                weighted_outcomes.extend([outcome] * int(weights[outcome['rarity']] * 10))
            
            outcome = random.choice(weighted_outcomes)
            message = outcome['text']
            effect = outcome['effect']
            
            # Apply effects
            if 'hp' in effect:
                old_hp = character.hp
                character.hp = min(max(character.hp + effect['hp'], 0), character.max_hp)
                message += f" HP: {old_hp} → {character.hp}"
            
            if 'max_hp' in effect:
                old_max_hp = character.max_hp
                character.max_hp += effect['max_hp']
                message += f" Max HP: {old_max_hp} → {character.max_hp}"
            
            if 'strength' in effect:
                old_str = character.strength
                character.strength += effect['strength']
                message += f" Strength: {old_str} → {character.strength}"
            
            if 'gold' in effect:
                character.gold = character.gold + effect['gold']
                message += f" Gold: +{effect['gold']}"
            
            if 'item' in effect:
                inventory = json.loads(character.inventory)
                inventory.append(effect['item'])
                character.inventory = json.dumps(inventory)
                message += f" Item gained: {effect['item']}"
            
            if 'ability' in effect:
                abilities = json.loads(character.abilities)
                if effect['ability'] not in abilities:
                    abilities.append(effect['ability'])
                    character.abilities = json.dumps(abilities)
                    message += f" New ability learned: {effect['ability']}"
            
            if 'shop' in effect:
                # Implement shop logic here
                shop_items = [
                    {'name': 'Health Potion', 'cost': 50},
                    {'name': 'Better Weapon', 'cost': 100},
                    {'name': 'Better Armor', 'cost': 100}
                ]
                message += "\nAvailable items:\n" + "\n".join([f"{item['name']}: {item['cost']} gold" for item in shop_items])
            
            db.session.commit()
            return render_template('game.html', character=character, form=form, message=message)
            
        elif action == 'fight':
            # Handle combat
            return redirect(url_for('combat', character_id=character_id))
            
        elif action == 'rest':
            # Increased rest healing
            old_hp = character.hp
            character.hp = min(character.hp + 15, character.max_hp)  # Increased from 5 to 15
            db.session.commit()
            message = f"You rest and recover some HP. HP: {old_hp} → {character.hp}"
            return render_template('game.html', character=character, form=form, message=message)
            
        elif action == 'inventory':
            # Handle inventory
            inventory = json.loads(character.inventory)
            if inventory:
                # Format inventory items in pairs (for items with quantities)
                formatted_items = []
                i = 0
                while i < len(inventory):
                    if i + 1 < len(inventory) and inventory[i] == 'Gold':
                        formatted_items.append(f"{inventory[i]}: {inventory[i+1]}")
                        i += 2
                    else:
                        formatted_items.append(inventory[i])
                        i += 1
                message = "Your inventory: " + ", ".join(formatted_items)
            else:
                message = "Your inventory is empty"
            return render_template('game.html', character=character, form=form, message=message)
    
    return render_template('game.html', character=character, form=form)

@app.route('/combat/<int:character_id>', methods=['GET', 'POST'])
@login_required
def combat(character_id):
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        return "Unauthorized", 403

    form = CombatForm()
    
    # Get character's abilities
    abilities = json.loads(character.abilities)
    ability_choices = [('attack', 'Basic Attack')] + [(ability, ability) for ability in abilities]
    form.action.choices = ability_choices
    
    # Base monster stats
    base_monsters = {
        'Goblin': {'hp': 8, 'damage': '1d6', 'xp': 15},
        'Skeleton': {'hp': 10, 'damage': '1d6', 'xp': 25},
        'Orc': {'hp': 12, 'damage': '1d8', 'xp': 35}
    }
    
    # Initialize or get current wave
    if 'wave' not in session:
        session['wave'] = 1
        session['shield'] = 0  # For Magic Shield ability
        session['dodge'] = 0   # For Evasion ability
    
    # Get or create session monsters with wave-based scaling
    if 'monsters' not in session:
        wave = session['wave']
        available_monsters = list(base_monsters.keys())
        session['monsters'] = []
        for _ in range(4):
            monster_name = random.choice(available_monsters)
            base_monster = base_monsters[monster_name].copy()
            scaled_hp = int(base_monster['hp'] * (1 + (wave - 1) * 0.5))
            scaled_xp = int(base_monster['xp'] * (1 + (wave - 1) * 0.3))
            session['monsters'].append({
                'name': monster_name,
                'hp': scaled_hp,
                'max_hp': scaled_hp,
                'damage': base_monster['damage'],
                'xp': scaled_xp
            })
    
    current_monsters = session['monsters']
    living_monsters = [m for m in current_monsters if m['hp'] > 0]
    
    # Check if all monsters are defeated before processing form
    if not living_monsters:
        # All monsters defeated - start new wave
        session.pop('monsters', None)
        session['wave'] = session.get('wave', 1) + 1
        session['shield'] = 0
        session['dodge'] = 0
        
        # Level up and increase stats
        old_level = character.level
        old_hp = character.max_hp
        old_str = character.strength
        
        character.level += 1
        character.max_hp = int(70 * (1 + (character.level - 1) * 0.2))
        character.hp = character.max_hp
        character.strength += 2
        
        db.session.commit()
        
        level_up_message = f"""Wave {session['wave'] - 1} completed! Level Up!
        Level: {old_level} → {character.level}
        Max HP: {old_hp} → {character.max_hp}
        Strength: {old_str} → {character.strength}
        You've been healed and enemies grow stronger!"""
        
        return render_template('combat.html', 
                            character=character,
                            monsters=[],  # Clear monsters for display
                            wave=session['wave'] - 1,
                            message=level_up_message,
                            combat_over=True,
                            form=form)
    
    # Update target choices based on living monsters
    form.target.choices = [(str(i), f"{m['name']} (HP: {m['hp']}/{m['max_hp']})") 
                          for i, m in enumerate(current_monsters) if m['hp'] > 0]
    
    if form.validate_on_submit():
        action = form.action.data
        message_parts = []
        
        # Handle abilities
        if action == 'attack':
            # Basic attack
            target_idx = int(form.target.data)
            base_damage = random.randint(1, 8)
            strength_bonus = max(0, (character.strength - 10) // 2)
            damage_dealt = base_damage + strength_bonus
            current_monsters[target_idx]['hp'] -= damage_dealt
            message_parts.append(f"You hit {current_monsters[target_idx]['name']} for {damage_dealt} damage!")
        else:
            ability = ABILITIES[action]
            if ability['type'] == 'attack_all':
                # AoE attack
                for monster in current_monsters:
                    if monster['hp'] > 0:
                        monster['hp'] -= ability['damage']
                message_parts.append(f"You use {action} and deal {ability['damage']} damage to all enemies!")
            elif ability['type'] == 'attack_single':
                # Single target attack
                target_idx = int(form.target.data)
                current_monsters[target_idx]['hp'] -= ability['damage']
                message_parts.append(f"You use {action} and deal {ability['damage']} damage to {current_monsters[target_idx]['name']}!")
            elif ability['type'] == 'heal':
                # Healing ability
                old_hp = character.hp
                character.hp = min(character.hp + ability['heal'], character.max_hp)
                message_parts.append(f"You use {action} and heal for {character.hp - old_hp} HP!")
            elif ability['type'] == 'shield':
                # Shield ability
                session['shield'] = ability['shield']
                message_parts.append(f"You use {action} and gain {ability['shield']} shield!")
            elif ability['type'] == 'buff':
                # Buff ability (like Evasion)
                session['dodge'] = ability['dodge']
                message_parts.append(f"You use {action} and gain increased dodge chance!")
        
        # Monster attacks
        total_damage_taken = 0
        for monster in living_monsters:
            if monster['hp'] > 0:  # Only living monsters attack
                # Check for dodge
                if session.get('dodge', 0) > 0 and random.random() < session['dodge']:
                    message_parts.append(f"You dodged {monster['name']}'s attack!")
                    continue
                
                damage_dice = monster['damage'].split('d')
                damage_taken = sum(random.randint(1, int(damage_dice[1])) 
                                 for _ in range(int(damage_dice[0])))
                
                # Apply shield if available
                if session.get('shield', 0) > 0:
                    absorbed = min(session['shield'], damage_taken)
                    session['shield'] -= absorbed
                    damage_taken -= absorbed
                    message_parts.append(f"Shield absorbed {absorbed} damage!")
                
                total_damage_taken += damage_taken
                message_parts.append(f"{monster['name']} hits for {damage_taken}")
        
        character.hp -= total_damage_taken
        
        # Reset temporary buffs
        session['shield'] = 0
        session['dodge'] = 0
        
        # Update session
        session['monsters'] = current_monsters
        
        if character.hp <= 0:
            character.hp = character.max_hp
            session.pop('monsters', None)
            session['wave'] = 1
            db.session.commit()
            return render_template('combat.html', 
                                character=character,
                                monsters=current_monsters,
                                wave=session['wave'],
                                message="You were defeated! But the gods have revived you. Starting from wave 1.",
                                combat_over=True,
                                form=form)
        
        # Create status message
        living_monster_count = sum(1 for m in current_monsters if m['hp'] > 0)
        status = f"Wave {session['wave']}\n" + "\n".join(message_parts) + f"\nRemaining enemies: {living_monster_count}"
        
        db.session.commit()
        return render_template('combat.html', 
                            character=character,
                            monsters=current_monsters,
                            wave=session['wave'],
                            message=status,
                            combat_over=False,
                            form=form)
    
    # GET request - initial combat screen
    return render_template('combat.html', 
                         character=character,
                         monsters=session.get('monsters', []),
                         wave=session.get('wave', 1),
                         message=f"Wave {session.get('wave', 1)} begins!",
                         combat_over=False,
                         form=form)

@app.route('/game_over', methods=['GET'])
def game_over():
    new_health = session.get('new_health', '')
    new_gold = session.get('new_gold', '')
    outcome_text = session.get('outcome_text', '')
    return render_template('game_over.html', new_health=new_health, new_gold=new_gold, outcome_text=outcome_text)

@app.route('/play', methods=['GET', 'POST'])
def play():
    form = PlayForm()
    if form.validate_on_submit():
        session['choice'] = form.choice.data
        return redirect(url_for('gameplay'))
    return render_template('play.html', form=form)

@app.route('/gameplay', methods=['GET'])
def gameplay():
    if 'choice' not in session:
        return redirect(url_for('play'))

    choice = session['choice']
    outcomes = {
        1: [
            {'outcome_text': "You find a hidden treasure chest!", 'new_health': 100, 'new_gold': 500},
            {'outcome_text': "You trip and fall, hurting yourself.", 'new_health': 50, 'new_gold': 200},
            {'outcome_text': "You see a group of goblins approaching.", 'new_health': 0, 'new_gold': -100},
            {'outcome_text': "You discover a secret door.", 'new_health': 75, 'new_gold': 300},
            {'outcome_text': "You get lost in the forest.", 'new_health': 25, 'new_gold': 100},
        ],
        2: [
            {'outcome_text': "You defeat the dragon and get its treasure!", 'new_health': 150, 'new_gold': 1000},
            {'outcome_text': "You get hit by a dragon fireball!", 'new_health': 0, 'new_gold': -500},
            {'outcome_text': "You find a dragon egg!", 'new_health': 100, 'new_gold': 300},
            {'outcome_text': "You get caught by a dragon and are taken to its lair.", 'new_health': 50, 'new_gold': -200},
            {'outcome_text': "You see a dragon flying overhead.", 'new_health': 75, 'new_gold': 200},
        ],
        3: [
            {'outcome_text': "You find a potion of healing!", 'new_health': 150, 'new_gold': 200},
            {'outcome_text': "You drink a potion that makes you sleepy.", 'new_health': 100, 'new_gold': 100},
            {'outcome_text': "You see a group of skeletons approaching.", 'new_health': 0, 'new_gold': -200},
            {'outcome_text': "You discover a hidden cave.", 'new_health': 125, 'new_gold': 400},
            {'outcome_text': "You get hurt by a rockslide.", 'new_health': 0, 'new_gold': -100},
        ],
        4: [
            {'outcome_text': "You defeat the giant spider and get its silk!", 'new_health': 175, 'new_gold': 500},
            {'outcome_text': "You get caught by a giant spider.", 'new_health': 0, 'new_gold': -300},
            {'outcome_text': "You see a group of orcs approaching.", 'new_health': 50, 'new_gold': -200},
            {'outcome_text': "You discover a secret passage.", 'new_health': 125, 'new_gold': 200},
            {'outcome_text': "You get hurt by a giant spider bite.", 'new_health': 0, 'new_gold': -100},
        ],
        5: [
            {'outcome_text': "You defeat the undead necromancer and get his spellbook!", 'new_health': 200, 'new_gold': 1000},
            {'outcome_text': "You get hit by a necromancer's spell.", 'new_health': 0, 'new_gold': -500},
            {'outcome_text': "You see a group of ghouls approaching.", 'new_health': 75, 'new_gold': -200},
            {'outcome_text': "You discover a hidden graveyard.", 'new_health': 125, 'new_gold': 300},
            {'outcome_text': "You get hurt by a necromancer's minions.", 'new_health': 0, 'new_gold': -100},
        ],
        6: [
            {'outcome_text': "You defeat the evil wizard and get his magic staff!", 'new_health': 225, 'new_gold': 1500},
            {'outcome_text': "You get hit by a wizard's spell.", 'new_health': 0, 'new_gold': -800},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 100, 'new_gold': -400},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 150, 'new_gold': 600},
            {'outcome_text': "You get hurt by a wizard's minions.", 'new_health': 0, 'new_gold': -200},
        ],
        7: [
            {'outcome_text': "You defeat the giant bear and get its fur!", 'new_health': 250, 'new_gold': 1200},
            {'outcome_text': "You get caught by a giant bear.", 'new_health': 0, 'new_gold': -600},
            {'outcome_text': "You see a group of elves approaching.", 'new_health': 125, 'new_gold': -300},
            {'outcome_text': "You discover a hidden forest glade.", 'new_health': 175, 'new_gold': 500},
            {'outcome_text': "You get hurt by a giant bear swipe.", 'new_health': 0, 'new_gold': -200},
        ],
        8: [
            {'outcome_text': "You defeat the dragon and get its treasure!", 'new_health': 275, 'new_gold': 1500},
            {'outcome_text': "You get hit by a dragon fireball!", 'new_health': 0, 'new_gold': -1000},
            {'outcome_text': "You see a group of dwarves approaching.", 'new_health': 150, 'new_gold': -400},
            {'outcome_text': "You discover a hidden mine.", 'new_health': 200, 'new_gold': 600},
            {'outcome_text': "You get hurt by a dragon claw.", 'new_health': 0, 'new_gold': -300},
        ],
        9: [
            {'outcome_text': "You defeat the giant and get its club!", 'new_health': 300, 'new_gold': 1800},
            {'outcome_text': "You get caught by a giant.", 'new_health': 0, 'new_gold': -1200},
            {'outcome_text': "You see a group of goblins approaching.", 'new_health': 175, 'new_gold': -500},
            {'outcome_text': "You discover a hidden cave-in.", 'new_health': 225, 'new_gold': 700},
            {'outcome_text': "You get hurt by a giant fist.", 'new_health': 0, 'new_gold': -400},
        ],
        10: [
            {'outcome_text': "You defeat the evil sorceress and get her magical staff!", 'new_health': 350, 'new_gold': 2200},
            {'outcome_text': "You get hit by a sorceress's spell.", 'new_health': 0, 'new_gold': -2000},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 200, 'new_gold': -1000},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 250, 'new_gold': 800},
            {'outcome_text': "You get hurt by a sorceress's minions.", 'new_health': 0, 'new_gold': -800},
        ],
        11: [
            {'outcome_text': "You defeat the giant spider and get its silk!", 'new_health': 375, 'new_gold': 2500},
            {'outcome_text': "You get caught by a giant spider.", 'new_health': 0, 'new_gold': -2500},
            {'outcome_text': "You see a group of orcs approaching.", 'new_health': 225, 'new_gold': -1500},
            {'outcome_text': "You discover a secret passage.", 'new_health': 275, 'new_gold': 1000},
            {'outcome_text': "You get hurt by a giant spider bite.", 'new_health': 0, 'new_gold': -1500},
        ],
        12: [
            {'outcome_text': "You defeat the undead necromancer and get his spellbook!", 'new_health': 400, 'new_gold': 2800},
            {'outcome_text': "You get hit by a necromancer's spell.", 'new_health': 0, 'new_gold': -3000},
            {'outcome_text': "You see a group of ghouls approaching.", 'new_health': 250, 'new_gold': -2000},
            {'outcome_text': "You discover a hidden graveyard.", 'new_health': 300, 'new_gold': 1200},
            {'outcome_text': "You get hurt by a necromancer's minions.", 'new_health': 0, 'new_gold': -2000},
        ],
        13: [
            {'outcome_text': "You defeat the evil wizard and get his magic staff!", 'new_health': 425, 'new_gold': 3200},
            {'outcome_text': "You get hit by a wizard's spell.", 'new_health': 0, 'new_gold': -3800},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 275, 'new_gold': -2800},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 325, 'new_gold': 1600},
            {'outcome_text': "You get hurt by a wizard's minions.", 'new_health': 0, 'new_gold': -2800},
        ],
        14: [
            {'outcome_text': "You defeat the giant bear and get its fur!", 'new_health': 450, 'new_gold': 3500},
            {'outcome_text': "You get caught by a giant bear.", 'new_health': 0, 'new_gold': -4000},
            {'outcome_text': "You see a group of elves approaching.", 'new_health': 300, 'new_gold': -3200},
            {'outcome_text': "You discover a hidden forest glade.", 'new_health': 350, 'new_gold': 1800},
            {'outcome_text': "You get hurt by a giant bear swipe.", 'new_health': 0, 'new_gold': -3200},
        ],
        15: [
            {'outcome_text': "You defeat the dragon and get its treasure!", 'new_health': 475, 'new_gold': 4000},
            {'outcome_text': "You get hit by a dragon fireball!", 'new_health': 0, 'new_gold': -4500},
            {'outcome_text': "You see a group of dwarves approaching.", 'new_health': 325, 'new_gold': -3800},
            {'outcome_text': "You discover a hidden mine.", 'new_health': 375, 'new_gold': 2200},
            {'outcome_text': "You get hurt by a dragon claw.", 'new_health': 0, 'new_gold': -3800},
        ],
        16: [
            {'outcome_text': "You defeat the giant and get its club!", 'new_health': 500, 'new_gold': 4400},
            {'outcome_text': "You get caught by a giant.", 'new_health': 0, 'new_gold': -5400},
            {'outcome_text': "You see a group of goblins approaching.", 'new_health': 350, 'new_gold': -4800},
            {'outcome_text': "You discover a hidden cave-in.", 'new_health': 400, 'new_gold': 2800},
            {'outcome_text': "You get hurt by a giant fist.", 'new_health': 0, 'new_gold': -4800},
        ],
        17: [
            {'outcome_text': "You defeat the evil sorceress and get her magical staff!", 'new_health': 525, 'new_gold': 4800},
            {'outcome_text': "You get hit by a sorceress's spell.", 'new_health': 0, 'new_gold': -5200},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 375, 'new_gold': -5200},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 425, 'new_gold': 3200},
            {'outcome_text': "You get hurt by a sorceress's minions.", 'new_health': 0, 'new_gold': -5200},
        ],
        18: [
            {'outcome_text': "You defeat the giant spider and get its silk!", 'new_health': 550, 'new_gold': 5200},
            {'outcome_text': "You get caught by a giant spider.", 'new_health': 0, 'new_gold': -6200},
            {'outcome_text': "You see a group of orcs approaching.", 'new_health': 400, 'new_gold': -6000},
            {'outcome_text': "You discover a secret passage.", 'new_health': 450, 'new_gold': 4400},
            {'outcome_text': "You get hurt by a giant spider bite.", 'new_health': 0, 'new_gold': -6000},
        ],
        19: [
            {'outcome_text': "You defeat the undead necromancer and get his spellbook!", 'new_health': 575, 'new_gold': 5600},
            {'outcome_text': "You get hit by a necromancer's spell.", 'new_health': 0, 'new_gold': -6000},
            {'outcome_text': "You see a group of ghouls approaching.", 'new_health': 425, 'new_gold': -5600},
            {'outcome_text': "You discover a hidden graveyard.", 'new_health': 475, 'new_gold': 4800},
            {'outcome_text': "You get hurt by a necromancer's minions.", 'new_health': 0, 'new_gold': -5600},
        ],
        20: [
            {'outcome_text': "You defeat the evil wizard and get his magic staff!", 'new_health': 600, 'new_gold': 6000},
            {'outcome_text': "You get hit by a wizard's spell.", 'new_health': 0, 'new_gold': -6400},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 450, 'new_gold': -6400},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 500, 'new_gold': 5600},
            {'outcome_text': "You get hurt by a wizard's minions.", 'new_health': 0, 'new_gold': -6400},
        ],
        21: [
            {'outcome_text': "You defeat the giant bear and get its fur!", 'new_health': 625, 'new_gold': 6600},
            {'outcome_text': "You get caught by a giant bear.", 'new_health': 0, 'new_gold': -7200},
            {'outcome_text': "You see a group of elves approaching.", 'new_health': 475, 'new_gold': -6800},
            {'outcome_text': "You discover a hidden forest glade.", 'new_health': 525, 'new_gold': 6400},
            {'outcome_text': "You get hurt by a giant bear swipe.", 'new_health': 0, 'new_gold': -6800},
        ],
        22: [
            {'outcome_text': "You defeat the dragon and get its treasure!", 'new_health': 650, 'new_gold': 7000},
            {'outcome_text': "You get hit by a dragon fireball!", 'new_health': 0, 'new_gold': -7600},
            {'outcome_text': "You see a group of dwarves approaching.", 'new_health': 500, 'new_gold': -7200},
            {'outcome_text': "You discover a hidden mine.", 'new_health': 550, 'new_gold': 6800},
            {'outcome_text': "You get hurt by a dragon claw.", 'new_health': 0, 'new_gold': -7200},
        ],
        23: [
            {'outcome_text': "You defeat the giant and get its club!", 'new_health': 675, 'new_gold': 7600},
            {'outcome_text': "You get caught by a giant.", 'new_health': 0, 'new_gold': -8800},
            {'outcome_text': "You see a group of goblins approaching.", 'new_health': 525, 'new_gold': -8000},
            {'outcome_text': "You discover a hidden cave-in.", 'new_health': 575, 'new_gold': 7800},
            {'outcome_text': "You get hurt by a giant fist.", 'new_health': 0, 'new_gold': -8000},
        ],
        24: [
            {'outcome_text': "You defeat the evil sorceress and get her magical staff!", 'new_health': 700, 'new_gold': 8200},
            {'outcome_text': "You get hit by a sorceress's spell.", 'new_health': 0, 'new_gold': -9200},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 550, 'new_gold': -9200},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 600, 'new_gold': 8800},
            {'outcome_text': "You get hurt by a sorceress's minions.", 'new_health': 0, 'new_gold': -9200},
        ],
        25: [
            {'outcome_text': "You defeat the giant spider and get its silk!", 'new_health': 725, 'new_gold': 8800},
            {'outcome_text': "You get caught by a giant spider.", 'new_health': 0, 'new_gold': -10000},
            {'outcome_text': "You see a group of orcs approaching.", 'new_health': 575, 'new_gold': -9000},
            {'outcome_text': "You discover a secret passage.", 'new_health': 625, 'new_gold': 8200},
            {'outcome_text': "You get hurt by a giant spider bite.", 'new_health': 0, 'new_gold': -9000},
        ],
        26: [
            {'outcome_text': "You defeat the undead necromancer and get his spellbook!", 'new_health': 750, 'new_gold': 9400},
            {'outcome_text': "You get hit by a necromancer's spell.", 'new_health': 0, 'new_gold': -10400},
            {'outcome_text': "You see a group of ghouls approaching.", 'new_health': 600, 'new_gold': -10400},
            {'outcome_text': "You discover a hidden graveyard.", 'new_health': 650, 'new_gold': 9200},
            {'outcome_text': "You get hurt by a necromancer's minions.", 'new_health': 0, 'new_gold': -10400},
        ],
        27: [
            {'outcome_text': "You defeat the evil wizard and get his magic staff!", 'new_health': 775, 'new_gold': 10200},
            {'outcome_text': "You get hit by a wizard's spell.", 'new_health': 0, 'new_gold': -11200},
            {'outcome_text': "You see a group of demons approaching.", 'new_health': 625, 'new_gold': -11200},
            {'outcome_text': "You discover a hidden laboratory.", 'new_health': 675, 'new_gold': 10200},
            {'outcome_text': "You get hurt by a wizard's minions.", 'new_health': 0, 'new_gold': -11200},
        ],
        28: [
            {'outcome_text': "You defeat the giant bear and get its fur!", 'new_health': 800, 'new_gold': 11400},
            {'outcome_text': "You get caught by a giant bear.", 'new_health': 0, 'new_gold': -13400},
            {'outcome_text': "You see a group of elves approaching.", 'new_health': 650, 'new_gold': -13400},
            {'outcome_text': "You discover a hidden forest glade.", 'new_health': 700, 'new_gold': 11400},
            {'outcome_text': "You get hurt by a giant bear swipe.", 'new_health': 0, 'new_gold': -13400},
        ],
        29: [
            {'outcome_text': "You defeat the dragon and get its treasure!", 'new_health': 825, 'new_gold': 12600},
            {'outcome_text': "You get hit by a dragon fireball!", 'new_health': 0, 'new_gold': -15600},
            {'outcome_text': "You see a group of dwarves approaching.", 'new_health': 675, 'new_gold': -15600},
            {'outcome_text': "You discover a hidden mine.", 'new_health': 725, 'new_gold': 12600},
            {'outcome_text': "You get hurt by a dragon claw.", 'new_health': 0, 'new_gold': -15600},
        ],
        30: [
            {'outcome_text': "You defeat the giant and get its club!", 'new_health': 850, 'new_gold': 14000},
            {'outcome_text': "You get caught by a giant.", 'new_health': 0, 'new_gold': -17000},
            {'outcome_text': "You see a group of goblins approaching.", 'new_health': 700, 'new_gold': -17000},
            {'outcome_text': "You discover a hidden cave-in.", 'new_health': 750, 'new_gold': 14000},
            {'outcome_text': "You get hurt by a giant fist.", 'new_health': 0, 'new_gold': -17000},
        ],
    }

    outcomes_choice = outcomes.get(choice)
    if not outcomes_choice:
        return "Invalid choice", 400

    outcome = random.choice(outcomes_choice)
    session['new_health'] = outcome['new_health']
    session['new_gold'] = outcome['new_gold']
    session['outcome_text'] = outcome['outcome_text']

    return redirect(url_for('game_over'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)