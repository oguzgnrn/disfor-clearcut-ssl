"""Build a Turkish beginner course from independently reviewed lesson sources.

Use the Codex bundled Python runtime for DOCX authoring. Export PDF with the
bundled documents renderer and visually inspect every page before delivery.
"""
from pathlib import Path
import json, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/egitim'; ASSETS=SOURCE/'assets'; OUT=ROOT/'output/egitim'
STEM='Orman_SSL_Sifirdan_Proje_Hakimiyet_Rehberi'
ASSETS.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
FONTROOT=Path('/Users/gnrnoguz/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')


def figures():
    with np.load(ROOT/'output/advanced_prediction/input.npz',allow_pickle=False) as d:
        ids=d['ids'].tolist(); x=d['x']; mask=d['observed']; bands=json.loads(str(d['metadata']))['channels']
    pred=json.loads((ROOT/'output/advanced_prediction/predictions.json').read_text())
    selected=['disfor-1733-2019','disfor-1664-2018']
    def font(size,bold=False):return ImageFont.truetype(str(FONTROOT/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size)
    img=Image.new('RGB',(1785,1230),'white');draw=ImageDraw.Draw(img)
    for panel,(key,label) in enumerate(zip(selected,['Doğru bulunan kesim','Kaçırılan kesim'])):
        i=ids.index(key);score=pred['probabilities'][pred['ids'].index(key)][1];year=int(key.rsplit('-',1)[1])
        top=panel*610+110;bottom=top+380;left=140;right=1710
        draw.text((left,top-95),f'{label}   {key}',font=font(29,True),fill='#172C38')
        draw.text((left,top-51),f'Kesim skoru {score:.4f}'.replace('.',','),font=font(26),fill='#47555E')
        peak=max(float(np.max(x[i,:,bands.index(b)][mask[i,:,bands.index(b)]])) for b in ['B04','B08','B12'])
        ymax=math.ceil(peak/1000)*1000
        xx=lambda j:left+(right-left)*j/23
        yy=lambda v:bottom-(bottom-top)*v/ymax
        for value in np.linspace(0,ymax,5):
            y=yy(value);draw.line((left,y,right,y),fill='#E2E8EB',width=2)
            draw.text((left-20,y),str(int(value)),font=font(23),fill='#47555E',anchor='rm')
        draw.text((left-15,top-20),'DN',font=font(24),fill='#47555E',anchor='rb')
        draw.line((left,top,left,bottom,right,bottom),fill='#717C83',width=2)
        for y in range(top,bottom,16):draw.line((xx(11.5),y,xx(11.5),min(y+8,bottom)),fill='#8D999F',width=2)
        for tick,labeltick in zip([0,5,12,17,23],[f'Oca {year-1}','Haz',f'Oca {year}','Haz','Ara']):
            draw.text((xx(tick),bottom+18),labeltick,font=font(22),fill='#47555E',anchor='mt')
        for band,color in [('B04','#AE673F'),('B08','#327A56'),('B12','#687CA9')]:
            c=bands.index(band);values=np.where(mask[i,:,c],x[i,:,c],np.nan)
            for j in range(24):
                if not np.isfinite(values[j]):continue
                px,py=xx(j),yy(values[j]);draw.ellipse((px-4,py-4,px+4,py+4),fill=color)
                if j and np.isfinite(values[j-1]):draw.line((xx(j-1),yy(values[j-1]),px,py),fill=color,width=3)
            lx=1190+['B04','B08','B12'].index(band)*170
            draw.line((lx,top-37,lx+36,top-37),fill=color,width=4);draw.text((lx+47,top-52),band,font=font(24),fill=color)
    img.save(ASSETS/'gercek_ornekler.png',dpi=(210,210))
    img=Image.new('RGB',(1785,760),'white');draw=ImageDraw.Draw(img)
    rows=[(95,['DISFOR ölçümleri','Aylık 24 × 10 seri','Kalite ve referans bilgisi']),
          (355,['paper_v4 araştırması','5 kat ve 3 seed','180 koşu ve karşılaştırma']),
          (625,['advanced_v3 ürünü','10 eğitimli üye','Skor ve inceleme ekranı'])]
    for y,labels in rows:
        for x0,label in zip([280,875,1460],labels):draw.text((x0,y),label,anchor='mm',font=font(28),fill='#172C38')
        for x0,x1 in [(510,610),(1110,1210)]:
            draw.line((x0,y,x1,y),fill='#547284',width=4);draw.polygon([(x1,y),(x1-16,y-10),(x1-16,y+10)],fill='#547284')
    draw.text((890,220),'Ayrı protokollerle iki kullanım yolu',anchor='mm',font=font(28),fill='#536571')
    draw.text((890,490),'Makale skoru ile ürün skoru aynı deney değildir',anchor='mm',font=font(28),fill='#536571')
    img.save(ASSETS/'is_akisi.png',dpi=(210,210))


def bookmark(paragraph,name):
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(int(re.sub(r'\D','',name) or '999')));start.set(qn('w:name'),name)
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),start.get(qn('w:id')))
    paragraph._p.insert(0,start);paragraph._p.append(end)


def link(paragraph,text,anchor=None,url=None):
    hl=OxmlElement('w:hyperlink')
    if anchor:hl.set(qn('w:anchor'),anchor)
    if url:
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        hl.set(qn('r:id'),paragraph.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement('w:r');pr=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'235775');pr.append(color)
    r.append(pr);t=OxmlElement('w:t');t.text=text;r.append(t);hl.append(r);paragraph._p.append(hl)


def setup():
    d=Document();s=d.sections[0];s.page_width=Cm(21);s.page_height=Cm(29.7)
    s.left_margin=s.right_margin=Cm(2.1);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.7);s.footer_distance=Cm(.7)
    normal=d.styles['Normal'];normal.font.name='DejaVu Sans';normal.font.size=Pt(10.5)
    normal.paragraph_format.line_spacing=1.14;normal.paragraph_format.space_after=Pt(7);normal.paragraph_format.widow_control=True
    for name,size in [('Title',26),('Subtitle',13),('Heading 1',18),('Heading 2',11.5),('Heading 3',10.5)]:
        st=d.styles[name];st.font.name='DejaVu Sans';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st.font.bold=name!='Subtitle';st.font.underline=False
        st.paragraph_format.space_before=Pt(11 if name.startswith('Heading') else 0);st.paragraph_format.space_after=Pt(8);st.paragraph_format.keep_with_next=True
        for border in st.element.xpath('./w:pPr/w:pBdr'):border.getparent().remove(border)
    for name in ['List Bullet','List Number']:
        d.styles[name].font.name='DejaVu Sans';d.styles[name].font.size=Pt(10.5)
        d.styles[name].paragraph_format.space_after=Pt(5)
    caption=d.styles['Caption'];caption.font.name='DejaVu Sans';caption.font.size=Pt(8.5);caption.font.color.rgb=RGBColor.from_string('47555E')
    from docx.enum.style import WD_STYLE_TYPE
    for name,size in [('Code Guide',8),('Evidence',7.5)]:
        st=d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH);st.font.name='DejaVu Sans Mono' if name.startswith('Code') else 'DejaVu Sans';st.font.size=Pt(size)
        st.paragraph_format.space_after=Pt(4);st.paragraph_format.line_spacing=1.05
    foot=s.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    foot.add_run('Orman SSL  |  Öğrenme rehberi  |  ').font.size=Pt(8)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');foot._p.append(fld)
    d.core_properties.title='Orman SSL Sıfırdan Proje Hakimiyet Rehberi'
    d.core_properties.subject='Temel kavramlar deneyler uygulama ve danışman görüşmesine hazırlık'
    d.core_properties.author='';d.core_properties.keywords='Orman SSL, eğitim, Türkçe, Sentinel 2'
    return d


def rich(paragraph,text):
    # Strip prose Markdown decoration from collaborators; retain readable text.
    text=str(text).translate(str.maketrans({'–':'-','—':'-','‑':'-','−':'-'}))
    for n,part in enumerate(re.split(r'(`[^`]+`|\*\*[^*]+\*\*)',str(text))):
        if part.startswith('**') and part.endswith('**'):paragraph.add_run(part[2:-2]).bold=True
        elif part.startswith('`') and part.endswith('`'):
            r=paragraph.add_run(part[1:-1]);r.font.name='DejaVu Sans Mono';r.font.size=Pt(9)
        else:paragraph.add_run(part)


def table(d,headers,rows,widths=None):
    n=len(headers);widths=widths or ({2:[5.1,11.7],3:[4.1,6.35,6.35],4:[6.3,3.5,3.5,3.5],5:[1.7,4.3,4.0,3.2,3.6]}.get(n,[16.8/n]*n))
    tab=d.add_table(rows=1,cols=n);tab.autofit=False;tab.alignment=WD_TABLE_ALIGNMENT.CENTER
    for j,w in enumerate(widths):tab.columns[j].width=Cm(w)
    for j,value in enumerate(headers):rich(tab.rows[0].cells[j].paragraphs[0],value)
    for row in rows:
        cells=tab.add_row().cells
        for j,val in enumerate(row):rich(cells[j].paragraphs[0],val)
    for i,row in enumerate(tab.rows):
        prop=row._tr.get_or_add_trPr();prop.append(OxmlElement('w:cantSplit'))
        if i==0:prop.append(OxmlElement('w:tblHeader'))
        for j,cell in enumerate(row.cells):
            cell.width=Cm(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
            for side in ['top','bottom','left','right']:
                el=OxmlElement('w:'+side)
                for k,v in [('val','single'),('sz','4'),('color','D9D9D9')]:el.set(qn('w:'+k),v)
                borders.append(el)
            cp.append(borders);mar=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'80');el.set(qn('w:type'),'dxa');mar.append(el)
            cp.append(mar);shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'244356' if i==0 else ('F0F4F6' if i%2==0 else 'FFFFFF'));cp.append(shd)
            for p in cell.paragraphs:
                p.paragraph_format.space_before=Pt(1);p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=1.08
                if i and re.fullmatch(r'[\d.,% +±/−–-]+',str(rows[i-1][j])):p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:run.font.size=Pt(9);run.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '000000');run.bold=i==0
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(5);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=Pt(2);p.add_run().font.size=Pt(2)


def main():
    figures();d=setup();md=[]
    groups=[];allpages=[]
    for filename,label in [('01_temeller.json','Temel kavramlar'),('02_modeller_ve_deneyler.json','Öğrenme ve bilimsel deney'),('03_dosyalar_ve_gosterim.json','Dosyalar ve canlı gösterim'),('04_hocaya_hazirlik.json','Görüşme ve kendini sınama'),('05_basvuru.json','Terimler kaynaklar ve son tekrar')]:
        data=json.loads((SOURCE/filename).read_text());groups.append((label,len(allpages)+3,len(data['pages'])))
        allpages+=data['pages']
    p=d.add_paragraph('Orman SSL\nSıfırdan Proje\nHakimiyet Rehberi','Title');bookmark(p,'cover0')
    d.add_paragraph('Temel kavramlar deneyler uygulama ve danışman görüşmesine hazırlık','Subtitle')
    d.add_paragraph('Türkçe çalışma kitabı  |  1 Ekim 2026 güncellemesi')
    d.add_paragraph('Bu rehber, konuya yeni başlayan biri için hazırlanmıştır. Hedefin, projenin girdisini ve çıktısını anlatmak, neden bu deneyleri yaptığımızı açıklamak, sonuçların sınırlarını bilmek ve hocanın karşısında doğru dosyayı açabilmektir. Her ayrıntıyı ezberlemek yerine, bir iddiayı nasıl kanıtlayacağını öğren.')
    d.add_paragraph('Bu kitabı bitirdiğinde yapabileceklerin','Heading 2')
    for text in ['Bir konumun 24 aylık uydu dizisini ve eksik gözlemlerini okuyabilmek.','Model eğitimi, tahmin üretimi ve başarı ölçümü arasındaki farkı açıklamak.','SSL kazancının eğitim bütçesine neden bağlı olduğunu gerçek sonuçlarla anlatmak.','Doğru ve yanlış tahminleri uygulamada açıp ilgili kanıt dosyasını bulmak.','Bilmediğin bir soruyu dürüstçe ele almak ve sonraki deneyi planlamak.']:
        d.add_paragraph(text,'List Bullet')
    d.add_paragraph('Nasıl çalışmalısın','Heading 2')
    d.add_paragraph('Her bölümün ardından kitabı kapatıp konuyu kendi cümlenle anlat. Mini soruyu yanıtla, sonra açıklamayı oku. Dosya ve demo bölümlerinde gerçekten tıkla ve dene. Son bölümdeki sınavı cevap anahtarına bakmadan çöz. Bölüm başına kısa çalışma oturumları, tek seferde uzun okumadan daha uygulanabilir bir başlangıçtır.')
    d.add_paragraph('Durum bilgisi','Heading 2')
    d.add_paragraph('Araştırma paper_v4 ve ürün advanced_v3 hazırdır. 30 Eylül denetiminde 58 yazılım testi geçti; 180 kayıtlı deney kontrol edildi ve paketten bir SSL koşusu yeniden eğitilerek aynı tahminler elde edildi. Bağımsız dış saha doğrulaması henüz yapılmadı. Ana dersler bu sabit sürümleri öğretir. 1 Ekim ürün ve deney eklerini output/final/Orman_SSL_Gelistirme_Eki.pdf ile birlikte oku. Alan uzmanlığı pratikle gelişir.')
    md+=['# Orman SSL Sıfırdan Proje Hakimiyet Rehberi','1 Ekim 2026 güncellemesi','Bu rehber konuya yeni başlayanlar için temel kavramları, gerçek deneyleri, dosyaları, canlı gösterimi ve hocayla görüşmeyi birlikte öğretir.']
    d.add_page_break();p=d.add_paragraph('İçindekiler ve çalışma rotası','Heading 1');bookmark(p,'toc1')
    d.add_paragraph('Başlıkların bağlantılarına tıklayarak bölümlere geçebilirsin. Sayfa numaraları bu sürüme aittir. Düzenlenebilir Word dosyasında metin uzatılırsa içerik listesi de güncellenmelidir.')
    for label,start,count in groups:
        p=d.add_paragraph();link(p,f'{label}   {start}-{start+count-1}',anchor=f'lesson{start}');p.paragraph_format.space_after=Pt(13)
    d.add_paragraph('Yalnız bir saatin varsa','Heading 2')
    d.add_paragraph('Önce temel soruyu, iki sürüm ayrımını ve gerçek sonuç tablosunu oku. Ardından beş dakikalık demoyu bir kez yap. Son tekrar sayfasından 30 saniyelik anlatımı prova et. Bu yol toplantıya başlangıç sağlar; kavramların tamamını öğrendiğin anlamına gelmez.')
    d.add_paragraph('Bir günün varsa','Heading 2')
    d.add_paragraph('Temel kavramlar ile model ve deney bölümlerini iki ayrı oturumda çalış. Sonra dosya haritasını aç, gerçek bir eğitim kaydını bul ve demoyu yap. Akşam son sınavı çöz; yanlış yanıtların olduğu bölümlere geri dön.')
    d.add_paragraph('Bir haftan varsa','Heading 2')
    d.add_paragraph('Görüşmeye hazırlık bölümündeki yedi günlük programı uygula. Her gün kısa bir sözlü açıklama kaydet. Son gün projeyi ekrana bakmadan iki dakika anlat; sonra bilgisayarda kanıtlarını göster.')
    d.add_paragraph('Okuma işaretleri','Heading 2')
    d.add_paragraph('“Kendini kontrol et” soruları hemen yanıtını verir; önce üzerini kapat. Son sınavın cevapları ayrı sayfadadır. “Dayanak” satırı projedeki dosyayı gösterir. G1 gibi kodlar kaynak bölümündeki dış kaynağa gider. Öğretici sayısal örnekler gerçek deney sonuçlarından açıkça ayrılır.')
    for i,page in enumerate(allpages,3):
        d.add_page_break();p=d.add_paragraph(page['title'],'Heading 1');bookmark(p,f'lesson{i}');md+=['\n## '+page['title']
        ]
        for block in page['blocks']:
            kind=block['kind']
            if kind=='p':p=d.add_paragraph();rich(p,block['text']);md.append(block['text'])
            elif kind=='h':d.add_paragraph(block['text'],'Heading 2');md.append('### '+block['text'])
            elif kind=='bullets':
                for item in block['items']:p=d.add_paragraph(style='List Bullet');rich(p,item);md.append('- '+item)
            elif kind=='table':
                table(d,block['headers'],block['rows'],block.get('widths'))
                md.append('| '+' | '.join(map(str,block['headers']))+' |\n| '+' | '.join(['---']*len(block['headers']))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in block['rows']))
            elif kind=='code':
                p=d.add_paragraph(style='Code Guide');p.paragraph_format.keep_together=True;p.add_run(block['text']);md.append('```bash\n'+block['text']+'\n```')
            elif kind=='figure':
                p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(ROOT/block['path']),width=Cm(block.get('width',16.6)))
                d.add_paragraph(block['caption'],'Caption');md.append('!['+block['caption']+'](../../'+block['path']+')')
            elif kind=='check':
                p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run('Kendini kontrol et  ').bold=True;rich(p,block['question'])
                p=d.add_paragraph();p.add_run('Yanıt  ').bold=True;rich(p,block['answer']);md+=['**Kendini kontrol et:** '+block['question'],'**Yanıt:** '+block['answer']]
            elif kind=='link':
                p=d.add_paragraph();link(p,block['text'],url=block['url']);md.append('['+block['text']+']('+block['url']+')')
            else:raise ValueError(kind)
        files=page.get('sourcefiles',[])
        if files:
            for f in files:
                if not (ROOT/f).is_file():raise FileNotFoundError(f)
            p=d.add_paragraph(style='Evidence');rich(p,'Dayanak  '+'  |  '.join(files));md.append('Dayanak: '+'; '.join(files))
    d.save(OUT/(STEM+'.docx'))
    (OUT/(STEM+'.md')).write_text('\n\n'.join(md)+'\n')
    (OUT/'icerik_haritasi.json').write_text(json.dumps({'expected_pages':len(allpages)+2,'groups':[dict(title=l,start=s,end=s+n-1) for l,s,n in groups],'pages':[dict(page=i,title=p['title']) for i,p in enumerate(allpages,3)]},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'docx':str(OUT/(STEM+'.docx')),'expected_pages':len(allpages)+2,'lesson_pages':len(allpages)},ensure_ascii=False))

if __name__=='__main__':main()
