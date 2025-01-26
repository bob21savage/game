# forms/__init__.py
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired
from database import init_db  # Switch to absolute import if this is needed at initialization

# Define all your forms below
class LoginForm(FlaskForm):
    # Define your fields here
    pass

class PlayForm(FlaskForm):
    choice = SelectField('Choice', choices=[(str(x), str(x)) for x in range(1, 31)], coerce=int, validators=[DataRequired()])