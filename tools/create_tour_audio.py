"""Generate the local tour voice and original soft effects, without playing audio."""
from array import array
import json
import math
from pathlib import Path
import random
import sys
import time
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.showcase import NARRATION, DURATION, ASSETS
from aura.voice import Speech

RATE=22050


def write(path,samples):
    with wave.open(str(path),"wb") as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(RATE)
        output.writeframes(samples.tobytes())


def main():
    voice=array('h',[0])*(RATE*DURATION)
    manifest=[]
    for start,end,text in NARRATION:
        captured=[]
        def capture(path):
            if path:
                with wave.open(str(path),'rb') as source:
                    captured.append(array('h',source.readframes(source.getnframes())))
        speech=Speech(player=capture)
        try:
            speech.speak(text,voice="female",rate=1,volume=85)
            deadline=time.monotonic()+60
            while not captured and time.monotonic()<deadline:
                speech.poll();time.sleep(.04)
            if not captured:raise RuntimeError("Tour voice preparation timed out.")
            pcm=captured[0]
            if len(pcm)/RATE>end-start:
                raise RuntimeError(f"Narration at {start} exceeds its scene: {len(pcm)/RATE:.2f}s")
            offset=start*RATE
            voice[offset:offset+len(pcm)]=pcm
            manifest.append(dict(start=start,end=end,text=text,audio_seconds=round(len(pcm)/RATE,3)))
        finally:speech.stop()
    write(ASSETS/'tour-voice.wav',voice)
    rng=random.Random(17)
    mix=array('h'); low=0
    for i,sample in enumerate(voice):
        t=i/RATE
        # Original synthesized rotor, rocket and impact. No licensed sound files.
        sound=0
        if 2<t<11:
            envelope=min(1,(t-2)/2)*min(1,(11-t)/2)
            sound += envelope*(math.sin(t*math.tau*48)*.032 + rng.uniform(-1,1)*.018)*( .55+.45*math.sin(t*math.tau*13)**2)
        if .65<t<1.8:
            progress=(t-.65)/1.15
            sound+=math.sin(math.tau*(950*t-220*t*t))*.033*math.sin(progress*math.pi)
        for hit in (1.8,5.2,5.6,6.0,6.4):
            age=t-hit
            if 0<age<1.2:
                low=low*.93+rng.uniform(-1,1)*.07
                sound+=(low*.3+math.sin(age*math.tau*54)*.065)*math.exp(-age*5)
        if 39<t<48:
            local=(t-39)%3
            sound += math.sin(math.tau*(220*t+16*math.sin(t)))*.008*math.sin(math.pi*local/3)**2
        value=round(sample*.9+sound*32767)
        mix.append(max(-32767,min(32767,value)))
    write(ASSETS/'tour-audio.wav',mix)
    (ASSETS/'tour-narration.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(dict(seconds=DURATION,clips=manifest,peak=max(abs(v) for v in mix))))

if __name__=='__main__':main()
