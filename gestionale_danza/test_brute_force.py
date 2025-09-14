#!/usr/bin/env python3
"""Test brute force protection"""

import requests
import time

def test_brute_force():
    """Testa la protezione brute force"""
    base_url = "http://localhost:5000"
    login_url = f"{base_url}/login"
    
    print("🔒 Testing Brute Force Protection")
    print("=" * 50)
    
    # Prima ottieni la pagina di login per ottenere il CSRF token
    session = requests.Session()
    
    for i in range(1, 8):  # Prova 7 volte (dovrebbe bloccare dopo 5)
        print(f"\n📡 Tentativo {i}/7...")
        
        try:
            # GET della pagina login
            response = session.get(login_url)
            if response.status_code == 429:
                print(f"✅ BLOCCATO al tentativo {i}! Status: {response.status_code}")
                print("🎉 Brute force protection funziona correttamente!")
                break
                
            # POST con credenziali sbagliate
            login_data = {
                'email': 'test@example.com',
                'password': 'wrong_password'
            }
            
            response = session.post(login_url, data=login_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 429:
                print(f"✅ BLOCCATO al tentativo {i}! Status: {response.status_code}")
                print("🎉 Brute force protection funziona correttamente!")
                break
            elif i == 7:
                print("❌ NON è stato bloccato dopo 7 tentativi")
                
        except requests.exceptions.ConnectionError:
            print("❌ Errore di connessione - assicurati che l'app sia in esecuzione")
            break
        except Exception as e:
            print(f"❌ Errore: {e}")
            break
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    test_brute_force()