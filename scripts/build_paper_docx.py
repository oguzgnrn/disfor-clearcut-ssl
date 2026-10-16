"""Render the measured manuscript as a restrained, editable academic document."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
blocks=json.loads((ROOT/'paper/manuscript_content.json').read_text())
doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1)
sec.header_distance=sec.footer_distance=Inches(.45)
normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.12;normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.widow_control=True
for name,size in [('Title',20),('Heading 1',13),('Heading 2',11.5)]:
    st=doc.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st.font.bold=True
    st.paragraph_format.keep_with_next=True;st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(6)
    st.font.underline=False
    for border in st.element.xpath('./w:pPr/w:pBdr'):border.getparent().remove(border)
foot=sec.footer.paragraphs[0];foot.alignment=2
r=foot.add_run();r.font.size=Pt(9)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
for b in blocks:
    kind=b['kind']
    if kind=='title':doc.add_paragraph(b['text'],'Title')
    elif kind=='heading':
        if b['text']=='References':doc.add_page_break()
        doc.add_paragraph(b['text'],'Heading 1')
    elif kind=='paragraph':
        p=doc.add_paragraph(b['text'])
        if b['text'].startswith('['):p.paragraph_format.space_after=Pt(8);p.paragraph_format.keep_together=True
    elif kind=='table':
        p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run(b['caption']).italic=True
        t=doc.add_table(rows=1,cols=len(b['headers']));t.autofit=False
        widths={2:[5.15,1.35],4:[2.6,1.8,1.05,1.05],5:[.55,1.75,1.8,1.15,1.25],6:[.7,1.1,1.1,1.1,1.2,1.3],7:[.6,1.0,.9,.9,.95,1.0,1.15]}[len(b['headers'])]
        if b['caption'].startswith('Table 2'):widths=[.6,1.2,1.2,3.5]
        for j,w in enumerate(widths):t.columns[j].width=Inches(w)
        for j,x in enumerate(b['headers']):t.rows[0].cells[j].text=x
        for row in b['rows']:
            cells=t.add_row().cells
            for j,x in enumerate(row):cells[j].text=x
        for i,row in enumerate(t.rows):
            pr=row._tr.get_or_add_trPr();no=OxmlElement('w:cantSplit');pr.append(no)
            if i==0:repeat=OxmlElement('w:tblHeader');pr.append(repeat)
            for j,cell in enumerate(row.cells):
                cell.width=Inches(widths[j])
                for p in cell.paragraphs:
                    p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(4)
                    p.paragraph_format.keep_with_next=(i<len(t.rows)-1)
                    for r in p.runs:r.font.size=Pt(9.5);r.font.bold=(i==0)
                if i==0:
                    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EDEFF0');cell._tc.get_or_add_tcPr().append(sh)
        doc.add_paragraph().paragraph_format.space_after=Pt(2)
    elif kind=='figure':
        doc.add_page_break();doc.add_paragraph(b['caption'].split('.')[0],'Heading 1')
        p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(ROOT/b['path']),width=Inches(6.5))
        p=doc.add_paragraph(b['caption']);p.paragraph_format.keep_together=True
        for r in p.runs:r.font.size=Pt(10)
        doc.add_paragraph('Vector PDF and high-resolution PNG versions accompany the manuscript.').runs[0].font.size=Pt(9)
doc.core_properties.title=blocks[0]['text'];doc.core_properties.author='';doc.core_properties.subject='Retrospective empirical audit on DISFOR';doc.core_properties.keywords='Sentinel-2, self-supervised learning, spatial validation'
out=ROOT/'output/paper/Orman_SSL_Manuscript.docx';out.parent.mkdir(parents=True,exist_ok=True);doc.save(out)
print(out)
