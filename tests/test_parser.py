from app.parser import parse_text

def test_m3u_parse_and_classify():
    text='''#EXTM3U\n#EXTINF:-1 group-title="央视",CCTV1\nhttps://example.com/a.m3u8\n#EXTINF:-1 group-title="体育",体育频道\nhttps://example.com/b.m3u8\n'''
    xs=parse_text(text,'test')
    assert len(xs)==2
    assert xs[0].name=='CCTV-1' and xs[0].group=='央卫'
    assert xs[1].subgroup=='体育'

def test_text_and_dedupe():
    text='A,https://a.example/x.m3u8\nA2,https://a.example/x.m3u8\n'
    xs=parse_text(text)
    assert len(xs)==1

def test_json_parse():
    xs=parse_text('{"channels":[{"name":"CCTV-5","url":"https://x/y.m3u8"}]}')
    assert len(xs)==1 and xs[0].group=='央卫'
