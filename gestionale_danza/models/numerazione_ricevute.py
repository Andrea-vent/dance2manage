# models/numerazione_ricevute.py
from . import db
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class NumerazioneRicevute(db.Model):
    __tablename__ = 'numerazione_ricevute'
    
    id = Column(Integer, primary_key=True)
    anno = Column(Integer, nullable=False, unique=True)  # Anno di riferimento
    ultimo_numero = Column(Integer, nullable=False, default=0)  # Ultimo numero utilizzato
    numero_iniziale = Column(Integer, nullable=False, default=1)  # Numero da cui iniziare (configurabile)
    data_creazione = Column(DateTime, default=datetime.now)
    data_aggiornamento = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<NumerazioneRicevute {self.anno}: {self.ultimo_numero}>'
    
    @classmethod
    def get_prossimo_numero(cls, anno):
        """
        Ottiene il prossimo numero di ricevuta per l'anno specificato.
        Se l'anno non esiste, lo crea partendo dal numero iniziale impostato nelle configurazioni.
        """
        from .settings import Settings
        
        # Cerca il record per l'anno corrente
        numerazione = cls.query.filter_by(anno=anno).first()
        
        if not numerazione:
            # Se non esiste, crea un nuovo record per l'anno
            settings = Settings.get_settings()
            numero_iniziale = getattr(settings, 'numero_ricevuta_iniziale', 1)
            
            numerazione = cls(
                anno=anno,
                ultimo_numero=numero_iniziale,
                numero_iniziale=numero_iniziale
            )
            db.session.add(numerazione)
            db.session.commit()
            return numero_iniziale
        else:
            # Se esiste, incrementa il numero
            numerazione.ultimo_numero += 1
            numerazione.data_aggiornamento = datetime.now()
            db.session.commit()
            return numerazione.ultimo_numero
    
    @classmethod
    def get_ultimo_numero(cls, anno):
        """
        Ottiene l'ultimo numero utilizzato per l'anno specificato senza incrementarlo.
        """
        numerazione = cls.query.filter_by(anno=anno).first()
        return numerazione.ultimo_numero if numerazione else 0
    
    @classmethod
    def imposta_numero_iniziale(cls, anno, numero_iniziale):
        """
        Imposta il numero iniziale per un anno specifico.
        Utilizzato principalmente per la prima configurazione.
        """
        numerazione = cls.query.filter_by(anno=anno).first()
        
        if not numerazione:
            numerazione = cls(
                anno=anno,
                ultimo_numero=numero_iniziale - 1,  # -1 perché get_prossimo_numero incrementerà
                numero_iniziale=numero_iniziale
            )
            db.session.add(numerazione)
        else:
            # Se esiste già, aggiorna solo se non sono state ancora emesse ricevute
            if numerazione.ultimo_numero == numerazione.numero_iniziale:
                numerazione.numero_iniziale = numero_iniziale
                numerazione.ultimo_numero = numero_iniziale - 1
            else:
                raise ValueError(f"Non è possibile modificare il numero iniziale per l'anno {anno}: sono già state emesse ricevute")
        
        db.session.commit()
        return numerazione