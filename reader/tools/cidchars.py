# extract chars with cid, font id, position for res.pdf
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar
from pdfminer.pdfpage import PDFPage
import pdfminer.converter as conv
import json, sys
captured=[]
orig=conv.PDFLayoutAnalyzer.render_char
def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
    adv=orig(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
    item=self.cur_item._objs[-1]
    item.cid=cid; item.fontid=id(font)
    return adv
conv.PDFLayoutAnalyzer.render_char=render_char
def chars(path, pages=None):
    rm=PDFResourceManager(); dev=PDFPageAggregator(rm, laparams=None); it=PDFPageInterpreter(rm,dev)
    out=[]
    with open(path,'rb') as f:
        for i,page in enumerate(PDFPage.get_pages(f)):
            if pages and i not in pages: continue
            it.process_page(page); lay=dev.get_result()
            h=page.mediabox[3]
            cs=[]
            def walk(o):
                for x in o:
                    if isinstance(x,LTChar):
                        cs.append(dict(t=x.get_text(),cid=x.cid,f=x.fontname.split('+')[-1],fid=x.fontid,x0=x.x0,x1=x.x1,top=h-x.y1,bottom=h-x.y0,size=x.size,col=str(getattr(x.graphicstate,'ncolor',None))))
                    elif hasattr(x,'_objs'): walk(x._objs)
            walk(lay._objs)
            out.append((i,cs))
    return out
if __name__=='__main__':
    res=chars(sys.argv[1])
    json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False)
