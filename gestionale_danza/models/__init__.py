# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import bcrypt

db = SQLAlchemy()
Base = declarative_base()

# Tabella di associazione per relazione molti-a-molti tra Clienti e Corsi
clienti_corsi = Table('clienti_corsi', db.Model.metadata,
    Column('cliente_id', Integer, ForeignKey('clienti.id'), primary_key=True),
    Column('corso_id', Integer, ForeignKey('corsi.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

from .cliente import Cliente
from .corso import Corso  
from .insegnante import Insegnante
from .pagamento import Pagamento
from .settings import Settings