# migrate_db.py - Script per aggiornare il database con i nuovi campi indirizzo
import sqlite3
import os

# Percorso database
database_path = os.path.join(os.path.dirname(__file__), 'data', 'database.db')

if os.path.exists(database_path):
    print(f"Aggiornamento database: {database_path}")
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # MIGRAZIONE CLIENTI
    print("\n🔄 Migrazione tabella CLIENTI...")
    cursor.execute("PRAGMA table_info(clienti)")
    clienti_columns = [column[1] for column in cursor.fetchall()]
    
    clienti_new_columns = ['via', 'civico', 'cap', 'citta', 'provincia']
    
    for column in clienti_new_columns:
        if column not in clienti_columns:
            print(f"Aggiungendo colonna clienti.{column}")
            if column == 'provincia':
                cursor.execute(f"ALTER TABLE clienti ADD COLUMN {column} VARCHAR(2)")
            elif column == 'via':
                cursor.execute(f"ALTER TABLE clienti ADD COLUMN {column} VARCHAR(200)")
            elif column in ['civico', 'cap']:
                cursor.execute(f"ALTER TABLE clienti ADD COLUMN {column} VARCHAR(10)")
            else:  # citta
                cursor.execute(f"ALTER TABLE clienti ADD COLUMN {column} VARCHAR(100)")
        else:
            print(f"Colonna clienti.{column} già esistente")
    
    # MIGRAZIONE INSEGNANTI
    print("\n🔄 Migrazione tabella INSEGNANTI...")
    cursor.execute("PRAGMA table_info(insegnanti)")
    insegnanti_columns = [column[1] for column in cursor.fetchall()]
    
    insegnanti_new_columns = ['codice_fiscale', 'via', 'civico', 'cap', 'citta', 'provincia']
    
    for column in insegnanti_new_columns:
        if column not in insegnanti_columns:
            print(f"Aggiungendo colonna insegnanti.{column}")
            if column == 'codice_fiscale':
                cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {column} VARCHAR(16)")
            elif column == 'provincia':
                cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {column} VARCHAR(2)")
            elif column == 'via':
                cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {column} VARCHAR(200)")
            elif column in ['civico', 'cap']:
                cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {column} VARCHAR(10)")
            else:  # citta
                cursor.execute(f"ALTER TABLE insegnanti ADD COLUMN {column} VARCHAR(100)")
        else:
            print(f"Colonna insegnanti.{column} già esistente")
    
    # MIGRAZIONE SETTINGS  
    print("\n🔄 Migrazione tabella SETTINGS...")
    cursor.execute("PRAGMA table_info(settings)")
    settings_columns = [column[1] for column in cursor.fetchall()]
    
    settings_new_columns = ['logo_filename']
    
    for column in settings_new_columns:
        if column not in settings_columns:
            print(f"Aggiungendo colonna settings.{column}")
            cursor.execute(f"ALTER TABLE settings ADD COLUMN {column} VARCHAR(200)")
        else:
            print(f"Colonna settings.{column} già esistente")
    
    # MIGRAZIONE PAGAMENTI
    print("\n🔄 Migrazione tabella PAGAMENTI...")
    cursor.execute("PRAGMA table_info(pagamenti)")
    pagamenti_columns = [column[1] for column in cursor.fetchall()]
    
    pagamenti_new_columns = ['metodo_pagamento']
    
    for column in pagamenti_new_columns:
        if column not in pagamenti_columns:
            print(f"Aggiungendo colonna pagamenti.{column}")
            cursor.execute(f"ALTER TABLE pagamenti ADD COLUMN {column} VARCHAR(50) DEFAULT 'Contanti'")
        else:
            print(f"Colonna pagamenti.{column} già esistente")
    
    # MIGRAZIONE CORSI
    print("\n🔄 Migrazione tabella CORSI...")
    cursor.execute("PRAGMA table_info(corsi)")
    corsi_columns = [column[1] for column in cursor.fetchall()]
    
    corsi_new_columns = ['costo_mensile', 'data_creazione']
    
    for column in corsi_new_columns:
        if column not in corsi_columns:
            print(f"Aggiungendo colonna corsi.{column}")
            if column == 'costo_mensile':
                cursor.execute(f"ALTER TABLE corsi ADD COLUMN {column} INTEGER DEFAULT 50")
            else:  # data_creazione
                cursor.execute(f"ALTER TABLE corsi ADD COLUMN {column} DATETIME")
        else:
            print(f"Colonna corsi.{column} già esistente")
    
    conn.commit()
    conn.close()
    print("\n✅ Migrazione database completata!")
    
else:
    print("Database non trovato. Verrà creato al primo avvio dell'applicazione.")