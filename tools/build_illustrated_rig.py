"""Import the versioned generated part sheet into the existing Aura Rig 1 format."""
from collections import deque
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'aura/assets/aura-illustrated-rig'
OUT.mkdir(exist_ok=True)
sheet=Image.open(ROOT/'aura/assets/aura-rig-sheet-v1.png').convert('RGB')
bones=[];layers=[]


def part(index,name,height,bone,pivot,z,trim=1):
    column,row=index%4,index//4
    rows=(0,320,635,890,1254)
    image=sheet.crop((round(column*sheet.width/4),rows[row],
                      round((column+1)*sheet.width/4),rows[row+1])).convert('RGBA')
    pixels=image.load();width,h=image.size
    seen=set();queue=deque([(x,y) for x in range(width) for y in (0,h-1)]+
                           [(x,y) for y in range(h) for x in (0,width-1)])
    while queue:
        x,y=queue.popleft()
        if (x,y) in seen or not (0<=x<width and 0<=y<h):continue
        seen.add((x,y));r,g,b,_=pixels[x,y]
        if min(r,g,b)<220 or max(r,g,b)-min(r,g,b)>15:continue
        pixels[x,y]=(r,g,b,0)
        queue.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
    box=image.getbbox()
    if not box:raise ValueError('Empty sheet cell')
    image=image.crop(box)
    if trim<1:image=image.crop((0,0,image.width,round(image.height*trim)))
    width=round(image.width*height/image.height)
    image=image.resize((width,height),Image.Resampling.LANCZOS)
    image.save(OUT/(name+'.png'))
    layers.append(dict(bone=bone,asset=name+'.png',pivot=[width*pivot[0],height*pivot[1]],z=z))


def joint(name,parent,x,y):bones.append(dict(name=name,parent=parent,position=[x,y],angle=0))


joint('root',None,300,350)
joint('chest','root',0,-170)
joint('head','chest',0,0)
joint('hair_back','head',0,-105)
part(0,'head',150,'head',(.5,.94),6)
part(1,'torso',190,'chest',(.5,.04),3)
part(2,'pelvis',100,'root',(.5,.05),4)
part(3,'hair-back',142,'hair_back',(.5,.1),-2)
for side,index,sign in [('left',0,-1),('right',1,1)]:
    joint(side+'_upper_arm','chest',sign*52,47)
    joint(side+'_forearm',side+'_upper_arm',0,102)
    joint(side+'_hand',side+'_forearm',0,94)
    joint(side+'_thigh','root',sign*36,62)
    joint(side+'_shin',side+'_thigh',0,139)
    joint(side+'_foot',side+'_shin',0,117)
    part(4+index,side+'-upper',118,side+'_upper_arm',(.5,.08),4)
    part(6+index,side+'-forearm',110,side+'_forearm',(.5,.04),2,trim=.79)
    part(8+index,side+'-hand',64,side+'_hand',(.5,.1),7)
    part(10+index,side+'-thigh',155,side+'_thigh',(.5,.06),1)
    part(12+index,side+'-shin',136,side+'_shin',(.5,.05),0)
    part(14+index,side+'-boot',100,side+'_foot',(.5,.1),2)
data=dict(schema='aura-rig-1',id='aura.illustrated.v1',name='Aura · illustrated Stealth Striker',
          author='Project Aura · generated art',license='MIT',size=[600,800],bones=bones,layers=layers,
          sockets={'hand_right':dict(bone='right_hand',position=[0,18]),
                   'holster_right':dict(bone='root',position=[65,50]),
                   'spell_origin':dict(bone='left_hand',position=[0,18]),
                   'back':dict(bone='root',position=[75,30]),
                   'charm':dict(bone='chest',position=[-80,110])})
(OUT/'model.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(OUT)
