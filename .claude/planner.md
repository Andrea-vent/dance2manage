Crea un'applicazione gestionale per una scuola di danza che giri interamente da chiavetta USB, senza installazione. Deve essere una web app Flask con salvataggio locale via SQLite (file .db nella cartella /data). Deve essere pronta per essere compilata in un singolo .exe con PyInstaller (--onefile) su Windows 10/11.

Segui tutte le specifiche tecniche, la struttura progetto e le funzionalità minime richieste indicate in questo documento. Genera tutto il codice (file .py, template HTML Jinja2, CSS, file .spec per PyInstaller, avvia.bat), un requirements.txt, istruzioni passo-passo per creare l'.exe e note di compatibilità/installation su Windows (specialmente per la generazione PDF con WeasyPrint). Fornisci inoltre esempi di comandi PyInstaller e suggerimenti per risolvere problemi comuni su Windows.

🎯 Obiettivi principali — cosa deve fare l’app
Web app Flask accessibile localmente (es. http://localhost:5000).
Anagrafica clienti (nome, cognome, telefono, email, attivo/inattivo).
Gestione corsi (nome, giorno, orario, insegnante, iscritti).
Gestione insegnanti (nome, contatti, corsi insegnati).
Gestione mensilità e pagamenti (mese, anno, importo, stato pagato/non pagato; collegamento cliente ⇄ corso).
Generazione e salvataggio PDF ricevute (cartella /pdf_ricevute) da template HTML (WeasyPrint preferito; reportlab come alternativa).
Salvataggio locale con SQLite (file data/database.db creato al primo avvio).
Autenticazione base (username/password) — login obbligatorio.
Funzione di backup: esportare il file database.db in uno zip.
Tutto deve funzionare offline su Windows (tranne Bootstrap via CDN è permesso).
📁 Struttura progetto da generare


1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
gestionale_danza/
│
├── app.py
├── requirements.txt
├── gestionale.spec
├── avvia.bat
├── /templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── clienti.html
│   ├── cliente_form.html
│   ├── corsi.html
│   ├── corso_form.html
│   ├── insegnanti.html
│   ├── insegnante_form.html
│   ├── pagamenti.html
│   ├── pagamento_form.html
│   ├── ricevuta.html
│
├── /static
│   ├── style.css
│
├── /data
│   └── database.db         # (creato al primo avvio)
│
├── /pdf_ricevute
│
├── /models
│   ├── __init__.py
│   ├── cliente.py
│   ├── corso.py
│   ├── insegnante.py
│   └── pagamento.py
│
├── /utils
│   ├── __init__.py
│   └── stampa_pdf.py
🧰 Tecnologie e librerie richieste (da mettere in requirements.txt)
Genera un requirements.txt con almeno:



1
2
3
4
5
6
7
8
flask
sqlalchemy
weasyprint
jinja2
werkzeug
pillow
bcrypt
pyinstaller
Aggiungi altre dipendenze necessarie (es. zipfile, datetime, tempfile, shutil per backup).

🔧 Requisiti funzionali dettagliati
Autenticazione: login semplice con credenziali memorizzate nella stessa DB (username e password hashed). Schermata di login obbligatoria.
Dashboard: riepilogo clienti, corsi attivi, pagamenti del mese corrente.
Clienti: elenco, ricerca, creazione/modifica, stato attivo/inattivo, associazione a corsi (molti-a-molti).
Corsi: nome, giorno, orario, insegnante; lista iscritti e numero massimo opzionale.
Insegnanti: anagrafica e lista corsi assegnati.
Pagamenti: inserimento mensilità (mese, anno, importo), stato, collegamento a cliente e corso; filtri per mese/cliente/corso; segnalazione debiti.
Ricevute PDF: template HTML (ricevuta.html) convertito in PDF con WeasyPrint; salvataggio in /pdf_ricevute con numerazione progressiva (es. RICEVUTA-00001.pdf). Link per scaricare/visualizzare.
Backup: pulsante per esportare data/database.db in uno zip (nome con timestamp) e scaricarlo.
Esecuzione: app.py avvia Flask locale (porta configurabile), avvia.bat per utenti Windows (lancia .exe o python app.py).
Packaging: file gestionale.spec ottimizzato per PyInstaller (--onefile); assicurarsi che templates, static, pdf_ricevute, data siano inclusi.
⚠️ Requisiti non funzionali e vincoli
Il progetto deve essere leggibile e ben commentato.
Deve funzionare su Windows 10/11.
Deve limitare l'uso di internet al solo CDN per Bootstrap (opzionale).
Non usare servizi cloud esterni.
Assicurare che il .exe generato contenga tutto (risorse, templates, DB se già presente) o crei i file necessari alla prima esecuzione nella stessa cartella/chiavetta.
📤 Output richiesto (obbligatorio)
Restituisci tutto in una sola risposta, nel seguente ordine:

L’albero dei file (come sopra) con il contenuto completo di ogni file.
Per ogni file, usa:


1
2
3
=== FILE: gestionale_danza/app.py ===
```python
[codice]
requirements.txt completo.
Istruzioni passo-passo per creare l'.exe con PyInstaller su Windows (con flag consigliati: --onefile, --add-data, --hidden-import, ecc.).
Esempio di comando PyInstaller (es. pyinstaller --onefile gestionale_danza/app.py ...) e spiegazione dei flag.
Note di compatibilità Windows e PDF (WeasyPrint): dipendenze binarie (GTK, Cairo, Pango), workaround con reportlab, inclusione risorse statiche nell'.exe.
Suggerimenti per test su chiavetta USB: struttura della chiavetta, permessi, lancio di avvia.bat, gestione del file database.db per più utenti.
Note di sicurezza minime: hashing password, backup, bind su localhost, debug off.
✍️ Linee guida per la generazione del codice
Codice funzionante e logico (non snippet spezzati).
Commenti in ogni file.
Template HTML con Bootstrap via CDN + Jinja2.
Schema SQLAlchemy con relazioni (Clienti ⇄ Corsi many-to-many, Pagamenti → Cliente & Corso).
stampa_pdf.py usa WeasyPrint per generare PDF da ricevuta.html e salvarlo in /pdf_ricevute con numerazione automatica.
gestionale.spec include templates, static, pdf_ricevute, data, modelli Python.
avvia.bat rileva se c’è gestionale.exe o esegue python app.py.
Nessuna chiamata a API o servizi esterni.
📝 Formato della risposta (obbligatorio)
Restituire prima l’albero dei file.
Poi tutti i file con intestazione:


1
2
3
=== FILE: gestionale_danza/app.py ===
```python
[codice]
Alla fine:
Istruzioni per PyInstaller
Note Windows/WeasyPrint
Suggerimenti per la chiavetta USB
Evitare spiegazioni prolisse: fornire codice e brevi note operative.
Se un componente ha alternative (es. WeasyPrint vs reportlab), fornire entrambe o spiegare come passare da una all'altra.
📄 Esempio di formattazione


1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
=== FILE: gestionale_danza/models/cliente.py ===
```python
# models/cliente.py
from sqlalchemy import Column, Integer, String, Boolean
from . import Base

class Cliente(Base):
    __tablename__ = 'clienti'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)
    telefono = Column(String)
    email = Column(String)
    attivo = Column(Boolean, default=True)
    # relazione con corsi definita in models/__init__.py
