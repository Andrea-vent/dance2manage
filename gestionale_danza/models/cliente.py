# models/cliente.py
from . import db, clienti_corsi
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class Cliente(db.Model):
    __tablename__ = 'clienti'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    codice_fiscale = Column(String(16))
    telefono = Column(String(20))
    email = Column(String(120))
    attivo = Column(Boolean, default=True)
    
    # Relazione molti-a-molti con Corsi
    corsi = relationship('Corso', secondary=clienti_corsi, back_populates='clienti')
    
    # Relazione uno-a-molti con Pagamenti
    pagamenti = relationship('Pagamento', back_populates='cliente', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cliente {self.nome} {self.cognome}>'
    
    @property
    def nome_completo(self):
        return f"{self.nome} {self.cognome}"