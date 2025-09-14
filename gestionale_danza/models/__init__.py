# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()
Base = declarative_base()

# Tabella di associazione per relazione molti-a-molti tra Clienti e Corsi
clienti_corsi = Table('clienti_corsi', db.Model.metadata,
    Column('cliente_id', Integer, ForeignKey('clienti.id'), primary_key=True),
    Column('corso_id', Integer, ForeignKey('corsi.id'), primary_key=True)
)

from .user import User, Role, WebAuthn
from .cliente import Cliente
from .corso import Corso  
from .insegnante import Insegnante
from .pagamento import Pagamento
from .settings import Settings
from .numerazione_ricevute import NumerazioneRicevute