#!/usr/bin/env python3
"""
Migration 003: Aggiunge campi luogo di nascita, sesso e calcolo automatico CF
Data: 17/09/2025
Descrizione: Aggiunge i campi comune_nascita, provincia_nascita, sesso
             e implementa il calcolo automatico del codice fiscale per i clienti.
"""

import os
import sys
import sqlite3
from datetime import datetime

def run_migration():
    """Esegue la migrazione per aggiungere i nuovi campi anagrafica"""
    
    print("🔄 MIGRAZIONE 003: Aggiunta campi luogo nascita, sesso e CF automatico")
    print("=" * 70)
    
    # Percorso database
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return False
    
    # Backup del database
    backup_path = f"{database_path}.backup_migration_003_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(database_path, backup_path)
    print(f"💾 Backup creato: {backup_path}")
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Controlla se le colonne esistono già
        cursor.execute("PRAGMA table_info(clienti)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📊 Colonne esistenti nella tabella clienti: {len(existing_columns)}")
        
        # Lista delle nuove colonne da aggiungere
        new_columns = [
            ("comune_nascita", "TEXT"),
            ("provincia_nascita", "TEXT"), 
            ("sesso", "TEXT"),
            ("cf_calcolato_automaticamente", "BOOLEAN DEFAULT 0")
        ]
        
        columns_added = 0
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE clienti ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Aggiunta colonna: {column_name} ({column_type})")
                    columns_added += 1
                except sqlite3.Error as e:
                    print(f"⚠️  Errore aggiungendo colonna {column_name}: {e}")
            else:
                print(f"ℹ️  Colonna {column_name} già esistente")
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(clienti)")
        final_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n📊 RIEPILOGO MIGRAZIONE:")
        print(f"   Colonne aggiunte: {columns_added}")
        print(f"   Totale colonne dopo migrazione: {len(final_columns)}")
        
        # Mostra le nuove colonne aggiunte
        if columns_added > 0:
            print(f"\n✨ Nuove colonne disponibili:")
            for column_name, column_type in new_columns:
                if column_name in final_columns:
                    print(f"   - {column_name}: {column_type}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 MIGRAZIONE 003 COMPLETATA!")
        print(f"💾 Backup disponibile in: {backup_path}")
        print(f"🆔 Ora è possibile calcolare automaticamente il codice fiscale")
        print(f"📍 Aggiunti campi per comune/provincia di nascita e sesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {str(e)}")
        
        # Ripristina backup in caso di errore
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, database_path)
            print(f"🔄 Database ripristinato dal backup")
        
        return False

def check_migration_status():
    """Controlla lo stato della migrazione"""
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    print(f"📊 STATO MIGRAZIONE 003")
    print("=" * 40)
    
    # Controlla struttura tabella clienti
    cursor.execute("PRAGMA table_info(clienti)")
    columns = cursor.fetchall()
    
    target_columns = ['comune_nascita', 'provincia_nascita', 'sesso', 'cf_calcolato_automaticamente']
    
    print(f"Totale colonne nella tabella clienti: {len(columns)}")
    print(f"\nControllo nuove colonne:")
    
    for target_col in target_columns:
        found = any(col[1] == target_col for col in columns)
        status = "✅ Presente" if found else "❌ Mancante"
        print(f"   {target_col}: {status}")
    
    # Conta clienti esistenti
    cursor.execute("SELECT COUNT(*) FROM clienti")
    total_clients = cursor.fetchone()[0]
    print(f"\nTotale clienti nel database: {total_clients}")
    
    conn.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_migration_status()
    else:
        success = run_migration()
        if not success:
            print("\n❌ Migrazione fallita!")
            sys.exit(1)
        else:
            print("\n✅ Migrazione completata con successo!")