from app.models import Source
from app.validator import calc_score

def test_score_valid_hd_audio():
    x=Source(id='1',name='x',url='https://x',valid=True,width=1920,height=1080,audio_codec='aac',video_codec='h264',latency_ms=100,first_frame_ms=1000)
    assert calc_score(x)>=90
