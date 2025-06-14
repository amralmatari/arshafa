from app import create_app
from app.utils.db_inspector import inspect_database

app = create_app()
with app.app_context():
    inspect_database()