# utils/stampa_pdf.py
import os
import sys
from datetime import datetime
from flask import render_template

def format_currency_it(value):
    """Formatta un numero come valuta italiana: €1.000,00"""
    if value is None:
        return "€0,00"
    try:
        # Formatta con separatore migliaia e virgola decimale
        formatted = "{:,.2f}".format(float(value))
        # Sostituisci . con , per decimali e , con . per migliaia (formato italiano)
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"€ {formatted}"
    except (ValueError, TypeError):
        return "€0,00"

def genera_ricevuta_pdf(pagamento, pdf_folder=None):
    """
    Genera una ricevuta PDF per il pagamento specificato
    Restituisce (pdf_content, filename) per streaming diretto
    """
    
    # Numerazione progressiva delle ricevute
    ricevuta_numero = f"{pagamento.numero_ricevuta:05d}" if pagamento.numero_ricevuta else f"ID{pagamento.id:05d}"
    filename = f"RICEVUTA-{ricevuta_numero}.pdf"
    
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
        return genera_pdf_weasyprint_memory(context, filename)
    except Exception as e:
        try:
            # Fallback su ReportLab
            return genera_pdf_reportlab_memory(pagamento, ricevuta_numero, filename)
        except Exception as e2:
            raise Exception(f"Impossibile generare PDF: WeasyPrint={e}, ReportLab={e2}")

def genera_pdf_weasyprint_memory(context, filename):
    """Genera PDF usando WeasyPrint in memoria"""
    import io
    try:
        import weasyprint
        from flask import render_template
        import os
        
        # Aggiungi il path assoluto del logo al context per WeasyPrint
        if context.get('settings') and context['settings'].logo_filename:
            logo_absolute_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', context['settings'].logo_filename)
            context['logo_absolute_path'] = f"file://{os.path.abspath(logo_absolute_path)}"
        
        # Render del template HTML
        html_content = render_template('ricevuta.html', **context)
        
        # Conversione in PDF in memoria
        pdf_doc = weasyprint.HTML(string=html_content)
        pdf_buffer = io.BytesIO()
        pdf_doc.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue(), filename
        
    except ImportError:
        raise Exception("WeasyPrint non è installato")
    except Exception as e:
        raise Exception(f"Errore WeasyPrint: {str(e)}")

def genera_pdf_reportlab_memory(pagamento, ricevuta_numero, filename):
    """Genera PDF usando ReportLab in memoria"""
    import io
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from models.settings import Settings
        
        # Buffer in memoria
        buffer = io.BytesIO()
        
        # Ottieni le impostazioni aziendali
        settings = Settings.get_settings()
        
        # Crea il documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titolo
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story.append(Paragraph(f"RICEVUTA PAGAMENTO N° {ricevuta_numero}", title_style))
        story.append(Spacer(1, 20))
        
        # Informazioni azienda
        if settings:
            company_info = f"<b>{settings.denominazione_sociale}</b><br/>"
            if settings.indirizzo_completo:
                company_info += f"{settings.indirizzo_completo}<br/>"
            if settings.telefono:
                company_info += f"Tel: {settings.telefono}<br/>"
            if settings.email:
                company_info += f"Email: {settings.email}"
            
            story.append(Paragraph(company_info, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Dettagli pagamento
        data_table = [
            ['Cliente:', pagamento.cliente.nome_completo],
            ['Corso:', pagamento.corso.nome],
            ['Periodo:', pagamento.periodo],
            ['Importo:', format_currency_it(pagamento.importo)],
            ['Data Pagamento:', pagamento.data_pagamento.strftime('%d/%m/%Y') if pagamento.data_pagamento else 'N/D'],
            ['Metodo:', pagamento.metodo_pagamento or 'Contanti']
        ]
        
        table = Table(data_table, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Data emissione: {datetime.now().strftime('%d/%m/%Y')}"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Genera PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue(), filename
        
    except ImportError:
        raise Exception("ReportLab non è installato")
    except Exception as e:
        raise Exception(f"Errore ReportLab: {str(e)}")

def genera_pdf_weasyprint(context, pdf_path):
    """Genera PDF usando WeasyPrint"""
    try:
        import weasyprint
        from flask import current_app
        import os
        
        # Aggiungi il path assoluto del logo al context per WeasyPrint
        if context.get('settings') and context['settings'].logo_filename:
            # Usa la stessa logica dei report
            logo_absolute_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', context['settings'].logo_filename)
            context['logo_absolute_path'] = f"file://{os.path.abspath(logo_absolute_path)}"
        
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
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageTemplate, Frame
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.canvas.canvas import Canvas
        from models.settings import Settings
        
        # Ottieni le impostazioni aziendali
        settings = Settings.get_settings()
        
        # Crea una classe per gestire il footer
        class FooterCanvas(Canvas):
            def __init__(self, *args, **kwargs):
                Canvas.__init__(self, *args, **kwargs)
                self.settings = settings
            
            def showPage(self):
                self.draw_footer()
                Canvas.showPage(self)
            
            def draw_footer(self):
                self.saveState()
                # Posizione del footer a 30px dal bottom
                footer_y = 30
                
                if self.settings:
                    footer_lines = []
                    
                    if self.settings.denominazione_sociale:
                        footer_lines.append(self.settings.denominazione_sociale)
                    
                    if self.settings.indirizzo_completo:
                        footer_lines.append(self.settings.indirizzo_completo)
                    
                    contatti = []
                    if self.settings.telefono:
                        contatti.append(f"Tel: {self.settings.telefono}")
                    if self.settings.email:
                        contatti.append(f"Email: {self.settings.email}")
                    if contatti:
                        footer_lines.append(" | ".join(contatti))
                    
                    fiscali = []
                    if self.settings.partita_iva:
                        fiscali.append(f"P.IVA: {self.settings.partita_iva}")
                    if self.settings.codice_fiscale:
                        fiscali.append(f"C.F.: {self.settings.codice_fiscale}")
                    if fiscali:
                        footer_lines.append(" | ".join(fiscali))
                    
                    # Disegna le linee del footer centrate
                    self.setFont("Helvetica", 10)
                    page_width = A4[0]
                    for i, line in enumerate(footer_lines):
                        text_width = self.stringWidth(line, "Helvetica", 10)
                        x = (page_width - text_width) / 2
                        y = footer_y + (len(footer_lines) - i - 1) * 12
                        self.drawString(x, y, line)
                else:
                    # Fallback
                    self.setFont("Helvetica-Bold", 10)
                    text = "Dance2Manage"
                    text_width = self.stringWidth(text, "Helvetica-Bold", 10)
                    x = (A4[0] - text_width) / 2
                    self.drawString(x, footer_y, text)
                
                self.restoreState()
        
        # Crea documento PDF con canvas personalizzato
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=120,
                              canvasmaker=FooterCanvas)
        
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
        
        # Header con logo centrato (nuovo layout per ricevute)
        header_style = ParagraphStyle('HeaderCentered',
                                     parent=styles['Normal'],
                                     fontSize=16,
                                     alignment=TA_CENTER,
                                     spaceAfter=20)
        
        if settings and settings.logo_filename:
            try:
                # Usa lo stesso path che funziona nel report insegnante
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', settings.logo_filename)
                if os.path.exists(logo_path):
                    from reportlab.platypus import Image
                    from reportlab.lib.utils import ImageReader
                    
                    # Logo centrato
                    logo_img = Image(logo_path, width=2*inch, height=2*inch, kind='proportional')
                    logo_table = Table([[logo_img]], colWidths=[6.5*inch])
                    logo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ]))
                    
                    story.append(logo_table)
                    story.append(Spacer(1, 20))
                else:
                    # File logo non trovato - solo nome azienda
                    denominazione = settings.denominazione_sociale if settings else "Dance2Manage"
                    story.append(Paragraph(denominazione, header_style))
                    
            except Exception as e:
                # Fallback senza logo - solo nome azienda
                denominazione = settings.denominazione_sociale if settings else "Dance2Manage"
                story.append(Paragraph(denominazione, header_style))
        else:
            # Header senza logo - solo nome azienda centrato
            denominazione = settings.denominazione_sociale if settings else "Dance2Manage"
            story.append(Paragraph(denominazione, header_style))
        
        # Titolo documento
        story.append(Paragraph("Ricevuta di Pagamento", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Layout a due colonne: Informazioni ricevuta a sinistra, Dati cliente a destra
        data_emissione = datetime.now().strftime('%d/%m/%Y')
        
        # Colonna sinistra: Informazioni documento
        info_doc = Paragraph("<b>Informazioni Documento</b>", heading_style)
        info_data = [
            ['Data emissione:', data_emissione],
            ['Ricevuta N°:', ricevuta_numero]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        # Colonna destra: Dati cliente
        cliente_title = Paragraph("<b>Dati Cliente</b>", heading_style)
        
        cliente_data = [
            ['Nome Completo:', pagamento.cliente.nome_completo],
            ['Codice Fiscale:', pagamento.cliente.codice_fiscale or '-']
        ]
        
        # Indirizzo completo cliente
        indirizzo_parts = []
        if pagamento.cliente.via:
            indirizzo_parts.append(pagamento.cliente.via)
        if pagamento.cliente.civico:
            indirizzo_parts.append(pagamento.cliente.civico)
        
        indirizzo_completo = ' '.join(indirizzo_parts) if indirizzo_parts else '-'
        
        if pagamento.cliente.cap or pagamento.cliente.citta:
            citta_parts = []
            if pagamento.cliente.cap:
                citta_parts.append(pagamento.cliente.cap)
            if pagamento.cliente.citta:
                citta_parts.append(pagamento.cliente.citta)
            if pagamento.cliente.provincia:
                citta_parts.append(f"({pagamento.cliente.provincia})")
            
            if citta_parts:
                indirizzo_completo += f"\n{' '.join(citta_parts)}"
        
        cliente_data.append(['Indirizzo:', indirizzo_completo])
        
        cliente_table = Table(cliente_data, colWidths=[1.2*inch, 2*inch])
        cliente_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Creiamo la struttura a due colonne
        left_content = [info_doc, Spacer(1, 10), info_table]
        right_content = [cliente_title, Spacer(1, 10), cliente_table]
        
        # Tabella principale per layout a due colonne
        main_table = Table([[left_content, right_content]], colWidths=[3*inch, 3.5*inch])
        main_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (1, 0), (1, 0), 20),
        ]))
        
        story.append(main_table)
        story.append(Spacer(1, 20))
        
        # Dettagli pagamento
        story.append(Paragraph("Dettagli Pagamento", heading_style))
        
        dettagli_data = [
            ['Descrizione', 'Periodo', 'Corso', 'Importo'],
            ['Quota mensile corso di danza', 
             pagamento.periodo, 
             pagamento.corso.nome, 
             format_currency_it(pagamento.importo)]
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
        
        story.append(Paragraph(f"<b>Totale: {format_currency_it(pagamento.importo)}</b>", totale_style))
        story.append(Spacer(1, 20))
        
        # Informazioni pagamento
        info_pagamento = [
            f"<b>Metodo di pagamento:</b> {getattr(pagamento, 'metodo_pagamento', 'Contanti')}",
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
            ['Incasso Totale Mensile:', format_currency_it(riepilogo['incasso_totale'])],
            ['Compensi Totali da Pagare:', format_currency_it(riepilogo['compensi_totali'])],
            ['Utile Netto Scuola:', format_currency_it(riepilogo['utile_netto'])],
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
                    format_currency_it(report.incasso_totale),
                    f"{report.percentuale_media:.1f}%",
                    format_currency_it(report.compenso_totale)
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
            
            story.append(Paragraph(f"<b>TOTALE COMPENSI DA PAGARE: {format_currency_it(riepilogo['compensi_totali'])}</b>", totale_style))
        
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
        
        # Header con logo e dati azienda
        if settings and settings.logo_filename:
            try:
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', settings.logo_filename)
                if os.path.exists(logo_path):
                    from reportlab.platypus import Image
                    from reportlab.lib.utils import ImageReader
                    
                    # Tabella header con logo a sinistra e dati azienda a destra
                    logo_img = Image(logo_path, width=1.5*inch, height=1.5*inch, kind='proportional')
                    
                    # Dati azienda formattati
                    denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
                    company_data = [denominazione]
                    
                    if settings.indirizzo_completo:
                        company_data.append(settings.indirizzo_completo)
                    
                    company_info = []
                    if settings.partita_iva:
                        company_info.append(f"P.IVA: {settings.partita_iva}")
                    if settings.codice_fiscale:
                        company_info.append(f"C.F.: {settings.codice_fiscale}")
                    if settings.telefono:
                        company_info.append(f"Tel: {settings.telefono}")
                    if settings.email:
                        company_info.append(f"Email: {settings.email}")
                    
                    if company_info:
                        company_data.extend(company_info)
                    
                    company_text = Paragraph('<br/>'.join(company_data), normal_style)
                    
                    # Tabella header
                    header_table = Table([[logo_img, company_text]], colWidths=[2*inch, 4*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    story.append(header_table)
                    story.append(Spacer(1, 20))
                else:
                    # File logo non trovato
                    denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
                    story.append(Paragraph(denominazione, title_style))
                    if settings and settings.indirizzo_completo:
                        story.append(Paragraph(settings.indirizzo_completo, normal_style))
                    
            except Exception as e:
                # Fallback senza logo
                denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
                story.append(Paragraph(denominazione, title_style))
                if settings and settings.indirizzo_completo:
                    story.append(Paragraph(settings.indirizzo_completo, normal_style))
        else:
            # Header senza logo
            denominazione = settings.denominazione_sociale if settings else "Dance2Manager"
            story.append(Paragraph(denominazione, title_style))
            
            if settings and settings.indirizzo_completo:
                story.append(Paragraph(settings.indirizzo_completo, normal_style))
        
        # Titolo documento
        story.append(Paragraph(f"Compenso {insegnante.nome_completo}", subtitle_style))
        story.append(Paragraph(f"{mesi[mese]} {anno}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Dati insegnante
        story.append(Paragraph("Dati Insegnante", heading_style))
        
        insegnante_data = [
            ['Nome Completo:', insegnante.nome_completo],
            ['Codice Fiscale:', insegnante.codice_fiscale or '-']
        ]
        
        # Indirizzo completo
        indirizzo_parts = []
        if insegnante.via:
            indirizzo_parts.append(insegnante.via)
        if insegnante.civico:
            indirizzo_parts.append(insegnante.civico)
        
        indirizzo_completo = ' '.join(indirizzo_parts) if indirizzo_parts else '-'
        
        if insegnante.cap or insegnante.citta:
            citta_parts = []
            if insegnante.cap:
                citta_parts.append(insegnante.cap)
            if insegnante.citta:
                citta_parts.append(insegnante.citta)
            if insegnante.provincia:
                citta_parts.append(f"({insegnante.provincia})")
            
            if citta_parts:
                indirizzo_completo += f"\n{' '.join(citta_parts)}"
        
        insegnante_data.append(['Indirizzo:', indirizzo_completo])
        insegnante_data.append(['Telefono:', insegnante.telefono or '-'])
        insegnante_data.append(['Email:', insegnante.email or '-'])
        
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
        
        # Dettaglio corsi con lista clienti
        story.append(Paragraph("Dettaglio Corsi e Clienti", heading_style))
        
        if corsi_insegnante:
            # Tabella riassuntiva corsi
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
                    format_currency_it(corso_report.incasso_corso),
                    f"{corso_report.percentuale_insegnante:.0f}%",
                    format_currency_it(corso_report.compenso_insegnante)
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
            
            # Lista dettagliata clienti per ogni corso
            story.append(Paragraph("Lista Clienti per Corso", heading_style))
            
            for corso_report in corsi_insegnante:
                corso = corso_report.corso
                
                # Titolo corso
                corso_title_style = ParagraphStyle('CorsoTitle',
                                                 parent=styles['Heading4'],
                                                 fontSize=12,
                                                 spaceAfter=10,
                                                 textColor=colors.darkblue,
                                                 borderWidth=1,
                                                 borderColor=colors.lightgrey,
                                                 backColor=colors.lightblue,
                                                 borderPadding=5)
                
                story.append(Paragraph(f"<b>{corso.nome}</b> - {corso.giorno} {corso.orario.strftime('%H:%M')}", corso_title_style))
                
                # Ottieni tutti i clienti iscritti al corso
                clienti_corso = corso.clienti
                
                if clienti_corso:
                    # Crea tabella clienti per questo corso (senza stato pagamento)
                    clienti_data = [['#', 'Nome Completo', 'Telefono', 'Email']]
                    
                    for idx, cliente in enumerate(clienti_corso, 1):
                        clienti_data.append([
                            str(idx),
                            cliente.nome_completo,
                            cliente.telefono or '-',
                            cliente.email or '-'
                        ])
                    
                    clienti_table = Table(clienti_data, colWidths=[0.4*inch, 2.5*inch, 1.5*inch, 2*inch])
                    clienti_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Numerazione centrata
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    story.append(clienti_table)
                else:
                    # Nessun cliente iscritto
                    story.append(Paragraph("Nessun cliente iscritto a questo corso", normal_style))
                
                story.append(Spacer(1, 15))
            
            story.append(Spacer(1, 10))
        
        # Riepilogo compenso
        story.append(Paragraph("Riepilogo Compenso", heading_style))
        
        riepilogo_data = [
            ['Totale Incasso dai Corsi:', format_currency_it(report_insegnante.incasso_totale)],
            ['Percentuale Media:', f"{report_insegnante.percentuale_media:.1f}%"],
            ['Numero Corsi Attivi:', str(len(report_insegnante.corsi_nomi))],
            ['COMPENSO TOTALE:', format_currency_it(report_insegnante.compenso_totale)]
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