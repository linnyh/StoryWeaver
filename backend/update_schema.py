import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "storyweaver.db")

def add_column(cursor, table, column_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        print(f"Added column {column_def} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {column_def} already exists in {table}")
        else:
            print(f"Error adding column {column_def} to {table}: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Module 1: Power & Asset State Machine
    # Character table update
    add_column(cursor, "characters", "power_state JSON")

    # Module 2: Catharsis & Tension Control
    # Scene table update
    add_column(cursor, "scenes", "tension_level INTEGER")
    add_column(cursor, "scenes", "emotional_target TEXT")

    # Module 3: Philosophical Editorial Room
    # Novel table update
    add_column(cursor, "novels", "philosophical_theme TEXT")

    conn.commit()
    conn.close()
    print("Database schema updated successfully.")

if __name__ == "__main__":
    main()