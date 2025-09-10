# models/settings.py
from . import db
from sqlalchemy import Column, Integer, String, Text

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
    note = Column(Text)
    
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
                email='info@scuoladanza.it'
            )
            db.session.add(settings)
            db.session.commit()
        return settings