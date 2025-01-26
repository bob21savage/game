from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Character
from forms.forms import LoginForm, RegistrationForm, CharacterCreationForm
import random

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.character_select'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.character_select'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.character_select'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.character_select'))
    return render_template('register.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/character/select', methods=['GET'])
@login_required
def character_select():
    characters = Character.query.filter_by(user_id=current_user.id).all()
    return render_template('character_select.html', characters=characters)

@main.route('/character/select', methods=['POST'])
@login_required
def select_character():
    character_id = request.form.get('character_id')
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        flash('Invalid character selection')
        return redirect(url_for('main.character_select'))
    return redirect(url_for('main.game', character_id=character_id))

@main.route('/character/create', methods=['GET', 'POST'])
@login_required
def create_character():
    form = CharacterCreationForm()
    if form.validate_on_submit():
        character = Character(
            name=form.character_name.data,
            char_class=form.char_class.data,
            user_id=current_user.id,
            strength=form.strength.data,
            dexterity=form.dexterity.data,
            constitution=form.constitution.data,
            intelligence=form.intelligence.data,
            wisdom=form.wisdom.data,
            charisma=form.charisma.data
        )
        
        # Set HP based on class and constitution modifier
        con_mod = (character.constitution - 10) // 2
        if character.char_class == 'warrior':
            character.max_hp = 10 + con_mod
        elif character.char_class == 'mage':
            character.max_hp = 6 + con_mod
        else:  # rogue
            character.max_hp = 8 + con_mod
        character.hp = character.max_hp
        
        # Starting inventory based on class
        if character.char_class == 'warrior':
            character.inventory = ['Longsword', 'Shield', 'Chain Mail']
        elif character.char_class == 'mage':
            character.inventory = ['Staff', 'Spellbook', 'Potion of Mana']
        else:  # rogue
            character.inventory = ['Dagger', 'Leather Armor', 'Thieves\' Tools']
        
        db.session.add(character)
        db.session.commit()
        return redirect(url_for('main.character_select'))
    return render_template('create_character.html', form=form)

@main.route('/game/<int:character_id>')
@login_required
def game(character_id):
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        flash('Invalid character selection')
        return redirect(url_for('main.character_select'))
    return render_template('game.html', character=character)

@main.route('/api/combat', methods=['POST'])
@login_required
def combat():
    data = request.get_json()
    character = Character.query.get_or_404(data['character_id'])
    if character.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    monster = data['monster']
    monster_stats = {
        'Goblin': {'hp': 7, 'damage': (1, 6), 'xp': 50},
        'Skeleton': {'hp': 13, 'damage': (1, 6), 'xp': 100},
        'Orc': {'hp': 15, 'damage': (1, 8), 'xp': 150}
    }
    
    # Combat simulation
    monster_hp = monster_stats[monster]['hp']
    damage_dice, damage_sides = monster_stats[monster]['damage']
    
    # Character's attack
    attack_roll = random.randint(1, 20)
    if attack_roll >= 10:  # Hit
        char_damage = random.randint(1, 8) + (character.strength - 10) // 2
        monster_hp -= char_damage
        combat_log = f"You hit the {monster} for {char_damage} damage! "
    else:
        combat_log = f"You missed the {monster}! "
    
    # Monster's counterattack if still alive
    if monster_hp > 0:
        monster_attack = random.randint(1, 20)
        if monster_attack >= 10:  # Hit
            monster_damage = random.randint(damage_dice, damage_sides)
            character.hp -= monster_damage
            combat_log += f"The {monster} hits you for {monster_damage} damage!"
        else:
            combat_log += f"The {monster} misses you!"
    else:
        combat_log += f"You defeated the {monster}!"
        character.experience += monster_stats[monster]['xp']
        
        # Level up check
        level_up = False
        while character.experience >= character.level * 1000:
            character.level += 1
            level_up = True
            # Increase HP on level up
            hp_increase = random.randint(1, 8) + (character.constitution - 10) // 2
            character.max_hp += hp_increase
            character.hp = character.max_hp
    
    # Save character state
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": combat_log,
        "character_hp": character.hp,
        "new_level": level_up if monster_hp <= 0 else False
    })

@main.route('/character/rest/<int:character_id>', methods=['POST'])
@login_required
def rest_character(character_id):
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    character.hp = character.max_hp
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "You have fully rested and recovered your HP!",
        "new_hp": character.hp
    })

@main.route('/character/inventory/<int:character_id>', methods=['GET'])
@login_required
def view_inventory(character_id):
    character = Character.query.get_or_404(character_id)
    if character.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "success": True,
        "inventory": character.inventory
    })