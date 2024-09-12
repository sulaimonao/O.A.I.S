from main import app, db
from data.models import User
from sqlalchemy import inspect

with app.app_context():
    # Query for users in the database
    users = User.query.all()
    print(f"Users in the database: {users}")
    
    if not users:
        # Create a new user if no users exist
        new_user = User(username="testuser", profile_data={})
        db.session.add(new_user)
        db.session.commit()
        print("Created a new user: testuser")
    
    # Get the list of tables using the SQLAlchemy inspector
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")

    # Query the database again to check for the newly created user
    users = User.query.all()
    print(f"Users in the database after creation: {users}")
