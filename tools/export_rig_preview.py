"""Export the actual rig renderer, not an independently animated concept video."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.models import load_pack
from aura.model_library import REFERENCE
from aura.equipment import BUILTINS

model,_=load_pack(REFERENCE)
width,height=model.data['size']
frames=[];clock=0
for motion in ('idle','bow','cast','wave','draw'):
    for index in range(32):
        t=index/10
        frame=Image.new('RGBA',(width,height+40),'#111827')
        frame.alpha_composite(model.render(t,motion,equipment=BUILTINS[:4],
                                           cast=t if motion=='cast' else -1,clock=clock))
        ImageDraw.Draw(frame).text((18,height+10),'Shared rig: '+motion+' (technical mannequin)',fill='#D5C4FF')
        frames.append(frame.convert('RGB').resize((400,500)))
        clock+=.1
out=Path('artifacts/shared-rig-motion.gif');out.parent.mkdir(exist_ok=True)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=100,loop=0)
frames[80].save(out.with_suffix('.png'))
print(out)
