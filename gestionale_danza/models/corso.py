# models/corso.py
from . import db, clienti_corsi
from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Corso(db.Model):
    __tablename__ = 'corsi'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    giorno = Column(String(20), nullable=False)  # Lunedì, Martedì, etc.
    orario = Column(Time, nullable=False)
    costo_mensile = Column(Integer, default=50)  # Costo mensile del corso
    max_iscritti = Column(Integer, default=20)
    data_creazione = Column(DateTime, default=datetime.now)
    
    # Chiave esterna verso Insegnante
    insegnante_id = Column(Integer, ForeignKey('insegnanti.id'), nullable=False)
    
    # Relazione molti-a-uno con Insegnante
    insegnante = relationship('Insegnante', back_populates='corsi')
    
    # Relazione molti-a-molti con Clienti
    clienti = relationship('Cliente', secondary=clienti_corsi, back_populates='corsi')
    
    # Relazione uno-a-molti con Pagamenti
    pagamenti = relationship('Pagamento', back_populates='corso', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Corso {self.nome} - {self.giorno} {self.orario}>'
    
    @property
    def numero_iscritti(self):
        return len(self.clienti)
    
    @property
    def posti_disponibili(self):
        return self.max_iscritti - self.numero_iscritti