# Database Migrations

## Convenzioni di naming:
- Formato: `XXX_descrizione_migrazione_YYYYMMDD.py`
- XXX = numero progressivo (001, 002, etc.)
- descrizione_migrazione = nome descrittivo
- YYYYMMDD = data creazione

## Ordine di esecuzione:
Le migrazioni vengono eseguite in ordine numerico progressivo.

## Sicurezza produzione:
1. Testare sempre in locale prima
2. Fare backup del database prima di applicare
3. Verificare che la migrazione sia reversibile
4. Documentare ogni migrazione

## Lista migrazioni:
- 001_add_born_date_customers_date_today.py - Aggiunge data nascita e riferimenti genitori per clienti