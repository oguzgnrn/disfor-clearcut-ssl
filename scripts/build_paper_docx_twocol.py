"""Two-column Word version of the manuscript (REVTeX-like look): full-width title/abstract, two-column body,
wide tables and figures in single-column continuous sections."""
import json, os, re
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
blocks = json.loads((ROOT / os.environ.get('ORMAN_CONTENT', 'paper/manuscript_content_authored.json')).read_text())
out = ROOT / os.environ.get('ORMAN_DOCX_OUT', 'TESLIM_2026-10-18/Orman_SSL_Makale_Kumbasar_Guneren_2col.docx')
AUTHOR_LINE = 'Nida Kumbasar¹ and Mehmet Oğuz Güneren²'
AFFIL = ['¹ TÜBİTAK BİLGEM, Information Technologies Institute (BTE), Data Valorization Department, 41400 Gebze, Kocaeli, Türkiye',
         '² Department of Artificial Intelligence and Data Engineering, Istanbul Technical University, 34469 Istanbul, Türkiye']
DATE_LINE = '(Dated: 18 October 2026; draft for coauthor review; version paper_v4 with declared extensions paper_v5 and paper_v6)'
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
for side in ('left_margin', 'right_margin'): setattr(sec, side, Inches(0.75))
sec.top_margin = sec.bottom_margin = Inches(0.85)
normal = doc.styles['Normal']; normal.font.name = 'Times New Roman'; normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
normal.paragraph_format.space_after = Pt(0); normal.paragraph_format.line_spacing = 1.08
normal.paragraph_format.first_line_indent = Inches(0.17)


def set_cols(section, n, space=0.3):
    sectPr = section._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols'); sectPr.append(cols)
    cols.set(qn('w:num'), str(n)); cols.set(qn('w:space'), str(int(space * 1440)))


def new_section(n):
    s = doc.add_section(WD_SECTION.CONTINUOUS); set_cols(s, n); return s


def para(text, align=None, size=None, bold=False, italic=False, indent=True, space_after=0, space_before=0):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align is not None: p.alignment = align
    if not indent: p.paragraph_format.first_line_indent = Inches(0)
    p.paragraph_format.space_after = Pt(space_after); p.paragraph_format.space_before = Pt(space_before)
    return p


def shade(cell, fill):
    sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), fill); cell._tc.get_or_add_tcPr().append(sh)


def table(b, wide):
    cap = re.sub(r'^Table \d+\.\s*', '', b['caption']); num = re.match(r'Table (\d+)', b['caption']).group(1)
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Inches(0); p.paragraph_format.space_before = Pt(6); p.paragraph_format.keep_with_next = True
    r = p.add_run(f'TABLE {num}. '); r.bold = True; r.font.size = Pt(8.5); r2 = p.add_run(cap); r2.font.size = Pt(8.5)
    t = doc.add_table(rows=1, cols=len(b['headers'])); t.autofit = True
    for j, h in enumerate(b['headers']): t.rows[0].cells[j].text = h
    for row in b['rows']:
        cells = t.add_row().cells
        for j, v in enumerate(row): cells[j].text = v
    for i, row in enumerate(t.rows):
        pr = row._tr.get_or_add_trPr(); pr.append(OxmlElement('w:cantSplit'))
        if i == 0: pr.append(OxmlElement('w:tblHeader'))
        for j, cell in enumerate(row.cells):
            tcPr = cell._tc.get_or_add_tcPr(); borders = OxmlElement('w:tcBorders')
            for side, on in [('top', i == 0), ('bottom', i == 0 or i == len(t.rows) - 1), ('left', False), ('right', False)]:
                el = OxmlElement('w:' + side); el.set(qn('w:val'), 'single' if on else 'nil'); el.set(qn('w:sz'), '6'); el.set(qn('w:color'), '000000'); borders.append(el)
            tcPr.append(borders)
            for pp in cell.paragraphs:
                pp.paragraph_format.first_line_indent = Inches(0); pp.paragraph_format.space_after = Pt(1); pp.paragraph_format.space_before = Pt(1)
                if j > 0 and len(cell.text) <= 22: pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for rr in pp.runs: rr.font.size = Pt(8 if wide else 8.5); rr.bold = (i == 0)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(b, wide):
    m = re.match(r'(Figure \d+)\. (.*)', b['caption']); num = m.group(1).split()[1]
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Inches(0); p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(str(ROOT / b['path']), width=Inches(6.4 if wide else 3.25))
    c = doc.add_paragraph(); c.paragraph_format.first_line_indent = Inches(0); c.paragraph_format.space_after = Pt(6)
    r = c.add_run(f'FIG. {num}. '); r.bold = True; r.font.size = Pt(8.5); r2 = c.add_run(m.group(2)); r2.font.size = Pt(8.5)


# ---- front matter (one column)
set_cols(sec, 1)
abstract, keywords, body, figs, refs = [], '', [], {}, []
in_abstract = False; title = ''
for b in blocks:
    k = b['kind']
    if k == 'title': title = b['text']; continue
    if k == 'heading':
        in_abstract = b['text'] == 'Abstract'
        if in_abstract or b['text'] == 'References': continue
        body.append(('heading', b['text'])); continue
    if k == 'paragraph':
        t = b['text']
        if t.startswith(('Mehmet Oğuz Güneren¹', '¹ ', '² ', 'Draft for coauthor', 'Draft for co')): continue
        if t.startswith('Keywords:'): keywords = t.replace('Keywords: ', ''); continue
        if re.match(r'^\[\d+\]', t): refs.append(t); continue
        (abstract if in_abstract else body).append(('para', t) if not in_abstract else t); continue
    if k == 'table': body.append(('table', b)); continue
    if k == 'figure': figs[int(re.match(r'Figure (\d+)', b['caption']).group(1))] = b

para(title, WD_ALIGN_PARAGRAPH.CENTER, 14, bold=True, indent=False, space_after=8)
para(AUTHOR_LINE, WD_ALIGN_PARAGRAPH.CENTER, 11, indent=False, space_after=2)
for a in AFFIL: para(a, WD_ALIGN_PARAGRAPH.CENTER, 9, italic=True, indent=False)
para(DATE_LINE, WD_ALIGN_PARAGRAPH.CENTER, 9, indent=False, space_before=4, space_after=8)
for t in abstract:
    p = para(t, WD_ALIGN_PARAGRAPH.JUSTIFY, 9, indent=False, space_after=3); p.paragraph_format.left_indent = p.paragraph_format.right_indent = Inches(0.55)
p = para('Keywords: ' + keywords, WD_ALIGN_PARAGRAPH.JUSTIFY, 9, indent=False, space_after=6); p.paragraph_format.left_indent = p.paragraph_format.right_indent = Inches(0.55)
p.runs[0].bold = False

# ---- body (two columns), with wide floats in one-column breaks
ANCHORS = {'3 Models and experimental controls': [1], '5.1 Label-budget curve (declared extension paper_v6)': [2, 3], '5.2 Grouping-radius sensitivity (declared extension paper_v5)': [4], '6 Discussion': [5]}
ANCHORS = {re.sub(r'-', ' ', k): v for k, v in ANCHORS.items()}
new_section(2); mode = 2; sec_no = 0; sub_no = 0


def ensure(n):
    global mode
    if mode != n: new_section(n); mode = n


for kind, val in body:
    if kind == 'heading':
        for num in ANCHORS.get(val, []):
            if num in figs:
                wide = figs[num]['path'].split('/')[-1] in ('01_primary.png', '02_controls.png', '03_data.png')
                ensure(1 if wide else 2); figure(figs[num], wide)
        ensure(2)
        text = re.sub(r'^\d+(\.\d+)?\s+', '', val)
        if re.match(r'^\d+\.\d+', val):
            sub_no += 1; para(f'{chr(64 + sub_no)}. {text}', WD_ALIGN_PARAGRAPH.CENTER, 10, bold=True, indent=False, space_before=8, space_after=4)
        elif re.match(r'^\d+\s', val):
            sec_no += 1; sub_no = 0; para(f'{ROMAN[sec_no - 1]}. {text.upper()}', WD_ALIGN_PARAGRAPH.CENTER, 10, bold=True, indent=False, space_before=10, space_after=4)
        else:
            para(text.upper(), WD_ALIGN_PARAGRAPH.CENTER, 10, bold=True, indent=False, space_before=10, space_after=4)
    elif kind == 'para':
        ensure(2); para(val, WD_ALIGN_PARAGRAPH.JUSTIFY)
    elif kind == 'table':
        wide = len(val['headers']) >= 4
        ensure(1 if wide else 2); table(val, wide)
ensure(2)
para('REFERENCES', WD_ALIGN_PARAGRAPH.CENTER, 10, bold=True, indent=False, space_before=10, space_after=4)
for r in refs:
    p = para(r, WD_ALIGN_PARAGRAPH.LEFT, 8, indent=False, space_after=2); p.paragraph_format.left_indent = Inches(0.25); p.paragraph_format.first_line_indent = Inches(-0.25)
doc.core_properties.title = title; doc.core_properties.author = 'Nida Kumbasar; Mehmet Oğuz Güneren'
out.parent.mkdir(parents=True, exist_ok=True); doc.save(out); print(out)
