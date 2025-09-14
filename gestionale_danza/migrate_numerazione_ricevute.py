#!/usr/bin/env python3
"""
Migrazione database per implementare la numerazione automatica delle ricevute
"""
import sys
import os
import sqlite3
from datetime import datetime

def migrate_database():
    """Migra il database per aggiungere la numerazione delle ricevute"""
    
    db_path = 'data/database.db'
    
    if not os.path.exists(db_path):
        print("❌ Database non trovato!")
        return False
    
    print("🔄 Avvio migrazione numerazione ricevute...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Aggiungi campo numero_ricevuta alla tabella pagamenti
        print("📝 Aggiunta campo numero_ricevuta alla tabella pagamenti...")
        try:
            cursor.execute("ALTER TABLE pagamenti ADD COLUMN numero_ricevuta INTEGER")
            print("   ✅ Campo numero_ricevuta aggiunto")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️ Campo numero_ricevuta già esistente")
            else:
                raise
        
        # 2. Aggiungi campo numero_ricevuta_iniziale alla tabella settings  
        print("📝 Aggiunta campo numero_ricevuta_iniziale alla tabella settings...")
        try:
            cursor.execute("ALTER TABLE settings ADD COLUMN numero_ricevuta_iniziale INTEGER DEFAULT 1")
            print("   ✅ Campo numero_ricevuta_iniziale aggiunto")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️ Campo numero_ricevuta_iniziale già esistente")
            else:
                raise
        
        # 3. Crea tabella numerazione_ricevute
        print("📝 Creazione tabella numerazione_ricevute...")
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
        print("   ✅ Tabella numerazione_ricevute creata")
        
        # 4. Assegna numeri ricevuta ai pagamenti già esistenti (solo quelli pagati)
        print("📝 Assegnazione numeri ricevuta ai pagamenti esistenti...")
        
        # Ottieni tutti i pagamenti pagati senza numero ricevuta, ordinati per data_pagamento
        cursor.execute("""
            SELECT id, data_pagamento 
            FROM pagamenti 
            WHERE pagato = 1 AND numero_ricevuta IS NULL 
            AND data_pagamento IS NOT NULL
            ORDER BY data_pagamento ASC
        """)
        
        pagamenti_da_numerare = cursor.fetchall()
        
        if pagamenti_da_numerare:
            print(f"   📊 Trovati {len(pagamenti_da_numerare)} pagamenti da numerare")
            
            # Raggruppa per anno
            pagamenti_per_anno = {}
            for pagamento_id, data_pagamento in pagamenti_da_numerare:
                # Converti stringa data in datetime
                if isinstance(data_pagamento, str):
                    try:
                        data_obj = datetime.fromisoformat(data_pagamento.replace('Z', '+00:00'))
                    except:
                        data_obj = datetime.strptime(data_pagamento, '%Y-%m-%d %H:%M:%S')
                else:
                    data_obj = data_pagamento
                
                anno = data_obj.year
                if anno not in pagamenti_per_anno:
                    pagamenti_per_anno[anno] = []
                pagamenti_per_anno[anno].append(pagamento_id)
            
            # Per ogni anno, crea record numerazione e assegna numeri
            for anno, pagamenti_ids in pagamenti_per_anno.items():
                print(f"   🗓️ Anno {anno}: {len(pagamenti_ids)} pagamenti")
                
                # Crea record numerazione per l'anno
                cursor.execute("""
                    INSERT OR IGNORE INTO numerazione_ricevute 
                    (anno, ultimo_numero, numero_iniziale, data_creazione, data_aggiornamento)
                    VALUES (?, 0, 1, ?, ?)
                """, (anno, datetime.now(), datetime.now()))
                
                # Assegna numeri progressivi
                for i, pagamento_id in enumerate(pagamenti_ids, 1):
                    cursor.execute("""
                        UPDATE pagamenti 
                        SET numero_ricevuta = ? 
                        WHERE id = ?
                    """, (i, pagamento_id))
                
                # Aggiorna ultimo numero utilizzato
                cursor.execute("""
                    UPDATE numerazione_ricevute 
                    SET ultimo_numero = ?, data_aggiornamento = ?
                    WHERE anno = ?
                """, (len(pagamenti_ids), datetime.now(), anno))
                
                print(f"   ✅ Assegnati numeri 1-{len(pagamenti_ids)} per l'anno {anno}")
        
        else:
            print("   ℹ️ Nessun pagamento esistente da numerare")
        
        # 5. Aggiorna settings esistenti per includere numero_ricevuta_iniziale
        cursor.execute("UPDATE settings SET numero_ricevuta_iniziale = 1 WHERE numero_ricevuta_iniziale IS NULL")
        
        # Commit delle modifiche
        conn.commit()
        print("✅ Migrazione completata con successo!")
        
        # Mostra riepilogo
        cursor.execute("SELECT COUNT(*) FROM pagamenti WHERE numero_ricevuta IS NOT NULL")
        pagamenti_numerati = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM numerazione_ricevute")
        anni_configurati = cursor.fetchone()[0]
        
        print(f"📊 Riepilogo:")
        print(f"   - Pagamenti con numero ricevuta: {pagamenti_numerati}")
        print(f"   - Anni configurati: {anni_configurati}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🎭 DANCE2MANAGE - MIGRAZIONE NUMERAZIONE RICEVUTE")
    print("=" * 60)
    
    # Conferma dall'utente
    risposta = input("⚠️ Questa operazione modificherà il database. Continuare? (s/N): ")
    if risposta.lower() not in ['s', 'si', 'y', 'yes']:
        print("❌ Migrazione annullata dall'utente")
        sys.exit(1)
    
    # Backup del database
    db_path = 'data/database.db'
    backup_path = f'data/database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backup creato: {backup_path}")
    except Exception as e:
        print(f"⚠️ Impossibile creare backup: {e}")
        risposta = input("Continuare comunque? (s/N): ")
        if risposta.lower() not in ['s', 'si', 'y', 'yes']:
            print("❌ Migrazione annullata")
            sys.exit(1)
    
    # Esegui migrazione
    success = migrate_database()
    
    if success:
        print("\n🎉 Migrazione completata! Il sistema di numerazione ricevute è ora attivo.")
        print("📋 Prossimi passi:")
        print("   1. Riavvia l'applicazione")
        print("   2. Vai in Impostazioni Azienda per configurare il numero iniziale delle ricevute")
        print("   3. I nuovi pagamenti riceveranno automaticamente un numero ricevuta")
    else:
        print("\n❌ Migrazione fallita. Controlla i log per dettagli.")
        if os.path.exists(backup_path):
            print(f"💾 Puoi ripristinare il backup da: {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()