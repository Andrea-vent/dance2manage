# models/pagamento.py
from . import db
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Pagamento(db.Model):
    __tablename__ = 'pagamenti'
    
    id = Column(Integer, primary_key=True)
    mese = Column(Integer, nullable=False)  # 1-12
    anno = Column(Integer, nullable=False)
    importo = Column(Float, nullable=False)
    pagato = Column(Boolean, default=False)
    data_pagamento = Column(DateTime)
    data_creazione = Column(DateTime, default=datetime.now)
    metodo_pagamento = Column(String(50), default='Contanti')  # Contanti, Bonifico, Bancomat, Carta di credito
    note = Column(String(500))
    
    # Chiavi esterne
    cliente_id = Column(Integer, ForeignKey('clienti.id'), nullable=False)
    corso_id = Column(Integer, ForeignKey('corsi.id'), nullable=False)
    
    # Relazioni
    cliente = relationship('Cliente', back_populates='pagamenti')
    corso = relationship('Corso', back_populates='pagamenti')
    
    def __repr__(self):
        return f'<Pagamento {self.mese}/{self.anno} - {self.cliente.nome_completo} - €{self.importo}>'
    
    @property
    def mese_nome(self):
        mesi = {
            1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
            5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
            9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
        }
        return mesi.get(self.mese, 'Sconosciuto')
    
    @property
    def periodo(self):
        return f"{self.mese_nome} {self.anno}"
    
    def marca_pagato(self):
        self.pagato = True
        self.data_pagamento = datetime.now()