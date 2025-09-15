#!/usr/bin/env python3
"""
Script completo di inizializzazione database per Dance2Manage
Unisce tutte le migrazioni e crea un database completo e funzionante
"""

import os
import sys
import sqlite3
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_complete_database():
    """Crea il database completo con tutte le tabelle e dati iniziali"""
    
    # Percorso database
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    # Crea la cartella data se non esiste
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    print("🎭 DANCE2MANAGE - SETUP DATABASE COMPLETO")
    print("=" * 60)
    print(f"📁 Database: {database_path}")
    
    # Se il database esiste, crea backup
    if os.path.exists(database_path):
        backup_path = f"{database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(database_path, backup_path)
        print(f"💾 Backup creato: {backup_path}")
        os.remove(database_path)
    
    # Crea database con schema completo
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    print("\n🔧 Creazione schema database...")
    
    # 1. Tabella role
    cursor.execute("""
        CREATE TABLE role (
            id INTEGER NOT NULL, 
            name VARCHAR(80), 
            description VARCHAR(255), 
            permissions TEXT, 
            PRIMARY KEY (id), 
            UNIQUE (name)
        )
    """)
    
    # 2. Tabella user
    cursor.execute("""
        CREATE TABLE user (
            id INTEGER NOT NULL, 
            email VARCHAR(255) NOT NULL, 
            username VARCHAR(255), 
            password VARCHAR(255) NOT NULL, 
            fs_uniquifier VARCHAR(255) NOT NULL, 
            active BOOLEAN, 
            confirmed_at DATETIME, 
            created_at DATETIME, 
            last_login_at DATETIME, 
            current_login_at DATETIME, 
            last_login_ip VARCHAR(100), 
            current_login_ip VARCHAR(100), 
            login_count INTEGER, 
            tf_phone_number VARCHAR(128), 
            tf_primary_method VARCHAR(64), 
            tf_totp_secret VARCHAR(255), 
            mf_recovery_codes TEXT, 
            first_name VARCHAR(100), 
            last_name VARCHAR(100), 
            PRIMARY KEY (id), 
            UNIQUE (email), 
            UNIQUE (username), 
            UNIQUE (fs_uniquifier)
        )
    """)
    
    # 3. Tabella roles_users
    cursor.execute("""
        CREATE TABLE roles_users (
            user_id INTEGER, 
            role_id INTEGER, 
            FOREIGN KEY(user_id) REFERENCES user (id), 
            FOREIGN KEY(role_id) REFERENCES role (id)
        )
    """)
    
    # 4. Tabella webauthn
    cursor.execute("""
        CREATE TABLE webauthn (
            id INTEGER NOT NULL, 
            credential_id VARCHAR(1024) NOT NULL, 
            public_key TEXT NOT NULL, 
            sign_count INTEGER, 
            transports TEXT, 
            backup_eligible BOOLEAN, 
            backup_state BOOLEAN, 
            device_type VARCHAR(64), 
            name VARCHAR(64) NOT NULL, 
            usage VARCHAR(64) NOT NULL, 
            lastuse_datetime DATETIME, 
            user_id INTEGER NOT NULL, 
            PRIMARY KEY (id), 
            UNIQUE (credential_id), 
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
    """)
    
    # 5. Tabella clienti
    cursor.execute("""
        CREATE TABLE clienti (
            id INTEGER NOT NULL, 
            nome VARCHAR(100) NOT NULL, 
            cognome VARCHAR(100) NOT NULL, 
            codice_fiscale VARCHAR(16), 
            telefono VARCHAR(20), 
            email VARCHAR(120), 
            via VARCHAR(200), 
            civico VARCHAR(10), 
            cap VARCHAR(10), 
            citta VARCHAR(100), 
            provincia VARCHAR(2), 
            attivo BOOLEAN, 
            PRIMARY KEY (id)
        )
    """)
    
    # 6. Tabella insegnanti
    cursor.execute("""
        CREATE TABLE insegnanti (
            id INTEGER NOT NULL, 
            nome VARCHAR(100) NOT NULL, 
            cognome VARCHAR(100) NOT NULL, 
            codice_fiscale VARCHAR(16), 
            telefono VARCHAR(20), 
            email VARCHAR(120), 
            via VARCHAR(200), 
            civico VARCHAR(10), 
            cap VARCHAR(10), 
            citta VARCHAR(100), 
            provincia VARCHAR(2), 
            percentuale_guadagno FLOAT, 
            PRIMARY KEY (id)
        )
    """)
    
    # 7. Tabella corsi
    cursor.execute("""
        CREATE TABLE corsi (
            id INTEGER NOT NULL, 
            nome VARCHAR(100) NOT NULL, 
            giorno VARCHAR(20) NOT NULL, 
            orario TIME NOT NULL, 
            costo_mensile INTEGER, 
            max_iscritti INTEGER, 
            data_creazione DATETIME, 
            insegnante_id INTEGER NOT NULL, 
            PRIMARY KEY (id), 
            FOREIGN KEY(insegnante_id) REFERENCES insegnanti (id)
        )
    """)
    
    # 8. Tabella clienti_corsi
    cursor.execute("""
        CREATE TABLE clienti_corsi (
            cliente_id INTEGER NOT NULL, 
            corso_id INTEGER NOT NULL, 
            PRIMARY KEY (cliente_id, corso_id), 
            FOREIGN KEY(cliente_id) REFERENCES clienti (id), 
            FOREIGN KEY(corso_id) REFERENCES corsi (id)
        )
    """)
    
    # 9. Tabella pagamenti
    cursor.execute("""
        CREATE TABLE pagamenti (
            id INTEGER NOT NULL, 
            mese INTEGER NOT NULL, 
            anno INTEGER NOT NULL, 
            importo FLOAT NOT NULL, 
            pagato BOOLEAN, 
            data_pagamento DATETIME, 
            data_creazione DATETIME, 
            metodo_pagamento VARCHAR(50), 
            note VARCHAR(500), 
            numero_ricevuta INTEGER, 
            cliente_id INTEGER NOT NULL, 
            corso_id INTEGER NOT NULL, 
            PRIMARY KEY (id), 
            FOREIGN KEY(cliente_id) REFERENCES clienti (id), 
            FOREIGN KEY(corso_id) REFERENCES corsi (id)
        )
    """)
    
    # 10. Tabella settings
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER NOT NULL, 
            denominazione_sociale VARCHAR(200) NOT NULL, 
            indirizzo VARCHAR(200), 
            cap VARCHAR(10), 
            citta VARCHAR(100), 
            provincia VARCHAR(2), 
            telefono VARCHAR(20), 
            email VARCHAR(120), 
            sito_web VARCHAR(200), 
            partita_iva VARCHAR(11), 
            codice_fiscale VARCHAR(16), 
            logo_filename VARCHAR(200), 
            note TEXT, 
            mail_server VARCHAR(200), 
            mail_port INTEGER, 
            mail_use_tls BOOLEAN, 
            mail_use_ssl BOOLEAN, 
            mail_username VARCHAR(200), 
            mail_password VARCHAR(200), 
            mail_default_sender VARCHAR(200), 
            mail_max_emails INTEGER, 
            mail_suppress_send BOOLEAN, 
            mail_debug BOOLEAN, 
            numero_ricevuta_iniziale INTEGER, 
            PRIMARY KEY (id)
        )
    """)
    
    # 11. Tabella numerazione_ricevute
    cursor.execute("""
        CREATE TABLE numerazione_ricevute (
            id INTEGER NOT NULL, 
            anno INTEGER NOT NULL, 
            ultimo_numero INTEGER NOT NULL, 
            numero_iniziale INTEGER NOT NULL, 
            data_creazione DATETIME, 
            data_aggiornamento DATETIME, 
            PRIMARY KEY (id), 
            UNIQUE (anno)
        )
    """)
    
    print("   ✅ Schema database creato")
    
    # Commit dello schema
    conn.commit()
    conn.close()
    
    # Ora usa Flask-Security per creare ruoli e utenti
    print("\n👥 Configurazione Flask-Security...")
    
    from app import app, db, user_datastore
    from werkzeug.security import generate_password_hash
    import uuid
    
    with app.app_context():
        # Crea ruoli
        admin_role = user_datastore.create_role(
            name='admin', 
            description='Administrator with full access'
        )
        user_role = user_datastore.create_role(
            name='user', 
            description='Standard user with limited access'
        )
        
        print("   ✅ Ruoli creati")
        
        # Crea utente admin principale
        admin_user = user_datastore.create_user(
            email='andreaventura79@gmail.com',
            username='admin',
            password=generate_password_hash('uNIPOSCA2010!'),
            fs_uniquifier=str(uuid.uuid4()),
            active=True,
            first_name='Andrea',
            last_name='Ventura',
            created_at=datetime.utcnow()
        )
        user_datastore.add_role_to_user(admin_user, admin_role)
        
        # Crea utente admin di backup
        backup_admin = user_datastore.create_user(
            email='admin@dance2manage.com',
            username='backup_admin',
            password=generate_password_hash('admin123'),
            fs_uniquifier=str(uuid.uuid4()),
            active=True,
            first_name='Admin',
            last_name='System',
            created_at=datetime.utcnow()
        )
        user_datastore.add_role_to_user(backup_admin, admin_role)
        
        print("   ✅ Utenti admin creati")
        
        # Crea record settings di default
        from models.settings import Settings
        default_settings = Settings(
            denominazione_sociale="Dance2Manage",
            indirizzo="Via Example 123",
            cap="00100",
            citta="Roma",
            provincia="RM",
            telefono="06-12345678",
            email="info@dance2manage.com",
            numero_ricevuta_iniziale=1,
            mail_suppress_send=True,
            mail_port=587,
            mail_use_tls=True,
            mail_use_ssl=False,
            mail_max_emails=100,
            mail_debug=False
        )
        db.session.add(default_settings)
        
        print("   ✅ Settings di default creati")
        
        # Commit finale
        db.session.commit()
        
        print("\n🎉 DATABASE SETUP COMPLETATO!")
        print("=" * 60)
        print("📋 Credenziali di accesso:")
        print("   📧 Email: andreaventura79@gmail.com")
        print("   🔐 Password: uNIPOSCA2010!")
        print("   📧 Backup: admin@dance2manage.com")
        print("   🔐 Password: admin123")
        print("=" * 60)
        print("🚀 Il database è pronto per l'uso!")
        
        return True

def verify_database():
    """Verifica che il database sia stato creato correttamente"""
    
    database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return False
    
    try:
        from app import app, user_datastore
        
        with app.app_context():
            # Verifica utenti
            admin_user = user_datastore.find_user(email='andreaventura79@gmail.com')
            backup_admin = user_datastore.find_user(email='admin@dance2manage.com')
            
            print("\n🔍 Verifica database:")
            print(f"   ✅ Utente principale: {admin_user.email if admin_user else 'NON TROVATO'}")
            print(f"   ✅ Utente backup: {backup_admin.email if backup_admin else 'NON TROVATO'}")
            
            if admin_user:
                print(f"   ✅ Ruoli admin: {[r.name for r in admin_user.roles]}")
                print(f"   ✅ Account attivo: {admin_user.active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nella verifica: {str(e)}")
        return False

if __name__ == '__main__':
    success = create_complete_database()
    
    if success:
        print("\n🔍 Verifica finale...")
        verify_database()
    else:
        print("\n❌ Setup fallito!")
        sys.exit(1)