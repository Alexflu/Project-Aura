"""Export the actual rig renderer, not an independently animated concept video."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aura.models import load_pack
from aura.model_library import REFERENCE
from aura.equipment import BUILTINS

model,_=load_pack(Path(sys.argv[1]) if len(sys.argv)>1 else REFERENCE)
width,height=model.data['size']
frames=[];clock=0
for motion in ('idle','bow','cast','wave','draw'):
    for index in range(32):
        t=index/10
        frame=Image.new('RGBA',(width,height+40),'#111827')
        frame.alpha_composite(model.render(t,motion,equipment=BUILTINS[:4],
                                           cast=t if motion=='cast' else -1,clock=clock))
        ImageDraw.Draw(frame).text((18,height+10),model.data['name']+' : '+motion,fill='#D5C4FF')
        frames.append(frame.convert('RGB').resize((400,round((height+40)*400/width)),Image.Resampling.LANCZOS))
        clock+=.1
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('artifacts/shared-rig-motion.gif');out.parent.mkdir(exist_ok=True)
frames[0].save(out,save_all=True,append_images=frames[1:],duration=100,loop=0)
frames[80].save(out.with_suffix('.png'))
print(out)
