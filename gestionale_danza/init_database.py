#!/usr/bin/env python3
"""
Script di inizializzazione completa del database per Dance2Manage
Unisce tutte le migrazioni in un unico script per setup iniziale
"""

import os
import sys
import sqlite3
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, user_datastore
from models import User, Role
from werkzeug.security import generate_password_hash

def create_unified_database():
    """Crea il database completo con tutte le migrazioni integrate"""
    
    # Percorso database
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    # Crea la cartella data se non esiste
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    print("🎭 DANCE2MANAGE - INIZIALIZZAZIONE DATABASE COMPLETA")
    print("=" * 60)
    print(f"📁 Database: {database_path}")
    
    with app.app_context():
        try:
            # 1. Crea tutte le tabelle base
            print("\n🔧 Creazione tabelle base...")
            db.create_all()
            print("   ✅ Tabelle base create")
            
            # 2. Aggiungi modifiche strutturali con SQL diretto
            print("\n🔄 Applicazione migrazioni strutturali...")
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Migrazioni da migrate_db.py - Campi indirizzo clienti
            clienti_fields = [
                ("via", "VARCHAR(200)"),
                ("civico", "VARCHAR(10)"),
                ("cap", "VARCHAR(10)"),
                ("citta", "VARCHAR(100)"),
                ("provincia", "VARCHAR(2)")
            ]
            
            print("   📝 Aggiornamento tabella clienti...")
            for field_name, field_type in clienti_fields:
                try:
                    cursor.execute(f"ALTER TABLE clienti ADD COLUMN {field_name} {field_type}")
                    print(f"      ✅ Aggiunto campo clienti.{field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"      ⚠️ Errore campo {field_name}: {e}")
            
            # Migrazioni insegnanti
            insegnanti_fields = [
                ("codice_fiscale", "VARCHAR(16)"),
                ("via", "VARCHAR(200)"),
                ("civico", "VARCHAR(10)"),
                ("cap", "VARCHAR(10)"),
                ("citta", "VARCHAR(100)"),
                ("provincia", "VARCHAR(2)")
            ]
            
            print("   📝 Aggiornamento tabella insegnanti...")
            for field_name, field_type in insegnanti_fields:
                try:
                    cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {field_name} {field_type}")
                    print(f"      ✅ Aggiunto campo insegnanti.{field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"      ⚠️ Errore campo {field_name}: {e}")
            
            # Migrazioni settings - Logo e numerazione ricevute
            settings_fields = [
                ("logo_filename", "VARCHAR(200)"),
                ("numero_ricevuta_iniziale", "INTEGER DEFAULT 1")
            ]
            
            print("   📝 Aggiornamento tabella settings...")
            for field_name, field_type in settings_fields:
                try:
                    cursor.execute(f"ALTER TABLE settings ADD COLUMN {field_name} {field_type}")
                    print(f"      ✅ Aggiunto campo settings.{field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"      ⚠️ Errore campo {field_name}: {e}")
            
            # Migrazioni da migrate_email_settings.py - Campi email
            email_fields = [
                ("mail_server", "TEXT"),
                ("mail_port", "INTEGER DEFAULT 587"),
                ("mail_use_tls", "BOOLEAN DEFAULT 1"),
                ("mail_use_ssl", "BOOLEAN DEFAULT 0"),
                ("mail_username", "TEXT"),
                ("mail_password", "TEXT"),
                ("mail_default_sender", "TEXT"),
                ("mail_max_emails", "INTEGER DEFAULT 100"),
                ("mail_suppress_send", "BOOLEAN DEFAULT 1"),
                ("mail_debug", "BOOLEAN DEFAULT 0")
            ]
            
            print("   📝 Aggiornamento tabella settings (campi email)...")
            for field_name, field_type in email_fields:
                try:
                    cursor.execute(f"ALTER TABLE settings ADD COLUMN {field_name} {field_type}")
                    print(f"      ✅ Aggiunto campo settings.{field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"      ⚠️ Errore campo {field_name}: {e}")
            
            # Migrazioni pagamenti
            print("   📝 Aggiornamento tabella pagamenti...")
            try:
                cursor.execute("ALTER TABLE pagamenti ADD COLUMN metodo_pagamento VARCHAR(50) DEFAULT 'Contanti'")
                print("      ✅ Aggiunto campo pagamenti.metodo_pagamento")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"      ⚠️ Errore campo metodo_pagamento: {e}")
            
            try:
                cursor.execute("ALTER TABLE pagamenti ADD COLUMN numero_ricevuta INTEGER")
                print("      ✅ Aggiunto campo pagamenti.numero_ricevuta")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"      ⚠️ Errore campo numero_ricevuta: {e}")
            
            # Migrazioni corsi
            corsi_fields = [
                ("costo_mensile", "INTEGER DEFAULT 50"),
                ("data_creazione", "DATETIME")
            ]
            
            print("   📝 Aggiornamento tabella corsi...")
            for field_name, field_type in corsi_fields:
                try:
                    cursor.execute(f"ALTER TABLE corsi ADD COLUMN {field_name} {field_type}")
                    print(f"      ✅ Aggiunto campo corsi.{field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"      ⚠️ Errore campo {field_name}: {e}")
            
            # 3. Crea tabella numerazione_ricevute
            print("   📝 Creazione tabella numerazione_ricevute...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS numerazione_ricevute (
                    id INTEGER PRIMARY KEY,
                    anno INTEGER NOT NULL UNIQUE,
                    ultimo_numero INTEGER NOT NULL DEFAULT 0,
                    numero_iniziale INTEGER NOT NULL DEFAULT 1,
                    data_creazione DATETIME NOT NULL,
                    data_aggiornamento DATETIME NOT NULL
                )
            """)
            print("      ✅ Tabella numerazione_ricevute creata")
            
            conn.commit()
            conn.close()
            
            # 4. Crea ruoli Flask-Security
            print("\n👥 Configurazione ruoli e utenti...")
            
            # Crea ruoli predefiniti
            if not user_datastore.find_role('admin'):
                admin_role = user_datastore.create_role(
                    name='admin', 
                    description='Administrator with full access'
                )
                print("   ✅ Creato ruolo 'admin'")
            
            if not user_datastore.find_role('user'):
                user_role = user_datastore.create_role(
                    name='user', 
                    description='Standard user with limited access'
                )
                print("   ✅ Creato ruolo 'user'")
            
            # 5. Crea utente admin principale
            admin_email = 'andreaventura79@gmail.com'
            admin_password = 'uNIPOSCA2010!'
            
            if not user_datastore.find_user(email=admin_email):
                admin_user = user_datastore.create_user(
                    email=admin_email,
                    username='admin',
                    password=generate_password_hash(admin_password),
                    active=True,
                    first_name='Andrea',
                    last_name='Ventura'
                )
                user_datastore.add_role_to_user(admin_user, 'admin')
                print(f"   ✅ Creato utente admin: {admin_email}")
            else:
                print(f"   ⚠️ Utente {admin_email} già esistente")
            
            # 6. Crea record settings di default se non esiste
            from models.settings import Settings
            if not Settings.query.first():
                default_settings = Settings(
                    nome_scuola="Dance2Manage",
                    numero_ricevuta_iniziale=1,
                    mail_suppress_send=True,
                    mail_port=587,
                    mail_use_tls=True,
                    mail_use_ssl=False,
                    mail_max_emails=100,
                    mail_debug=False
                )
                db.session.add(default_settings)
                print("   ✅ Creato record settings di default")
            
            # Commit finale
            db.session.commit()
            
            print("\n🎉 INIZIALIZZAZIONE COMPLETATA!")
            print("=" * 60)
            print("📋 Credenziali di accesso:")
            print(f"   📧 Email: {admin_email}")
            print(f"   🔐 Password: {admin_password}")
            print("=" * 60)
            print("🚀 Il database è pronto per l'uso!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Errore durante l'inizializzazione: {str(e)}")
            db.session.rollback()
            return False

def verify_database():
    """Verifica che il database sia stato creato correttamente"""
    
    database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return False
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Verifica tabelle principali
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'clienti', 'corsi', 'insegnanti', 'pagamenti', 'settings',
            'user', 'role', 'roles_users', 'numerazione_ricevute', 'webauthn'
        ]
        
        print("\n🔍 Verifica database:")
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ Tabella {table}: {count} record")
            else:
                print(f"   ❌ Tabella {table}: MANCANTE")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore nella verifica: {str(e)}")
        return False

if __name__ == '__main__':
    success = create_unified_database()
    
    if success:
        print("\n🔍 Verifica finale...")
        verify_database()
    else:
        print("\n❌ Inizializzazione fallita!")
        sys.exit(1)