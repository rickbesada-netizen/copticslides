# Table of contents of the Book of the Holy Pascha (book page numbers; PDF page = book page + 9)
OFFSET = 9
LAST_BOOK_PAGE = 642

def H(n, day_en, day_ar):
    names = {1: ('First', 'الأولى'), 3: ('Third', 'الثالثة'), 6: ('Sixth', 'السادسة'), 9: ('Ninth', 'التاسعة'), 11: ('Eleventh', 'الحادية عشر'), 12: ('Twelfth', 'الثانية عشر')}
    en, ar = names[n]
    return (f'{en} Hour of {day_en}', f'الساعة {ar} من {day_ar}')

GROUPS = [
    dict(id='last-friday', holy='last-friday', en='Last Friday of the Great Lent', ar='جمعة ختام الصوم', sections=[
        (15, 'Matins of the Last Friday of the Great Lent', 'باكر جمعة ختام الصوم', 'Matins'),
        (22, 'Sacrament of Holy Unction', 'سر مسحة المرضى (القنديل)', 'Unction')]),
    dict(id='lazarus', holy='lazarus', en='Lazarus Saturday', ar='سبت لعازر', sections=[
        (47, 'Lazarus Saturday', 'سبت لعازر', 'Lazarus')]),
    dict(id='palm', holy='palm', en='Palm Sunday', ar='أحد الشعانين', sections=[
        (59, 'Palm Sunday: Vespers and Matins', 'أحد الشعانين: عشية وباكر', 'Palm Sunday'),
        (69, 'Procession of Palm Sunday', 'دورة أحد الشعانين', 'Procession'),
        (82, 'Liturgy of Palm Sunday', 'قداس أحد الشعانين', 'Liturgy'),
        (95, 'Public Funeral, Sixth Hour of Palm Sunday', 'التجنيز العام، الساعة السادسة من أحد الشعانين', 'Funeral'),
        (127, *H(9, 'Palm Sunday', 'أحد الشعانين'), 'Ninth Hour'),
        (130, *H(11, 'Palm Sunday', 'أحد الشعانين'), 'Eleventh Hour')]),
    dict(id='every-hour', holy=None, en='Repeated Prayers of Every Hour', ar='الصلوات المتكررة في كل ساعة', sections=[
        (101, 'Repeated Prayers of Every Hour', 'الصلوات المتكررة في كل ساعة', 'Repeated Prayers')]),
]

def day(gid, holy, en, ar, start, hours, day_en, day_ar):
    secs = [(start, f'{en}: Introduction', f'{ar}: مقدمة', en)]
    for n, p in hours:
        secs.append((p, *H(n, day_en, day_ar), H(n, day_en, day_ar)[0].split(' of ')[0]))
    return dict(id=gid, holy=holy, en=en, ar=ar, sections=secs)

GROUPS += [
    day('monday-eve', 'monday-eve', 'Monday Eve of the Holy Pascha', 'ليلة الاثنين من البصخة المقدسة', 134,
        [(1, 136), (3, 139), (6, 141), (9, 144), (11, 147)], 'Monday Eve', 'ليلة الاثنين'),
    day('monday', 'monday', 'Monday of the Holy Pascha', 'يوم الاثنين من البصخة المقدسة', 150,
        [(1, 152), (3, 158), (6, 162), (9, 165), (11, 171)], 'Monday', 'يوم الاثنين'),
    day('tuesday-eve', 'tuesday-eve', 'Tuesday Eve of the Holy Pascha', 'ليلة الثلاثاء من البصخة المقدسة', 176,
        [(1, 178), (3, 181), (6, 184), (9, 187), (11, 190)], 'Tuesday Eve', 'ليلة الثلاثاء'),
    day('tuesday', 'tuesday', 'Tuesday of the Holy Pascha', 'يوم الثلاثاء من البصخة المقدسة', 193,
        [(1, 195), (3, 200), (6, 204), (9, 208), (11, 218)], 'Tuesday', 'يوم الثلاثاء'),
    day('wednesday-eve', 'wednesday-eve', 'Wednesday Eve of the Holy Pascha', 'ليلة الأربعاء من البصخة المقدسة', 225,
        [(1, 227), (3, 230), (6, 233), (9, 236), (11, 238)], 'Wednesday Eve', 'ليلة الأربعاء'),
    day('wednesday', 'wednesday', 'Wednesday of the Holy Pascha', 'يوم الأربعاء من البصخة المقدسة', 241,
        [(1, 243), (3, 248), (6, 252), (9, 256), (11, 262)], 'Wednesday', 'يوم الأربعاء'),
    day('thursday-eve', 'thursday-eve', 'Thursday Eve of the Holy Pascha', 'ليلة الخميس من البصخة المقدسة', 265,
        [(1, 267), (3, 270), (6, 273), (9, 276), (11, 279)], 'Thursday Eve', 'ليلة الخميس'),
    dict(id='thursday', holy='thursday', en='Great (Covenant) Thursday', ar='خميس العهد', sections=[
        (281, 'Great Thursday: Introduction', 'خميس العهد: مقدمة', 'Introduction'),
        (283, *H(1, 'Thursday', 'يوم الخميس'), 'First Hour'),
        (286, 'Offering of Morning Incense', 'رفع بخور باكر', 'Morning Incense'),
        (291, *H(3, 'Thursday', 'يوم الخميس'), 'Third Hour'),
        (294, *H(6, 'Thursday', 'يوم الخميس'), 'Sixth Hour'),
        (297, *H(9, 'Thursday', 'يوم الخميس'), 'Ninth Hour'),
        (303, 'Liturgy of Blessing the Water (Lakkan)', 'صلاة اللقان', 'Blessing the Water'),
        (321, 'Liturgy of Holy Thursday', 'قداس خميس العهد', 'Liturgy of the Holy Thursday'),
        (324, *H(11, 'Thursday', 'يوم الخميس'), 'Eleventh Hour')]),
    day('friday-eve', 'friday-eve', 'Good Friday Eve of the Holy Pascha', 'ليلة الجمعة العظيمة', 329,
        [(1, 331), (3, 343), (6, 347), (9, 352), (11, 358)], 'Good Friday Eve', 'ليلة الجمعة'),
    dict(id='friday', holy='friday', en='Good Friday', ar='الجمعة العظيمة', sections=[
        (367, *H(1, 'Good Friday', 'الجمعة العظيمة'), 'First Hour'),
        (381, *H(3, 'Good Friday', 'الجمعة العظيمة'), 'Third Hour'),
        (393, *H(6, 'Good Friday', 'الجمعة العظيمة'), 'Sixth Hour'),
        (415, *H(9, 'Good Friday', 'الجمعة العظيمة'), 'Ninth Hour'),
        (429, *H(11, 'Good Friday', 'الجمعة العظيمة'), 'Eleventh Hour'),
        (437, *H(12, 'Good Friday', 'الجمعة العظيمة'), 'Twelfth Hour')]),
    dict(id='psalms', holy=None, en='Book of Psalms (Bright Saturday)', ar='سفر المزامير (ليلة سبت الفرح)', sections=[
        (449, 'Book of Psalms', 'سفر المزامير', 'Psalms')]),
    dict(id='saturday', holy='saturday', en='Bright Saturday', ar='سبت الفرح', sections=[
        (517, 'Bright Saturday: Praises of the Night', 'سبت الفرح: التسبحة', 'Bright Saturday'),
        (553, 'Morning Prayer of Bright Saturday', 'صلاة باكر سبت الفرح', 'Morning Prayer'),
        (575, *H(3, 'Bright Saturday', 'سبت الفرح'), 'Third Hour'),
        (577, *H(6, 'Bright Saturday', 'سبت الفرح'), 'Sixth Hour'),
        (579, 'Book of Revelation (Apocalypse)', 'سفر الرؤيا', 'Revelation'),
        (601, *H(9, 'Bright Saturday', 'سبت الفرح'), 'Ninth Hour'),
        (604, 'Holy Liturgy of Bright Saturday', 'قداس سبت الفرح', 'Liturgy')]),
    dict(id='easter-eve', holy='easter-eve', en='Resurrection Feast Eve', ar='ليلة عيد القيامة', sections=[
        (615, 'Resurrection Feast Eve', 'ليلة عيد القيامة', 'Resurrection Feast Eve'),
        (617, 'Prophecies of the Resurrection Eve', 'نبوات ليلة العيد', 'Prophecies'),
        (625, 'Liturgy of the Resurrection', 'قداس العيد', 'Liturgy'),
        (630, 'Commemoration of the Resurrection', 'تذكار القيامة', 'Commemoration')]),
]
