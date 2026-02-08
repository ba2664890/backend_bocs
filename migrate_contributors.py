"""
Migration script to update contributor users to local_manager role
Run this script after deploying the new code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fati_backend.settings')
django.setup()

from fati_accounts.models import User

def migrate_contributors():
    """Migrate all contributor users to local_manager role"""
    print("🔄 Starting migration of contributor users...")
    
    # Find all users with contributor role
    contributors = User.objects.filter(role='contributor')
    count = contributors.count()
    
    if count == 0:
        print("✅ No contributor users found. Migration not needed.")
        return
    
    print(f"📊 Found {count} contributor user(s) to migrate")
    
    # Update all contributors to local_manager
    updated = contributors.update(role='local_manager')
    
    print(f"✅ Successfully migrated {updated} user(s) from contributor to local_manager")
    
    # Display migrated users
    print("\n📋 Migrated users:")
    for user in User.objects.filter(role='local_manager'):
        print(f"  - {user.email} ({user.first_name} {user.last_name})")

if __name__ == '__main__':
    migrate_contributors()
