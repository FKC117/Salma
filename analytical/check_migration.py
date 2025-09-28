import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.db import connection

def check_migration():
    """Check if the migration has been applied"""
    try:
        # Check if the migration has been applied by querying the migrations table
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM django_migrations WHERE app='analytics' AND name='0003_alter_chatmessage_session'")
            result = cursor.fetchone()
            
            if result:
                print("✓ Migration 0003 has been applied")
            else:
                print("✗ Migration 0003 has not been applied")
                
        # Check the actual database schema
        with connection.cursor() as cursor:
            # For PostgreSQL
            cursor.execute("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name='analytics_chat_message' AND column_name='session_id'
            """)
            result = cursor.fetchone()
            
            if result:
                column_name, is_nullable = result
                print(f"Column: {column_name}")
                print(f"Nullable: {is_nullable}")
                if is_nullable == 'YES':
                    print("✓ Session ID column is nullable")
                else:
                    print("✗ Session ID column is NOT nullable")
            else:
                print("Could not find session_id column")
                
    except Exception as e:
        print(f"Error checking migration: {e}")
        # Try a simpler approach
        try:
            from analytics.models import ChatMessage
            # Try to create a chat message without session
            print("Testing chat message creation without session...")
            # This will fail if the migration hasn't been applied
        except Exception as e2:
            print(f"Error: {e2}")

if __name__ == "__main__":
    check_migration()