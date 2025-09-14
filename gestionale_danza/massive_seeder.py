# massive_seeder.py - Script unificato per caricamento massivo di dati di test
import sys
import os
from datetime import datetime, time, date, timedelta
import random
from faker import Faker
import sqlite3

# Aggiunta del path per importare i modelli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Role, Cliente, Corso, Insegnante, Pagamento, Settings
from flask_security import SQLAlchemyUserDatastore

# Configura Faker per dati italiani
fake = Faker('it_IT')

def create_app():
    """Crea app Flask per seeding"""
    from flask import Flask
    
    app = Flask(__name__)
    
    # Configurazione database
    base_path = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(base_path, 'data', 'database.db')
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'massive-seed-key'
    
    # Configurazioni Flask-Security
    app.config['SECURITY_REGISTERABLE'] = False
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECURITY_PASSWORD_SALT'] = 'massive-seed-salt'
    app.config['SECURITY_JOIN_USER_ROLES'] = True
    
    db.init_app(app)
    return app

def reset_database(app):
    """Reset completo del database"""
    print("🗑️  [RESET] Reset completo database...")
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database resettato e tabelle ricreate")

def create_massive_data(app, num_clients=500, num_courses=50, num_teachers=20, years_data=3):
    """Crea massicciamente dati di test"""
    
    with app.app_context():
        print(f"🚀 [START] Inizio caricamento massivo dati...")
        print(f"📊 Target: {num_clients} clienti, {num_courses} corsi, {num_teachers} insegnanti, {years_data} anni di dati")
        
        # 1. SETUP SECURITY E ADMIN
        print("\n👤 [SECURITY] Configurazione utenti e ruoli...")
        
        # Crea ruoli
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Amministratore sistema')
            db.session.add(admin_role)
        
        user_role = Role.query.filter_by(name='user').first()  
        if not user_role:
            user_role = Role(name='user', description='Utente normale')
            db.session.add(user_role)
        
        db.session.commit()
        
        # Crea user_datastore
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        
        # Crea admin
        if not user_datastore.find_user(email='admin@dance2manage.com'):
            admin_user = user_datastore.create_user(
                email='admin@dance2manage.com',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='Sistema',
                active=True
            )
            user_datastore.add_role_to_user(admin_user, admin_role)
            print("✅ Utente admin creato")
        
        db.session.commit()
        
        # 2. IMPOSTAZIONI GLOBALI
        print("\n⚙️  [SETTINGS] Configurazione impostazioni...")
        settings = Settings.get_settings()
        settings.denominazione_sociale = "Dance Academy Pro"
        settings.partita_iva = "IT12345678901"
        settings.codice_fiscale = "DNCP123456789"
        settings.via = "Via della Danza"
        settings.civico = "123"
        settings.cap = "20100"
        settings.citta = "Milano"
        settings.provincia = "MI"
        settings.telefono = "02-12345678"
        settings.email = "info@danceacademy.it"
        settings.note = "Seeded con dati massivi per test di carico"
        db.session.commit()
        print("✅ Impostazioni configurate")
        
        # 3. INSEGNANTI
        print(f"\n👨‍🏫 [TEACHERS] Creazione {num_teachers} insegnanti...")
        
        specialita_danza = [
            "Danza Classica", "Danza Moderna", "Hip Hop", "Jazz", "Contemporaneo",
            "Ballo Latino", "Tango", "Salsa", "Bachata", "Kizomba", "Pilates",
            "Danza del Ventre", "Flamenco", "Breakdance", "Street Dance",
            "Pole Dance", "Aerial", "Musical Theatre", "Tap Dance", "Swing"
        ]
        
        insegnanti = []
        for i in range(num_teachers):
            nome = fake.first_name()
            cognome = fake.last_name()
            
            insegnante = Insegnante(
                nome=nome,
                cognome=cognome,
                telefono=fake.phone_number(),
                email=f"{nome.lower()}.{cognome.lower()}@dance.academy.it",
                percentuale_guadagno=round(random.uniform(20.0, 45.0), 1),
                via=fake.street_name(),
                civico=str(fake.building_number()),
                cap=fake.postcode(),
                citta=fake.city(),
                provincia=fake.state_abbr(),
                codice_fiscale=fake.ssn()
            )
            db.session.add(insegnante)
            insegnanti.append(insegnante)
            
            if (i + 1) % 5 == 0:
                print(f"   📝 Creati {i + 1}/{num_teachers} insegnanti...")
        
        db.session.commit()
        print(f"✅ {len(insegnanti)} insegnanti creati")
        
        # 4. CORSI
        print(f"\n🏫 [COURSES] Creazione {num_courses} corsi...")
        
        tipi_corso = [
            "Danza Classica Principianti", "Danza Classica Intermedio", "Danza Classica Avanzato",
            "Danza Moderna Principianti", "Danza Moderna Intermedio", "Danza Moderna Avanzato", 
            "Hip Hop Kids", "Hip Hop Teen", "Hip Hop Adulti",
            "Jazz Dance Principianti", "Jazz Dance Intermedio",
            "Contemporaneo Base", "Contemporaneo Avanzato",
            "Ballo Latino Principianti", "Ballo Latino Intermedio",
            "Salsa Cubana", "Bachata Sensual", "Kizomba",
            "Tango Argentino", "Pilates per Danzatori",
            "Danza del Ventre", "Flamenco", "Breakdance",
            "Street Dance", "Pole Dance Base", "Pole Dance Avanzato",
            "Aerial Silk", "Musical Theatre", "Tap Dance",
            "Swing Dance", "Lindy Hop", "Charleston",
            "Danza Afro", "Reggaeton", "Commercial Dance",
            "Lyrical Jazz", "Heels Dance", "Vogue",
            "Danza Irlandese", "Danza Indiana", "Belly Dance Fusion",
            "Contact Improvisation", "Release Technique", "Cunningham",
            "Graham Technique", "Horton", "Limón",
            "Gaga Movement", "Floor Work", "Partnering",
            "Composition", "Dance Theatre", "Performance Skills"
        ]
        
        giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        orari_possibili = [
            time(9, 0), time(10, 0), time(11, 0), time(14, 30), time(15, 30),
            time(16, 0), time(16, 30), time(17, 0), time(17, 30), time(18, 0),
            time(18, 30), time(19, 0), time(19, 30), time(20, 0), time(20, 30),
            time(21, 0)
        ]
        
        corsi = []
        for i in range(num_courses):
            corso = Corso(
                nome=random.choice(tipi_corso),
                giorno=random.choice(giorni_settimana),
                orario=random.choice(orari_possibili),
                max_iscritti=random.randint(8, 25),
                insegnante_id=random.choice(insegnanti).id,
                costo_mensile=random.choice([45, 50, 60, 70, 80, 90, 100, 120]),
                data_creazione=fake.date_between(start_date='-2y', end_date='today')
            )
            db.session.add(corso)
            corsi.append(corso)
            
            if (i + 1) % 10 == 0:
                print(f"   📝 Creati {i + 1}/{num_courses} corsi...")
        
        db.session.commit()
        print(f"✅ {len(corsi)} corsi creati")
        
        # 5. CLIENTI
        print(f"\n👥 [CLIENTS] Creazione {num_clients} clienti...")
        
        clienti = []
        for i in range(num_clients):
            nome = fake.first_name()
            cognome = fake.last_name()
            
            # Genera codice fiscale casuale (pattern italiano)
            cf_letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=6))
            cf_numbers = ''.join(random.choices('0123456789', k=2))
            cf_month = random.choice(['A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T'])
            cf_day = f"{random.randint(1, 31):02d}"
            cf_place = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
            cf_check = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            codice_fiscale = f"{cf_letters}{cf_numbers}{cf_month}{cf_day}{cf_place}{cf_check}"
            
            cliente = Cliente(
                nome=nome,
                cognome=cognome,
                codice_fiscale=codice_fiscale if random.random() > 0.3 else None,  # 70% hanno CF
                telefono=fake.phone_number(),
                email=f"{nome.lower()}.{cognome.lower()}{random.randint(1,999)}@email.it",
                via=fake.street_name(),
                civico=str(fake.building_number()),
                cap=fake.postcode(),
                citta=fake.city(),
                provincia=fake.state_abbr(),
                attivo=random.choice([True, True, True, True, False])  # 80% attivi
            )
            db.session.add(cliente)
            clienti.append(cliente)
            
            if (i + 1) % 50 == 0:
                print(f"   📝 Creati {i + 1}/{num_clients} clienti...")
        
        db.session.commit()
        print(f"✅ {len(clienti)} clienti creati")
        
        # 6. ISCRIZIONI AI CORSI (RELAZIONI MANY-TO-MANY)
        print("\n🔗 [ENROLLMENTS] Creazione iscrizioni ai corsi...")
        iscrizioni_totali = 0
        
        for cliente in clienti:
            # Ogni cliente si iscrive a 1-4 corsi (distribuzione realistica)
            num_corsi_cliente = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5], k=1)[0]
            corsi_cliente = random.sample(corsi, min(num_corsi_cliente, len(corsi)))
            cliente.corsi = corsi_cliente
            iscrizioni_totali += len(corsi_cliente)
        
        db.session.commit()
        print(f"✅ {iscrizioni_totali} iscrizioni create")
        
        # 7. PAGAMENTI STORICI (ANNI PRECEDENTI)
        print(f"\n💰 [PAYMENTS] Creazione pagamenti per {years_data} anni...")
        
        anni_da_creare = []
        anno_corrente = date.today().year
        for i in range(years_data):
            anni_da_creare.append(anno_corrente - i)
        
        metodi_pagamento = ["Contanti", "Carta", "Bonifico", "PayPal", "Assegno"]
        
        pagamenti_totali = 0
        
        for anno in anni_da_creare:
            print(f"   📅 Creando pagamenti per anno {anno}...")
            
            for mese in range(1, 13):  # Tutti i mesi
                mese_pagamenti = 0
                
                for cliente in clienti:
                    for corso in cliente.corsi:
                        # Probabilità di pagamento per mese (simulazione realistica)
                        probabilita_pagamento = 0.85 if anno == anno_corrente else 0.95
                        
                        if random.random() < probabilita_pagamento:
                            # Verifica che non esista già
                            pagamento_esistente = Pagamento.query.filter_by(
                                cliente_id=cliente.id,
                                corso_id=corso.id,
                                mese=mese,
                                anno=anno
                            ).first()
                            
                            if not pagamento_esistente:
                                # Varia leggermente l'importo del corso
                                importo_base = corso.costo_mensile or 60
                                variazione = random.uniform(0.9, 1.1)  # ±10%
                                importo = round(importo_base * variazione, 2)
                                
                                # Probabilità di essere pagato (più alta per anni passati)
                                probabilita_pagato = 0.95 if anno < anno_corrente else 0.8
                                pagato = random.random() < probabilita_pagato
                                
                                data_pagamento = None
                                if pagato:
                                    # Data casuale nel mese
                                    try:
                                        start_date = date(anno, mese, 1)
                                        if mese == 12:
                                            end_date = date(anno + 1, 1, 1) - timedelta(days=1)
                                        else:
                                            end_date = date(anno, mese + 1, 1) - timedelta(days=1)
                                        
                                        data_pagamento = fake.date_between(start_date=start_date, end_date=end_date)
                                    except:
                                        data_pagamento = date(anno, mese, 15)
                                
                                pagamento = Pagamento(
                                    mese=mese,
                                    anno=anno,
                                    importo=importo,
                                    cliente_id=cliente.id,
                                    corso_id=corso.id,
                                    pagato=pagato,
                                    data_pagamento=data_pagamento,
                                    metodo_pagamento=random.choice(metodi_pagamento) if pagato else None,
                                    note=fake.text(max_nb_chars=30) if random.random() > 0.8 else None
                                )
                                
                                db.session.add(pagamento)
                                mese_pagamenti += 1
                                pagamenti_totali += 1
                
                # Commit ogni mese per evitare timeout
                db.session.commit()
                if mese_pagamenti > 0:
                    print(f"      📝 Mese {mese:02d}/{anno}: {mese_pagamenti} pagamenti")
        
        print(f"✅ {pagamenti_totali} pagamenti creati per {years_data} anni")
        
        # 8. STATISTICHE FINALI E PERFORMANCE TEST
        print("\n📊 [STATS] Calcolo statistiche finali...")
        
        try:
            # Test performance query complesse
            start_time = datetime.now()
            
            stats = {
                'utenti': User.query.count(),
                'insegnanti': Insegnante.query.count(),
                'insegnanti_attivi': Insegnante.query.filter_by(attivo=True).count(),
                'corsi': Corso.query.count(),
                'clienti': Cliente.query.count(),
                'clienti_attivi': Cliente.query.filter_by(attivo=True).count(),
                'pagamenti_totali': Pagamento.query.count(),
                'pagamenti_pagati': Pagamento.query.filter_by(pagato=True).count(),
                'pagamenti_non_pagati': Pagamento.query.filter_by(pagato=False).count(),
                'iscrizioni_totali': sum([len(c.corsi) for c in clienti])
            }
            
            # Calcoli finanziari
            all_payments = Pagamento.query.filter_by(pagato=True).all()
            incasso_totale = sum([p.importo for p in all_payments])
            debiti_totali = sum([p.importo for p in Pagamento.query.filter_by(pagato=False).all()])
            
            # Performance query per anno corrente
            pagamenti_anno_corrente = Pagamento.query.filter_by(anno=anno_corrente).count()
            incasso_anno_corrente = sum([p.importo for p in Pagamento.query.filter(
                Pagamento.anno == anno_corrente,
                Pagamento.pagato == True
            ).all()])
            
            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()
            
            print(f"\n🎯 [PERFORMANCE] Query statistiche completate in {query_time:.2f} secondi")
            
            print(f"\n📈 [FINAL STATS] Database popolato con successo!")
            print(f"{'='*60}")
            print(f"👤 Utenti sistema: {stats['utenti']}")
            print(f"👨‍🏫 Insegnanti: {stats['insegnanti']} (attivi: {stats['insegnanti_attivi']})")
            print(f"🏫 Corsi: {stats['corsi']}")
            print(f"👥 Clienti: {stats['clienti']} (attivi: {stats['clienti_attivi']})")
            print(f"🔗 Iscrizioni totali: {stats['iscrizioni_totali']}")
            print(f"💰 Pagamenti totali: {stats['pagamenti_totali']}")
            print(f"✅ Pagamenti pagati: {stats['pagamenti_pagati']} (€{incasso_totale:,.2f})")
            print(f"⏳ Pagamenti non pagati: {stats['pagamenti_non_pagati']} (€{debiti_totali:,.2f})")
            print(f"📅 Pagamenti {anno_corrente}: {pagamenti_anno_corrente} (€{incasso_anno_corrente:,.2f})")
            print(f"{'='*60}")
            
            # Test dimensione database
            database_path = os.path.join(os.path.dirname(__file__), 'data', 'database.db')
            if os.path.exists(database_path):
                size_mb = os.path.getsize(database_path) / (1024 * 1024)
                print(f"💾 Dimensione database: {size_mb:.2f} MB")
            
        except Exception as e:
            print(f"❌ Errore nel calcolo statistiche: {str(e)}")
        
        print(f"\n🚀 [SUCCESS] Caricamento massivo completato!")
        print(f"\n🔑 [LOGIN] Credenziali admin:")
        print(f"   Email: admin@dance2manage.com")
        print(f"   Username: admin")  
        print(f"   Password: admin123")

def test_database_performance(app):
    """Test performance del database con query complesse"""
    print("\n🔥 [PERFORMANCE TEST] Test prestazioni database...")
    
    with app.app_context():
        tests = []
        
        # Test 1: Query semplici
        start = datetime.now()
        client_count = Cliente.query.count()
        tests.append(("Conteggio clienti", (datetime.now() - start).total_seconds()))
        
        # Test 2: Query con JOIN
        start = datetime.now()
        clienti_con_corsi = Cliente.query.join(Cliente.corsi).count()
        tests.append(("Clienti con corsi (JOIN)", (datetime.now() - start).total_seconds()))
        
        # Test 3: Query aggregate complesse
        start = datetime.now()
        incassi_per_mese = db.session.query(
            Pagamento.mese, 
            db.func.sum(Pagamento.importo)
        ).filter(
            Pagamento.pagato == True,
            Pagamento.anno == date.today().year
        ).group_by(Pagamento.mese).all()
        tests.append(("Incassi per mese (GROUP BY)", (datetime.now() - start).total_seconds()))
        
        # Test 4: Query con multiple relazioni
        start = datetime.now()
        report_corsi = db.session.query(Corso).join(Insegnante).join(Corso.clienti).all()[:10]
        tests.append(("Report corsi con relazioni", (datetime.now() - start).total_seconds()))
        
        print("📊 Risultati test performance:")
        for test_name, duration in tests:
            status = "🟢" if duration < 0.1 else "🟡" if duration < 0.5 else "🔴"
            print(f"   {status} {test_name}: {duration:.3f}s")

def main():
    """Funzione principale"""
    print("🎭 DANCE2MANAGE - MASSIVE DATA SEEDER")
    print("="*50)
    
    # Parametri configurabili
    NUM_CLIENTS = 1000      # Numero clienti (default: 1000)
    NUM_COURSES = 80        # Numero corsi (default: 80)
    NUM_TEACHERS = 30       # Numero insegnanti (default: 30)
    YEARS_DATA = 3          # Anni di dati storici (default: 3)
    
    # Parsing argomenti da linea di comando
    if len(sys.argv) > 1:
        try:
            NUM_CLIENTS = int(sys.argv[1])
            if len(sys.argv) > 2:
                NUM_COURSES = int(sys.argv[2])
            if len(sys.argv) > 3:
                NUM_TEACHERS = int(sys.argv[3])
            if len(sys.argv) > 4:
                YEARS_DATA = int(sys.argv[4])
        except ValueError:
            print("❌ Parametri non validi. Uso: python massive_seeder.py [clienti] [corsi] [insegnanti] [anni]")
            return
    
    print(f"🎯 Configurazione: {NUM_CLIENTS} clienti, {NUM_COURSES} corsi, {NUM_TEACHERS} insegnanti, {YEARS_DATA} anni")
    
    # Conferma prima del reset (solo in modalità interattiva)
    if '--auto' not in sys.argv:
        confirm = input("\n⚠️  Questo resetterà COMPLETAMENTE il database. Continuare? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Operazione annullata")
            return
    
    # Crea app
    app = create_app()
    
    try:
        # Reset database
        reset_database(app)
        
        # Carica dati massivi
        create_massive_data(app, NUM_CLIENTS, NUM_COURSES, NUM_TEACHERS, YEARS_DATA)
        
        # Test performance
        test_database_performance(app)
        
        print(f"\n🎉 [COMPLETE] Database popolato e testato con successo!")
        print(f"▶️  Avvia l'applicazione con: python app.py")
        
    except Exception as e:
        print(f"\n❌ [ERROR] Errore durante il seeding: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()