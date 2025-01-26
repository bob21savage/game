cd C:\Users\bpier\Desktop\rpg
python -m venv .venv_new  # Create a new virtual environment
.\.venv_new\Scripts\activate  # Activate the new environment
pip install pyinstaller  # Install PyInstaller
pyinstaller --onefile --hidden-import flask_sqlalchemy --add-data "templates;templates" --add-data "static;static" --add-data "app/models;app/models" app.py
pip install Flask Flask-WTF Flask-Login 
pip install Flask-SQLAlchemy
pip install flask-migrate flask-sqlalchemy flask-login werkzeug
set FLASK_APP=app.py
flask db init
flask db migrate -m "recreate schema with version"
flask db upgrade