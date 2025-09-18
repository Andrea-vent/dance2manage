#!/usr/bin/env python3
"""
Migration 001: Aggiunge data di nascita e riferimenti genitori per clienti
Data: 17/09/2025
Descrizione: Aggiunge campo data_nascita e campi per riferimenti genitori (nome_cognome_madre, 
             telefono_madre, nome_cognome_padre, telefono_padre) alla tabella clienti.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Aggiungi il percorso del progetto per importare i modelli
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Esegue la migrazione"""
    
    print("🔄 MIGRAZIONE 001: Aggiunta data nascita e riferimenti genitori")
    print("=" * 70)
    
    # Percorso database
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return False
    
    # Backup del database
    backup_path = f"{database_path}.backup_migration_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(database_path, backup_path)
    print(f"💾 Backup creato: {backup_path}")
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Verifica che la tabella clienti esista
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clienti'")
        if not cursor.fetchone():
            print("❌ Tabella 'clienti' non trovata!")
            return False
        
        print("📋 Aggiunta colonne alla tabella clienti...")
        
        # Aggiungi campo data_nascita
        try:
            cursor.execute("ALTER TABLE clienti ADD COLUMN data_nascita DATE")
            print("   ✅ Campo 'data_nascita' aggiunto")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("   ⚠️ Campo 'data_nascita' già esistente")
            else:
                raise
        
        # Aggiungi campi genitori
        parent_fields = [
            ('nome_cognome_madre', 'VARCHAR(200)'),
            ('telefono_madre', 'VARCHAR(20)'),
            ('nome_cognome_padre', 'VARCHAR(200)'),
            ('telefono_padre', 'VARCHAR(20)')
        ]
        
        for field_name, field_type in parent_fields:
            try:
                cursor.execute(f"ALTER TABLE clienti ADD COLUMN {field_name} {field_type}")
                print(f"   ✅ Campo '{field_name}' aggiunto")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠️ Campo '{field_name}' già esistente")
                else:
                    raise
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica che i campi siano stati aggiunti
        cursor.execute("PRAGMA table_info(clienti)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_fields = ['data_nascita', 'nome_cognome_madre', 'telefono_madre', 
                          'nome_cognome_padre', 'telefono_padre']
        
        for field in required_fields:
            if field in columns:
                print(f"   ✅ Campo '{field}' verificato")
            else:
                print(f"   ❌ Campo '{field}' mancante!")
                return False
        
        conn.close()
        
        print("\n🎉 MIGRAZIONE 001 COMPLETATA CON SUCCESSO!")
        print(f"💾 Backup disponibile in: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {str(e)}")
        
        # Ripristina backup in caso di errore
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, database_path)
            print(f"🔄 Database ripristinato dal backup")
        
        return False

def rollback_migration():
    """Annulla la migrazione (rimuove i campi aggiunti)"""
    
    print("🔄 ROLLBACK MIGRAZIONE 001")
    print("=" * 40)
    
    # SQLite non supporta DROP COLUMN facilmente
    # Per un rollback completo servirebbe ricreare la tabella
    print("⚠️ SQLite non supporta DROP COLUMN nativamente.")
    print("💡 Per fare rollback completo, ripristina dal backup:")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    # Trova l'ultimo backup
    backup_dir = os.path.dirname(database_path)
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('database.db.backup_migration_001_')]
    
    if backup_files:
        latest_backup = sorted(backup_files)[-1]
        backup_path = os.path.join(backup_dir, latest_backup)
        print(f"📁 Ultimo backup: {backup_path}")
        print(f"🔄 Per ripristinare: cp {backup_path} {database_path}")
    else:
        print("❌ Nessun backup trovato per questa migrazione")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        success = run_migration()
        if not success:
            print("\n❌ Migrazione fallita!")
            sys.exit(1)
        else:
            print("\n✅ Migrazione completata con successo!")