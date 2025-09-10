# models/insegnante.py
from . import db
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

class Insegnante(db.Model):
    __tablename__ = 'insegnanti'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    telefono = Column(String(20))
    email = Column(String(120))
    percentuale_guadagno = Column(Float, default=30.0)  # Percentuale sui pagamenti del corso
    
    # Relazione uno-a-molti con Corsi
    corsi = relationship('Corso', back_populates='insegnante', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Insegnante {self.nome} {self.cognome}>'
    
    @property
    def nome_completo(self):
        return f"{self.nome} {self.cognome}"
    
    @property
    def numero_corsi(self):
        return len(self.corsi)
    
    def calcola_guadagno_corso(self, corso, mese=None, anno=None):
        """Calcola il guadagno dell'insegnante per un corso in un periodo specifico"""
        from .pagamento import Pagamento
        
        query = Pagamento.query.filter_by(corso_id=corso.id, pagato=True)
        
        if mese:
            query = query.filter_by(mese=mese)
        if anno:
            query = query.filter_by(anno=anno)
        
        pagamenti = query.all()
        incasso_totale = sum(p.importo for p in pagamenti)
        guadagno = incasso_totale * (self.percentuale_guadagno / 100)
        
        return {
            'incasso_totale': incasso_totale,
            'percentuale': self.percentuale_guadagno,
            'guadagno': guadagno,
            'numero_pagamenti': len(pagamenti)
        }