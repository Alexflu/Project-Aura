"""Show actual music poses with synthetic levels; not a beat-sync demonstration."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.models import load_pack
from aura.music import Transition

model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
frames=[];transition=Transition()
for mode in ('gentle','dance','headbang','read'):
    for index in range(24):
        t=index/12
        reaction=transition.update(mode,1/12,.8)
        body=model.render(len(frames)/12,music=reaction)
        frame=Image.new('RGBA',(600,840),'#10151F')
        frame.alpha_composite(body)
        ImageDraw.Draw(frame).text((20,810),'Music reaction: '+mode+' (simulated level)',fill='#B6A0FF')
        frames.append(frame.convert('RGB').resize((360,504),Image.Resampling.LANCZOS))
out=Path('artifacts/aura-music-reactions.gif');out.parent.mkdir(exist_ok=True)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=83,loop=0)
frames[-1].save(out.with_suffix('.png'))
print(out)
