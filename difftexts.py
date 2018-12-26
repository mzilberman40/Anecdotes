

def canonize(source):
    stop_symbols = '@#$%".,!?:;-\n\r()—1234567890\'*'

    stop_words = (u'это', u'как', u'так',
                  u'и', u'в', u'над',
                  u'к', u'до', u'не',
                  u'на', u'но', u'за',
                  u'то', u'с', u'ли',
                  u'а', u'во', u'от',
                  u'со', u'для', u'о',
                  u'же', u'ну', u'вы',
                  u'бы', u'что', u'кто',
                  u'он', u'она', u'у', u'из',
                  u'это', u'эту', u'эта')

    return ([x for x in [y.strip(stop_symbols) for y in source.lower().split()] if x and (x not in stop_words)])

def genshingle(source, shingleLen=4):
    import binascii
    if len(source) < shingleLen:
        source += ["any"] * (shingleLen - len(source))
    out = []
    for i in range(len(source)-(shingleLen-1)):
        out.append(binascii.crc32(' '.join( [x for x in source[i:i+shingleLen]]).encode('utf-8')))
    if len(out) == 0:
        pass
    return out

def compare (source1,source2):
    same = 0
    for i in range(len(source1)):
        if source1[i] in source2:
            same = same + 1
    return same*2/float(len(source1) + len(source2))*100


def compareText(text1, text2):
    k = 2  # Will assume if lengthes of  texts after canonization differ mor then k times then
    # texts are different
    x1 = canonize(text1)
    x2 = canonize(text2)
    if len(x1) > k * len(x2) or len(x2) > k * len(x1):
        return False
    shinglelen = min(4, len(x1), len(x2))
    return compare(genshingle(x1, shinglelen), genshingle(x2, shinglelen)) > 0

if __name__ == '__main__':
    file1 = "text1.txt"
    encod = "cp1251"
    with open(file1, encoding=encod) as txt1:
        try:
            ttt1 = txt1.read()
        except UnicodeDecodeError as e:
            print(e.encoding)
            print(e.reason)
            print(e.object)
            print(e.start)
            print(e.end)


    file2 = "text3.txt"
    with open(file2, encoding=encod) as txt2:
        ttt2 = txt2.read()

    x1 = canonize(ttt1)
    x2 = canonize(ttt2)
    y1 = genshingle(x1,3)
    y2 = genshingle(x2,3)
    print(x1, x2)
    print(y1, y2)
    print(compare(x1, x2))
    print(compare(y1,y2))


