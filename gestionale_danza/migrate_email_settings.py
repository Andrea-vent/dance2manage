#!/usr/bin/env python3
"""
Script di migrazione per aggiungere i campi di configurazione email alla tabella settings
Eseguire questo script per aggiornare il database esistente
"""

import os
import sys
import sqlite3
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_email_settings():
    """Aggiunge i campi email alla tabella settings se non esistono"""
    
    # Percorso del database
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print(f"❌ Database non trovato: {database_path}")
        return False
    
    print(f"🔧 Migrazione database: {database_path}")
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Verifica se i campi email esistono già
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        email_fields = [
            'mail_server', 'mail_port', 'mail_use_tls', 'mail_use_ssl',
            'mail_username', 'mail_password', 'mail_default_sender',
            'mail_max_emails', 'mail_suppress_send', 'mail_debug'
        ]
        
        # Controlla quali campi sono mancanti
        missing_fields = [field for field in email_fields if field not in columns]
        
        if not missing_fields:
            print("✅ Tutti i campi email sono già presenti nel database")
            conn.close()
            return True
        
        print(f"📋 Campi da aggiungere: {', '.join(missing_fields)}")
        
        # Crea backup del database
        backup_path = database_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(database_path, backup_path)
        print(f"💾 Backup creato: {backup_path}")
        
        # Aggiungi i campi mancanti
        alterations = [
            "ALTER TABLE settings ADD COLUMN mail_server TEXT",
            "ALTER TABLE settings ADD COLUMN mail_port INTEGER DEFAULT 587",
            "ALTER TABLE settings ADD COLUMN mail_use_tls BOOLEAN DEFAULT 1",
            "ALTER TABLE settings ADD COLUMN mail_use_ssl BOOLEAN DEFAULT 0",
            "ALTER TABLE settings ADD COLUMN mail_username TEXT",
            "ALTER TABLE settings ADD COLUMN mail_password TEXT",
            "ALTER TABLE settings ADD COLUMN mail_default_sender TEXT",
            "ALTER TABLE settings ADD COLUMN mail_max_emails INTEGER DEFAULT 100",
            "ALTER TABLE settings ADD COLUMN mail_suppress_send BOOLEAN DEFAULT 1",
            "ALTER TABLE settings ADD COLUMN mail_debug BOOLEAN DEFAULT 0"
        ]
        
        for alter_sql in alterations:
            field_name = alter_sql.split()[-3] if 'ADD COLUMN' in alter_sql else alter_sql.split()[-1]
            if field_name in missing_fields or field_name.replace('DEFAULT', '').strip() in missing_fields:
                try:
                    cursor.execute(alter_sql)
                    print(f"  ✅ Aggiunto campo: {field_name}")
                except sqlite3.Error as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"  ⚠️  Errore aggiungendo {field_name}: {e}")
        
        # Commit delle modifiche
        conn.commit()
        print("✅ Migrazione completata con successo!")
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(settings)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📊 Campi totali nella tabella settings: {len(new_columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_migration():
    """Verifica che la migrazione sia stata completata correttamente"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Controlla la struttura della tabella
        cursor.execute("PRAGMA table_info(settings)")
        columns = cursor.fetchall()
        
        print("\n📋 Struttura attuale della tabella settings:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore nella verifica: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Avvio migrazione campi email...")
    
    if migrate_email_settings():
        print("\n🔍 Verifica migrazione...")
        verify_migration()
        print("\n🎉 Migrazione completata! Il database è pronto per le configurazioni email.")
    else:
        print("\n❌ Migrazione fallita. Controlla i messaggi di errore sopra.")
    
    input("\nPremi INVIO per chiudere...")