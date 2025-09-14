# models/settings.py
from . import db
from sqlalchemy import Column, Integer, String, Text, Boolean
import os
from cryptography.fernet import Fernet

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    denominazione_sociale = Column(String(200), nullable=False, default='Scuola di Danza')
    indirizzo = Column(String(200))
    cap = Column(String(10))
    citta = Column(String(100))
    provincia = Column(String(2))
    telefono = Column(String(20))
    email = Column(String(120))
    sito_web = Column(String(200))
    partita_iva = Column(String(11))
    codice_fiscale = Column(String(16))
    logo_filename = Column(String(200))  # Nome del file logo
    note = Column(Text)
    
    # Configurazioni Email/SMTP
    mail_server = Column(String(200))  # es. smtp.gmail.com, smtp.outlook.com
    mail_port = Column(Integer, default=587)  # 587 per TLS, 465 per SSL
    mail_use_tls = Column(Boolean, default=True)  # TLS encryption
    mail_use_ssl = Column(Boolean, default=False)  # SSL encryption
    mail_username = Column(String(200))  # Username/email per SMTP
    mail_password = Column(String(200))  # Password per SMTP
    mail_default_sender = Column(String(200))  # Email mittente di default
    mail_max_emails = Column(Integer, default=100)  # Limite email per connessione
    mail_suppress_send = Column(Boolean, default=True)  # Disabilita invio in sviluppo
    mail_debug = Column(Boolean, default=False)  # Debug mode per mail
    
    # Numerazione Ricevute
    numero_ricevuta_iniziale = Column(Integer, default=1)  # Numero da cui iniziare la numerazione ricevute
    
    def __repr__(self):
        return f'<Settings {self.denominazione_sociale}>'
    
    @property
    def indirizzo_completo(self):
        """Restituisce l'indirizzo completo formattato"""
        parti = []
        if self.indirizzo:
            parti.append(self.indirizzo)
        if self.cap and self.citta:
            parti.append(f"{self.cap} {self.citta}")
        elif self.citta:
            parti.append(self.citta)
        if self.provincia:
            parti.append(f"({self.provincia})")
        return ', '.join(parti) if parti else None
    
    @staticmethod
    def _get_encryption_key():
        """Ottiene chiave di cifratura per database"""
        key = os.environ.get('DATABASE_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key().decode()
            print(f"⚠️ DATABASE_ENCRYPTION_KEY non trovata! Generata: {key}")
        return key.encode() if isinstance(key, str) else key
    
    def set_mail_password(self, password):
        """Imposta password email cifrata"""
        if password:
            fernet = Fernet(self._get_encryption_key())
            self.mail_password = fernet.encrypt(password.encode()).decode()
        else:
            self.mail_password = None
    
    def get_mail_password(self):
        """Ottiene password email decifrata"""
        if not self.mail_password:
            return None
        try:
            fernet = Fernet(self._get_encryption_key())
            return fernet.decrypt(self.mail_password.encode()).decode()
        except:
            return None
    
    @property
    def mail_configured(self):
        """Verifica se la configurazione email è completa"""
        return bool(
            self.mail_server and 
            self.mail_username and 
            self.mail_password and 
            self.mail_default_sender
        )
    
    @classmethod
    def get_settings(cls):
        """Ottiene l'istanza delle impostazioni (ne esiste sempre solo una)"""
        settings = cls.query.first()
        if not settings:
            # Crea impostazioni di default
            settings = cls(
                denominazione_sociale='Scuola di Danza',
                indirizzo='Via Roma 1',
                cap='00100',
                citta='Roma',
                provincia='RM',
                telefono='06 12345678',
                email='info@scuoladanza.it',
                # Configurazioni email di default
                mail_server='',
                mail_port=587,
                mail_use_tls=True,
                mail_use_ssl=False,
                mail_username='',
                mail_password='',
                mail_default_sender='',
                mail_max_emails=100,
                mail_suppress_send=True,
                mail_debug=False,
                # Numerazione ricevute
                numero_ricevuta_iniziale=1
            )
            db.session.add(settings)
            db.session.commit()
        return settings