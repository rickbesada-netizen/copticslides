# Legacy Coptic font -> Unicode Coptic converters
JENKIM = '̀'
OVER = '̅'

CS = {
 'a':'ⲁ','b':'ⲃ','g':'ⲅ','d':'ⲇ','e':'ⲉ','^':'ⲋ','z':'ⲍ','y':'ⲏ',';':'ⲑ','i':'ⲓ','k':'ⲕ','l':'ⲗ','m':'ⲙ','n':'ⲛ',
 'x':'ⲝ','o':'ⲟ','p':'ⲡ','r':'ⲣ','c':'ⲥ','t':'ⲧ','u':'ⲩ','v':'ⲫ',',':'ⲭ',"'":'ⲯ','w':'ⲱ','s':'ϣ','f':'ϥ',
 'q':'ϧ','h':'ϩ','j':'ϫ','[':'ϭ',']':'ϯ',
 'A':'Ⲁ','B':'Ⲃ','G':'Ⲅ','D':'Ⲇ','E':'Ⲉ','Z':'Ⲍ','Y':'Ⲏ',':':'Ⲑ','I':'Ⲓ','K':'Ⲕ','L':'Ⲗ','M':'Ⲙ','N':'Ⲛ',
 'X':'Ⲝ','O':'Ⲟ','P':'Ⲡ','R':'Ⲣ','C':'Ⲥ','T':'Ⲧ','U':'Ⲩ','V':'Ⲫ','<':'Ⲭ','"':'Ⲯ','W':'Ⲱ','S':'Ϣ','F':'Ϥ',
 'Q':'Ϧ','H':'Ϩ','J':'Ϫ','{':'Ϭ','}':'Ϯ',
 '@':':', '/':'/', '-':'-', '.':'.', '+':'+', '!':'!', '(':'(', ')':')',
}
ATH = {
 'a':'ⲁ','b':'ⲃ','g':'ⲅ','d':'ⲇ','e':'ⲉ','z':'ⲍ','h':'ⲏ','q':'ⲑ','i':'ⲓ','k':'ⲕ','l':'ⲗ','m':'ⲙ','n':'ⲛ',
 '[':'ⲝ','o':'ⲟ','p':'ⲡ','r':'ⲣ','c':'ⲥ','t':'ⲧ','u':'ⲩ','v':'ⲫ','x':'ⲭ','y':'ⲯ','w':'ⲱ',']':'ϣ','f':'ϥ',
 "'":'ϧ','\\':'ϩ','j':'ϫ','s':'ϭ',';':'ϯ',
 'A':'Ⲁ','B':'Ⲃ','G':'Ⲅ','D':'Ⲇ','E':'Ⲉ','Z':'Ⲍ','H':'Ⲏ','Q':'Ⲑ','I':'Ⲓ','K':'Ⲕ','L':'Ⲗ','M':'Ⲙ','N':'Ⲛ',
 'O':'Ⲟ','P':'Ⲡ','R':'Ⲣ','C':'Ⲥ','T':'Ⲧ','U':'Ⲩ','V':'Ⲫ','X':'Ⲭ','Y':'Ⲯ','W':'Ⲱ','}':'Ϣ','F':'Ϥ',
 '"':'Ϧ','|':'Ϩ','J':'Ϫ','S':'Ϭ',':':'Ϯ',
 '>':':', '_':'ϭ'+OVER+'ⲥ'+OVER, '-':'-', '.':'.', '(':'(', ')':')', '…':'...', '—':'-',
 '#':'', '$':'', '“':'', '”':'', '„':'', '‟':'',
}
# legacy (non-CS) Avva Shenouda: mostly vocal extensions in this book
AVVA = dict(CS)
AVVA.update({'v':'ⲩ','u':'ⲩ','7':'ⲝ','4':'ϥ','h':'ϩ','s':'ϭ','>':':','_':'-','3':'ϣ','0':'ϫ','1':'','5':'','=':''})

FONTMAP = {'CS New Athanasius':CS,'CS Avva Shenouda':CS,'Athanasius':ATH,'Avva_Shenouda':AVVA}
COPTIC_FONTS = set(FONTMAP)
POST_OVERLINE = {'Athanasius':set('/?')}

def convert(text, font):
    """Convert a run of legacy-font text to Unicode Coptic."""
    m = FONTMAP[font]
    out = []
    pend_j = False; pend_o = False
    post = POST_OVERLINE.get(font, set())
    for ch in text:
        if ch == '`':
            pend_j = True; continue
        if font != 'Athanasius' and ch == '=':
            pend_o = True; continue
        if ch in post:
            # overline on previous letter
            if out and out[-1] not in ' ':
                out.append(OVER)
            continue
        if ch == ' ':
            if pend_j: pend_j = False
            pend_o = False
            out.append(' '); continue
        u = m.get(ch, ch)
        if u == '':
            continue
        out.append(u)
        if pend_o: out.append(OVER); pend_o = False
        if pend_j and u[:1].isalpha(): out.append(JENKIM); pend_j = False
    s = ''.join(out)
    return s
