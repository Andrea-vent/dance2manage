# 🚀 Guida al Deployment di Dance2Manage su VPS

## Prerequisiti sul VPS
```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa Python e strumenti necessari
sudo apt install python3 python3-pip python3-venv git nginx supervisor sqlite3 -y

# Verifica versione Python (deve essere >= 3.8)
python3 --version
```

## 1. Clona il Repository
```bash
cd ~/myflaskapp
git clone https://github.com/Andrea-vent/dance2manage.git
cd dance2manage

# Oppure se esiste già, aggiorna:
git pull origin feature/clienti-sorting-live-search
```

## 2. Crea Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

## 3. Installa Dipendenze
```bash
cd gestionale_danza
pip install -r requirements.txt

# Se mancano dipendenze, installa manualmente:
pip install Flask Flask-SQLAlchemy Flask-Security-Too python-dotenv
pip install reportlab pillow qrcode[pil] werkzeug
```

## 4. Configura Environment
```bash
# Copia e configura .env
cp .env.example .env
nano .env
```

Contenuto file `.env`:
```env
# Database
DATABASE_URL=sqlite:///data/database.db

# Flask-Security
SECRET_KEY=your-super-secret-key-here
SECURITY_PASSWORD_SALT=your-password-salt-here

# Email (opzionale)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Produzione
FLASK_ENV=production
FORCE_HTTPS=True
```

## 5. Inizializza Database
```bash
# Esegui lo script di inizializzazione
python3 init_database.py

# Verifica che sia stato creato
ls -la data/database.db
```

## 6. Test Locale
```bash
# Test rapido
python3 app.py

# Dovresti vedere: "Running on http://127.0.0.1:5000"
# Premi Ctrl+C per fermare
```

## 7. Configurazione Nginx
```bash
sudo nano /etc/nginx/sites-available/dance2manage
```

Contenuto file Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Sostituisci con il tuo dominio o IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/debian/myflaskapp/dance2manage/gestionale_danza/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Abilita il sito
sudo ln -s /etc/nginx/sites-available/dance2manage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Configurazione Supervisor
```bash
sudo nano /etc/supervisor/conf.d/dance2manage.conf
```

Contenuto file Supervisor:
```ini
[program:dance2manage]
command=/home/debian/myflaskapp/dance2manage/venv/bin/python app.py
directory=/home/debian/myflaskapp/dance2manage/gestionale_danza
user=debian
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
environment=FLASK_ENV=production,FORCE_HTTPS=True
stdout_logfile=/var/log/dance2manage.log
stderr_logfile=/var/log/dance2manage_error.log
```

```bash
# Ricarica configurazione Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dance2manage
```

## 9. Verifica Deployment
```bash
# Controlla status applicazione
sudo supervisorctl status dance2manage

# Controlla logs
sudo tail -f /var/log/dance2manage.log

# Test connessione
curl http://localhost:5000
```

## 10. Accesso all'Applicazione
- **URL:** `http://your-server-ip/`
- **Email:** `andreaventura79@gmail.com`
- **Password:** `uNIPOSCA2010!`

## 🔧 Comandi Utili per Manutenzione

```bash
# Aggiornare l'applicazione
cd ~/myflaskapp/dance2manage
git pull origin feature/clienti-sorting-live-search
sudo supervisorctl restart dance2manage

# Backup database
cp gestionale_danza/data/database.db backups/database_$(date +%Y%m%d).db

# Vedere logs errori
sudo tail -f /var/log/dance2manage_error.log

# Restart servizi
sudo supervisorctl restart dance2manage
sudo systemctl reload nginx
```

## 🛡️ Sicurezza (Opzionale)
```bash
# Firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# SSL con Let's Encrypt (se hai un dominio)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## ⚠️ Note Importanti
1. Sostituisci `your-domain.com` con il tuo dominio o IP
2. Cambia le chiavi segrete nel file `.env`
3. Il database SQLite funziona per progetti piccoli/medi
4. Per maggiore sicurezza, considera PostgreSQL per produzione
5. Fai backup regolari del database

## 🆘 Risoluzione Problemi
- Se non parte: controlla `sudo supervisorctl status`
- Se errori 502: controlla che l'app sia in ascolto su porta 5000
- Se errori database: verifica permessi cartella `data/`
- Logs dettagliati: `/var/log/dance2manage_error.log`