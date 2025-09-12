# app.py
import os
import sys
import shutil
import zipfile
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Cliente, Corso, Insegnante, Pagamento, Settings
from utils.stampa_pdf import genera_ricevuta_pdf
import tempfile

# Configurazione percorsi per PyInstaller
if getattr(sys, 'frozen', False):
    # Modalità eseguibile
    base_path = os.path.dirname(sys.executable)
    template_folder = os.path.join(base_path, 'templates')
    static_folder = os.path.join(base_path, 'static')
else:
    # Modalità sviluppo
    base_path = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(base_path, 'templates')
    static_folder = os.path.join(base_path, 'static')

# Inizializza Flask
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.secret_key = 'chiave-segreta-danza-2024'

# Configurazione database SQLite
database_path = os.path.join(base_path, 'data', 'database.db')
os.makedirs(os.path.dirname(database_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializza database
db.init_app(app)

# Crea cartelle necessarie
pdf_folder = os.path.join(base_path, 'pdf_ricevute')
os.makedirs(pdf_folder, exist_ok=True)

def init_db():
    """Inizializza il database e crea utente admin se non esiste"""
    with app.app_context():
        db.create_all()
        
        # Crea utente admin se non esiste
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

def login_required(f):
    """Decorator per richiedere autenticazione"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ROUTES

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Accesso effettuato con successo!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenziali non valide', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Disconnessione effettuata', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    # Statistiche dashboard
    total_clienti = Cliente.query.filter_by(attivo=True).count()
    total_corsi = Corso.query.count()
    total_insegnanti = Insegnante.query.count()
    
    # Pagamenti del mese corrente
    mese_corrente = date.today().month
    anno_corrente = date.today().year
    pagamenti_mese = Pagamento.query.filter_by(mese=mese_corrente, anno=anno_corrente).all()
    incasso_mese = sum(p.importo for p in pagamenti_mese if p.pagato)
    debiti_mese = sum(p.importo for p in pagamenti_mese if not p.pagato)
    
    return render_template('dashboard.html', 
                         total_clienti=total_clienti,
                         total_corsi=total_corsi, 
                         total_insegnanti=total_insegnanti,
                         incasso_mese=incasso_mese,
                         debiti_mese=debiti_mese,
                         mese_corrente=mese_corrente,
                         anno_corrente=anno_corrente)

# CLIENTI ROUTES
@app.route('/clienti')
@login_required
def clienti():
    search = request.args.get('search', '')
    stato = request.args.get('stato', 'tutti')
    
    query = Cliente.query
    
    if search:
        query = query.filter(
            (Cliente.nome.contains(search)) | 
            (Cliente.cognome.contains(search)) |
            (Cliente.email.contains(search))
        )
    
    if stato == 'attivi':
        query = query.filter_by(attivo=True)
    elif stato == 'inattivi':
        query = query.filter_by(attivo=False)
    
    clienti = query.all()
    return render_template('clienti.html', clienti=clienti, search=search, stato=stato)

@app.route('/clienti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_cliente():
    if request.method == 'POST':
        cliente = Cliente(
            nome=request.form['nome'],
            cognome=request.form['cognome'],
            codice_fiscale=request.form.get('codice_fiscale', '').upper() or None,
            telefono=request.form['telefono'],
            email=request.form['email'],
            via=request.form.get('via', ''),
            civico=request.form.get('civico', ''),
            cap=request.form.get('cap', ''),
            citta=request.form.get('citta', ''),
            provincia=request.form.get('provincia', '').upper() or None,
            attivo=bool(request.form.get('attivo'))
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente creato con successo!', 'success')
        return redirect(url_for('clienti'))
    
    corsi = Corso.query.all()
    return render_template('cliente_form.html', cliente=None, corsi=corsi)

@app.route('/clienti/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.cognome = request.form['cognome']
        cliente.codice_fiscale = request.form.get('codice_fiscale', '').upper() or None
        cliente.telefono = request.form['telefono']
        cliente.email = request.form['email']
        cliente.via = request.form.get('via', '')
        cliente.civico = request.form.get('civico', '')
        cliente.cap = request.form.get('cap', '')
        cliente.citta = request.form.get('citta', '')
        cliente.provincia = request.form.get('provincia', '').upper() or None
        cliente.attivo = bool(request.form.get('attivo'))
        
        # Gestione corsi associati
        corsi_ids = request.form.getlist('corsi')
        cliente.corsi = [Corso.query.get(int(cid)) for cid in corsi_ids]
        
        db.session.commit()
        flash('Cliente modificato con successo!', 'success')
        return redirect(url_for('clienti'))
    
    corsi = Corso.query.all()
    return render_template('cliente_form.html', cliente=cliente, corsi=corsi)

@app.route('/clienti/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminato con successo!', 'success')
    return redirect(url_for('clienti'))

# CORSI ROUTES
@app.route('/corsi')
@login_required
def corsi():
    corsi = Corso.query.all()
    return render_template('corsi.html', corsi=corsi)

@app.route('/corsi/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_corso():
    if request.method == 'POST':
        from datetime import datetime
        orario = datetime.strptime(request.form['orario'], '%H:%M').time()
        
        corso = Corso(
            nome=request.form['nome'],
            giorno=request.form['giorno'],
            orario=orario,
            max_iscritti=int(request.form['max_iscritti']),
            insegnante_id=int(request.form['insegnante_id'])
        )
        db.session.add(corso)
        db.session.commit()
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('corsi'))
    
    insegnanti = Insegnante.query.all()
    return render_template('corso_form.html', corso=None, insegnanti=insegnanti)

@app.route('/corsi/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_corso(id):
    corso = Corso.query.get_or_404(id)
    
    if request.method == 'POST':
        from datetime import datetime
        orario = datetime.strptime(request.form['orario'], '%H:%M').time()
        
        corso.nome = request.form['nome']
        corso.giorno = request.form['giorno']
        corso.orario = orario
        corso.max_iscritti = int(request.form['max_iscritti'])
        corso.insegnante_id = int(request.form['insegnante_id'])
        
        db.session.commit()
        flash('Corso modificato con successo!', 'success')
        return redirect(url_for('corsi'))
    
    insegnanti = Insegnante.query.all()
    return render_template('corso_form.html', corso=corso, insegnanti=insegnanti)

@app.route('/corsi/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_corso(id):
    corso = Corso.query.get_or_404(id)
    db.session.delete(corso)
    db.session.commit()
    flash('Corso eliminato con successo!', 'success')
    return redirect(url_for('corsi'))

# INSEGNANTI ROUTES
@app.route('/insegnanti')
@login_required
def insegnanti():
    insegnanti = Insegnante.query.all()
    return render_template('insegnanti.html', insegnanti=insegnanti)

@app.route('/insegnanti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_insegnante():
    if request.method == 'POST':
        insegnante = Insegnante(
            nome=request.form['nome'],
            cognome=request.form['cognome'],
            codice_fiscale=request.form.get('codice_fiscale', '').upper() or None,
            telefono=request.form['telefono'],
            email=request.form['email'],
            via=request.form.get('via', ''),
            civico=request.form.get('civico', ''),
            cap=request.form.get('cap', ''),
            citta=request.form.get('citta', ''),
            provincia=request.form.get('provincia', '').upper() or None,
            percentuale_guadagno=float(request.form.get('percentuale_guadagno', 30.0))
        )
        db.session.add(insegnante)
        db.session.commit()
        flash('Insegnante creato con successo!', 'success')
        return redirect(url_for('insegnanti'))
    
    return render_template('insegnante_form.html', insegnante=None)

@app.route('/insegnanti/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_insegnante(id):
    insegnante = Insegnante.query.get_or_404(id)
    
    if request.method == 'POST':
        insegnante.nome = request.form['nome']
        insegnante.cognome = request.form['cognome']
        insegnante.codice_fiscale = request.form.get('codice_fiscale', '').upper() or None
        insegnante.telefono = request.form['telefono']
        insegnante.email = request.form['email']
        insegnante.via = request.form.get('via', '')
        insegnante.civico = request.form.get('civico', '')
        insegnante.cap = request.form.get('cap', '')
        insegnante.citta = request.form.get('citta', '')
        insegnante.provincia = request.form.get('provincia', '').upper() or None
        insegnante.percentuale_guadagno = float(request.form.get('percentuale_guadagno', 30.0))
        
        db.session.commit()
        flash('Insegnante modificato con successo!', 'success')
        return redirect(url_for('insegnanti'))
    
    return render_template('insegnante_form.html', insegnante=insegnante)

@app.route('/insegnanti/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_insegnante(id):
    insegnante = Insegnante.query.get_or_404(id)
    db.session.delete(insegnante)
    db.session.commit()
    flash('Insegnante eliminato con successo!', 'success')
    return redirect(url_for('insegnanti'))

# PAGAMENTI ROUTES
@app.route('/pagamenti')
@login_required
def pagamenti():
    mese = request.args.get('mese', date.today().month, type=int)
    anno = request.args.get('anno', date.today().year, type=int)
    cliente_id = request.args.get('cliente_id', type=int)
    corso_id = request.args.get('corso_id', type=int)
    
    query = Pagamento.query
    
    if mese:
        query = query.filter_by(mese=mese)
    if anno:
        query = query.filter_by(anno=anno)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if corso_id:
        query = query.filter_by(corso_id=corso_id)
    
    pagamenti = query.all()
    clienti = Cliente.query.filter_by(attivo=True).all()
    corsi = Corso.query.all()
    
    return render_template('pagamenti.html', 
                         pagamenti=pagamenti, 
                         clienti=clienti, 
                         corsi=corsi,
                         mese_filtro=mese,
                         anno_filtro=anno,
                         cliente_filtro=cliente_id,
                         corso_filtro=corso_id)

@app.route('/pagamenti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_pagamento():
    if request.method == 'POST':
        pagamento = Pagamento(
            mese=int(request.form['mese']),
            anno=int(request.form['anno']),
            importo=float(request.form['importo']),
            cliente_id=int(request.form['cliente_id']),
            corso_id=int(request.form['corso_id']),
            note=request.form.get('note', '')
        )
        db.session.add(pagamento)
        db.session.commit()
        flash('Pagamento creato con successo!', 'success')
        return redirect(url_for('pagamenti'))
    
    clienti = Cliente.query.filter_by(attivo=True).all()
    corsi = Corso.query.all()
    return render_template('pagamento_form.html', pagamento=None, clienti=clienti, corsi=corsi)

@app.route('/pagamenti/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_pagamento(id):
    pagamento = Pagamento.query.get_or_404(id)
    
    if request.method == 'POST':
        pagamento.mese = int(request.form['mese'])
        pagamento.anno = int(request.form['anno'])
        pagamento.importo = float(request.form['importo'])
        pagamento.cliente_id = int(request.form['cliente_id'])
        pagamento.corso_id = int(request.form['corso_id'])
        pagamento.note = request.form.get('note', '')
        
        # Gestione stato pagamento
        if request.form.get('pagato') and not pagamento.pagato:
            pagamento.marca_pagato()
        elif not request.form.get('pagato') and pagamento.pagato:
            pagamento.pagato = False
            pagamento.data_pagamento = None
        
        db.session.commit()
        flash('Pagamento modificato con successo!', 'success')
        return redirect(url_for('pagamenti'))
    
    clienti = Cliente.query.filter_by(attivo=True).all()
    corsi = Corso.query.all()
    return render_template('pagamento_form.html', pagamento=pagamento, clienti=clienti, corsi=corsi)

@app.route('/pagamenti/<int:id>/marca-pagato', methods=['POST'])
@login_required
def marca_pagato(id):
    pagamento = Pagamento.query.get_or_404(id)
    pagamento.marca_pagato()
    db.session.commit()
    flash('Pagamento marcato come pagato!', 'success')
    return redirect(url_for('pagamenti'))

@app.route('/pagamenti/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_pagamento(id):
    pagamento = Pagamento.query.get_or_404(id)
    db.session.delete(pagamento)
    db.session.commit()
    flash('Pagamento eliminato con successo!', 'success')
    return redirect(url_for('pagamenti'))

@app.route('/pagamenti/<int:id>/ricevuta')
@login_required
def genera_ricevuta(id):
    pagamento = Pagamento.query.get_or_404(id)
    
    try:
        pdf_path = genera_ricevuta_pdf(pagamento, pdf_folder)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash(f'Errore nella generazione della ricevuta: {str(e)}', 'error')
        return redirect(url_for('pagamenti'))

# BACKUP ROUTE
@app.route('/backup')
@login_required
def backup_database():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_danza_{timestamp}.zip'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Aggiungi database
                zipf.write(database_path, 'database.db')
                
                # Aggiungi ricevute PDF se esistenti
                if os.path.exists(pdf_folder):
                    for root, dirs, files in os.walk(pdf_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, base_path)
                            zipf.write(file_path, arc_path)
            
            return send_file(temp_file.name, as_attachment=True, download_name=backup_name)
    
    except Exception as e:
        flash(f'Errore nel backup: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# SETTINGS ROUTES
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings = Settings.get_settings()
    
    if request.method == 'POST':
        settings.denominazione_sociale = request.form['denominazione_sociale']
        settings.indirizzo = request.form.get('indirizzo')
        settings.cap = request.form.get('cap')
        settings.citta = request.form.get('citta')
        settings.provincia = request.form.get('provincia', '').upper() or None
        settings.telefono = request.form.get('telefono')
        settings.email = request.form.get('email')
        settings.sito_web = request.form.get('sito_web')
        settings.partita_iva = request.form.get('partita_iva')
        settings.codice_fiscale = request.form.get('codice_fiscale', '').upper() or None
        settings.note = request.form.get('note')
        
        # Gestione caricamento logo
        from werkzeug.utils import secure_filename
        import uuid
        
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                # Verifica estensione file
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if file_ext in allowed_extensions:
                    # Genera nome file unico
                    unique_filename = f"logo_{uuid.uuid4().hex}.{file_ext}"
                    upload_path = os.path.join(static_folder, 'uploads', unique_filename)
                    
                    # Salva il file
                    file.save(upload_path)
                    
                    # Elimina vecchio logo se esiste
                    if settings.logo_filename:
                        old_logo_path = os.path.join(static_folder, 'uploads', settings.logo_filename)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)
                    
                    # Aggiorna database
                    settings.logo_filename = unique_filename
                    flash('Logo caricato con successo!', 'success')
                else:
                    flash('Formato file non supportato. Usa JPG, PNG o GIF.', 'error')
        
        db.session.commit()
        flash('Impostazioni salvate con successo!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=settings)

@app.route('/help')
@login_required
def help_page():
    """Pagina guida all'uso del software"""
    return render_template('help.html')

# REPORTS ROUTES
def genera_report_data(mese_filtro, anno_filtro):
    """Genera i dati per i report (usata sia per HTML che Excel)"""
    # Ottieni tutti i corsi con pagamenti per il periodo
    corsi = Corso.query.all()
    report_corsi = []
    incasso_totale = 0
    compensi_totali = 0
    numero_pagamenti_totale = 0
    
    for corso in corsi:
        # Pagamenti del corso per il periodo specifico
        pagamenti = Pagamento.query.filter_by(
            corso_id=corso.id,
            mese=mese_filtro,
            anno=anno_filtro,
            pagato=True
        ).all()
        
        if pagamenti:  # Solo corsi con pagamenti
            incasso_corso = sum(p.importo for p in pagamenti)
            percentuale_insegnante = corso.insegnante.percentuale_guadagno
            compenso_insegnante = incasso_corso * (percentuale_insegnante / 100)
            utile_corso = incasso_corso - compenso_insegnante
            
            # Crea oggetto con attributi per compatibilità template
            class ReportCorso:
                def __init__(self, corso, insegnante, num_pag, inc_corso, perc_ins, comp_ins, ut_corso):
                    self.corso = corso
                    self.insegnante = insegnante
                    self.numero_pagamenti = num_pag
                    self.incasso_corso = inc_corso
                    self.percentuale_insegnante = perc_ins
                    self.compenso_insegnante = comp_ins
                    self.utile_corso = ut_corso
            
            report_corsi.append(ReportCorso(
                corso, corso.insegnante, len(pagamenti), 
                incasso_corso, percentuale_insegnante, compenso_insegnante, utile_corso
            ))
            
            incasso_totale += incasso_corso
            compensi_totali += compenso_insegnante
            numero_pagamenti_totale += len(pagamenti)
    
    # Report per insegnanti
    insegnanti = Insegnante.query.all()
    report_insegnanti = []
    
    for insegnante in insegnanti:
        corsi_insegnante = [r for r in report_corsi if r.insegnante.id == insegnante.id]
        if corsi_insegnante:
            compenso_totale = sum(r.compenso_insegnante for r in corsi_insegnante)
            incasso_totale_insegnante = sum(r.incasso_corso for r in corsi_insegnante)
            percentuale_media = sum(r.percentuale_insegnante for r in corsi_insegnante) / len(corsi_insegnante)
            corsi_nomi = [r.corso.nome for r in corsi_insegnante]
            
            # Crea oggetto per template
            class ReportInsegnante:
                def __init__(self, insegnante, comp_tot, inc_tot, perc_media, corsi_nomi):
                    self.insegnante = insegnante
                    self.compenso_totale = comp_tot
                    self.incasso_totale = inc_tot
                    self.percentuale_media = perc_media
                    self.corsi_nomi = corsi_nomi
            
            report_insegnanti.append(ReportInsegnante(
                insegnante, compenso_totale, incasso_totale_insegnante, percentuale_media, corsi_nomi
            ))
    
    # Riepilogo generale
    riepilogo = {
        'incasso_totale': incasso_totale,
        'compensi_totali': compensi_totali,
        'utile_netto': incasso_totale - compensi_totali,
        'numero_pagamenti': numero_pagamenti_totale
    }
    
    return report_corsi, report_insegnanti, riepilogo

@app.route('/reports')
@login_required
def reports():
    # Parametri filtro con validazione
    mese_filtro = request.args.get('mese', date.today().month, type=int)
    anno_filtro = request.args.get('anno', date.today().year, type=int)
    
    # Validazione parametri
    if mese_filtro < 1 or mese_filtro > 12:
        mese_filtro = date.today().month
    if anno_filtro < 2020 or anno_filtro > 2030:
        anno_filtro = date.today().year
    
    # Nomi dei mesi per i template
    mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    
    # Usa la funzione unificata per generare i dati
    report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
    
    # Settings per la stampa
    settings = Settings.get_settings()
    
    return render_template('reports.html',
                         report_corsi=report_corsi,
                         report_insegnanti=report_insegnanti,
                         riepilogo=riepilogo,
                         mese_filtro=mese_filtro,
                         anno_filtro=anno_filtro,
                         mesi=mesi,
                         settings=settings,
                         moment=datetime.now)

@app.route('/reports/excel')
@login_required
def esporta_report_excel():
    """Esporta report in formato Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Parametri filtro
        mese_filtro = int(request.args.get('mese', datetime.now().month))
        anno_filtro = int(request.args.get('anno', datetime.now().year))
        
        # Ottieni dati report (stesso codice della route reports)
        report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
        
        # Prepara dati per Excel
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Sheet 1: Riepilogo Generale
            riepilogo_data = pd.DataFrame([{
                'Incasso Totale': riepilogo['incasso_totale'],
                'Compensi Insegnanti': riepilogo['compensi_totali'],
                'Utile Netto': riepilogo['utile_netto'],
                'Numero Pagamenti': riepilogo['numero_pagamenti']
            }])
            riepilogo_data.to_excel(writer, sheet_name='Riepilogo', index=False)
            
            # Sheet 2: Report per Corso
            if report_corsi:
                corsi_data = []
                for report in report_corsi:
                    corsi_data.append({
                        'Corso': report.corso.nome,
                        'Giorno': report.corso.giorno,
                        'Orario': report.corso.orario.strftime('%H:%M'),
                        'Insegnante': report.insegnante.nome_completo,
                        'Iscritti': report.corso.numero_iscritti,
                        'Pagamenti': report.numero_pagamenti,
                        'Incasso': report.incasso_corso,
                        'Percentuale Insegnante': report.percentuale_insegnante,
                        'Compenso': report.compenso_insegnante,
                        'Utile Corso': report.utile_corso
                    })
                
                corsi_df = pd.DataFrame(corsi_data)
                corsi_df.to_excel(writer, sheet_name='Report Corsi', index=False)
            
            # Sheet 3: Report per Insegnante
            if report_insegnanti:
                insegnanti_data = []
                for report in report_insegnanti:
                    insegnanti_data.append({
                        'Insegnante': report.insegnante.nome_completo,
                        'Telefono': report.insegnante.telefono or '',
                        'Corsi': ', '.join(report.corsi_nomi),
                        'Incasso Totale': report.incasso_totale,
                        'Percentuale Media': report.percentuale_media,
                        'Compenso Totale': report.compenso_totale
                    })
                
                insegnanti_df = pd.DataFrame(insegnanti_data)
                insegnanti_df.to_excel(writer, sheet_name='Compensi Insegnanti', index=False)
        
        excel_buffer.seek(0)
        
        # Nome file con data
        filename = f"report_dance2manager_{mese_filtro:02d}_{anno_filtro}.xlsx"
        
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except ImportError:
        flash('Libreria pandas non installata. Installare con: pip install pandas openpyxl', 'error')
        return redirect(url_for('reports'))
    except Exception as e:
        flash(f'Errore durante export Excel: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports/compensi_pdf')
@login_required
def genera_pdf_compensi():
    """Genera PDF con compensi per tutti gli insegnanti"""
    # Parametri filtro
    mese_filtro = request.args.get('mese', date.today().month, type=int)
    anno_filtro = request.args.get('anno', date.today().year, type=int)
    
    # Genera dati
    report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
    
    try:
        from utils.stampa_pdf import genera_compensi_pdf
        
        # Genera PDF
        pdf_path = genera_compensi_pdf(
            report_insegnanti, 
            riepilogo, 
            mese_filtro, 
            anno_filtro,
            pdf_folder
        )
        
        return send_file(pdf_path, as_attachment=True)
        
    except Exception as e:
        flash(f'Errore durante generazione PDF compensi: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports/compensi_pdf/<int:insegnante_id>')
@login_required
def genera_pdf_compensi_insegnante(insegnante_id):
    """Genera PDF compensi per singolo insegnante"""
    # Parametri filtro
    mese_filtro = request.args.get('mese', date.today().month, type=int)
    anno_filtro = request.args.get('anno', date.today().year, type=int)
    
    # Trova insegnante
    insegnante = Insegnante.query.get_or_404(insegnante_id)
    
    # Genera dati
    report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
    
    # Filtra solo questo insegnante
    report_insegnante = next((r for r in report_insegnanti if r.insegnante.id == insegnante_id), None)
    if not report_insegnante:
        flash('Nessun dato per questo insegnante nel periodo selezionato', 'warning')
        return redirect(url_for('reports'))
    
    try:
        from utils.stampa_pdf import genera_compensi_insegnante_pdf
        
        # Genera PDF
        pdf_path = genera_compensi_insegnante_pdf(
            insegnante,
            report_insegnante, 
            [r for r in report_corsi if r.insegnante.id == insegnante_id],
            mese_filtro, 
            anno_filtro,
            pdf_folder
        )
        
        return send_file(pdf_path, as_attachment=True)
        
    except Exception as e:
        flash(f'Errore durante generazione PDF: {str(e)}', 'error')
        return redirect(url_for('reports'))

if __name__ == '__main__':
    init_db()
    
    # Porta configurabile via argomento
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    app.run(host='127.0.0.1', port=port, debug=True)