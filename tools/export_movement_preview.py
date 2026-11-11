"""Export implemented movement from the avatar renderer; music levels are simulated."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.models import load_pack
from aura.music import Transition

model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
frames=[];transition=Transition()
for label in ('stretch','wave','dance','headbang'):
    for index in range(48):
        t=index/15;clock=len(frames)/15
        reaction=transition.update(label if label in ('dance','headbang') else 'off',1/15,.8)
        frame=Image.new('RGBA',(600,840),'#10151F')
        frame.alpha_composite(model.render(t,label if label in ('stretch','wave') else 'idle',clock=clock,music=reaction))
        ImageDraw.Draw(frame).text((20,810),'Movement preview: '+label,fill='#B6A0FF')
        frames.append(frame.convert('RGB').resize((360,504),Image.Resampling.LANCZOS))
out=Path('artifacts/avatar-movements.gif');out.parent.mkdir(exist_ok=True)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=67,loop=0)
frames[24].save(out.with_suffix('.png'))
print(out)
