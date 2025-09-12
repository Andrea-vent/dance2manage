# populate_test_data.py - Script per aggiungere dati di test
import os
import sys
from datetime import datetime, date
import random

# Aggiungi il percorso dell'applicazione
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Cliente, Corso, Insegnante, Pagamento

def populate_test_data():
    """Popola il database con dati di test per il 2024"""
    
    with app.app_context():
        print("🔄 Popolamento dati di test...")
        
        # Crea alcuni insegnanti se non esistono
        if Insegnante.query.count() == 0:
            insegnanti = [
                Insegnante(nome="Maria", cognome="Rossi", telefono="333-1234567", email="maria.rossi@danza.it", percentuale_guadagno=35.0),
                Insegnante(nome="Luca", cognome="Bianchi", telefono="333-2345678", email="luca.bianchi@danza.it", percentuale_guadagno=30.0),
                Insegnante(nome="Giulia", cognome="Verdi", telefono="333-3456789", email="giulia.verdi@danza.it", percentuale_guadagno=40.0)
            ]
            for ins in insegnanti:
                db.session.add(ins)
            db.session.commit()
            print(f"✅ Creati {len(insegnanti)} insegnanti")
        
        # Crea alcuni corsi se non esistono
        if Corso.query.count() == 0:
            from datetime import time
            corsi = [
                Corso(nome="Danza Classica Bambini", giorno="Lunedì", orario=time(16, 30), max_iscritti=15, insegnante_id=1),
                Corso(nome="Hip Hop Adolescenti", giorno="Martedì", orario=time(18, 0), max_iscritti=20, insegnante_id=2),
                Corso(nome="Danza Moderna Adulti", giorno="Mercoledì", orario=time(20, 0), max_iscritti=12, insegnante_id=1),
                Corso(nome="Ballo Latino", giorno="Giovedì", orario=time(19, 30), max_iscritti=18, insegnante_id=3),
                Corso(nome="Pilates Danza", giorno="Venerdì", orario=time(17, 30), max_iscritti=10, insegnante_id=3),
                Corso(nome="Street Dance", giorno="Sabato", orario=time(15, 0), max_iscritti=16, insegnante_id=2)
            ]
            for corso in corsi:
                db.session.add(corso)
            db.session.commit()
            print(f"✅ Creati {len(corsi)} corsi")
        
        # Crea alcuni clienti se non esistono
        if Cliente.query.count() == 0:
            clienti = [
                Cliente(nome="Anna", cognome="Ferrari", codice_fiscale="FRRNNA85M01H501X", telefono="339-1111111", email="anna.ferrari@email.it", 
                       via="Via Roma", civico="123", cap="20100", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Marco", cognome="Colombo", telefono="339-2222222", email="marco.colombo@email.it",
                       via="Via Dante", civico="45", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Lucia", cognome="Romano", telefono="339-3333333", email="lucia.romano@email.it",
                       via="Corso Buenos Aires", civico="67", cap="20124", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Davide", cognome="Ricci", telefono="339-4444444", email="davide.ricci@email.it",
                       via="Via Brera", civico="89", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Sara", cognome="Galli", telefono="339-5555555", email="sara.galli@email.it",
                       via="Via Montenapoleone", civico="12", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Matteo", cognome="Conti", telefono="339-6666666", email="matteo.conti@email.it",
                       via="Via Garibaldi", civico="34", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Francesca", cognome="Barbieri", telefono="339-7777777", email="francesca.barbieri@email.it",
                       via="Via Torino", civico="56", cap="20123", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Alessandro", cognome="Moretti", telefono="339-8888888", email="alessandro.moretti@email.it",
                       via="Via Venezia", civico="78", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Chiara", cognome="Fontana", telefono="339-9999999", email="chiara.fontana@email.it",
                       via="Via Manzoni", civico="90", cap="20121", citta="Milano", provincia="MI", attivo=True),
                Cliente(nome="Roberto", cognome="Villa", telefono="339-0000000", email="roberto.villa@email.it",
                       via="Via della Spiga", civico="11", cap="20121", citta="Milano", provincia="MI", attivo=True)
            ]
            for cliente in clienti:
                db.session.add(cliente)
            db.session.commit()
            print(f"✅ Creati {len(clienti)} clienti")
        
        # Associa clienti ai corsi casualmente
        clienti = Cliente.query.all()
        corsi = Corso.query.all()
        
        for cliente in clienti:
            if not cliente.corsi:  # Solo se non ha già corsi associati
                # Ogni cliente si iscrive a 1-3 corsi casuali
                num_corsi = random.randint(1, 3)
                corsi_casuali = random.sample(corsi, min(num_corsi, len(corsi)))
                cliente.corsi = corsi_casuali
        
        db.session.commit()
        print(f"✅ Associati clienti ai corsi")
        
        # Crea pagamenti per il 2024 (diversi mesi)
        mesi_2024 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # Escludo dicembre per test
        importi = [50.0, 60.0, 70.0, 80.0, 90.0]  # Importi casuali
        
        pagamenti_creati = 0
        for cliente in clienti:
            for corso in cliente.corsi:
                for mese in mesi_2024:
                    # 80% di probabilità che ci sia un pagamento per ogni mese
                    if random.random() < 0.8:
                        # Verifica se il pagamento non esiste già
                        pagamento_esistente = Pagamento.query.filter_by(
                            cliente_id=cliente.id,
                            corso_id=corso.id,
                            mese=mese,
                            anno=2024
                        ).first()
                        
                        if not pagamento_esistente:
                            importo = random.choice(importi)
                            pagato = random.random() < 0.9  # 90% pagato, 10% non pagato
                            
                            pagamento = Pagamento(
                                mese=mese,
                                anno=2024,
                                importo=importo,
                                cliente_id=cliente.id,
                                corso_id=corso.id,
                                note=f"Pagamento {mese}/2024"
                            )
                            
                            if pagato:
                                pagamento.marca_pagato()
                            
                            db.session.add(pagamento)
                            pagamenti_creati += 1
        
        db.session.commit()
        print(f"✅ Creati {pagamenti_creati} pagamenti per il 2024")
        
        # Statistiche finali
        print("\n📊 STATISTICHE DATABASE:")
        print(f"👥 Clienti: {Cliente.query.count()}")
        print(f"🏫 Corsi: {Corso.query.count()}")
        print(f"👨‍🏫 Insegnanti: {Insegnante.query.count()}")
        print(f"💰 Pagamenti totali: {Pagamento.query.count()}")
        print(f"💰 Pagamenti 2024: {Pagamento.query.filter_by(anno=2024).count()}")
        print(f"✅ Pagamenti pagati 2024: {Pagamento.query.filter_by(anno=2024, pagato=True).count()}")
        print(f"⚠️ Pagamenti non pagati 2024: {Pagamento.query.filter_by(anno=2024, pagato=False).count()}")
        
        print("\n🎉 Popolamento completato!")

if __name__ == '__main__':
    populate_test_data()