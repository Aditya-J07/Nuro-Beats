
import sqlite3
import os

def migrate_database():
    """Add stroke-specific columns to existing database"""
    db_path = os.path.join('instance', 'neurobeat.db')
    
    if not os.path.exists(db_path):
        print("Database doesn't exist yet. Run the app first to create it.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of new columns to add
    new_columns = [
        ('stroke_affected_side', 'VARCHAR(20)'),
        ('stroke_severity', 'VARCHAR(20)'),
        ('aphasia_type', 'VARCHAR(30)'),
        ('dysarthria_severity', 'VARCHAR(20)'),
        ('motor_impairment_level', 'VARCHAR(20)'),
        ('cognitive_status', 'VARCHAR(20)'),
        ('emotional_status', 'VARCHAR(30)'),
        ('preferred_music_genre', 'VARCHAR(50)'),
        ('preferred_beat_sound', 'VARCHAR(20)')
    ]
    
    try:
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(patient_profiles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE patient_profiles ADD COLUMN {column_name} {column_type}")
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"Error adding column {column_name}: {e}")
        
        # Also add new columns to therapy_sessions if they don't exist
        cursor.execute("PRAGMA table_info(therapy_sessions)")
        existing_session_columns = [row[1] for row in cursor.fetchall()]
        
        session_columns = [
            ('affected_limb', 'VARCHAR(20)'),
            ('speech_clarity_score', 'FLOAT'),
            ('cognitive_load_level', 'INTEGER'),
            ('emotional_response', 'VARCHAR(20)'),
            ('generated_beat_url', 'VARCHAR(500)')
        ]
        
        for column_name, column_type in session_columns:
            if column_name not in existing_session_columns:
                try:
                    cursor.execute(f"ALTER TABLE therapy_sessions ADD COLUMN {column_name} {column_type}")
                    print(f"Added session column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"Error adding session column {column_name}: {e}")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
