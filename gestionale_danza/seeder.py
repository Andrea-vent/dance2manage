# seeder.py - Script per popolare il database con dati di prova
import sys
import os
from datetime import datetime, time, date
from flask import Flask

# Aggiunta del path per importare i modelli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Cliente, Corso, Insegnante, Pagamento

def create_app():
    """Crea app Flask per seeding"""
    app = Flask(__name__)
    
    # Configurazione database
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def seed_database():
    """Popola il database con dati di prova"""
    print("[SEED] Inizio seeding del database...")
    
    # Crea le tabelle se non esistono
    db.create_all()
    
    # 1. Crea utente admin se non esiste
    print("[ADMIN] Creazione utente admin...")
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("   [OK] Utente admin creato")
    else:
        print("   [EXIST] Utente admin già esistente")
    
    # 2. Crea insegnanti
    print("[INSEGNANTI] Creazione insegnanti...")
    insegnanti_data = [
        {"nome": "Maria", "cognome": "Rossi", "telefono": "3471234567", "email": "maria.rossi@scuoladanza.it", "percentuale_guadagno": 35.0},
        {"nome": "Giulia", "cognome": "Bianchi", "telefono": "3489876543", "email": "giulia.bianchi@scuoladanza.it", "percentuale_guadagno": 30.0},
        {"nome": "Francesco", "cognome": "Verdi", "telefono": "3495551234", "email": "francesco.verdi@scuoladanza.it", "percentuale_guadagno": 40.0},
        {"nome": "Elena", "cognome": "Neri", "telefono": "3467778899", "email": "elena.neri@scuoladanza.it", "percentuale_guadagno": 25.0},
    ]
    
    insegnanti = []
    for data in insegnanti_data:
        if not Insegnante.query.filter_by(email=data["email"]).first():
            insegnante = Insegnante(**data)
            db.session.add(insegnante)
            insegnanti.append(insegnante)
            print(f"   [OK] Insegnante {data['nome']} {data['cognome']} creato")
        else:
            insegnante = Insegnante.query.filter_by(email=data["email"]).first()
            insegnanti.append(insegnante)
            print(f"   [EXIST] Insegnante {data['nome']} {data['cognome']} già esistente")
    
    db.session.commit()
    
    # 3. Crea corsi
    print("[CORSI] Creazione corsi...")
    corsi_data = [
        {"nome": "Danza Classica Principianti", "giorno": "Lunedì", "orario": time(17, 0), "max_iscritti": 15, "insegnante": insegnanti[0]},
        {"nome": "Danza Moderna", "giorno": "Martedì", "orario": time(18, 30), "max_iscritti": 12, "insegnante": insegnanti[1]},
        {"nome": "Hip Hop Junior", "giorno": "Mercoledì", "orario": time(16, 30), "max_iscritti": 20, "insegnante": insegnanti[2]},
        {"nome": "Danza Classica Avanzato", "giorno": "Giovedì", "orario": time(19, 0), "max_iscritti": 10, "insegnante": insegnanti[0]},
        {"nome": "Contemporaneo", "giorno": "Venerdì", "orario": time(17, 30), "max_iscritti": 14, "insegnante": insegnanti[1]},
        {"nome": "Ballo Latino", "giorno": "Sabato", "orario": time(10, 0), "max_iscritti": 16, "insegnante": insegnanti[3]},
    ]
    
    corsi = []
    for data in corsi_data:
        if not Corso.query.filter_by(nome=data["nome"]).first():
            corso = Corso(
                nome=data["nome"],
                giorno=data["giorno"], 
                orario=data["orario"],
                max_iscritti=data["max_iscritti"],
                insegnante_id=data["insegnante"].id
            )
            db.session.add(corso)
            corsi.append(corso)
            print(f"   [OK] Corso {data['nome']} creato")
        else:
            corso = Corso.query.filter_by(nome=data["nome"]).first()
            corsi.append(corso)
            print(f"   [EXIST] Corso {data['nome']} già esistente")
    
    db.session.commit()
    
    # 4. Crea clienti
    print("[CLIENTI] Creazione clienti...")
    clienti_data = [
        {"nome": "Anna", "cognome": "Martini", "codice_fiscale": "MRTANN95M45H501X", "telefono": "3401234567", "email": "anna.martini@email.it"},
        {"nome": "Sofia", "cognome": "Romano", "codice_fiscale": "RMNSFO02A41H501Y", "telefono": "3412345678", "email": "sofia.romano@email.it"},
        {"nome": "Marco", "cognome": "Ferrari", "codice_fiscale": "FRRMRC88D15H501Z", "telefono": "3423456789", "email": "marco.ferrari@email.it"},
        {"nome": "Giulia", "cognome": "Costa", "codice_fiscale": "CSTGLI90T42H501W", "telefono": "3434567890", "email": "giulia.costa@email.it"},
        {"nome": "Luca", "cognome": "Ricci", "codice_fiscale": "RCCLCU85H10H501V", "telefono": "3445678901", "email": "luca.ricci@email.it"},
        {"nome": "Chiara", "cognome": "Galli", "codice_fiscale": "GLLCHR92S52H501U", "telefono": "3456789012", "email": "chiara.galli@email.it"},
        {"nome": "Matteo", "cognome": "Conti", "codice_fiscale": "CNTMTT87A20H501T", "telefono": "3467890123", "email": "matteo.conti@email.it"},
        {"nome": "Federica", "cognome": "Marini", "codice_fiscale": "MRNFRC93E45H501S", "telefono": "3478901234", "email": "federica.marini@email.it"},
        {"nome": "Alessandro", "cognome": "Greco", "codice_fiscale": "GRCALS89M12H501R", "telefono": "3489012345", "email": "alessandro.greco@email.it"},
        {"nome": "Valentina", "cognome": "Villa", "codice_fiscale": "VLLVNT91C48H501Q", "telefono": "3490123456", "email": "valentina.villa@email.it"},
    ]
    
    clienti = []
    for data in clienti_data:
        if not Cliente.query.filter_by(email=data["email"]).first():
            cliente = Cliente(**data)
            db.session.add(cliente)
            clienti.append(cliente)
            print(f"   [OK] Cliente {data['nome']} {data['cognome']} creato")
        else:
            cliente = Cliente.query.filter_by(email=data["email"]).first()
            clienti.append(cliente)
            print(f"   [EXIST] Cliente {data['nome']} {data['cognome']} già esistente")
    
    db.session.commit()
    
    # 5. Assegna clienti ai corsi (relazione many-to-many)
    print("[ISCRIZIONI] Assegnazione clienti ai corsi...")
    assegnazioni = [
        (clienti[0], [corsi[0], corsi[1]]),  # Anna: Classica Principianti + Moderna
        (clienti[1], [corsi[2]]),            # Sofia: Hip Hop Junior
        (clienti[2], [corsi[0]]),            # Marco: Classica Principianti  
        (clienti[3], [corsi[1], corsi[4]]),  # Giulia: Moderna + Contemporaneo
        (clienti[4], [corsi[2], corsi[5]]),  # Luca: Hip Hop + Latino
        (clienti[5], [corsi[3]]),            # Chiara: Classica Avanzato
        (clienti[6], [corsi[4]]),            # Matteo: Contemporaneo
        (clienti[7], [corsi[0], corsi[5]]),  # Federica: Classica Principianti + Latino
        (clienti[8], [corsi[2]]),            # Alessandro: Hip Hop Junior
        (clienti[9], [corsi[1]]),            # Valentina: Moderna
    ]
    
    for cliente, corso_list in assegnazioni:
        if not cliente.corsi:  # Solo se non ha già corsi assegnati
            cliente.corsi = corso_list
            corso_nomi = [c.nome for c in corso_list]
            print(f"   [OK] {cliente.nome_completo} iscritto a: {', '.join(corso_nomi)}")
        else:
            print(f"   [EXIST] {cliente.nome_completo} ha già corsi assegnati")
    
    db.session.commit()
    
    # 6. Crea pagamenti (alcuni pagati, alcuni no)
    print("[PAGAMENTI] Creazione pagamenti...")
    mese_corrente = date.today().month
    anno_corrente = date.today().year
    
    pagamenti_creati = 0
    for cliente in clienti:
        for corso in cliente.corsi:
            # Pagamento mese corrente
            if not Pagamento.query.filter_by(cliente_id=cliente.id, corso_id=corso.id, 
                                            mese=mese_corrente, anno=anno_corrente).first():
                pagamento = Pagamento(
                    mese=mese_corrente,
                    anno=anno_corrente,
                    importo=60.0,  # Quota standard
                    cliente_id=cliente.id,
                    corso_id=corso.id,
                    pagato=(pagamenti_creati % 3 != 0),  # 2/3 pagati, 1/3 non pagati
                    data_pagamento=datetime.now() if (pagamenti_creati % 3 != 0) else None,
                    note="Pagamento mensile" if (pagamenti_creati % 2 == 0) else None
                )
                db.session.add(pagamento)
                stato = "pagato" if pagamento.pagato else "non pagato"
                print(f"   [OK] Pagamento {cliente.nome_completo} - {corso.nome}: €60 ({stato})")
                pagamenti_creati += 1
            
            # Pagamento mese precedente (tutti pagati)
            mese_prec = mese_corrente - 1 if mese_corrente > 1 else 12
            anno_prec = anno_corrente if mese_corrente > 1 else anno_corrente - 1
            
            if not Pagamento.query.filter_by(cliente_id=cliente.id, corso_id=corso.id,
                                            mese=mese_prec, anno=anno_prec).first():
                pagamento_prec = Pagamento(
                    mese=mese_prec,
                    anno=anno_prec,
                    importo=60.0,
                    cliente_id=cliente.id,
                    corso_id=corso.id,
                    pagato=True,
                    data_pagamento=datetime(anno_prec, mese_prec, 15, 14, 30),
                    note="Pagamento mensile precedente"
                )
                db.session.add(pagamento_prec)
    
    db.session.commit()
    
    # 7. Statistiche finali
    print("\n[STATS] Statistiche database:")
    print(f"   Utenti: {User.query.count()}")
    print(f"   Insegnanti: {Insegnante.query.count()}")
    print(f"   Corsi: {Corso.query.count()}")
    print(f"   Clienti: {Cliente.query.count()}")
    print(f"   Pagamenti: {Pagamento.query.count()}")
    
    # Statistiche pagamenti
    pagamenti_pagati = Pagamento.query.filter_by(pagato=True).count()
    pagamenti_non_pagati = Pagamento.query.filter_by(pagato=False).count()
    incasso_totale = sum([p.importo for p in Pagamento.query.filter_by(pagato=True).all()])
    debiti_totali = sum([p.importo for p in Pagamento.query.filter_by(pagato=False).all()])
    
    print(f"   Pagamenti pagati: {pagamenti_pagati} (Euro {incasso_totale:.2f})")
    print(f"   Pagamenti non pagati: {pagamenti_non_pagati} (Euro {debiti_totali:.2f})")
    
    print("\n[SUCCESS] Seeding completato con successo!")
    print("\n[LOGIN] Credenziali:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n[RUN] Avvia l'app con: python app.py")

def reset_database():
    """Cancella tutti i dati e ricrea il database"""
    print("[RESET] Reset database...")
    db.drop_all()
    db.create_all()
    print("[OK] Database resettato")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            reset_database()
        
        seed_database()