# app.py
import os
import sys
import shutil
import zipfile
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_security import Security, SQLAlchemyUserDatastore, login_required as security_login_required, roles_required
from flask_mailman import Mail
from flask_toastr import Toastr
from models import db, User, Role, WebAuthn, Cliente, Corso, Insegnante, Pagamento, Settings
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
# app.config['DEBUG'] = True  # Disabled debug mode

# Flask-Security-Too Configuration
app.config['SECURITY_PASSWORD_SALT'] = 'danza-security-salt-2024'
app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['email', 'authenticator']
app.config['SECURITY_TWO_FACTOR'] = True
app.config['SECURITY_TWO_FACTOR_RESCUE_EMAIL'] = 'admin@dance2manage.com'
app.config['SECURITY_TWO_FACTOR_LOGIN_VALIDITY'] = '1 weeks'
app.config['SECURITY_TWO_FACTOR_ALWAYS_VALIDATE'] = False
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_REGISTERABLE'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_RESET_EMAIL'] = True
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = True
app.config['SECURITY_RECOVERABLE'] = True

# Disable strict email validation
app.config['SECURITY_EMAIL_VALIDATOR_ARGS'] = {'check_deliverability': False}
app.config['SECURITY_LOGIN_WITHOUT_CONFIRMATION'] = True

# TOTP Configuration for 2FA
app.config['SECURITY_TOTP_SECRETS'] = {'1': 'dance2manage-secret-key-2024'}
app.config['SECURITY_TOTP_ISSUER'] = 'Dance2Manage'
app.config['SECURITY_TWO_FACTOR_REQUIRED'] = False  # Make 2FA optional

# QR Code configuration - ensure all required libraries are available  
app.config['SECURITY_TWO_FACTOR_AUTHENTICATOR_VALIDITY'] = 120  # 2 minutes
app.config['SECURITY_TWO_FACTOR_EMAIL_VALIDITY'] = 300  # 5 minutes

# Force disable SMS to simplify setup
app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['email', 'authenticator']  # Remove SMS
app.config['SECURITY_TWO_FACTOR_SMS_SERVICE'] = None

# Disable all email features to avoid connection errors
app.config['SECURITY_EMAIL_SENDER'] = 'noreply@dance2manage.com'
app.config['MAIL_SUPPRESS_SEND'] = True

# Configure Flask-Security to use custom templates
app.config['SECURITY_TEMPLATE_DIRECTORY'] = template_folder
app.config['SECURITY_TWO_FACTOR_VERIFY_CODE_TEMPLATE'] = 'security/two_factor_verify_code.html'

# Configurazione database SQLite
database_path = os.path.join(base_path, 'data', 'database.db')
os.makedirs(os.path.dirname(database_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializza database
db.init_app(app)

# Setup Flask-Security-Too (standard)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Initialize Mail
mail = Mail(app)

# Initialize Toastr for better flash messages
toastr = Toastr(app)

# Configure Toastr settings for better appearance (simplified to avoid JavaScript errors)
app.config['TOASTR_TIMEOUT'] = 5000
app.config['TOASTR_POSITION_CLASS'] = 'toast-top-right'

# Context processor per rendere settings disponibili in tutti i template
@app.context_processor
def inject_settings():
    try:
        settings = Settings.get_settings()
        return dict(global_settings=settings)
    except Exception:
        return dict(global_settings=None)

# Filtro Jinja2 per formattazione valuta italiana
@app.template_filter('currency')
def currency_filter(value):
    """Formatta un numero come valuta italiana: 1.000,00"""
    if value is None:
        return "0,00"
    try:
        # Converti in float se necessario
        if isinstance(value, str):
            value = float(value.replace(',', '.').replace('.', ''))
        
        # Formatta con separatore migliaia e virgola decimale
        formatted = "{:,.2f}".format(float(value))
        # Sostituisci . con , per decimali e , con . per migliaia (formato italiano)
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return formatted
    except (ValueError, TypeError):
        return "0,00"

@app.template_filter('euro')
def euro_filter(value):
    """Formatta un numero come euro: €1.000,00"""
    return f"€{currency_filter(value)}"

# Crea cartelle necessarie
pdf_folder = os.path.join(base_path, 'pdf_ricevute')
os.makedirs(pdf_folder, exist_ok=True)

def update_mail_config(settings):
    """Aggiorna la configurazione Flask-Mail dinamicamente"""
    if settings.mail_configured:
        app.config['MAIL_SERVER'] = settings.mail_server
        app.config['MAIL_PORT'] = settings.mail_port
        app.config['MAIL_USE_TLS'] = settings.mail_use_tls
        app.config['MAIL_USE_SSL'] = settings.mail_use_ssl
        app.config['MAIL_USERNAME'] = settings.mail_username
        app.config['MAIL_PASSWORD'] = settings.mail_password
        app.config['MAIL_DEFAULT_SENDER'] = settings.mail_default_sender
        app.config['MAIL_MAX_EMAILS'] = settings.mail_max_emails
        app.config['MAIL_SUPPRESS_SEND'] = settings.mail_suppress_send
        app.config['MAIL_DEBUG'] = settings.mail_debug
        
        # Aggiorna anche le configurazioni Flask-Security per email
        app.config['SECURITY_EMAIL_SENDER'] = settings.mail_default_sender
        app.config['MAIL_SUPPRESS_SEND'] = settings.mail_suppress_send
        
        # Re-inizializza Mail con nuove configurazioni
        global mail
        mail.init_app(app)
        
        print(f"✓ Configurazione email aggiornata: {settings.mail_server}:{settings.mail_port}")
    else:
        # Disabilita email se non configurata
        app.config['MAIL_SUPPRESS_SEND'] = True
        app.config['SECURITY_EMAIL_SENDER'] = 'noreply@dance2manage.com'
        print("⚠ Email non configurata - invio disabilitato")

def init_mail_config():
    """Inizializza la configurazione email all'avvio"""
    try:
        with app.app_context():
            settings = Settings.get_settings()
            update_mail_config(settings)
    except Exception as e:
        print(f"⚠ Errore inizializzazione email: {str(e)}")
        # Fallback su configurazione di default
        app.config['MAIL_SUPPRESS_SEND'] = True

def init_db():
    """Inizializza il database e crea utente admin se non esiste"""
    with app.app_context():
        db.create_all()
        
        # Crea ruolo admin se non esiste
        if not user_datastore.find_role('admin'):
            user_datastore.create_role(name='admin', description='Administrator')
        
        # Crea ruolo user se non esiste  
        if not user_datastore.find_role('user'):
            user_datastore.create_role(name='user', description='Standard User')
        
        # Crea utente admin se non esiste
        if not user_datastore.find_user(email='admin@dance2manage.com'):
            admin = user_datastore.create_user(
                email='admin@dance2manage.com',
                username='admin',
                password=generate_password_hash('admin123'),
                active=True,
                first_name='Admin',
                last_name='User'
            )
            user_datastore.add_role_to_user(admin, 'admin')
        
        db.session.commit()
        
        # Inizializza configurazione email
        init_mail_config()

# Use Flask-Security login_required decorator
from flask_security import login_required

# ROUTES

# Flask-Security will handle login/logout automatically
# Remove custom login routes since Flask-Security provides them

# Redirect root to security login
@app.route('/login')
def custom_login():
    return redirect(url_for('security.login'))

@app.route('/logout')  
def custom_logout():
    return redirect(url_for('security.logout'))

@app.route('/profile')
@login_required
def user_profile():
    """Pagina profilo utente"""
    from flask_security import current_user
    return render_template('security/user_profile.html', user=current_user)

@app.route('/admin/users')
@login_required
@roles_required('admin')
def gestione_utenti():
    """Pagina gestione utenti per admin"""
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def nuovo_utente():
    """Crea nuovo utente"""
    if request.method == 'POST':
        from flask_security.utils import hash_password
        
        user = user_datastore.create_user(
            email=request.form['email'],
            username=request.form.get('username'),
            password=hash_password(request.form['password']),
            active=request.form.get('active') == 'on',
            first_name=request.form.get('first_name', ''),
            last_name=request.form.get('last_name', '')
        )
        
        # Assegna ruoli
        selected_roles = request.form.getlist('roles')
        for role_name in selected_roles:
            role = user_datastore.find_role(role_name)
            if role:
                user_datastore.add_role_to_user(user, role)
        
        user_datastore.commit()
        flash('Utente creato con successo!', 'success')
        return redirect(url_for('gestione_utenti'))
    
    roles = Role.query.all()
    return render_template('admin/user_form.html', user=None, roles=roles)

@app.route('/admin/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def modifica_utente(id):
    """Modifica utente esistente"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        from flask_security.utils import hash_password
        
        user.email = request.form['email']
        user.username = request.form.get('username')
        user.first_name = request.form.get('first_name', '')
        user.last_name = request.form.get('last_name', '')
        user.active = request.form.get('active') == 'on'
        
        # Cambia password solo se fornita
        if request.form.get('password'):
            user.password = hash_password(request.form['password'])
        
        # Aggiorna ruoli
        user.roles = []
        selected_roles = request.form.getlist('roles')
        for role_name in selected_roles:
            role = user_datastore.find_role(role_name)
            if role:
                user_datastore.add_role_to_user(user, role)
        
        user_datastore.commit()
        flash('Utente aggiornato con successo!', 'success')
        return redirect(url_for('gestione_utenti'))
    
    roles = Role.query.all()
    return render_template('admin/user_form.html', user=user, roles=roles)

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def elimina_utente(id):
    """Elimina utente"""
    from flask_security import current_user
    
    user = User.query.get_or_404(id)
    
    # Non permettere di eliminare se stesso
    if user.id == current_user.id:
        flash('Non puoi eliminare il tuo stesso account!', 'error')
        return redirect(url_for('gestione_utenti'))
    
    user_datastore.delete_user(user)
    user_datastore.commit()
    flash('Utente eliminato con successo!', 'success')
    return redirect(url_for('gestione_utenti'))

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
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    sort_by = request.args.get('sort_by', 'cognome')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Validazione per_page
    if per_page not in [10, 25, 50]:
        per_page = 25
        
    # Validazione sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
        
    # Validazione sort_by
    valid_sort_fields = ['nome', 'cognome', 'email', 'codice_fiscale', 'telefono']
    if sort_by not in valid_sort_fields:
        sort_by = 'cognome'
    
    query = Cliente.query
    
    if search:
        query = query.filter(
            (Cliente.nome.contains(search)) | 
            (Cliente.cognome.contains(search)) |
            (Cliente.email.contains(search)) |
            (Cliente.codice_fiscale.contains(search)) |
            (Cliente.telefono.contains(search))
        )
    
    if stato == 'attivi':
        query = query.filter_by(attivo=True)
    elif stato == 'inattivi':
        query = query.filter_by(attivo=False)
    
    # Ordinamento dinamico
    sort_column = getattr(Cliente, sort_by)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Ordinamento secondario per consistenza
    if sort_by != 'cognome':
        query = query.order_by(sort_column.desc() if sort_order == 'desc' else sort_column.asc(), Cliente.cognome)
    
    # Paginazione
    clienti = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('clienti.html', 
                         clienti=clienti, 
                         search=search, 
                         stato=stato,
                         per_page=per_page,
                         sort_by=sort_by,
                         sort_order=sort_order)

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

@app.route('/clienti/<int:id>')
@login_required
def dettagli_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template('cliente_view.html', cliente=cliente)

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

@app.route('/corsi/<int:id>')
@login_required
def dettagli_corso(id):
    corso = Corso.query.get_or_404(id)
    return render_template('corso_view.html', corso=corso)

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

@app.route('/insegnanti/<int:id>')
@login_required
def dettagli_insegnante(id):
    insegnante = Insegnante.query.get_or_404(id)
    return render_template('insegnante_view.html', insegnante=insegnante)

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
    # Parametri di filtro esistenti
    mese = request.args.get('mese', type=int)
    anno = request.args.get('anno', type=int) 
    cliente_id = request.args.get('cliente_id', type=int)
    corso_id = request.args.get('corso_id', type=int)
    
    # Nuovi parametri per ricerca, ordinamento e paginazione
    search = request.args.get('search', '')
    stato = request.args.get('stato', 'tutti')  # tutti, pagati, non_pagati
    sort_by = request.args.get('sort_by', 'data_creazione')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Validazioni
    if per_page not in [10, 25, 50]:
        per_page = 25
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Campi ordinabili
    valid_sort_fields = ['periodo', 'cliente', 'corso', 'importo', 'stato', 'data_pagamento', 'data_creazione']
    if sort_by not in valid_sort_fields:
        sort_by = 'data_creazione'
    
    # Query base con join per ricerca
    query = Pagamento.query.join(Cliente).join(Corso)
    
    # Filtri esistenti
    if mese:
        query = query.filter(Pagamento.mese == mese)
    if anno:
        query = query.filter(Pagamento.anno == anno)
    if cliente_id:
        query = query.filter(Pagamento.cliente_id == cliente_id)
    if corso_id:
        query = query.filter(Pagamento.corso_id == corso_id)
    
    # Ricerca live
    if search:
        query = query.filter(
            (Cliente.nome.contains(search)) | 
            (Cliente.cognome.contains(search)) |
            (Corso.nome.contains(search)) |
            (Pagamento.metodo_pagamento.contains(search)) |
            (Pagamento.note.contains(search))
        )
    
    # Filtro stato pagamento
    if stato == 'pagati':
        query = query.filter(Pagamento.pagato == True)
    elif stato == 'non_pagati':
        query = query.filter(Pagamento.pagato == False)
    
    # Ordinamento dinamico
    if sort_by == 'periodo':
        sort_column = Pagamento.anno.desc() if sort_order == 'desc' else Pagamento.anno.asc()
        query = query.order_by(sort_column, Pagamento.mese.desc() if sort_order == 'desc' else Pagamento.mese.asc())
    elif sort_by == 'cliente':
        sort_column = Cliente.cognome.desc() if sort_order == 'desc' else Cliente.cognome.asc()
        query = query.order_by(sort_column, Cliente.nome)
    elif sort_by == 'corso':
        sort_column = Corso.nome.desc() if sort_order == 'desc' else Corso.nome.asc()
        query = query.order_by(sort_column)
    elif sort_by == 'importo':
        sort_column = Pagamento.importo.desc() if sort_order == 'desc' else Pagamento.importo.asc()
        query = query.order_by(sort_column)
    elif sort_by == 'stato':
        sort_column = Pagamento.pagato.desc() if sort_order == 'desc' else Pagamento.pagato.asc()
        query = query.order_by(sort_column)
    elif sort_by == 'data_pagamento':
        sort_column = Pagamento.data_pagamento.desc() if sort_order == 'desc' else Pagamento.data_pagamento.asc()
        query = query.order_by(sort_column)
    else:  # data_creazione (default)
        sort_column = Pagamento.data_creazione.desc() if sort_order == 'desc' else Pagamento.data_creazione.asc()
        query = query.order_by(sort_column)
    
    # Paginazione
    pagamenti_paginated = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Dati per select
    clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.cognome, Cliente.nome).all()
    corsi = Corso.query.order_by(Corso.nome).all()
    
    return render_template('pagamenti.html', 
                         pagamenti=pagamenti_paginated.items,
                         pagamenti_paginated=pagamenti_paginated,
                         clienti=clienti, 
                         corsi=corsi,
                         mese_filtro=mese,
                         anno_filtro=anno,
                         cliente_filtro=cliente_id,
                         corso_filtro=corso_id,
                         search=search,
                         stato=stato,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         per_page=per_page)

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
            metodo_pagamento=request.form.get('metodo_pagamento', 'Contanti'),
            note=request.form.get('note', '')
        )
        db.session.add(pagamento)
        db.session.commit()
        flash('Pagamento creato con successo!', 'success')
        return redirect(url_for('pagamenti'))
    
    clienti = Cliente.query.filter_by(attivo=True).all()
    corsi = Corso.query.all()
    corso_preselezionato = request.args.get('corso_id', type=int)
    mese_corrente = datetime.now().month
    anno_corrente = datetime.now().year
    return render_template('pagamento_form.html', pagamento=None, clienti=clienti, corsi=corsi, 
                         corso_preselezionato=corso_preselezionato, mese_corrente=mese_corrente, anno_corrente=anno_corrente)

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
        pagamento.metodo_pagamento = request.form.get('metodo_pagamento', 'Contanti')
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

@app.route('/genera_ricevute_bulk', methods=['POST'])
@login_required
def genera_ricevute_bulk():
    try:
        # Ottieni parametri dal form
        clienti_ids = request.form.getlist('clienti_ids')
        mese = int(request.form['mese'])
        anno = int(request.form['anno'])
        
        if not clienti_ids:
            flash('Nessun cliente selezionato', 'error')
            return redirect(url_for('clienti'))
        
        ricevute_create = 0
        errori = []
        clienti_senza_corsi = []
        
        for cliente_id in clienti_ids:
            cliente = Cliente.query.get_or_404(cliente_id)
            
            # Controlla se il cliente ha corsi
            if not cliente.corsi:
                clienti_senza_corsi.append(cliente.nome_completo)
                continue
                
            # Per ogni corso del cliente
            for corso in cliente.corsi:
                # Verifica se esiste già un pagamento per questo mese/anno/cliente/corso
                pagamento_esistente = Pagamento.query.filter_by(
                    cliente_id=cliente_id,
                    corso_id=corso.id,
                    mese=mese,
                    anno=anno
                ).first()
                
                if pagamento_esistente:
                    errori.append(f"{cliente.nome_completo} - {corso.nome}: pagamento già esistente")
                    continue
                
                # Crea nuovo pagamento
                pagamento = Pagamento(
                    mese=mese,
                    anno=anno,
                    importo=corso.costo_mensile,
                    cliente_id=cliente_id,
                    corso_id=corso.id,
                    pagato=True,  # Lo marco già come pagato
                    data_pagamento=datetime.now(),
                    metodo_pagamento='Contanti',
                    note=f'Generato automaticamente il {datetime.now().strftime("%d/%m/%Y")}'
                )
                
                db.session.add(pagamento)
                ricevute_create += 1
        
        db.session.commit()
        
        # Messaggi di risultato
        if ricevute_create > 0:
            flash(f'Create {ricevute_create} ricevute con successo!', 'success')
        
        if clienti_senza_corsi:
            if len(clienti_senza_corsi) == 1:
                flash(f'{clienti_senza_corsi[0]} non è iscritto a nessun corso', 'warning')
            else:
                flash(f'{len(clienti_senza_corsi)} clienti non sono iscritti a nessun corso: {", ".join(clienti_senza_corsi[:3])}{"..." if len(clienti_senza_corsi) > 3 else ""}', 'warning')
        
        if errori:
            for errore in errori[:5]:  # Mostra solo i primi 5 errori
                flash(errore, 'warning')
            if len(errori) > 5:
                flash(f'... e altri {len(errori) - 5} errori', 'warning')
                
        # Se non è stata creata nessuna ricevuta, mostra messaggio esplicativo
        if ricevute_create == 0:
            if clienti_senza_corsi and not errori:
                flash('Nessuna ricevuta generata: i clienti selezionati devono essere prima iscritti ai corsi', 'info')
            elif errori and not clienti_senza_corsi:
                flash('Nessuna ricevuta generata: tutti i pagamenti esistono già per il periodo selezionato', 'info')
        
        return redirect(url_for('pagamenti'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Errore nella generazione delle ricevute: {str(e)}', 'error')
        return redirect(url_for('clienti'))

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
            
            flash('Backup database creato con successo!', 'info')
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
        
        # Configurazioni Email/SMTP
        settings.mail_server = request.form.get('mail_server', '').strip()
        settings.mail_port = int(request.form.get('mail_port', 587))
        settings.mail_use_tls = bool(request.form.get('mail_use_tls'))
        settings.mail_use_ssl = bool(request.form.get('mail_use_ssl'))
        settings.mail_username = request.form.get('mail_username', '').strip()
        settings.mail_password = request.form.get('mail_password', '').strip()
        settings.mail_default_sender = request.form.get('mail_default_sender', '').strip()
        settings.mail_max_emails = int(request.form.get('mail_max_emails', 100))
        settings.mail_suppress_send = bool(request.form.get('mail_suppress_send'))
        settings.mail_debug = bool(request.form.get('mail_debug'))
        
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
        
        # Aggiorna configurazione Flask-Mail dinamicamente
        try:
            update_mail_config(settings)
            flash('Impostazioni salvate con successo! Configurazione email aggiornata.', 'success')
        except Exception as e:
            flash(f'Impostazioni salvate, ma errore nella configurazione email: {str(e)}', 'warning')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=settings)

@app.route('/settings/test-email', methods=['POST'])
@login_required
def test_email():
    """Route per testare la configurazione email"""
    from flask_mailman import EmailMessage
    from flask_security import current_user
    
    try:
        # Ottieni configurazioni attuali
        settings = Settings.get_settings()
        
        if not settings.mail_configured:
            return jsonify({'success': False, 'message': 'Configurazione email incompleta'})
        
        # Aggiorna configurazione Flask-Mail
        update_mail_config(settings)
        
        
        # Email di test
        test_email_recipient = request.json.get('email', current_user.email)
        
        if not test_email_recipient:
            return jsonify({'success': False, 'message': 'Indirizzo email destinatario non specificato'})
        
        # Crea messaggio di test
        msg = EmailMessage(
            subject=f'Test Email - {settings.denominazione_sociale}',
            body=f'''Questa è un'email di test dal sistema Dance2Manage.
            
Configurazione utilizzata:
- Server SMTP: {settings.mail_server}:{settings.mail_port}
- TLS: {"Sì" if settings.mail_use_tls else "No"}
- SSL: {"Sì" if settings.mail_use_ssl else "No"}
- Username: {settings.mail_username}
- Mittente: {settings.mail_default_sender}

Data/Ora: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

Se ricevi questa email, la configurazione SMTP è corretta!

--
{settings.denominazione_sociale}
Dance2Manage System''',
            from_email=settings.mail_default_sender,
            to=[test_email_recipient]
        )
        
        # Invia email
        if not settings.mail_suppress_send:
            msg.send()
            message = f'Email di test inviata con successo a {test_email_recipient}'
        else:
            message = f'Email di test preparata ma non inviata (modalità test attiva). Destinatario: {test_email_recipient}'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        error_message = f'Errore durante l\'invio dell\'email di test: {str(e)}'
        print(f"❌ Test email fallito: {error_message}")
        return jsonify({'success': False, 'message': error_message})

@app.route('/debug/email-config')
@login_required
def debug_email_config():
    """Route di debug per verificare configurazione email"""
    settings = Settings.get_settings()
    
    config_info = {
        'Database Settings': {
            'mail_server': settings.mail_server,
            'mail_port': settings.mail_port,
            'mail_username': settings.mail_username,
            'mail_password': '***' if settings.mail_password else None,
            'mail_default_sender': settings.mail_default_sender,
            'mail_use_tls': settings.mail_use_tls,
            'mail_use_ssl': settings.mail_use_ssl,
            'mail_suppress_send': settings.mail_suppress_send,
            'mail_configured': settings.mail_configured
        },
        'Flask App Config': {
            'MAIL_SERVER': app.config.get('MAIL_SERVER'),
            'MAIL_PORT': app.config.get('MAIL_PORT'),
            'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
            'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
            'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL'),
            'MAIL_SUPPRESS_SEND': app.config.get('MAIL_SUPPRESS_SEND'),
            'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER')
        }
    }
    
    return jsonify(config_info)

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

# EMAIL REPORTS ROUTES
@app.route('/reports/email_teacher/<int:insegnante_id>')
@login_required
def email_teacher_report(insegnante_id):
    """Invia report via email a singolo insegnante"""
    from flask_mailman import EmailMultiAlternatives
    
    # Parametri filtro
    mese_filtro = request.args.get('mese', date.today().month, type=int)
    anno_filtro = request.args.get('anno', date.today().year, type=int)
    
    # Trova insegnante
    insegnante = Insegnante.query.get_or_404(insegnante_id)
    
    if not insegnante.email:
        flash(f'Insegnante {insegnante.nome_completo} non ha un indirizzo email configurato', 'error')
        return redirect(url_for('reports'))
    
    # Genera dati
    report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
    
    # Filtra solo questo insegnante
    report_insegnante = next((r for r in report_insegnanti if r.insegnante.id == insegnante_id), None)
    if not report_insegnante:
        flash('Nessun dato per questo insegnante nel periodo selezionato', 'warning')
        return redirect(url_for('reports'))
    
    # Corsi dell'insegnante
    corsi_dettaglio = [r for r in report_corsi if r.insegnante.id == insegnante_id]
    
    try:
        # Ottieni impostazioni per mittente
        settings = Settings.get_settings()
        
        # Verifica configurazione email
        if not settings.mail_configured:
            flash('Configurazione email non completata. Vai in Impostazioni per configurare SMTP.', 'error')
            return redirect(url_for('reports'))
        
        # Nomi mesi per template
        mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        
        # Dati per template
        template_data = {
            'insegnante': insegnante,
            'report': report_insegnante,
            'corsi_dettaglio': corsi_dettaglio,
            'mese_nome': mesi[mese_filtro],
            'mese_filtro': mese_filtro,
            'anno': anno_filtro,
            'settings': settings,
            'data_generazione': datetime.now().strftime('%d/%m/%Y alle %H:%M')
        }
        
        # Render templates
        html_content = render_template('emails/teacher_report.html', **template_data)
        text_content = render_template('emails/teacher_report.txt', **template_data)
        
        # Soggetto email
        subject = f"Report Compensi {mesi[mese_filtro]} {anno_filtro} - {insegnante.nome_completo}"
        
        # Crea email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.mail_default_sender,
            to=[insegnante.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Allega logo se presente
        if settings.logo_filename:
            import mimetypes
            logo_path = os.path.join(static_folder, 'uploads', settings.logo_filename)
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    content_type, _ = mimetypes.guess_type(logo_path)
                    if not content_type:
                        content_type = 'image/png'
                    
                    from email.mime.image import MIMEImage
                    # Crea allegato inline per cid:logo
                    logo_attachment = MIMEImage(logo_data)
                    logo_attachment.add_header('Content-ID', '<logo>')
                    logo_attachment.add_header('Content-Disposition', 'inline', filename=settings.logo_filename)
                    email.attach(logo_attachment)
        
        # Invia email
        email.send()
        
        flash(f'Report inviato con successo all\'insegnante {insegnante.nome_completo} ({insegnante.email})', 'success')
        
    except Exception as e:
        flash(f'Errore durante invio email: {str(e)}', 'error')
        print(f"Email error: {str(e)}")  # Debug
    
    return redirect(url_for('reports'))

@app.route('/reports/email_all_teachers')
@login_required
def email_all_teachers_reports():
    """Invia report via email a tutti gli insegnanti che hanno un compenso"""
    from flask_mailman import EmailMultiAlternatives
    
    # Parametri filtro
    mese_filtro = request.args.get('mese', date.today().month, type=int)
    anno_filtro = request.args.get('anno', date.today().year, type=int)
    
    # Genera dati
    report_corsi, report_insegnanti, riepilogo = genera_report_data(mese_filtro, anno_filtro)
    
    if not report_insegnanti:
        flash('Nessun dato disponibile per il periodo selezionato', 'warning')
        return redirect(url_for('reports'))
    
    try:
        # Ottieni impostazioni per mittente
        settings = Settings.get_settings()
        
        # Verifica configurazione email
        if not settings.mail_configured:
            flash('Configurazione email non completata. Vai in Impostazioni per configurare SMTP.', 'error')
            return redirect(url_for('reports'))
        
        # Nomi mesi per template
        mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        
        emails_sent = 0
        emails_skipped = 0
        
        for report_insegnante in report_insegnanti:
            insegnante = report_insegnante.insegnante
            
            # Salta insegnanti senza email
            if not insegnante.email:
                emails_skipped += 1
                continue
            
            # Corsi dell'insegnante
            corsi_dettaglio = [r for r in report_corsi if r.insegnante.id == insegnante.id]
            
            # Dati per template
            template_data = {
                'insegnante': insegnante,
                'report': report_insegnante,
                'corsi_dettaglio': corsi_dettaglio,
                'mese_nome': mesi[mese_filtro],
                'mese_filtro': mese_filtro,
                'anno': anno_filtro,
                'settings': settings,
                'data_generazione': datetime.now().strftime('%d/%m/%Y alle %H:%M')
            }
            
            # Render templates
            html_content = render_template('emails/teacher_report.html', **template_data)
            text_content = render_template('emails/teacher_report.txt', **template_data)
            
            # Soggetto email
            subject = f"Report Compensi {mesi[mese_filtro]} {anno_filtro} - {insegnante.nome_completo}"
            
            # Crea e invia email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.mail_default_sender,
                to=[insegnante.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Allega logo se presente
            if settings.logo_filename:
                import mimetypes
                logo_path = os.path.join(static_folder, 'uploads', settings.logo_filename)
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        logo_data = f.read()
                        content_type, _ = mimetypes.guess_type(logo_path)
                        if not content_type:
                            content_type = 'image/png'
                        
                        from email.mime.image import MIMEImage
                        # Crea allegato inline per cid:logo
                        logo_attachment = MIMEImage(logo_data)
                        logo_attachment.add_header('Content-ID', '<logo>')
                        logo_attachment.add_header('Content-Disposition', 'inline', filename=settings.logo_filename)
                        email.attach(logo_attachment)
            
            email.send()
            
            emails_sent += 1
        
        if emails_sent > 0:
            flash(f'Report inviati con successo a {emails_sent} insegnanti', 'success')
        
        if emails_skipped > 0:
            flash(f'{emails_skipped} insegnanti saltati (email mancante)', 'info')
            
    except Exception as e:
        flash(f'Errore durante invio email: {str(e)}', 'error')
        print(f"Email error: {str(e)}")  # Debug
    
    return redirect(url_for('reports'))

# Route rimossa - Flask-Security-Too gestisce tutto automaticamente

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