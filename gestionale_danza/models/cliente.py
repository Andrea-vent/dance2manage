# models/cliente.py
from . import db, clienti_corsi
from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import date
import re

class Cliente(db.Model):
    __tablename__ = 'clienti'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    codice_fiscale = Column(String(16))
    telefono = Column(String(20))
    email = Column(String(120))
    
    # Campi indirizzo
    via = Column(String(200))
    civico = Column(String(10))
    cap = Column(String(10))
    citta = Column(String(100))
    provincia = Column(String(2))
    
    # Data di nascita
    data_nascita = Column(Date)
    
    # Luogo di nascita
    comune_nascita = Column(String(100))
    provincia_nascita = Column(String(2))
    
    # Sesso
    sesso = Column(String(1))  # M o F
    
    # Flag per codice fiscale calcolato automaticamente
    cf_calcolato_automaticamente = Column(Boolean, default=False)
    
    # Riferimenti genitori (per minorenni)
    nome_cognome_madre = Column(String(200))
    telefono_madre = Column(String(20))
    nome_cognome_padre = Column(String(200))
    telefono_padre = Column(String(20))
    
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
    
    @property
    def eta(self):
        """Calcola l'età del cliente dalla data di nascita"""
        if not self.data_nascita:
            return None
        
        today = date.today()
        return today.year - self.data_nascita.year - ((today.month, today.day) < (self.data_nascita.month, self.data_nascita.day))
    
    @property
    def is_minorenne(self):
        """Determina se il cliente è minorenne (< 18 anni)"""
        eta = self.eta
        return eta is not None and eta < 18
    
    @property 
    def ha_riferimenti_genitori(self):
        """Verifica se ci sono riferimenti dei genitori inseriti"""
        return bool(self.nome_cognome_madre or self.nome_cognome_padre)
    
    @property
    def puo_calcolare_cf(self):
        """Verifica se è possibile calcolare il codice fiscale automaticamente"""
        return all([
            self.nome and self.nome.strip(),
            self.cognome and self.cognome.strip(),
            self.data_nascita,
            self.comune_nascita and self.comune_nascita.strip(),
            self.provincia_nascita and self.provincia_nascita.strip(),
            self.sesso in ['M', 'F']
        ])
    
    def calcola_codice_fiscale(self):
        """Calcola il codice fiscale italiano basato sui dati anagrafici"""
        if not self.puo_calcolare_cf:
            return None
        
        # Consonanti e vocali per cognome e nome
        def estrai_consonanti_vocali(testo):
            testo = testo.upper().replace(' ', '')
            consonanti = ''.join([c for c in testo if c.isalpha() and c not in 'AEIOU'])
            vocali = ''.join([c for c in testo if c in 'AEIOU'])
            return consonanti, vocali
        
        def codifica_nome_cognome(testo, is_nome=False):
            consonanti, vocali = estrai_consonanti_vocali(testo)
            
            if is_nome and len(consonanti) >= 4:
                # Per il nome, se ci sono 4+ consonanti, prendi 1°, 3°, 4°
                return consonanti[0] + consonanti[2] + consonanti[3]
            elif len(consonanti) >= 3:
                # Prendi le prime 3 consonanti
                return consonanti[:3]
            else:
                # Prendi consonanti + vocali fino a 3 caratteri
                result = consonanti + vocali
                return (result + 'XXX')[:3]
        
        # Codifica cognome (prime 3 consonanti)
        cf_cognome = codifica_nome_cognome(self.cognome)
        
        # Codifica nome
        cf_nome = codifica_nome_cognome(self.nome, is_nome=True)
        
        # Anno di nascita (ultime 2 cifre)
        cf_anno = str(self.data_nascita.year)[-2:]
        
        # Mese di nascita
        mesi_cf = {
            1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'H',
            7: 'L', 8: 'M', 9: 'P', 10: 'R', 11: 'S', 12: 'T'
        }
        cf_mese = mesi_cf[self.data_nascita.month]
        
        # Giorno di nascita (+ 40 per le femmine)
        cf_giorno = self.data_nascita.day
        if self.sesso == 'F':
            cf_giorno += 40
        cf_giorno = f"{cf_giorno:02d}"
        
        # Codice comune (semplificato - useremo un codice generico basato su provincia)
        # In un'implementazione completa, questo dovrebbe essere un lookup da una tabella ufficiale
        cf_comune = self._get_codice_comune_semplificato()
        
        # Costruisci CF senza carattere di controllo
        cf_parziale = cf_cognome + cf_nome + cf_anno + cf_mese + cf_giorno + cf_comune
        
        # Calcola carattere di controllo
        carattere_controllo = self._calcola_carattere_controllo(cf_parziale)
        
        return cf_parziale + carattere_controllo
    
    def _get_codice_comune_semplificato(self):
        """Restituisce un codice comune semplificato basato sulla provincia"""
        # Mapping semplificato provincia -> codice comune generico
        # In produzione, dovrebbe essere sostituito con una tabella completa dei comuni
        codici_provincia = {
            'AG': 'A000', 'AL': 'A001', 'AN': 'A002', 'AO': 'A003', 'AR': 'A004',
            'AP': 'A005', 'AT': 'A006', 'AV': 'A007', 'BA': 'B000', 'BT': 'B001',
            'BL': 'B002', 'BN': 'B003', 'BG': 'B004', 'BI': 'B005', 'BO': 'B006',
            'BZ': 'B007', 'BS': 'B008', 'BR': 'B009', 'CA': 'C000', 'CL': 'C001',
            'CB': 'C002', 'CI': 'C003', 'CE': 'C004', 'CT': 'C005', 'CZ': 'C006',
            'CH': 'C007', 'CO': 'C008', 'CS': 'C009', 'CR': 'C010', 'KR': 'C011',
            'CN': 'C012', 'EN': 'E000', 'FM': 'F000', 'FE': 'F001', 'FI': 'F002',
            'FG': 'F003', 'FC': 'F004', 'FR': 'F005', 'GE': 'G000', 'GO': 'G001',
            'GR': 'G002', 'IM': 'I000', 'IS': 'I001', 'SP': 'S000', 'AQ': 'A008',
            'LT': 'L000', 'LE': 'L001', 'LC': 'L002', 'LI': 'L003', 'LO': 'L004',
            'LU': 'L005', 'MC': 'M000', 'MN': 'M001', 'MS': 'M002', 'MT': 'M003',
            'VS': 'V000', 'ME': 'M004', 'MI': 'M005', 'MO': 'M006', 'MB': 'M007',
            'NA': 'N000', 'NO': 'N001', 'NU': 'N002', 'OG': 'O000', 'OT': 'O001',
            'OR': 'O002', 'PD': 'P000', 'PA': 'P001', 'PR': 'P002', 'PV': 'P003',
            'PG': 'P004', 'PU': 'P005', 'PE': 'P006', 'PC': 'P007', 'PI': 'P008',
            'PT': 'P009', 'PN': 'P010', 'PZ': 'P011', 'PO': 'P012', 'RG': 'R000',
            'RA': 'R001', 'RC': 'R002', 'RE': 'R003', 'RI': 'R004', 'RN': 'R005',
            'RM': 'R006', 'RO': 'R007', 'SA': 'S001', 'SS': 'S002', 'SV': 'S003',
            'SI': 'S004', 'SR': 'S005', 'SO': 'S006', 'TA': 'T000', 'TE': 'T001',
            'TR': 'T002', 'TO': 'T003', 'TP': 'T004', 'TN': 'T005', 'TV': 'T006',
            'TS': 'T007', 'UD': 'U000', 'VA': 'V001', 'VE': 'V002', 'VB': 'V003',
            'VC': 'V004', 'VR': 'V005', 'VV': 'V006', 'VI': 'V007', 'VT': 'V008'
        }
        
        provincia = self.provincia_nascita.upper() if self.provincia_nascita else 'RM'
        return codici_provincia.get(provincia, 'A000')
    
    def _calcola_carattere_controllo(self, cf_parziale):
        """Calcola il carattere di controllo del codice fiscale"""
        # Valori per posizioni dispari (1-based)
        valori_dispari = {
            '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19, '9': 21,
            'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17, 'I': 19, 'J': 21,
            'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
            'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
        }
        
        # Valori per posizioni pari (1-based)
        valori_pari = {
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
            'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
            'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
        }
        
        # Caratteri di controllo
        caratteri_controllo = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        somma = 0
        for i, char in enumerate(cf_parziale):
            if i % 2 == 0:  # posizione dispari (0-based)
                somma += valori_dispari.get(char, 0)
            else:  # posizione pari (0-based)
                somma += valori_pari.get(char, 0)
        
        return caratteri_controllo[somma % 26]
    
    def aggiorna_codice_fiscale_se_possibile(self):
        """Aggiorna automaticamente il codice fiscale se possibile"""
        if self.puo_calcolare_cf:
            cf_calcolato = self.calcola_codice_fiscale()
            if cf_calcolato:
                self.codice_fiscale = cf_calcolato
                self.cf_calcolato_automaticamente = True
                return True
        return False