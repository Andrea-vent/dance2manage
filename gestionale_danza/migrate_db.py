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
    
    conn.commit()
    conn.close()
    print("\n✅ Migrazione database completata!")
    
else:
    print("Database non trovato. Verrà creato al primo avvio dell'applicazione.")