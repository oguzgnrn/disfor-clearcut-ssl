"""Compose the compact Turkish course while tracking every original lesson block."""
from pathlib import Path
import hashlib,json,re,math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/egitim'; SHORT=SOURCE/'kisa'; OUT=ROOT/'output/egitim'; ASSETS=SHORT/'assets'
STEM='Orman_SSL_15_Sayfada_Proje_Rehberi'
FONTROOT=Path('/Users/gnrnoguz/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')
FONT='Carlito'; WIDTH=18.0
FILES=['01_temeller.json','02_modeller_ve_deneyler.json','03_dosyalar_ve_gosterim.json','04_hocaya_hazirlik.json','05_basvuru.json']
LAYOUT=[
 ('Proje ve uydu ölçümleri',[(0,0),(0,1)]),
 ('Örneğin yapısı ve veri hazırlama',[(0,2),(0,3),(0,4)]),
 ('Öğrenme tahmin ve gerçek örnekler',[(0,5),(0,6),(0,7)]),
 ('Model aileleri ve özdenetimli öğrenme',[(1,0),(1,1),(1,2)]),
 ('Adil deney ve coğrafi değerlendirme',[(1,3),(1,4),(1,5)]),
 ('Başarı hesabı ve deney sonuçları',[(1,6),(1,7),(1,8)]),
 ('Sınırlar sürümler ve dosya haritası',[(1,9),(2,0),(2,1)]),
 ('Ürünü açma ve canlı gösterim',[(2,2),(2,3),(2,4)]),
 ('Eğitim kaydı paketler ve çalışma programı',[(2,5),(2,6),(3,0)]),
 ('Hocaya anlatım ve ilk beş soru',[(3,1),(3,2)]),
 ('Zor sorular sonraki deney ve toplantı',[(3,3),(3,4),(3,7)]),
 ('Kendini sınama ve cevap anahtarı',[(3,5),(3,6)]),
 ('Sözlük ve teknik başvuru',[(4,0),(4,1),(4,2)]),
 ('Kaynaklar ve son tekrar',[(4,3),(4,4)]),
 ('Dosya dayanakları ve okuma rotası',[]),
]


def clean(s):
    return str(s).translate(str.maketrans({'–':'-','—':'-','‑':'-','−':'-'}))


def rich(p,s):
    for part in re.split(r'(`[^`]+`|\*\*[^*]+\*\*)',clean(s)):
        r=p.add_run(part.strip('`') if part.startswith('`') else part.strip('*') if part.startswith('**') else part)
        if part.startswith('**'):r.bold=True
        if part.startswith('`'):r.font.name='DejaVu Sans Mono';r.font.size=Pt(8.6)


def bookmark(p,name,identifier):
    b=OxmlElement('w:bookmarkStart');b.set(qn('w:id'),str(identifier));b.set(qn('w:name'),name)
    e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(identifier));p._p.insert(0,b);p._p.append(e)


def hyperlink(p,label,url=None,anchor=None,size=None):
    el=OxmlElement('w:hyperlink')
    if anchor:el.set(qn('w:anchor'),anchor)
    if url:
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        el.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement('w:r');props=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'245675');props.append(color)
    if size:
        sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(int(size*2)));props.append(sz)
    r.append(props)
    t=OxmlElement('w:t');t.text=label;r.append(t);el.append(r);p._p.append(el)


def setup():
    d=Document();s=d.sections[0];s.page_width=Cm(21);s.page_height=Cm(29.7)
    s.left_margin=s.right_margin=Cm(1.5);s.top_margin=Cm(1.3);s.bottom_margin=Cm(1.3);s.footer_distance=Cm(.55)
    normal=d.styles['Normal'];normal.font.name=FONT;normal.font.size=Pt(10.5)
    normal.paragraph_format.line_spacing=1.0;normal.paragraph_format.space_after=Pt(1.8)
    normal.paragraph_format.widow_control=True
    for name,size in [('Title',22),('Subtitle',11),('Heading 1',16),('Heading 2',12),('Heading 3',11)]:
        st=d.styles[name];st.font.name=FONT;st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st.font.bold=name!='Subtitle';st.font.underline=False
        st.paragraph_format.space_before=Pt(4 if name=='Heading 2' else 7 if name=='Heading 1' else 0);st.paragraph_format.space_after=Pt(2);st.paragraph_format.keep_with_next=True
        for n in st.element.xpath('./w:pPr/w:pBdr'):n.getparent().remove(n)
    from docx.enum.style import WD_STYLE_TYPE
    for name,size in [('Evidence',8.5),('Code',8.7),('Caption compact',9.5),('File index',9.3)]:
        st=d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH);st.font.name='DejaVu Sans Mono' if name=='Code' else FONT;st.font.size=Pt(size)
        st.paragraph_format.space_after=Pt(2);st.paragraph_format.line_spacing=1.0;st.paragraph_format.widow_control=True
    footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=footer.add_run('Orman SSL  |  Proje rehberi  |  ');r.font.name=FONT;r.font.size=Pt(8.5)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
    d.core_properties.title='Orman SSL Proje Rehberi';d.core_properties.subject='Temel kavramlar deneyler dosyalar gösterim ve hocaya hazırlık'
    d.core_properties.author=''
    return d


def table(d,headers,rows,widths=None,font_size=10.2):
    n=len(headers)
    widths=widths or {2:[5.3,12.3],3:[4.0,5.6,8.0],4:[6.7,3.63,3.63,3.64],5:[1.5,5.0,4.1,3.5,3.5]}.get(n,[WIDTH/n]*n)
    widths=[w*WIDTH/sum(widths) for w in widths]
    t=d.add_table(rows=1,cols=n);t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for j,w in enumerate(widths):t.columns[j].width=Cm(w)
    for j,v in enumerate(headers):rich(t.rows[0].cells[j].paragraphs[0],v)
    for row in rows:
        c=t.add_row().cells
        for j,v in enumerate(row):rich(c[j].paragraphs[0],v)
    for i,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if not i:pr.append(OxmlElement('w:tblHeader'))
        for j,cell in enumerate(row.cells):
            cell.width=Cm(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=cell._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for side in ['top','bottom','left','right']:
                x=OxmlElement('w:'+side)
                for k,v in [('val','single'),('sz','4'),('color','D9D9D9')]:x.set(qn('w:'+k),v)
                b.append(x)
            cp.append(b);mar=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                x=OxmlElement('w:'+side);x.set(qn('w:w'),'30' if side in ['top','bottom'] else '70');x.set(qn('w:type'),'dxa');mar.append(x)
            cp.append(mar);shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'243F51' if i==0 else ('F0F4F6' if i%2==0 else 'FFFFFF'));cp.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
                p.paragraph_format.widow_control=True
                if i and re.fullmatch(r'[\d.,% +±/−–-]+',str(rows[i-1][j])):p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size=Pt(font_size);r.bold=i==0;r.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '000000')
    spacer=d.add_paragraph();spacer.paragraph_format.space_after=Pt(2);spacer.paragraph_format.line_spacing=Pt(1);spacer.add_run().font.size=Pt(1)
    return t


def figures():
    ASSETS.mkdir(parents=True,exist_ok=True)
    def font(s,b=False):return ImageFont.truetype(str(FONTROOT/('Carlito-Bold.ttf' if b else 'Carlito-Regular.ttf')),s)
    with np.load(ROOT/'output/advanced_prediction/input.npz',allow_pickle=False) as raw:
        ids=raw['ids'].tolist();x=raw['x'];mask=raw['observed'];bands=json.loads(str(raw['metadata']))['channels']
    pred=json.loads((ROOT/'output/advanced_prediction/predictions.json').read_text())
    im=Image.new('RGB',(2000,620),'white');dr=ImageDraw.Draw(im)
    for k,(key,title) in enumerate([('disfor-1733-2019','Doğru bulunan kesim'),('disfor-1664-2018','Kaçırılan kesim')]):
        i=ids.index(key);year=int(key.rsplit('-',1)[1]);score=pred['probabilities'][pred['ids'].index(key)][1]
        left=105+k*1010;right=965+k*1010;top=125;bottom=475
        dr.text(((left+right)/2,12),title,anchor='mt',font=font(42,True),fill='#172C38')
        dr.text(((left+right)/2,60),f'{key}   Skor {score:.4f}'.replace('.',','),anchor='mt',font=font(36),fill='#47555E')
        peak=max(float(np.max(x[i,:,bands.index(b)][mask[i,:,bands.index(b)]])) for b in ['B04','B08','B12']);ymax=math.ceil(peak/1000)*1000
        xx=lambda j:left+(right-left)*j/23;yy=lambda v:bottom-(bottom-top)*v/ymax
        for value in np.linspace(0,ymax,5):
            y=yy(value);dr.line((left,y,right,y),fill='#E2E8EB',width=2);dr.text((left-12,y),str(int(value)),font=font(34),fill='#47555E',anchor='rm')
        dr.text((left+5,top-8),'DN',font=font(32),fill='#47555E',anchor='lb')
        dr.line((left,top,left,bottom,right,bottom),fill='#717C83',width=2)
        for y in range(top,bottom,16):dr.line((xx(11.5),y,xx(11.5),min(y+8,bottom)),fill='#8D999F',width=2)
        for tick,label in zip([0,5,12,17,23],[f'Oca {year-1}','Haz',f'Oca {year}','Haz','Ara']):
            dr.text((xx(tick),bottom+15),label,font=font(32),fill='#47555E',anchor='lt' if tick==0 else 'rt' if tick==23 else 'mt')
        for band,color in [('B04','#AE673F'),('B08','#327A56'),('B12','#687CA9')]:
            c=bands.index(band);values=np.where(mask[i,:,c],x[i,:,c],np.nan)
            for j in range(24):
                if not np.isfinite(values[j]):continue
                px,py=xx(j),yy(values[j]);dr.ellipse((px-5,py-5,px+5,py+5),fill=color)
                if j and np.isfinite(values[j-1]):dr.line((xx(j-1),yy(values[j-1]),px,py),fill=color,width=4)
    for k,(band,color) in enumerate([('B04','#AE673F'),('B08','#327A56'),('B12','#687CA9')]):
        lx=640+k*270;dr.line((lx,567,lx+45,567),fill=color,width=5);dr.text((lx+58,542),band,font=font(40),fill=color)
    im.save(ASSETS/'gercek_ornekler_kisa.png',dpi=(292,292))
    im=Image.new('RGB',(2000,430),'white');dr=ImageDraw.Draw(im)
    for y,labels in [(55,['DISFOR ölçümleri','Aylık 24 × 10 seri','Kalite ve referans bilgisi']), (205,['paper_v4 araştırması','5 kat ve 3 seed','180 koşu ve karşılaştırma']), (365,['advanced_v3 ürünü','10 eğitimli üye','Skor ve inceleme ekranı'])]:
        for xx,label in zip([320,1000,1675],labels):dr.text((xx,y),label,anchor='mm',font=font(39),fill='#172C38')
        for a,b in [(600,690),(1290,1380)]:dr.line((a,y,b,y),fill='#547284',width=4);dr.polygon([(b,y),(b-17,y-10),(b-17,y+10)],fill='#547284')
    dr.text((1000,128),'Ayrı protokollerle iki kullanım yolu',anchor='mm',font=font(37),fill='#536571')
    dr.text((1000,285),'Makale skoru ile ürün skoru aynı deney değildir',anchor='mm',font=font(37),fill='#536571')
    im.save(ASSETS/'is_akisi_kisa.png',dpi=(292,292))


def main():
    modules=[json.loads((SHORT/f).read_text()) for f in FILES]
    originals=[json.loads((SOURCE/f).read_text()) for f in FILES]
    coverage=[]
    for m,(source,edited) in enumerate(zip(originals,modules)):
        assert len(source['pages'])==len(edited['pages'])
        for i,(a,b) in enumerate(zip(source['pages'],edited['pages'])):
            assert a['title']==b['title'] and a.get('sourcefiles')==b.get('sourcefiles')
            assert len(a['blocks'])==len(b['blocks'])
            for j,(x,y) in enumerate(zip(a['blocks'],b['blocks'])):
                assert x['kind']==y['kind']
                if x['kind'] in ['table','code','figure','link']:
                    for k in ['rows','headers','text' if x['kind']=='code' else 'path','url']:
                        if k in x:assert x[k]==y[k],(FILES[m],i,j,k)
                if x['kind']=='bullets':assert len(x['items'])==len(y['items'])
                coverage.append(dict(module=FILES[m],lesson=i,block=j,kind=x['kind'],destination_section=next(n for n,(_,pairs) in enumerate(LAYOUT,1) if (m,i) in pairs)))
    assigned=[pair for _,pairs in LAYOUT for pair in pairs]
    assert len(set(assigned))==len(assigned)==sum(len(m['pages']) for m in modules)==38
    sources=sorted({s for m in modules for p in m['pages'] for s in p.get('sourcefiles',[])})
    for s in sources:assert (ROOT/s).is_file(),s
    source_id={s:i for i,s in enumerate(sources,1)}
    d=setup();figures();md=['# Orman SSL Proje Rehberi','16 Ekim 2026 | Kısaltılmış çalışma kitabı']
    for number,(title,pairs) in enumerate(LAYOUT,1):
        if number==15:
            pass
        if number==1:
            p=d.add_paragraph('Orman SSL Proje Rehberi','Title');bookmark(p,'top',0)
            d.add_paragraph('Temelden uygulamaya ve hocayla görüşmeye hazırlık  |  16 Ekim 2026','Subtitle')
            p=d.add_paragraph('Bu rehberle 24 aylık veriyi okuyacak; eğitim, tahmin ve değerlendirmeyi ayıracak; sonuçların nedenlerini, sınırlarını ve kanıt dosyalarını öğreneceksin. Doğru ve yanlış tahmini üründe göster, bilmediğini ayır ve sonraki deneyi planla. Her dersin ardından kaynağı kapatıp anlat; soruyu önce kendin yanıtla. Uzmanlık pratik ve yeni araştırmalarla gelişir.')
            d.add_paragraph('Ana dersler paper_v4 ve advanced_v3 içindir. 30 Eylül denetiminde 58 test geçti; 180 kayıt kontrol edildi, paketten bir SSL eğitimi aynı tahminleri verdi. Bağımsız saha doğrulaması yapılmadı. Öğretici örnekler ile gerçek deney sayıları ayrı belirtilir; D kodları son bölümde dosyaya, G kodları kaynak bölümünde dış kaynağa gider.')
        if number==1:
            p=d.add_paragraph();p.paragraph_format.space_after=Pt(5)
            p.add_run('Hızlı erişim  ').bold=True
            for i,(label,anchor) in enumerate([('Veri','lesson0_2'),('Modeller','lesson1_0'),('Sonuçlar','lesson1_8'),('Demo','lesson2_3'),('Sınav','lesson3_5'),('Kaynaklar','lesson4_3'),('Dosyalar','page15')]):
                if i:p.add_run('  ·  ')
                hyperlink(p,label,anchor=anchor)
        if number==15:
            p=d.add_paragraph(title,'Heading 1');bookmark(p,f'page{number}',number)
        md.append('\n## '+title)
        if number==15:
            p=d.add_paragraph('Dayanaklar proje köküne göre dosya yollarıdır. Ders sonundaki D numarası burada karşılığını gösterir. Bir dosyanın bulunması veya hash eşleşmesi, bilimsel yorumun doğruluğunu tek başına kanıtlamaz.')
            half=(len(sources)+1)//2
            rows=[[f'D{source_id[path]:02d}  {path}',f'D{source_id[sources[i+half]]:02d}  {sources[i+half]}' if i+half<len(sources) else ''] for i,path in enumerate(sources[:half])]
            tab=table(d,['Dosya dayanakları','Dosya dayanakları'],rows,[8.8,8.8],9.3)
            for row in tab.rows:
                for cell in row.cells:
                    for node in cell._tc.xpath('./w:tcPr/w:tcMar/w:top | ./w:tcPr/w:tcMar/w:bottom'):node.set(qn('w:w'),'10')
            for i,row in enumerate(tab.rows[1:]):
                for j,cell in enumerate(row.cells):
                    k=i+j*half
                    if k<len(sources):bookmark(cell.paragraphs[0],'file'+str(source_id[sources[k]]),100+source_id[sources[k]])
            for path in sources:md.append(f'D{source_id[path]:02d} {path}')
            d.add_paragraph('Zamanına göre çalışma rotası','Heading 2')
            for label,body in [
                ('Bir saat','Temel soru, sürüm ayrımı ve sonuç tablosu → beş dakikalık demo → 30 saniyelik anlatım. Bu yol yalnız toplantıya başlangıçtır.'),
                ('Bir gün','Temeller ve deneyleri iki oturumda oku. Dosya haritası, gerçek eğitim kaydı ve demoyu aç; akşam sınavı çöz, yanlışlara dön.'),
                ('Bir hafta','Günlük çalışma planını uygula; kısa sözlü açıklamalar kaydet. Son gün projeyi ekransız iki dakika anlatıp kanıtları göster.')]:
                p=d.add_paragraph();p.add_run(label+'  ').bold=True;rich(p,body)
            d.add_paragraph('Hızlı erişim ve D bağlantıları tıklanabilir. Word metnini uzatırsan sayfa numaraları değişebilir; düzeni ve yönlendirmeleri yeniden kontrol et.',style='Evidence')
            continue
        for mod,idx in pairs:
            lesson=modules[mod]['pages'][idx]
            p=d.add_paragraph(lesson['title'],'Heading 2');bookmark(p,f'lesson{mod}_{idx}',200+mod*50+idx)
            md.append('\n### '+lesson['title'])
            blocks=lesson['blocks'];j=0
            while j<len(blocks):
                b=blocks[j];kind=b['kind']
                if kind=='h' and j+1<len(blocks) and blocks[j+1]['kind']=='p':
                    p=d.add_paragraph();p.add_run(clean(b['text'])+'  ').bold=True;rich(p,blocks[j+1]['text']);md.extend([b['text'],blocks[j+1]['text']]);j+=2;continue
                if kind=='p':
                    pieces=[b['text']]
                    while j+1<len(blocks) and blocks[j+1]['kind']=='p' and len((' '.join(pieces)+' '+blocks[j+1]['text']).split())<=105:
                        j+=1;pieces.append(blocks[j]['text'])
                    p=d.add_paragraph();rich(p,' '.join(pieces));md.extend(pieces)
                elif kind=='h':
                    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run(clean(b['text'])).bold=True;md.append(b['text'])
                elif kind=='bullets':
                    for item in b['items']:
                        p=d.add_paragraph();p.paragraph_format.left_indent=Cm(.22);p.paragraph_format.first_line_indent=Cm(-.22)
                        p.add_run('• ');rich(p,item);md.append('- '+item)
                elif kind=='check':
                    p=d.add_paragraph();p.add_run('Kontrol  ').bold=True;rich(p,b['question']);p.add_run('  Yanıt: ').bold=True;rich(p,b['answer']);md.extend([b['question'],b['answer']])
                elif kind=='table':
                    if mod==4 and idx in [0,1]:
                        # Term definitions retain their full wording in two reading columns.
                        rows=b['rows'];half=(len(rows)+1)//2;packed=[]
                        for k in range(half):
                            pair=rows[k+half] if k+half<len(rows) else ['','']
                            packed.append([rows[k][0]+'  '+rows[k][1],pair[0]+'  '+pair[1]])
                        table(d,['Terim ve anlamı','Terim ve anlamı'],packed,[8.8,8.8],10.1)
                    else:table(d,b['headers'],b['rows'],b.get('widths'))
                    md.append('| '+' | '.join(b['headers'])+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in b['rows']))
                elif kind=='code':
                    p=d.add_paragraph(style='Code');p.paragraph_format.keep_together=True;p.add_run(b['text']);md.append('```\n'+b['text']+'\n```')
                elif kind=='figure':
                    name='gercek_ornekler_kisa.png' if 'gercek_ornekler' in b['path'] else 'is_akisi_kisa.png'
                    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(1)
                    inline=p.add_run().add_picture(str(ASSETS/name),width=Cm(WIDTH));inline._inline.docPr.set('descr',b['caption'])
                    p=d.add_paragraph(style='Caption compact');rich(p,b['caption']);md.append(b['caption'])
                elif kind=='link':
                    p=d.add_paragraph();p.paragraph_format.space_after=Pt(3);hyperlink(p,b['text'],url=b['url']);md.append(f'[{b["text"]}]({b["url"]})')
                else:raise ValueError(kind)
                j+=1
            p=d.paragraphs[-1]
            r=p.add_run('  [');r.font.size=Pt(8.5)
            for k,f in enumerate(lesson.get('sourcefiles',[])):
                if k:p.add_run(' · ').font.size=Pt(8.5)
                hyperlink(p,f'D{source_id[f]:02d}',anchor='file'+str(source_id[f]),size=8.5)
            p.add_run(']').font.size=Pt(8.5)
    OUT.mkdir(exist_ok=True,parents=True);d.save(OUT/(STEM+'.docx'));(OUT/(STEM+'.md')).write_text('\n\n'.join(md)+'\n')
    report={'status':'structure_passed_pending_visual_and_semantic_review','expected_pages':15,'original_lessons':38,
            'retained_lessons':len(assigned),'retained_blocks':len(coverage),'sourcefiles':len(sources),'mapping':coverage,
            'source_sha256':{str((SOURCE/f).relative_to(ROOT)):hashlib.sha256((SOURCE/f).read_bytes()).hexdigest() for f in FILES},
            'compact_sha256':{str((SHORT/f).relative_to(ROOT)):hashlib.sha256((SHORT/f).read_bytes()).hexdigest() for f in FILES},
            'figures':'Same observations and predictions, redrawn with compact placement; workflow labels retained',
            'body_font':'Carlito 10.5 pt; table text 10.1–10.2 pt; no miniature body text',
            'layout':[{'section':i,'title':t,'lessons':ps} for i,(t,ps) in enumerate(LAYOUT,1)]}
    (ROOT/'reports/compact_learning_guide_coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['expected_pages','retained_lessons','retained_blocks','sourcefiles']},ensure_ascii=False))

if __name__=='__main__':main()
