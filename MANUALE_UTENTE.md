# Dance2Manager - Manuale Utente

## Indice
1. [Introduzione](#introduzione)
2. [Installazione e Avvio](#installazione-e-avvio)
3. [Primo Accesso](#primo-accesso)
4. [Gestione Clienti](#gestione-clienti)
5. [Gestione Insegnanti](#gestione-insegnanti)
6. [Gestione Corsi](#gestione-corsi)
7. [Gestione Pagamenti](#gestione-pagamenti)
8. [Report e Statistiche](#report-e-statistiche)
9. [Impostazioni Azienda](#impostazioni-azienda)
10. [Backup e Sicurezza](#backup-e-sicurezza)

## Introduzione

**Dance2Manager** è un software gestionale completo per scuole di danza che permette di:
- Gestire anagrafica clienti con dati fiscali
- Organizzare corsi con orari e insegnanti
- Tracciare pagamenti e generare ricevute PDF
- Calcolare compensi insegnanti automaticamente
- Produrre report finanziari dettagliati
- Gestire dati aziendali per fatturazione

Il software è completamente portatile e funziona senza installazione da chiavetta USB.

## Installazione e Avvio

### Requisiti di Sistema
- Windows 10/11
- 100MB di spazio libero
- Nessuna installazione richiesta

### Primo Avvio
1. Copiare la cartella `Dance2Manager` sulla chiavetta USB
2. Aprire la cartella `gestionale_danza`
3. Eseguire `python app.py` da prompt dei comandi
4. Aprire il browser all'indirizzo: `http://127.0.0.1:5000`

### Login Iniziale
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **IMPORTANTE**: Cambiare la password dopo il primo accesso

## Primo Accesso

### 1. Configurazione Dati Azienda
Prima di iniziare, configurare i dati della scuola di danza:
1. Andare su **Impostazioni Azienda** dal menu utente
2. Inserire:
   - Denominazione sociale
   - Indirizzo completo
   - Partita IVA (formato: 11 cifre)
   - Codice Fiscale
   - Telefono ed email
3. Salvare le impostazioni

### 2. Inizializzazione Database
Se si parte da zero:
```bash
cd gestionale_danza
python seeder.py --reset
```
Questo comando crea dati di esempio per testare il sistema.

## Gestione Clienti

### Aggiungere un Nuovo Cliente
1. Andare su **Clienti** dalla navbar
2. Cliccare **Nuovo Cliente**
3. Compilare i campi obbligatori:
   - Nome e Cognome
   - Data di nascita
   - Codice Fiscale (opzionale ma consigliato)
   - Contatti (telefono, email)
4. Salvare

### Iscrivere Cliente a un Corso
1. Aprire la scheda del cliente
2. Nella sezione **Iscrizioni**, cliccare **Iscriviti a Corso**
3. Selezionare il corso desiderato
4. Il sistema creerà automaticamente i pagamenti mensili

### Gestione Dati Cliente
- **Modifica**: Cliccare l'icona matita nella lista clienti
- **Visualizza**: Cliccare sul nome per vedere dettagli e pagamenti
- **Elimina**: ⚠️ Elimina anche tutti i pagamenti associati

## Gestione Insegnanti

### Aggiungere Insegnante
1. Andare su **Insegnanti**
2. Cliccare **Nuovo Insegnante**
3. Inserire dati anagrafici
4. **IMPORTANTE**: Impostare la **percentuale di guadagno** (es. 30% = inserire 30)

### Percentuale Guadagno
La percentuale determina quanto l'insegnante guadagna dagli incassi del corso:
- **Esempio**: Corso incassa €1000, insegnante al 30% riceve €300
- La percentuale si applica solo ai pagamenti effettivamente ricevuti
- Modificabile in qualsiasi momento

## Gestione Corsi

### Creare un Nuovo Corso
1. Andare su **Corsi**
2. Cliccare **Nuovo Corso**
3. Compilare:
   - Nome corso (es. "Danza Classica Principianti")
   - Giorno della settimana
   - Orario (formato 24h)
   - Prezzo mensile
   - Assegnare insegnante
4. Salvare

### Corsi con Orari Multipli
**Per lo stesso tipo di danza in orari diversi, creare corsi separati:**
- "Danza Classica Principianti - Lunedì 18:00"
- "Danza Classica Principianti - Mercoledì 19:00"
- "Danza Classica Principianti - Sabato 10:00"

Ogni corso gestisce separatamente:
- Iscrizioni
- Pagamenti
- Compensi insegnante

### Gestione Iscrizioni
- La lista iscritti è visibile nella scheda corso
- I clienti si iscrivono dalla propria scheda anagrafica
- Il sistema genera automaticamente i pagamenti mensili

## Gestione Pagamenti

### Registrare un Pagamento
1. Andare su **Pagamenti**
2. Trovare il pagamento in stato "Non Pagato"
3. Cliccare **Segna come Pagato**
4. Il sistema aggiorna automaticamente:
   - Data pagamento
   - Stato del pagamento
   - Calcoli per report

### Generare Ricevuta PDF
1. Nella lista pagamenti, cliccare **Ricevuta PDF**
2. Il sistema genera automaticamente:
   - Ricevuta con dati azienda
   - Informazioni cliente (incluso Codice Fiscale)
   - Dettagli corso e importo
   - Numerazione progressiva

### Filtri Pagamenti
- **Per periodo**: Filtrare per mese/anno
- **Per stato**: Solo pagati/non pagati
- **Per cliente**: Cercare per nome
- **Per corso**: Filtrare per corso specifico

## Report e Statistiche

### Accedere ai Report
1. Andare su **Report** dalla navbar
2. Selezionare mese e anno
3. Cliccare **Genera Report**

### Report Generale
Il riepilogo mostra:
- **Incasso Totale**: Somma di tutti i pagamenti del periodo
- **Compensi Insegnanti**: Totale da pagare agli insegnanti
- **Utile Netto**: Differenza tra incassi e compensi
- **Numero Pagamenti**: Quantità pagamenti processati

### Report per Corso
Tabella dettagliata con:
- Nome corso e insegnante
- Numero iscritti vs pagamenti ricevuti
- Incasso specifico del corso
- Percentuale e compenso insegnante
- Utile netto del corso

### Report per Insegnante
Riassunto per ogni insegnante:
- Lista corsi assegnati
- Incasso totale dai propri corsi
- Percentuale media applicata
- Compenso totale da ricevere

### Esportazione Report
- **Stampa**: Cliccare "Stampa" per versione stampabile
- **Excel**: Cliccare "Esporta Excel" per foglio di calcolo

## Impostazioni Azienda

### Dati Obbligatori
- **Denominazione Sociale**: Nome ufficiale della scuola
- Questi dati appaiono su tutte le ricevute generate

### Dati Opzionali
- **Indirizzo**: Via, CAP, città, provincia
- **Partita IVA**: 11 cifre numeriche
- **Codice Fiscale**: 16 caratteri alfanumerici
- **Contatti**: Telefono, email, sito web
- **Note**: Informazioni aggiuntive

### Anteprima Dati
La sezione "Anteprima" mostra come appariranno i dati nelle ricevute.

## Backup e Sicurezza

### Backup Database
1. Dal menu utente, selezionare **Backup Database**
2. Il sistema scarica il file `backup_YYYYMMDD_HHMMSS.db`
3. Conservare il backup in luogo sicuro

### Backup Manuale
Il database si trova in: `gestionale_danza/database.db`
Copiare questo file per backup manuale.

### Ripristino
Per ripristinare un backup:
1. Fermare l'applicazione
2. Sostituire `database.db` con il file di backup
3. Riavviare l'applicazione

### Sicurezza Password
- Cambiare la password predefinita
- Non condividere le credenziali
- Fare backup regolari

## Domande Frequenti

### Il software funziona offline?
Sì, completamente offline. Richiede solo Python installato.

### Posso usarlo su più computer?
Sì, copiando la cartella sulla chiavetta USB.

### Quanti clienti può gestire?
Illimitati, dipende solo dallo spazio di archiviazione.

### Come aggiorno il software?
Sostituire i file Python mantenendo il database.

### Posso personalizzare le ricevute?
Sì, modificando il template `templates/ricevuta.html`.

## Supporto Tecnico

Per problemi tecnici:
1. Verificare che Python sia installato
2. Controllare che la porta 5000 sia libera
3. Consultare i log dell'applicazione
4. Verificare i permessi di scrittura sulla cartella

## Changelog

**Versione 1.0**
- Gestione completa clienti, corsi, insegnanti
- Sistema pagamenti con ricevute PDF
- Report finanziari e compensi
- Gestione dati aziendali
- Database portatile SQLite