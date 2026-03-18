import io
import tempfile
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)

# ── Palette ────────────────────────────────────────────────────────────────────
INK    = colors.HexColor("#111111")
MUTED  = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#1d4ed8")
RULE   = colors.HexColor("#e5e7eb")
ALT    = colors.HexColor("#f9fafb")

SEV = {
    "Critical": colors.HexColor("#dc2626"),
    "High":     colors.HexColor("#ea580c"),
    "Medium":   colors.HexColor("#ca8a04"),
    "Low":      colors.HexColor("#16a34a"),
}
PRIO = {
    "Immediate":  colors.HexColor("#dc2626"),
    "Short-term": colors.HexColor("#ea580c"),
    "Long-term":  colors.HexColor("#16a34a"),
}


def _styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "title":   s("t",  fontSize=20, fontName="Helvetica-Bold", textColor=INK,    spaceAfter=2),
        "sub":     s("sb", fontSize=10, textColor=MUTED,           spaceAfter=8),
        "h1":      s("h1", fontSize=12, fontName="Helvetica-Bold", textColor=INK,    spaceBefore=8, spaceAfter=4),
        "h2":      s("h2", fontSize=10, fontName="Helvetica-Bold", textColor=ACCENT, spaceAfter=3),
        "body":    s("b",  fontSize=9,  textColor=INK,  leading=14, spaceAfter=3),
        "small":   s("sm", fontSize=8,  textColor=MUTED, leading=12),
        "label":   s("lb", fontSize=7,  textColor=MUTED, leading=10),
        "bold_sm": s("bs", fontSize=9,  fontName="Helvetica-Bold", textColor=INK),
        "white_b": s("wb", fontSize=9,  fontName="Helvetica-Bold", textColor=colors.white),
    }


def _grid(data, col_widths, extra_cmds=None):
    t = Table(data, colWidths=col_widths)
    cmds = [
        ("FONTSIZE",       (0,0),(-1,-1), 9),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("LEFTPADDING",    (0,0),(-1,-1), 6),
        ("RIGHTPADDING",   (0,0),(-1,-1), 6),
        ("BOX",            (0,0),(-1,-1), 0.4, RULE),
        ("INNERGRID",      (0,0),(-1,-1), 0.4, RULE),
        ("VALIGN",         (0,0),(-1,-1), "TOP"),
    ]
    if extra_cmds:
        cmds += extra_cmds
    t.setStyle(TableStyle(cmds))
    return t


def _to_jpg(img_bytes: bytes) -> str:
    """Save image bytes to a temp JPEG and return the path."""
    pil = PILImage.open(io.BytesIO(img_bytes)).convert("RGB")
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    pil.save(tmp.name, "JPEG")
    tmp.close()
    return tmp.name


def _img_cell(img_bytes: bytes | None, caption: str, st: dict) -> list:
    if not img_bytes:
        return [Paragraph("Image Not Available", st["label"])]
    try:
        path = _to_jpg(img_bytes)
        return [RLImage(path, width=78*mm, height=58*mm),
                Paragraph(caption, st["label"])]
    except Exception:
        return [Paragraph("Image Not Available", st["label"])]


def build(ddr: dict, all_images: list) -> bytes:
    # ── Split images by source ─────────────────────────────────────────────
    # Each area gets its nth inspection image and nth thermal image by order.
    insp_imgs  = [img["data"] for img in all_images if img["source"] == "inspection"]
    therm_imgs = [img["data"] for img in all_images if img["source"] == "thermal"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=18*mm,
    )
    st    = _styles()
    story = []

    # ── Header ─────────────────────────────────────────────────────────────
    overall_sev = ddr.get("overall_severity", "Low")
    sev_clr     = SEV.get(overall_sev, MUTED)

    story += [
        Paragraph("Detailed Diagnostic Report", st["title"]),
        Spacer(1, 3*mm),
        Paragraph(ddr.get("property_name", ""), st["sub"]),
        HRFlowable(width="100%", thickness=0.5, color=RULE),
        Spacer(1, 3*mm),
    ]

    # Meta table — 4 cols, severity badge uses white bold text
    meta = _grid(
        [
            [Paragraph("Inspection Date", st["bold_sm"]),
             Paragraph(ddr.get("inspection_date", "Not Available"), st["body"]),
             Paragraph("Report Ref", st["bold_sm"]),
             Paragraph(ddr.get("report_ref", "Not Available"), st["body"])],
            [Paragraph("Overall Severity", st["bold_sm"]),
             Paragraph(overall_sev, st["white_b"]),
             Paragraph("Report Title", st["bold_sm"]),
             Paragraph(ddr.get("report_title", "Not Available"), st["body"])],
        ],
        [32*mm, 58*mm, 26*mm, 54*mm],
        extra_cmds=[
            ("BACKGROUND", (1,1),(1,1), sev_clr),
            ("BACKGROUND", (0,0),(-1,-1), ALT),
        ]
    )
    story += [meta, Spacer(1, 5*mm)]

    # ── 1. Issue Summary ───────────────────────────────────────────────────
    story += [
        Paragraph("1. Property Issue Summary", st["h1"]),
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 2*mm),
        Paragraph(ddr.get("property_issue_summary", "Not Available"), st["body"]),
        Spacer(1, 5*mm),
    ]

    # ── 2. Area-wise Observations ──────────────────────────────────────────
    story += [
        Paragraph("2. Area-wise Observations", st["h1"]),
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 3*mm),
    ]

    for i, area in enumerate(ddr.get("areas", [])):
        asev    = area.get("severity", "Low")
        asev_clr = SEV.get(asev, MUTED)
        block   = []

        # Area header
        hdr = _grid(
            [[Paragraph(f"{i+1}.  {area.get('area_name','')}", st["h2"]),
              Paragraph(asev, st["white_b"])]],
            [148*mm, 22*mm],
            extra_cmds=[
                ("BACKGROUND",  (1,0),(1,0), asev_clr),
                ("ALIGN",       (1,0),(1,0), "CENTER"),
                ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
                ("BOX",         (0,0),(-1,-1), 0,  colors.white),
                ("INNERGRID",   (0,0),(-1,-1), 0,  colors.white),
                ("LEFTPADDING", (0,0),(0,0),   0),
            ]
        )
        block += [hdr, Spacer(1, 2*mm)]

        # Observations
        obs = _grid(
            [
                [Paragraph("Visual Observation", st["bold_sm"]),
                 Paragraph("Thermal Finding",    st["bold_sm"])],
                [Paragraph(area.get("visual_observation", "Not Available"), st["body"]),
                 Paragraph(area.get("thermal_finding",    "Not Available"), st["body"])],
            ],
            [85*mm, 85*mm],
            extra_cmds=[("BACKGROUND", (0,0),(-1,0), ALT)]
        )
        block += [obs, Spacer(1, 2*mm)]

        # ── Images: use sequential index per source ────────────────────────
        vi = insp_imgs[i]  if i < len(insp_imgs)  else None
        ti = therm_imgs[i] if i < len(therm_imgs) else None
        v_caption = area.get("visual_image_label", "Visual Image")
        t_caption = area.get("thermal_image_label", "Thermal Image")

        img_t = Table(
            [[_img_cell(vi, v_caption, st), _img_cell(ti, t_caption, st)]],
            colWidths=[85*mm, 85*mm]
        )
        img_t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
        block += [img_t, Spacer(1, 2*mm)]

        # Root cause + severity reasoning
        cause = _grid(
            [
                [Paragraph("Probable Root Cause", st["bold_sm"]),
                 Paragraph("Severity Reasoning",  st["bold_sm"])],
                [Paragraph(area.get("probable_root_cause", "Not Available"), st["body"]),
                 Paragraph(area.get("severity_reasoning",  "Not Available"), st["body"])],
            ],
            [85*mm, 85*mm],
            extra_cmds=[("BACKGROUND", (0,0),(-1,0), ALT)]
        )
        block += [cause, Spacer(1, 6*mm)]

        story.append(KeepTogether(block[:3]))
        for item in block[3:]:
            story.append(item)

    # ── 3. Recommended Actions ─────────────────────────────────────────────
    story += [
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 3*mm),
        Paragraph("3. Recommended Actions", st["h1"]),
        Spacer(1, 2*mm),
    ]

    ra_rows = [[
        Paragraph("#",        st["bold_sm"]),
        Paragraph("Action",   st["bold_sm"]),
        Paragraph("Area",     st["bold_sm"]),
        Paragraph("Priority", st["bold_sm"]),
    ]]
    for j, ra in enumerate(ddr.get("recommended_actions", []), 1):
        ra_rows.append([
            Paragraph(str(j),               st["body"]),
            Paragraph(ra.get("action",""),  st["body"]),
            Paragraph(ra.get("area",""),    st["body"]),
            Paragraph(ra.get("priority",""),st["white_b"]),
        ])

    prio_cmds = [
        ("BACKGROUND", (0,0),(-1,0), ALT),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, ALT]),
    ]
    for j, ra in enumerate(ddr.get("recommended_actions", []), 1):
        c = PRIO.get(ra.get("priority",""), MUTED)
        prio_cmds += [("BACKGROUND", (3,j),(3,j), c)]

    story += [
        _grid(ra_rows, [8*mm, 102*mm, 42*mm, 26*mm], extra_cmds=prio_cmds),
        Spacer(1, 5*mm),
    ]

    # ── 4. Additional Notes ────────────────────────────────────────────────
    story += [
        Paragraph("4. Additional Notes", st["h1"]),
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 2*mm),
    ]
    for note in ddr.get("additional_notes", ["Not Available"]):
        story.append(Paragraph(f"— {note}", st["body"]))
    story.append(Spacer(1, 4*mm))

    # ── 5. Missing / Unclear ───────────────────────────────────────────────
    story += [
        Paragraph("5. Missing or Unclear Information", st["h1"]),
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 2*mm),
    ]
    for item in ddr.get("missing_or_unclear", ["Not Available"]):
        story.append(Paragraph(f"— {item}", st["body"]))
    story.append(Spacer(1, 6*mm))

    # ── Footer ─────────────────────────────────────────────────────────────
    story += [
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 2*mm),
        Paragraph(
            "AI-generated report. All findings must be verified by a qualified professional.",
            st["small"]
        ),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.read()
