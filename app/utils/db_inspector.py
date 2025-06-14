from app import db
from sqlalchemy import inspect

def inspect_database():
    """Inspect the current database structure"""
    inspector = inspect(db.engine)
    
    # Get all table names
    tables = inspector.get_table_names()
    print("Tables in database:", tables)
    
    # For each table, get column information
    for table in tables:
        print(f"\nTable: {table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")

if __name__ == "__main__":
    inspect_database()