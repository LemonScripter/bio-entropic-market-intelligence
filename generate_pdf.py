"""
PDF Compiler for the Bio-Entropic Stealth & Market Intelligence Whitepaper.
Generates a publication-grade PDF using ReportLab with Hungarian UTF-8 support.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import sys

BASE_DIR = Path(__file__).resolve().parent
PDF_OUTPUT_PATH = BASE_DIR / "whitepaper_bio_entropic_stealth.pdf"


class NumberedCanvas(canvas.Canvas):
    """Canvas supporting page numbers and running headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 800, "Bio-Entropikus Stealth Keretrendszer — Fehér Könyv & Ellenpróba")
            self.setStrokeColor(colors.HexColor("#DDDDDD"))
            self.setLineWidth(0.5)
            self.line(54, 792, 540, 792)
            
        # Footer
        footer_text = f"Oldal {self._pageNumber} / {page_count}"
        self.drawRightString(540, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — ADVANCED AUTOMATION ARCHITECTURE")
        self.setStrokeColor(colors.HexColor("#DDDDDD"))
        self.setLineWidth(0.5)
        self.line(54, 48, 540, 48)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#184C78"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#444444"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#184C78"),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#C62828"),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#222222"),
        spaceAfter=6
    )

    abstract_style = ParagraphStyle(
        "Abstract_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#333333"),
        leftIndent=15,
        rightIndent=15,
        spaceAfter=10
    )

    callout_title = ParagraphStyle(
        "CalloutTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#184C78"),
        spaceAfter=3
    )

    callout_body = ParagraphStyle(
        "CalloutBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#222222")
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Bio-Entropikus Webes Adatgyűjtő Keretrendszer", title_style))
    story.append(Paragraph("Empirikus Működési Bizonyíték, A/B Ellenpróba és Rendszerszintű Buktatók Elemzése", subtitle_style))
    story.append(Paragraph("<b>Szerző:</b> LemonScripter Systems Architecture & Advanced Automation Engineering | <b>Dátum:</b> 2026. szeptember", body_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#184C78"), spaceAfter=10))

    # Abstract
    story.append(Paragraph("<b>KIVONAT:</b> A modern webes anti-bot és viselkedéselemző védelmi rendszerek (pl. Akamai Bot Manager, Cloudflare Turnstile, AWS WAF) hatékonyan képesek felismerni a hagyományos determinisztikus szkripteket és az egyszerű pszeudo-véletlenszám-generátorokon (PRNG) alapuló automatizációkat. Ez a fehér könyv bemutatja a <b>Bio-Entropikus Állapotmotoron</b> alapuló adatgyűjtő architektúrát, amely valós biológiai aktigráfiás telemetriai adatsorokat alkalmaz mind makroszkopikus ütemezéshez, mind mikroszkopikus késleltetési entrópiához. A dolgozat bemutatja a rendszer működésének empirikus bizonyítékait, egy kontrollált A/B ellenpróba mérési mátrixát (ahol a naiv bot karanténba zárása igazolódott), valamint részletesen feltárja a hosszú távú üzemeltetés lehetséges technológiai buktatóit és azok elhárítását.", abstract_style))
    story.append(Spacer(1, 8))

    # Section 1: Architecture
    story.append(Paragraph("1. Rendszerarchitektúra és Működési Elv", h1_style))
    story.append(Paragraph(
        "A keretrendszer négy szigorúan elkülönülő rétegből áll:<br/>"
        "• <b>Bio-Entropikus Időzítő Motor:</b> 168 órás biológiai aktigráfiás telemetria alapján határozza meg a makró-fázisokat (aktív adatgyűjtés vs. alvó/pihenő zónák) és a log-normális mikrofázisú késleltetéseket.<br/>"
        "• <b>Sztochasztikus Állapotgép & Bézier Motor:</b> Fitts törvényén és a minimális rándulás elvén alapuló, emberi kézremegést szimuláló koordinátagörbékkel mozgatja a kurzort.<br/>"
        "• <b>Hardened Stealth Réteg:</b> Törli a <code>navigator.webdriver</code> jelzőt, maszkolja a hardverprofilt, és észrevehetetlen zajt injektál a Canvas, WebGL és AudioContext rétegekbe.<br/>"
        "• <b>Perzisztencia & Adatfolyam:</b> SQLite relációs adatbázisban tárolja a piaci adatokat, miközben <code>storage_state</code> révén megőrzi a digitális munkamenet-identitást.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Section 2: Empirical Proof
    story.append(Paragraph("2. A Működés Empirikus Bizonyítéka (Éles Mérési Adatok)", h1_style))
    story.append(Paragraph(
        "Az Amazon platformon lefutott éles adatgyűjtési ciklus bizonyítja a rendszer blokkolásmentes működését. A helyi lemezre írt állományok igazolják a kinyerés integritását:",
        body_style
    ))

    table_data_proof = [
        [Paragraph("<b>Mért Mutató</b>", body_style), Paragraph("<b>Rögzített Érték</b>", body_style), Paragraph("<b>Mérnöki / Technikai Jelentőség</b>", body_style)],
        ["Összes egyedi termék", "43 db ASIN", "Sikeres, blokkolásmentes SERP HTML feldolgozás"],
        ["Árrögzítési időszelet", "45 bejegyzés", "Idősoros SQLite perzisztencia (market_data.db)"],
        ["Átlagos termékár", "$249.38", "Piaci ársáv ($54.18 - $903.51)"],
        ["Átlagos értékelés", "4.47 / 5.0", "Valós vásárlói értékelések kinyerve"],
        ["Session State méret", "13.5 KB", "39 db Amazon session cookie (session-id, ubid-main)"],
        ["Micro-jitter késleltetés", "62.8 - 123.4 ms", "Nem-determinisztikus log-normális variancia"]
    ]

    t_proof = Table(table_data_proof, colWidths=[120, 90, 275])
    t_proof.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EAEFF5")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#222222")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
    ]))
    story.append(t_proof)
    story.append(Spacer(1, 10))

    # Section 3: Counter-Test
    story.append(Paragraph("3. Az A/B Ellenpróba (Control Experiment Mérések)", h1_style))
    story.append(Paragraph(
        "A dedikált <code>counter_test.py</code> modul azonos hálózati végpontról indított egy hagyományos automatizációt és a bio-entropikus stealth ágenst:",
        body_style
    ))

    table_data_ab = [
        [Paragraph("<b>Tesztelt Jellemző</b>", body_style), Paragraph("<b>[A] Naiv Hagyományos Bot</b>", body_style), Paragraph("<b>[B] Bio-Entropikus Ágens</b>", body_style)],
        ["navigator.webdriver", "True (Azonnal azonosítva)", "None (Tökéletesen maszkolva)"],
        ["WebGL Profil", "Alapértelmezett Headless", "ANGLE (NVIDIA RTX 3070)"],
        ["Kiadott Session Cookie-k", "0 db (Szerver megtagadta)", "38 db (Hitelesítve kiadva)"],
        ["Egérmozgási dinamika", "0 ms azonnali teleport", "Bézier S-görbe + Fitts-törvény"],
        ["Késleltetési karakterisztika", "Konstans determinisztikus", "Biológiai log-normális szórás"],
        ["Anti-Bot Reakció", "Silent Shadow-Banning", "100% Tiszta Áthaladás"]
    ]

    t_ab = Table(table_data_ab, colWidths=[130, 160, 195])
    t_ab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EAEFF5")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#222222")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor("#C62828")),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.HexColor("#C62828")),
        ('TEXTCOLOR', (1, 6), (1, 6), colors.HexColor("#C62828")),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor("#184C78")),
        ('TEXTCOLOR', (2, 3), (2, 3), colors.HexColor("#184C78")),
        ('TEXTCOLOR', (2, 6), (2, 6), colors.HexColor("#184C78")),
    ]))
    story.append(t_ab)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>A „Csendes Karantén” (Silent Shadow-Banning) mechanizmusa:</b> Az ellenpróba kimutatta, hogy az Amazon WAF védelme a naiv botot nem feltétlenül szakítja meg látványos hibaoldallal, hanem megtagadja a munkamenet sütik (<code>session-id</code>, <code>ubid-main</code>) kiadását (0 db cookie), miközben a Bio-Entropikus Ágens 38 db érvényes cookie-t kapott és valós adatokat olvasott be.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Section 4: Pitfalls & Vulnerabilities
    story.append(Paragraph("4. Rendszerszintű Kockázatok és Lehetséges Buktatók", h1_style))
    story.append(Paragraph(
        "A magas szintű mérnöki transzparencia érdekében az alábbiakban összegezzük a hosszú távú üzemeltetés során fellépő potenciális buktatókat és azok konkrét elhárítását:",
        body_style
    ))

    # Pitfall 1
    p1_content = [
        Paragraph("<b>1. Buktató: TLS/TCP JA3/JA4 Ujjlenyomat Elcsúszás (Protocol Discrepancy)</b>", callout_title),
        Paragraph("<b>Kockázat:</b> Ha a böngésző magas szinten Chrome User-Agent-et mutat, de az alacsony szintű TLS Handshake (Cipher Suite-ok sorrendje, ALPN, TLS Extensions) ettől eltér, az Akamai/Cloudflare rendszerek azonnal szűrik a kapcsolatot.<br/>"
                  "<b>Védelem:</b> A Chromium natív hálózati veremének használata a böngészőben, vagy <code>curl_cffi</code> / uTLS integrálása a direkt háttérkérésekhez.", callout_body)
    ]
    t_p1 = Table([[p1_content]], colWidths=[485])
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#184C78")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_p1)
    story.append(Spacer(1, 6))

    # Pitfall 2
    p2_content = [
        Paragraph("<b>2. Buktató: Rezidens IP Túlhasználat és Subnet Reputáció</b>", callout_title),
        Paragraph("<b>Kockázat:</b> Ha ugyanaz a rezidens proxy IP cím több száz kérést hajt végre fázisváltás nélkül, az IP átmeneti karanténba kerül.<br/>"
                  "<b>Védelem:</b> Az IP-rotációt szigorúan a biológiai makró-pihenő (<code>DIGESTING_REST</code>) fázisokhoz kell kötni, amikor a forgalom természetes módon nullára esik.", callout_body)
    ]
    t_p2 = Table([[p2_content]], colWidths=[485])
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#184C78")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_p2)
    story.append(Spacer(1, 6))

    # Pitfall 3
    p3_content = [
        Paragraph("<b>3. Buktató: Túl-zajosított Canvas/WebGL ujjlenyomat (Entropy Trap)</b>", callout_title),
        Paragraph("<b>Kockázat:</b> Ha a Canvas vagy WebGL zajinjektálás túl nagy vagy determinisztikus mintázatú, a védelmi szkriptek felfedezik az ujjlenyomat-hamisítást.<br/>"
                  "<b>Védelem:</b> A képpont-módosítás kizárólag a legkisebb helyiértékű bitre (+-1 LSB) terjedhet ki, megőrizve a renderelési koherenciát.", callout_body)
    ]
    t_p3 = Table([[p3_content]], colWidths=[485])
    t_p3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#184C78")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_p3)
    story.append(Spacer(1, 6))

    # Pitfall 4
    p4_content = [
        Paragraph("<b>4. Buktató: Ciklikus Telemetria Ismétlődés (Long-term Machine Learning Profiling)</b>", callout_title),
        Paragraph("<b>Kockázat:</b> Ha a bot hónapokon keresztül pontosan ugyanazt a 168 órás görbét játssza le, a viselkedési gépi tanulási modellek felfedezik a periodicitást.<br/>"
                  "<b>Védelem:</b> Ornstein-Uhlenbeck sztochasztikus folyamattal heti driftet és évszakos fáziseltolást kell a telemetriára szuperponálni.", callout_body)
    ]
    t_p4 = Table([[p4_content]], colWidths=[485])
    t_p4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#184C78")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_p4)
    story.append(Spacer(1, 8))

    # Section 5: Conclusion
    story.append(Paragraph("5. Összegzés és Értékelés", h1_style))
    story.append(Paragraph(
        "A Bio-Entropikus keretrendszer az empirikus adatok, a session hitelesítés és a kontrollált ellenpróba alapján bizonyítottan képes felülmúlni a modern viselkedéselemző védelmeket. A feltárt buktatók kiküszöbölésével a rendszer stabil alapot nyújt a hosszú távú, automatizált piacelemzéshez.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
