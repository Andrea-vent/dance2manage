# utils/stampa_pdf.py
import os
import sys
from datetime import datetime
from flask import render_template

def genera_ricevuta_pdf(pagamento, pdf_folder):
    """
    Genera una ricevuta PDF per il pagamento specificato
    Supporta sia WeasyPrint che ReportLab come fallback
    """
    
    # Numerazione progressiva delle ricevute
    ricevuta_numero = f"{pagamento.id:05d}"
    filename = f"RICEVUTA-{ricevuta_numero}.pdf"
    pdf_path = os.path.join(pdf_folder, filename)
    
    # Importa Settings qui per evitare circular imports
    from models.settings import Settings
    
    # Ottieni le impostazioni aziendali
    settings = Settings.get_settings()
    
    # Dati per il template
    context = {
        'pagamento': pagamento,
        'ricevuta_numero': ricevuta_numero,
        'data_emissione': datetime.now(),
        'moment': datetime.now,
        'settings': settings
    }
    
    try:
        # Prova prima con WeasyPrint (preferito)
        return genera_pdf_weasyprint(context, pdf_path)
    except Exception as e:
        print(f"WeasyPrint fallito: {e}")
        try:
            # Fallback su ReportLab
            return genera_pdf_reportlab(pagamento, pdf_path, ricevuta_numero)
        except Exception as e2:
            print(f"ReportLab fallito: {e2}")
            raise Exception(f"Impossibile generare PDF: WeasyPrint={e}, ReportLab={e2}")

def genera_pdf_weasyprint(context, pdf_path):
    """Genera PDF usando WeasyPrint"""
    try:
        import weasyprint
        from flask import current_app
        
        # Render del template HTML
        html_content = render_template('ricevuta.html', **context)
        
        # Conversione in PDF
        pdf_doc = weasyprint.HTML(string=html_content)
        pdf_doc.write_pdf(pdf_path)
        
        return pdf_path
        
    except ImportError:
        raise Exception("WeasyPrint non è installato")
    except Exception as e:
        raise Exception(f"Errore WeasyPrint: {str(e)}")

def genera_pdf_reportlab(pagamento, pdf_path, ricevuta_numero):
    """Genera PDF usando ReportLab come fallback"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from models.settings import Settings
        
        # Ottieni le impostazioni aziendali
        settings = Settings.get_settings()
        
        # Crea documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle',
                                   parent=styles['Heading1'],
                                   fontSize=24,
                                   spaceAfter=30,
                                   alignment=TA_CENTER,
                                   textColor=colors.darkblue)
        
        subtitle_style = ParagraphStyle('CustomSubtitle',
                                      parent=styles['Heading2'],
                                      fontSize=18,
                                      spaceAfter=20,
                                      alignment=TA_CENTER,
                                      textColor=colors.grey)
        
        normal_style = styles['Normal']
        heading_style = styles['Heading3']
        
        # Contenuto del PDF
        story = []
        
        # Header
        denominazione = settings.denominazione_sociale if settings else "Dance2Manage"
        story.append(Paragraph(denominazione, title_style))
        story.append(Paragraph("Ricevuta di Pagamento", subtitle_style))
        
        # Informazioni azienda
        if settings and settings.indirizzo_completo:
            story.append(Paragraph(settings.indirizzo_completo, normal_style))
        
        info_azienda = []
        if settings and settings.partita_iva:
            info_azienda.append(f"P.IVA: {settings.partita_iva}")
        if settings and settings.codice_fiscale:
            info_azienda.append(f"C.F.: {settings.codice_fiscale}")
        if settings and settings.telefono:
            info_azienda.append(f"Tel: {settings.telefono}")
        
        if info_azienda:
            story.append(Paragraph(" - ".join(info_azienda), normal_style))
        
        story.append(Spacer(1, 20))
        
        # Informazioni ricevuta
        data_emissione = datetime.now().strftime('%d/%m/%Y')
        info_table = Table([
            ['Data emissione:', data_emissione],
            ['Ricevuta N°:', ricevuta_numero]
        ], colWidths=[2*inch, 2*inch])
        
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Dati cliente
        story.append(Paragraph("Dati Cliente", heading_style))
        cliente_info = [
            f"<b>Nome:</b> {pagamento.cliente.nome_completo}",
        ]
        if pagamento.cliente.codice_fiscale:
            cliente_info.append(f"<b>Codice Fiscale:</b> {pagamento.cliente.codice_fiscale}")
        if pagamento.cliente.telefono:
            cliente_info.append(f"<b>Telefono:</b> {pagamento.cliente.telefono}")
        if pagamento.cliente.email:
            cliente_info.append(f"<b>Email:</b> {pagamento.cliente.email}")
        
        for info in cliente_info:
            story.append(Paragraph(info, normal_style))
        story.append(Spacer(1, 20))
        
        # Dettagli pagamento
        story.append(Paragraph("Dettagli Pagamento", heading_style))
        
        dettagli_data = [
            ['Descrizione', 'Periodo', 'Corso', 'Importo'],
            ['Quota mensile corso di danza', 
             pagamento.periodo, 
             pagamento.corso.nome, 
             f"€ {pagamento.importo:.2f}"]
        ]
        
        dettagli_table = Table(dettagli_data, colWidths=[2.5*inch, 1.5*inch, 2*inch, 1*inch])
        dettagli_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(dettagli_table)
        story.append(Spacer(1, 30))
        
        # Totale
        totale_style = ParagraphStyle('Totale',
                                    parent=styles['Normal'],
                                    fontSize=16,
                                    alignment=TA_RIGHT,
                                    textColor=colors.darkblue,
                                    borderWidth=2,
                                    borderColor=colors.darkblue,
                                    borderPadding=10,
                                    backColor=colors.lightgrey)
        
        story.append(Paragraph(f"<b>Totale: € {pagamento.importo:.2f}</b>", totale_style))
        story.append(Spacer(1, 20))
        
        # Informazioni pagamento
        info_pagamento = [
            f"<b>Metodo di pagamento:</b> Contanti",
            f"<b>Data pagamento:</b> {pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else 'N/A'}",
            f"<b>Stato:</b> {'✓ Pagato' if pagamento.pagato else '⚠ Non pagato'}"
        ]
        
        for info in info_pagamento:
            story.append(Paragraph(info, normal_style))
        
        # Note
        if pagamento.note:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Note:", heading_style))
            story.append(Paragraph(pagamento.note, normal_style))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle('Footer',
                                    parent=styles['Normal'],
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    textColor=colors.grey)
        
        footer_company = settings.denominazione_sociale if settings else "Dance2Manage"
        story.append(Paragraph(f"Questa ricevuta è stata generata automaticamente da {footer_company}.", footer_style))
        story.append(Paragraph(f"Ricevuta generata il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))
        
        if settings and settings.denominazione_sociale:
            footer_info = [settings.denominazione_sociale]
            if settings.partita_iva:
                footer_info.append(f"P.IVA {settings.partita_iva}")
            story.append(Paragraph(" - ".join(footer_info), footer_style))
        
        # Genera PDF
        doc.build(story)
        return pdf_path
        
    except ImportError:
        raise Exception("ReportLab non è installato")
    except Exception as e:
        raise Exception(f"Errore ReportLab: {str(e)}")

def genera_compensi_pdf(report_insegnanti, riepilogo, mese, anno, pdf_folder):
    """Genera PDF con riepilogo compensi per tutti gli insegnanti"""
    
    # Nome file
    filename = f"COMPENSI-{anno}{mese:02d}.pdf"
    pdf_path = os.path.join(pdf_folder, filename)
    
    # Importa Settings per dati azienda
    from models.settings import Settings
    settings = Settings.get_settings()
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        
        # Crea documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle',
                                   parent=styles['Heading1'],
                                   fontSize=20,
                                   spaceAfter=30,
                                   alignment=TA_CENTER,
                                   textColor=colors.darkblue)
        
        subtitle_style = ParagraphStyle('CustomSubtitle',
                                      parent=styles['Heading2'],
                                      fontSize=16,
                                      spaceAfter=20,
                                      alignment=TA_CENTER,
                                      textColor=colors.grey)
        
        normal_style = styles['Normal']
        heading_style = styles['Heading3']
        
        # Nomi mesi
        mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        
        # Contenuto del PDF
        story = []
        
        # Header
        denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
        story.append(Paragraph(denominazione, title_style))
        story.append(Paragraph(f"Riepilogo Compensi - {mesi[mese]} {anno}", subtitle_style))
        
        # Informazioni azienda
        if settings and settings.indirizzo_completo:
            story.append(Paragraph(settings.indirizzo_completo, normal_style))
        
        info_azienda = []
        if settings and settings.partita_iva:
            info_azienda.append(f"P.IVA: {settings.partita_iva}")
        if settings and settings.codice_fiscale:
            info_azienda.append(f"C.F.: {settings.codice_fiscale}")
        
        if info_azienda:
            story.append(Paragraph(" - ".join(info_azienda), normal_style))
        
        story.append(Spacer(1, 30))
        
        # Riepilogo generale
        story.append(Paragraph("Riepilogo Generale", heading_style))
        
        riepilogo_data = [
            ['Incasso Totale Mensile:', f"€ {riepilogo['incasso_totale']:.2f}"],
            ['Compensi Totali da Pagare:', f"€ {riepilogo['compensi_totali']:.2f}"],
            ['Utile Netto Scuola:', f"€ {riepilogo['utile_netto']:.2f}"],
            ['Numero Pagamenti:', str(riepilogo['numero_pagamenti'])]
        ]
        
        riepilogo_table = Table(riepilogo_data, colWidths=[3*inch, 2*inch])
        riepilogo_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ]))
        
        story.append(riepilogo_table)
        story.append(Spacer(1, 30))
        
        # Dettaglio compensi per insegnante
        if report_insegnanti:
            story.append(Paragraph("Dettaglio Compensi per Insegnante", heading_style))
            
            # Tabella insegnanti
            table_data = [
                ['Insegnante', 'Telefono', 'Corsi', 'Incasso', '% Media', 'Compenso']
            ]
            
            for report in report_insegnanti:
                table_data.append([
                    report.insegnante.nome_completo,
                    report.insegnante.telefono or '-',
                    '\n'.join(report.corsi_nomi) if len(report.corsi_nomi) <= 3 else f"{len(report.corsi_nomi)} corsi",
                    f"€ {report.incasso_totale:.2f}",
                    f"{report.percentuale_media:.1f}%",
                    f"€ {report.compenso_totale:.2f}"
                ])
            
            compensi_table = Table(table_data, colWidths=[1.8*inch, 1*inch, 1.5*inch, 1*inch, 0.7*inch, 1*inch])
            compensi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Nomi a sinistra
                ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Importi a destra
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(compensi_table)
            story.append(Spacer(1, 20))
            
            # Totale compensi
            totale_style = ParagraphStyle('Totale',
                                        parent=styles['Normal'],
                                        fontSize=14,
                                        alignment=TA_RIGHT,
                                        textColor=colors.darkgreen,
                                        borderWidth=2,
                                        borderColor=colors.darkgreen,
                                        borderPadding=8,
                                        backColor=colors.lightgreen)
            
            story.append(Paragraph(f"<b>TOTALE COMPENSI DA PAGARE: € {riepilogo['compensi_totali']:.2f}</b>", totale_style))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle('Footer',
                                    parent=styles['Normal'],
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    textColor=colors.grey)
        
        story.append(Paragraph("Questo riepilogo è stato generato automaticamente da Dance2Manager.", footer_style))
        story.append(Paragraph(f"Documento generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))
        
        if settings and settings.denominazione_sociale:
            footer_info = [settings.denominazione_sociale]
            if settings.partita_iva:
                footer_info.append(f"P.IVA {settings.partita_iva}")
            story.append(Paragraph(" - ".join(footer_info), footer_style))
        
        # Genera PDF
        doc.build(story)
        return pdf_path
        
    except ImportError:
        raise Exception("ReportLab non è installato")
    except Exception as e:
        raise Exception(f"Errore generazione PDF compensi: {str(e)}")

def genera_compensi_insegnante_pdf(insegnante, report_insegnante, corsi_insegnante, mese, anno, pdf_folder):
    """Genera PDF compensi per singolo insegnante"""
    
    # Nome file
    nome_pulito = insegnante.nome_completo.replace(' ', '_')
    filename = f"COMPENSI_{nome_pulito}_{anno}{mese:02d}.pdf"
    pdf_path = os.path.join(pdf_folder, filename)
    
    # Importa Settings per dati azienda
    from models.settings import Settings
    settings = Settings.get_settings()
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        
        # Crea documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle',
                                   parent=styles['Heading1'],
                                   fontSize=18,
                                   spaceAfter=20,
                                   alignment=TA_CENTER,
                                   textColor=colors.darkblue)
        
        subtitle_style = ParagraphStyle('CustomSubtitle',
                                      parent=styles['Heading2'],
                                      fontSize=14,
                                      spaceAfter=15,
                                      alignment=TA_CENTER,
                                      textColor=colors.grey)
        
        normal_style = styles['Normal']
        heading_style = styles['Heading3']
        
        # Nomi mesi
        mesi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        
        # Contenuto del PDF
        story = []
        
        # Header
        denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
        story.append(Paragraph(denominazione, title_style))
        story.append(Paragraph(f"Compenso {insegnante.nome_completo}", subtitle_style))
        story.append(Paragraph(f"{mesi[mese]} {anno}", subtitle_style))
        
        # Informazioni azienda
        if settings and settings.indirizzo_completo:
            story.append(Paragraph(settings.indirizzo_completo, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Dati insegnante
        story.append(Paragraph("Dati Insegnante", heading_style))
        
        insegnante_data = [
            ['Nome Completo:', insegnante.nome_completo],
            ['Telefono:', insegnante.telefono or '-'],
            ['Email:', insegnante.email or '-'],
            ['Percentuale Guadagno:', f"{insegnante.percentuale_guadagno}%"]
        ]
        
        insegnante_table = Table(insegnante_data, colWidths=[2*inch, 3*inch])
        insegnante_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ]))
        
        story.append(insegnante_table)
        story.append(Spacer(1, 20))
        
        # Dettaglio corsi
        story.append(Paragraph("Dettaglio Corsi", heading_style))
        
        if corsi_insegnante:
            corsi_data = [
                ['Corso', 'Giorno', 'Orario', 'Iscritti', 'Pagamenti', 'Incasso', '%', 'Compenso']
            ]
            
            for corso_report in corsi_insegnante:
                corsi_data.append([
                    corso_report.corso.nome,
                    corso_report.corso.giorno,
                    corso_report.corso.orario.strftime('%H:%M'),
                    str(corso_report.corso.numero_iscritti),
                    str(corso_report.numero_pagamenti),
                    f"€ {corso_report.incasso_corso:.2f}",
                    f"{corso_report.percentuale_insegnante:.0f}%",
                    f"€ {corso_report.compenso_insegnante:.2f}"
                ])
            
            corsi_table = Table(corsi_data, colWidths=[1.5*inch, 0.8*inch, 0.7*inch, 0.6*inch, 0.7*inch, 0.8*inch, 0.4*inch, 0.8*inch])
            corsi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Nome corso a sinistra
                ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),  # Importi a destra
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(corsi_table)
            story.append(Spacer(1, 20))
        
        # Riepilogo compenso
        story.append(Paragraph("Riepilogo Compenso", heading_style))
        
        riepilogo_data = [
            ['Totale Incasso dai Corsi:', f"€ {report_insegnante.incasso_totale:.2f}"],
            ['Percentuale Media:', f"{report_insegnante.percentuale_media:.1f}%"],
            ['Numero Corsi Attivi:', str(len(report_insegnante.corsi_nomi))],
            ['COMPENSO TOTALE:', f"€ {report_insegnante.compenso_totale:.2f}"]
        ]
        
        riepilogo_table = Table(riepilogo_data, colWidths=[3*inch, 2*inch])
        riepilogo_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 2), 'Helvetica-Bold'),
            ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 2), 'Helvetica'),
            ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 2), 11),
            ('FONTSIZE', (0, 3), (-1, 3), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightgreen),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.darkgreen),
        ]))
        
        story.append(riepilogo_table)
        story.append(Spacer(1, 30))
        
        # Note
        story.append(Paragraph("Note", heading_style))
        story.append(Paragraph(f"Compenso calcolato sui pagamenti effettivamente ricevuti nel mese di {mesi[mese]} {anno}.", normal_style))
        story.append(Paragraph("Le percentuali si applicano agli incassi reali, non alle quote teoriche.", normal_style))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle('Footer',
                                    parent=styles['Normal'],
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    textColor=colors.grey)
        
        story.append(Paragraph("Questo documento è stato generato automaticamente da Dance2Manager.", footer_style))
        story.append(Paragraph(f"Documento generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))
        
        if settings and settings.denominazione_sociale:
            footer_info = [settings.denominazione_sociale]
            if settings.partita_iva:
                footer_info.append(f"P.IVA {settings.partita_iva}")
            story.append(Paragraph(" - ".join(footer_info), footer_style))
        
        # Genera PDF
        doc.build(story)
        return pdf_path
        
    except ImportError:
        raise Exception("ReportLab non è installato")
    except Exception as e:
        raise Exception(f"Errore generazione PDF insegnante: {str(e)}")

def get_next_ricevuta_numero():
    """Genera il prossimo numero progressivo di ricevuta"""
    # Implementazione semplice basata su timestamp
    # In un sistema più complesso si potrebbe usare un contatore nel database
    return datetime.now().strftime('%Y%m%d%H%M%S')