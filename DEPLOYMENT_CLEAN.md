# 🚀 Guida al Deployment Pulito - Dance2Manage

## ✅ SCRIPT TESTATO E FUNZIONANTE

Questa guida usa il nuovo script `setup_database.py` che crea un database completo e funzionante.

## STEP 1: Preparazione Server VPS

```bash
# Connettiti al server
ssh debian@79.137.73.184
# Password: Temporanea2010!

# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa dipendenze di sistema
sudo apt install python3 python3-pip python3-venv git nginx supervisor sqlite3 -y
```

## STEP 2: Rimuovi Installazione Precedente

```bash
# Ferma servizi esistenti
sudo supervisorctl stop dance2manage 2>/dev/null || true
sudo supervisorctl stop miosito 2>/dev/null || true

# Rimuovi configurazioni vecchie
sudo rm -f /etc/supervisor/conf.d/dance2manage.conf
sudo rm -f /etc/supervisor/conf.d/miosito.conf
sudo rm -f /etc/nginx/sites-enabled/dance2manage
sudo rm -f /etc/nginx/sites-available/dance2manage

# Rimuovi directory progetto
sudo rm -rf /var/www/dance2manage
rm -rf ~/dance2manage

# Ricarica configurazioni
sudo supervisorctl reread
sudo supervisorctl update
sudo nginx -t && sudo systemctl reload nginx
```

## STEP 3: Clone Progetto Aggiornato

```bash
# Clona nella home directory (senza problemi di permessi)
cd ~
git clone https://github.com/Andrea-vent/dance2manage.git
cd dance2manage
```

## STEP 4: Setup Python Environment

```bash
# Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# Vai nella cartella app
cd gestionale_danza

# Installa tutte le dipendenze
pip install -r requirements.txt
```

## STEP 5: Inizializza Database (NUOVO SCRIPT)

```bash
# Esegui il nuovo script completo
python3 setup_database.py
```

**Dovresti vedere:**
```
🎭 DANCE2MANAGE - SETUP DATABASE COMPLETO
============================================================
📋 Credenziali di accesso:
   📧 Email: andreaventura79@gmail.com
   🔐 Password: uNIPOSCA2010!
   📧 Backup: admin@dance2manage.com
   🔐 Password: admin123
🚀 Il database è pronto per l'uso!
```

## STEP 6: Test Locale

```bash
# Test rapido dell'applicazione
python3 app.py

# Dovresti vedere: "Running on http://127.0.0.1:5000"
# Premi Ctrl+C per fermare
```

## STEP 7: Installa Gunicorn

```bash
# Assicurati che venv sia attivo
source ~/dance2manage/venv/bin/activate
pip install gunicorn
```

## STEP 8: Configurazione Nginx

```bash
sudo nano /etc/nginx/sites-available/dance2manage
```

**Contenuto file Nginx:**
```nginx
server {
    listen 80;
    server_name 79.137.73.184;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/debian/dance2manage/gestionale_danza/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 10M;
}
```

```bash
# Abilita il sito
sudo ln -s /etc/nginx/sites-available/dance2manage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## STEP 9: Configurazione Supervisor

```bash
sudo nano /etc/supervisor/conf.d/dance2manage.conf
```

**Contenuto Supervisor:**
```ini
[program:dance2manage]
command=/home/debian/dance2manage/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
directory=/home/debian/dance2manage/gestionale_danza
user=debian
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
environment=FLASK_ENV=production
stdout_logfile=/var/log/dance2manage.log
stderr_logfile=/var/log/dance2manage_error.log
```

```bash
# Avvia applicazione
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dance2manage
```

## STEP 10: Verifica Deployment

```bash
# Controlla status
sudo supervisorctl status dance2manage

# Test locale
curl http://127.0.0.1:8000

# Controlla log
sudo tail -20 /var/log/dance2manage.log
```

## STEP 11: Accesso Web

**URL:** `http://79.137.73.184`

**Credenziali principali:**
- Email: `andreaventura79@gmail.com`
- Password: `uNIPOSCA2010!`

**Credenziali di backup:**
- Email: `admin@dance2manage.com`
- Password: `admin123`

## 🔧 Risoluzione Problemi

**Se 502 Bad Gateway:**
```bash
sudo supervisorctl restart dance2manage
sudo tail -f /var/log/dance2manage_error.log
```

**Se problemi di permessi:**
```bash
sudo chown -R debian:debian ~/dance2manage
```

**Per vedere log in tempo reale:**
```bash
sudo tail -f /var/log/dance2manage.log
```

**Per riavviare tutto:**
```bash
sudo supervisorctl restart dance2manage
sudo systemctl reload nginx
```

## ✅ Checklist Deployment

- [ ] Server aggiornato
- [ ] Progetto clonato
- [ ] Virtual environment creato
- [ ] Dipendenze installate
- [ ] Database inizializzato con `setup_database.py`
- [ ] Gunicorn installato
- [ ] Nginx configurato
- [ ] Supervisor configurato
- [ ] Applicazione avviata
- [ ] Login funzionante

**Se tutti i punti sono ✅, l'applicazione è online e funzionante!** 🎉