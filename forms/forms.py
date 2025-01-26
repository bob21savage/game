from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

class CharacterCreationForm(FlaskForm):
    character_name = StringField('Character Name', validators=[DataRequired(), Length(min=2, max=30)])
    char_class = SelectField('Character Class', 
        choices=[('warrior', 'Warrior'), ('mage', 'Mage'), ('rogue', 'Rogue')],
        validators=[DataRequired()])
    strength = HiddenField('Strength', validators=[DataRequired()])
    dexterity = HiddenField('Dexterity', validators=[DataRequired()])
    constitution = HiddenField('Constitution', validators=[DataRequired()])
    intelligence = HiddenField('Intelligence', validators=[DataRequired()])
    wisdom = HiddenField('Wisdom', validators=[DataRequired()])
    charisma = HiddenField('Charisma', validators=[DataRequired()])