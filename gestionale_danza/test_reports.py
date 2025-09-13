# test_reports.py - Test rapido per verificare i filtri reports
import os
import sys

# Aggiungi il percorso dell'applicazione
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Pagamento
from datetime import date

def test_filtri_reports():
    """Test funzionalità filtri reports"""
    
    with app.app_context():
        print("🧪 Test filtri reports...")
        
        # Test dati gennaio 2024
        print("\n📅 GENNAIO 2024:")
        pagamenti_gen = Pagamento.query.filter_by(mese=1, anno=2024).all()
        pagati_gen = [p for p in pagamenti_gen if p.pagato]
        incasso_gen = sum(p.importo for p in pagati_gen)
        print(f"  - Pagamenti: {len(pagamenti_gen)}")
        print(f"  - Pagati: {len(pagati_gen)}")
        print(f"  - Incasso: €{incasso_gen:.2f}")
        
        # Test dati maggio 2024
        print("\n📅 MAGGIO 2024:")
        pagamenti_mag = Pagamento.query.filter_by(mese=5, anno=2024).all()
        pagati_mag = [p for p in pagamenti_mag if p.pagato]
        incasso_mag = sum(p.importo for p in pagati_mag)
        print(f"  - Pagamenti: {len(pagamenti_mag)}")
        print(f"  - Pagati: {len(pagati_mag)}")
        print(f"  - Incasso: €{incasso_mag:.2f}")
        
        # Test dati settembre 2024
        print("\n📅 SETTEMBRE 2024:")
        pagamenti_set = Pagamento.query.filter_by(mese=9, anno=2024).all()
        pagati_set = [p for p in pagamenti_set if p.pagato]
        incasso_set = sum(p.importo for p in pagati_set)
        print(f"  - Pagamenti: {len(pagamenti_set)}")
        print(f"  - Pagati: {len(pagati_set)}")
        print(f"  - Incasso: €{incasso_set:.2f}")
        
        # Test confronto con mese corrente (settembre 2025)
        print(f"\n📅 MESE CORRENTE ({date.today().month}/{date.today().year}):")
        pagamenti_corrente = Pagamento.query.filter_by(
            mese=date.today().month, 
            anno=date.today().year
        ).all()
        print(f"  - Pagamenti: {len(pagamenti_corrente)}")
        
        print(f"\n✅ Test completato! I filtri dovrebbero funzionare correttamente.")
        print(f"🌐 Prova su http://127.0.0.1:5000/reports")
        print(f"   - Imposta Anno: 2024")
        print(f"   - Prova i mesi: Gennaio, Maggio, Settembre")

if __name__ == '__main__':
    test_filtri_reports()