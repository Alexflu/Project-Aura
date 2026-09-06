"""Original technical mannequin demonstrating Aura Rig 1 joints and sockets."""
from pathlib import Path
import json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]/'aura/assets/rig-reference'
ROOT.mkdir(parents=True,exist_ok=True)
bones=[];layers=[]
def bone(name,parent,x,y):bones.append(dict(name=name,parent=parent,position=[x,y],angle=0))
def part(name,joint,size,pivot,z,draw):
    im=Image.new('RGBA',size);draw(ImageDraw.Draw(im));im.save(ROOT/(name+'.png'))
    layers.append(dict(bone=joint,asset=name+'.png',pivot=list(pivot),z=z))

bone('root',None,260,425)
bone('chest','root',0,-155)
bone('head','chest',0,-22)
for side,sign in [('left',-1),('right',1)]:
    bone(side+'_upper_arm','chest',sign*65,7)
    bone(side+'_forearm',side+'_upper_arm',0,90)
    bone(side+'_hand',side+'_forearm',0,85)
    bone(side+'_thigh','root',sign*34,0)
    bone(side+'_shin',side+'_thigh',0,120)
    bone(side+'_foot',side+'_shin',0,118)
    part(side+'-upper',side+'_upper_arm',(54,111),(27,15),1,lambda d:(d.rounded_rectangle((8,8,46,104),18,fill='#45445F',outline='#B4A0D9',width=2),d.line((17,30,17,85),fill='#9781CB',width=3),d.ellipse((14,2,40,28),fill='#24283D',outline='#AF9BDC',width=2)))
    part(side+'-forearm',side+'_forearm',(50,102),(25,8),3,lambda d:(d.rounded_rectangle((7,1,43,92),12,fill='#23283B',outline='#929FBF',width=2),d.polygon((9,25,41,25,38,74,13,74),fill='#555276'),d.line((17,35,17,63),fill='#8CE5F0',width=3)))
    part(side+'-palm',side+'_hand',(36,34),(18,3),4,lambda d:d.rounded_rectangle((5,1,31,28),7,fill='#938AAE',outline='#DBD3ED',width=2))
    for i,label in enumerate(('thumb','index','middle','ring')):
        bone(side+'_'+label,side+'_hand',-12+i*8,20)
        part(side+'-'+label,side+'_'+label,(9,27),(4,1),5,lambda d:d.rounded_rectangle((1,0,7,24),3,fill='#B1A5C8',outline='#5F5777'))
    part(side+'-thigh',side+'_thigh',(67,143),(33,10),0,lambda d:(d.rounded_rectangle((9,0,57,137),18,fill='#353B51',outline='#9393AD',width=2),d.line((20,25,20,110),fill='#9B80C7',width=3)))
    part(side+'-shin',side+'_shin',(58,137),(29,8),1,lambda d:(d.rounded_rectangle((9,0,49,130),15,fill='#272B3D',outline='#9C95B1',width=2),d.polygon((14,28,44,28,39,94,19,94),fill='#41465D')))
    part(side+'-foot',side+'_foot',(70,54),(32,7),3,lambda d:(d.rounded_rectangle((4,2,65,48),10,fill='#212636',outline='#9787B8',width=2),d.line((8,39,62,39),fill='#A386DA',width=3)))
part('torso','chest',(156,190),(78,25),2,lambda d:(d.polygon((28,8,128,8,146,48,122,166,34,166,10,48),fill='#2E344C',outline='#A8A1C2'),d.polygon((39,35,117,35,111,106,45,106),fill='#4B446B'),d.line((78,30,78,154),fill='#9082B6',width=3),d.ellipse((63,48,93,78),fill='#AC8CF0',outline='#DBD2F6',width=2),d.rounded_rectangle((34,145,123,169),4,fill='#1D2332',outline='#A1A7BD',width=2)))
part('head','head',(120,134),(60,111),4,lambda d:(d.rounded_rectangle((20,18,100,115),30,fill='#77758E',outline='#C9C5D9',width=2),d.polygon((16,24,39,5,89,9,108,39,92,55,27,53),fill='#2B2C44',outline='#B3A0D8'),d.rounded_rectangle((30,55,90,73),7,fill='#131E30',outline='#9280B8'),d.line((36,63,50,63),fill='#98F3F1',width=4),d.line((69,63,84,63),fill='#98F3F1',width=4),d.line((48,94,72,94),fill='#322B4B',width=2)))
data=dict(schema='aura-rig-1',id='aura.reference',name='Reference rig · articulated mannequin',author='Project Aura',license='MIT',size=[520,760],bones=bones,layers=layers,sockets={
 'mouth':dict(bone='head',position=[0,-17]),'hand_right':dict(bone='right_hand',position=[0,15]),
 'holster_right':dict(bone='root',position=[65,15]),'back':dict(bone='root',position=[65,-20]),
 'charm':dict(bone='chest',position=[-110,35]),'spell_origin':dict(bone='left_hand',position=[-38,5])})
(ROOT/'model.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('Generated original reference rig:',len(bones),'joints',len(layers),'layers')
