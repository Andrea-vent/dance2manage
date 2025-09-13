#!/usr/bin/env python3
"""
Script per migrare il database esistente al nuovo modello Flask-Security-Too
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, user_datastore
from models import User, Role
from werkzeug.security import generate_password_hash

def migrate_to_security():
    """Migra il database per Flask-Security-Too"""
    with app.app_context():
        print("🔄 Migrazione database per Flask-Security-Too...")
        
        # Crea le nuove tabelle
        db.create_all()
        
        # Crea ruoli predefiniti
        if not user_datastore.find_role('admin'):
            admin_role = user_datastore.create_role(
                name='admin', 
                description='Administrator with full access'
            )
            print("✅ Creato ruolo 'admin'")
        
        if not user_datastore.find_role('user'):
            user_role = user_datastore.create_role(
                name='user', 
                description='Standard user with limited access'
            )
            print("✅ Creato ruolo 'user'")
        
        # Crea utente admin predefinito
        if not user_datastore.find_user(email='admin@dance2manage.com'):
            admin_user = user_datastore.create_user(
                email='admin@dance2manage.com',
                username='admin',
                password=generate_password_hash('admin123'),
                active=True,
                first_name='Administrator',
                last_name='System'
            )
            user_datastore.add_role_to_user(admin_user, 'admin')
            print("✅ Creato utente admin: admin@dance2manage.com / admin123")
        
        # Crea utente demo
        if not user_datastore.find_user(email='demo@dance2manage.com'):
            demo_user = user_datastore.create_user(
                email='demo@dance2manage.com',
                username='demo',
                password=generate_password_hash('demo123'),
                active=True,
                first_name='Demo',
                last_name='User'
            )
            user_datastore.add_role_to_user(demo_user, 'user')
            print("✅ Creato utente demo: demo@dance2manage.com / demo123")
        
        db.session.commit()
        print("✅ Migrazione completata!")
        
        print("\n📋 Credenziali di accesso:")
        print("   Admin: admin@dance2manage.com / admin123")
        print("   Demo:  demo@dance2manage.com / demo123")

if __name__ == '__main__':
    migrate_to_security()