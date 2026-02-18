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

    # Add image_prompts and image_urls to scenes table
    # Using JSON type for structured data
    add_column(cursor, "scenes", "image_prompts JSON")
    
    conn.commit()
    conn.close()
    print("Database schema updated successfully.")

if __name__ == "__main__":
    main()
