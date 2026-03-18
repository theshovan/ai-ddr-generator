"""
Generates two sample PDFs for testing the DDR system:
  - inspection_report.pdf
  - thermal_report.pdf
"""
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)
from PIL import Image as PILImage, ImageDraw


# ── Image generators ───────────────────────────────────────────────────────────

def _crack_img(path):
    img = PILImage.new("RGB", (420, 300), (205, 195, 182))
    d = ImageDraw.Draw(img)
    for x in range(0, 420, 18):
        for y in range(0, 300, 18):
            d.rectangle([x, y, x+17, y+17], outline=(185, 175, 162), width=1)
    pts = [(55,10),(72,55),(62,100),(78,145),(68,190),(83,235),(73,275),(92,295)]
    d.line(pts, fill=(60, 42, 30), width=5)
    d.line([(p[0]+8, p[1]) for p in pts], fill=(90, 72, 58), width=2)
    d.text((8, 280), "Fig 1 — Diagonal crack, south wall, 1st floor", fill=(20, 20, 20))
    img.save(path, "JPEG")

def _damp_img(path):
    img = PILImage.new("RGB", (420, 300), (228, 222, 214))
    d = ImageDraw.Draw(img)
    d.ellipse([95, 70, 310, 200], fill=(162, 148, 136), outline=(112, 95, 82), width=3)
    d.ellipse([130, 98, 272, 172], fill=(142, 128, 116))
    d.text((8, 280), "Fig 2 — Damp patch, bathroom ceiling, Unit 304", fill=(20, 20, 20))
    img.save(path, "JPEG")

def _spalling_img(path):
    img = PILImage.new("RGB", (420, 300), (172, 165, 158))
    d = ImageDraw.Draw(img)
    for (x, y, w, h) in [(78,55,65,42),(195,95,82,52),(145,175,72,48),(88,198,52,38)]:
        d.polygon([(x,y),(x+w,y+5),(x+w-5,y+h),(x+5,y+h)],
                  fill=(112, 102, 92), outline=(72, 62, 52))
    d.text((8, 280), "Fig 3 — Concrete spalling, column C7 base", fill=(20, 20, 20))
    img.save(path, "JPEG")

def _thermal_hot(path, caption):
    img = PILImage.new("RGB", (420, 300), (15, 15, 70))
    d = ImageDraw.Draw(img)
    for y in range(300):
        r = int(15 + (y / 300) * 35)
        g = int(15 + (y / 300) * 25)
        b = int(70 + (y / 300) * 18)
        d.line([(0, y), (420, y)], fill=(r, g, b))
    for x in range(148, 282):
        for yy in range(78, 182):
            dist = ((x - 215)**2 + (yy - 130)**2) ** 0.5
            if dist < 62:
                t = 1 - dist / 62
                d.point((x, yy), fill=(int(255*t), int(100*(1-t)), 0))
    d.text((8, 280), caption, fill=(255, 255, 255))
    img.save(path, "JPEG")

def _thermal_cold(path, caption):
    img = PILImage.new("RGB", (420, 300), (15, 15, 70))
    d = ImageDraw.Draw(img)
    for y in range(300):
        r = int(15 + (y / 300) * 35)
        g = int(15 + (y / 300) * 25)
        b = int(70 + (y / 300) * 18)
        d.line([(0, y), (420, y)], fill=(r, g, b))
    for x in range(118, 302):
        for yy in range(88, 202):
            dist = ((x - 210)**2 + (yy - 145)**2) ** 0.5
            if dist < 72:
                t = 1 - dist / 72
                d.point((x, yy), fill=(0, int(80 + 175 * t), 255))
    d.text((8, 280), caption, fill=(255, 255, 255))
    img.save(path, "JPEG")


# ── Shared style helpers ───────────────────────────────────────────────────────

def _doc(path):
    return SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)

def _st():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "title": ParagraphStyle("T", parent=base["Title"],   fontSize=16, spaceAfter=4),
        "h1":    ParagraphStyle("H1", parent=base["Heading1"], fontSize=12, spaceAfter=4),
        "h2":    ParagraphStyle("H2", parent=base["Heading2"], fontSize=10, spaceAfter=3),
        "body":  s("B", fontSize=9, leading=14, spaceAfter=4),
        "small": s("S", fontSize=8, textColor=colors.grey),
    }

def _meta_table(rows):
    t = Table(rows, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 9),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f9fafb"), colors.white]),
        ("BOX",       (0,0),(-1,-1), 0.4, colors.HexColor("#e5e7eb")),
        ("INNERGRID", (0,0),(-1,-1), 0.4, colors.HexColor("#e5e7eb")),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    return t

def _fig(path, caption, st):
    return [RLImage(path, width=82*mm, height=62*mm),
            Paragraph(caption, st["small"]),
            Spacer(1, 3*mm)]


# ── Inspection Report ──────────────────────────────────────────────────────────

def create_inspection(out_path):
    _crack_img("/tmp/s_crack.jpg")
    _damp_img("/tmp/s_damp.jpg")
    _spalling_img("/tmp/s_spalling.jpg")

    doc   = _doc(out_path)
    st    = _st()
    story = []

    story += [
        Paragraph("SITE INSPECTION REPORT", st["title"]),
        _meta_table([
            ["Project:",          "Greenview Residential Complex – Block C"],
            ["Inspection Date:",  "12 March 2025"],
            ["Inspector:",        "Rahul Sharma, Civil Engineer (Reg. CE-4821)"],
            ["Client:",           "Greenview Developers Pvt. Ltd."],
            ["Report Ref:",       "SIR-2025-0312-GVC"],
        ]),
        Spacer(1, 5*mm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 4*mm),
    ]

    story += [
        Paragraph("1. Executive Summary", st["h1"]),
        Paragraph(
            "A structural and waterproofing inspection of Block C was conducted on 12 March 2025. "
            "The building is approximately 8 years old and shows signs of deferred maintenance. "
            "Issues were identified across multiple areas. Immediate attention is required for "
            "external wall cracks and the exposed reinforcement at column C7.", st["body"]),
        Spacer(1, 4*mm),
    ]

    story += [Paragraph("2. Area-wise Observations", st["h1"])]

    story += [
        Paragraph("2.1  External Wall — South Elevation", st["h2"]),
        Paragraph(
            "A diagonal crack approximately 4 mm wide and 1.2 m long was observed on the south-facing "
            "external wall at first-floor level. The crack originates at the window corner and extends "
            "toward the lintel. Efflorescence is visible along the crack edges, indicating prolonged "
            "moisture ingress. No structural displacement was noted.", st["body"]),
    ] + _fig("/tmp/s_crack.jpg", "Figure 1 — Diagonal crack, south wall, first floor", st)

    story += [
        Paragraph("2.2  Master Bathroom Ceiling — Unit 304", st["h2"]),
        Paragraph(
            "Significant damp patches cover approximately 40% of the bathroom ceiling. Paint peeling "
            "and plaster discolouration are present. The source is likely water seepage from the "
            "bathroom of Unit 404 directly above. A musty odour was detected. No visible mould "
            "growth at time of inspection.", st["body"]),
    ] + _fig("/tmp/s_damp.jpg", "Figure 2 — Damp patch, bathroom ceiling, Unit 304", st)

    story += [
        Paragraph("2.3  Basement Parking Area", st["h2"]),
        Paragraph(
            "Active water seepage was observed through the north basement retaining wall. "
            "Water staining and efflorescence are present over a 3 m wide section. "
            "Standing water (approx. 5 mm deep) was noted near column C7. "
            "Seepage appears intermittent and linked to rainfall infiltration through "
            "failed waterproofing.", st["body"]),
        Spacer(1, 3*mm),
    ]

    story += [
        Paragraph("2.4  Ground Floor — Column C7 Base", st["h2"]),
        Paragraph(
            "Concrete spalling at the base of column C7 exposes reinforcement bars over an area of "
            "approximately 150 mm × 200 mm. Surface rust is visible on exposed rebar. "
            "This is a structural concern requiring prompt attention. "
            "The spalling is likely accelerated by moisture ingress from the basement.", st["body"]),
    ] + _fig("/tmp/s_spalling.jpg", "Figure 3 — Spalling at column C7 base", st)

    story += [
        Paragraph("2.5  Terrace / Roof Level", st["h2"]),
        Paragraph(
            "The terrace waterproofing membrane shows blistering and delamination over approximately "
            "25% of the total area. Hairline cracks are present in the screed layer. "
            "Drainage outlets are partially blocked. Ponding marks are visible near the parapet wall.", st["body"]),
        Spacer(1, 4*mm),
    ]

    story += [
        Paragraph("3. Inspector Notes", st["h1"]),
        Paragraph(
            "Structural drawings for Block C were not available during inspection. "
            "Age of the terrace waterproofing membrane is unknown — client to confirm. "
            "Access to Unit 404 was not granted; internal plumbing above Unit 304 remains unverified.",
            st["body"]),
        Spacer(1, 5*mm),
        HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 2*mm),
        Paragraph("End of Report — SIR-2025-0312-GVC", st["small"]),
    ]

    doc.build(story)
    print(f"✓  {out_path}")


# ── Thermal Report ─────────────────────────────────────────────────────────────

def create_thermal(out_path):
    _thermal_hot("/tmp/t_wall.jpg",    "Thermal T-01 — South wall window corner hot spot")
    _thermal_cold("/tmp/t_bath.jpg",   "Thermal T-02 — Bathroom ceiling moisture zone")
    _thermal_hot("/tmp/t_col.jpg",     "Thermal T-03 — Column C7 base rebar heat")
    _thermal_cold("/tmp/t_terrace.jpg","Thermal T-04 — Terrace membrane delamination")

    doc   = _doc(out_path)
    st    = _st()
    story = []

    story += [
        Paragraph("THERMAL IMAGING REPORT", st["title"]),
        _meta_table([
            ["Project:",          "Greenview Residential Complex – Block C"],
            ["Survey Date:",      "12 March 2025"],
            ["Thermographer:",    "Priya Nair, Certified Thermographer Level II"],
            ["Camera:",           "FLIR E86 — 320×240, sensitivity 0.05°C"],
            ["Conditions:",       "Ambient 28°C · Humidity 65% · 09:00–13:00 IST"],
            ["Report Ref:",       "TIR-2025-0312-GVC"],
        ]),
        Spacer(1, 5*mm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 4*mm),
    ]

    story += [
        Paragraph("1. Survey Overview", st["h1"]),
        Paragraph(
            "A thermal imaging survey was conducted concurrently with the visual inspection. "
            "The survey identifies moisture ingress, heat anomalies, and structural issues "
            "not visible to the naked eye. All temperatures are in degrees Celsius.", st["body"]),
        Spacer(1, 4*mm),
    ]

    story += [Paragraph("2. Thermal Findings", st["h1"])]

    def reading_table(rows):
        t = Table(rows, colWidths=[58*mm, 112*mm])
        t.setStyle(TableStyle([
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("BACKGROUND",(0,0),(0,-1), colors.HexColor("#f9fafb")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f9fafb"), colors.white]),
            ("BOX",       (0,0),(-1,-1), 0.4, colors.HexColor("#e5e7eb")),
            ("INNERGRID", (0,0),(-1,-1), 0.4, colors.HexColor("#e5e7eb")),
            ("TOPPADDING",(0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]))
        return t

    # 2.1 South wall
    story += [
        Paragraph("2.1  External South Wall — Window Corner", st["h2"]),
        reading_table([
            ["Location",       "South elevation, 1st floor, window corner"],
            ["Max Temp",       "47.3°C"],
            ["Ambient Avg",    "31.2°C"],
            ["Delta T",        "+16.1°C above ambient surface"],
            ["Pattern",        "Localised hot spot radiating from crack line"],
            ["Interpretation", "Elevated temperature consistent with moisture evaporation at crack / thermal bridge"],
        ]),
        Spacer(1, 3*mm),
    ] + _fig("/tmp/t_wall.jpg", "Thermal T-01 — South wall window corner hot spot", st)

    # 2.2 Bathroom
    story += [
        Paragraph("2.2  Master Bathroom Ceiling — Unit 304", st["h2"]),
        reading_table([
            ["Location",       "Bathroom ceiling, Unit 304, 3rd floor"],
            ["Min Temp (zone)","24.1°C"],
            ["Ambient Avg",    "30.8°C"],
            ["Delta T",        "−6.7°C below ambient surface"],
            ["Pattern",        "Diffuse cold zone covering ~40% of ceiling"],
            ["Interpretation", "Cold signature consistent with water-saturated plaster and active moisture accumulation"],
        ]),
        Spacer(1, 3*mm),
    ] + _fig("/tmp/t_bath.jpg", "Thermal T-02 — Bathroom ceiling moisture zone", st)

    # 2.3 Column C7
    story += [
        Paragraph("2.3  Column C7 Base — Ground Floor / Basement", st["h2"]),
        reading_table([
            ["Location",       "Column C7 base, basement entry"],
            ["Max Temp",       "43.8°C"],
            ["Ambient Avg",    "30.5°C"],
            ["Delta T",        "+13.3°C above ambient surface"],
            ["Pattern",        "Concentrated hot zone at rebar exposure area"],
            ["Interpretation", "Heat consistent with active corrosion reaction in exposed reinforcement"],
        ]),
        Spacer(1, 3*mm),
    ] + _fig("/tmp/t_col.jpg", "Thermal T-03 — Column C7 base rebar heat", st)

    # 2.4 Terrace
    story += [
        Paragraph("2.4  Terrace Waterproofing Membrane", st["h2"]),
        reading_table([
            ["Location",       "Terrace / roof level, central zone"],
            ["Min Temp (zone)","23.5°C"],
            ["Ambient Avg",    "38.2°C"],
            ["Delta T",        "−14.7°C below ambient surface"],
            ["Pattern",        "Large irregular cold zone, approx. 12 sq m"],
            ["Interpretation", "Cold signature under membrane indicates delamination and trapped moisture"],
        ]),
        Spacer(1, 3*mm),
    ] + _fig("/tmp/t_terrace.jpg", "Thermal T-04 — Terrace membrane delamination", st)

    story += [
        Paragraph("3. Thermographer Notes", st["h1"]),
        Paragraph(
            "The north basement retaining wall could not be fully scanned due to parked vehicles. "
            "Thermal data for the basement seepage area is therefore not available. "
            "Terrace scan was completed at 09:00 IST before significant solar loading — "
            "a re-scan after 14:00 IST is recommended to confirm delamination extent.",
            st["body"]),
        Spacer(1, 5*mm),
        HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 2*mm),
        Paragraph("End of Report — TIR-2025-0312-GVC", st["small"]),
    ]

    doc.build(story)
    print(f"✓  {out_path}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    base = os.path.dirname(os.path.abspath(__file__))
    create_inspection(os.path.join(base, "inspection_report.pdf"))
    create_thermal(os.path.join(base, "thermal_report.pdf"))
    print("Sample documents ready.")
