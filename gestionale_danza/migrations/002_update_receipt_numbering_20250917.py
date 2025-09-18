#!/usr/bin/env python3
"""
Migration 002: Aggiorna numerazione ricevute - ricevuta #1 diventa #80
Data: 17/09/2025
Descrizione: Aggiorna tutte le ricevute esistenti aggiungendo 79 al numero,
             così la ricevuta #1 diventa #80, la #34 diventa #113, ecc.
"""

import os
import sys
import sqlite3
from datetime import datetime

def run_migration():
    """Esegue la migrazione per aggiornare la numerazione ricevute"""
    
    print("🔄 MIGRAZIONE 002: Aggiornamento numerazione ricevute (#1 → #80)")
    print("=" * 60)
    
    # Percorso database
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return False
    
    # Backup del database
    backup_path = f"{database_path}.backup_migration_002_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(database_path, backup_path)
    print(f"💾 Backup creato: {backup_path}")
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Controlla ricevute esistenti
        cursor.execute("""
            SELECT COUNT(*), MIN(numero_ricevuta), MAX(numero_ricevuta)
            FROM pagamenti 
            WHERE numero_ricevuta IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        if stats[0] > 0:
            print(f"📊 Ricevute esistenti da aggiornare: {stats[0]}")
            print(f"   Range attuale: da {stats[1]} a {stats[2]}")
            print(f"   Nuovo range: da {stats[1] + 79} a {stats[2] + 79}")
            
            # Aggiorna tutte le ricevute esistenti aggiungendo 79
            cursor.execute("""
                UPDATE pagamenti 
                SET numero_ricevuta = numero_ricevuta + 79
                WHERE numero_ricevuta IS NOT NULL
            """)
            
            ricevute_aggiornate = cursor.rowcount
            print(f"✅ Aggiornate {ricevute_aggiornate} ricevute esistenti")
        else:
            print("📊 Nessuna ricevuta esistente da aggiornare")
        
        # Anno corrente
        current_year = datetime.now().year
        
        # Aggiorna il sistema di numerazione
        cursor.execute("SELECT * FROM numerazione_ricevute WHERE anno = ?", (current_year,))
        current_record = cursor.fetchone()
        
        if current_record:
            # Aggiorna il contatore aggiungendo 79
            nuovo_ultimo = current_record[2] + 79
            cursor.execute("""
                UPDATE numerazione_ricevute 
                SET ultimo_numero = ?, 
                    data_aggiornamento = ? 
                WHERE anno = ?
            """, (nuovo_ultimo, datetime.now(), current_year))
            
            print(f"✅ Numerazione sistema aggiornata: prossima ricevuta sarà numero {nuovo_ultimo + 1}")
            
        else:
            # Se non esiste record, calcola il prossimo numero basato sulle ricevute esistenti
            cursor.execute("""
                SELECT COALESCE(MAX(numero_ricevuta), 79) FROM pagamenti 
                WHERE numero_ricevuta IS NOT NULL
            """)
            max_ricevuta = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO numerazione_ricevute 
                (anno, ultimo_numero, numero_iniziale, data_creazione, data_aggiornamento)
                VALUES (?, ?, ?, ?, ?)
            """, (current_year, max_ricevuta, 80, datetime.now(), datetime.now()))
            
            print(f"✅ Creato record numerazione: prossima ricevuta sarà numero {max_ricevuta + 1}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 MIGRAZIONE 002 COMPLETATA!")
        print(f"💾 Backup disponibile in: {backup_path}")
        print(f"🎯 Ricevuta #1 è ora ricevuta #80, ricevuta #34 è ora ricevuta #113")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {str(e)}")
        
        # Ripristina backup in caso di errore
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, database_path)
            print(f"🔄 Database ripristinato dal backup")
        
        return False

def check_numbering_status():
    """Controlla lo stato attuale della numerazione"""
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(base_path, 'data', 'database.db')
    
    if not os.path.exists(database_path):
        print("❌ Database non trovato!")
        return
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    current_year = datetime.now().year
    
    print(f"📊 STATO NUMERAZIONE RICEVUTE {current_year}")
    print("=" * 50)
    
    # Stato numerazione
    cursor.execute("SELECT * FROM numerazione_ricevute WHERE anno = ?", (current_year,))
    record = cursor.fetchone()
    
    if record:
        print(f"Ultimo numero utilizzato: {record[2]}")
        print(f"Numero iniziale: {record[3]}")
        print(f"Prossima ricevuta: {record[2] + 1}")
    else:
        print("Nessun record di numerazione trovato per l'anno corrente")
    
    # Ricevute emesse
    cursor.execute("""
        SELECT COUNT(*), MIN(numero_ricevuta), MAX(numero_ricevuta)
        FROM pagamenti 
        WHERE numero_ricevuta IS NOT NULL
    """)
    
    stats = cursor.fetchone()
    if stats[0] > 0:
        print(f"\nRicevute totali emesse: {stats[0]}")
        print(f"Prima ricevuta: {stats[1]}")
        print(f"Ultima ricevuta: {stats[2]}")
    else:
        print("\nNessuna ricevuta emessa")
    
    conn.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_numbering_status()
    else:
        success = run_migration()
        if not success:
            print("\n❌ Migrazione fallita!")
            sys.exit(1)
        else:
            print("\n✅ Migrazione completata con successo!")