"""Aura Rig 1: validated local PNG layers, named joints, sockets and shared motions."""
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
from PIL import Image
from .core import AuraError

MOTIONS=('idle','wave','inspect','draw')
MAX_PIXELS=16_000_000


def number(value,low,high):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise AuraError('Model coordinate is outside its supported bounds.')
    return value


def pair(value,low,high):
    if not isinstance(value,list) or len(value)!=2:raise AuraError('Use a two-number coordinate.')
    return [number(v,low,high) for v in value]


def load_pack(path):
    path=Path(path).resolve()
    if path.stat().st_size>65536:raise AuraError('Model manifests must be smaller than 64 KB.')
    try:data=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as exc:raise AuraError('Invalid model JSON.') from exc
    keys={'schema','id','name','author','license','size','bones','layers','sockets'}
    if not isinstance(data,dict) or set(data)!=keys or data['schema']!='aura-rig-1':
        raise AuraError('Choose an aura-rig-1 model manifest with the documented fields.')
    for key in ('id','name','author','license'):
        if not isinstance(data[key],str) or not 1<=len(data[key])<=100 or any(ord(c)<32 for c in data[key]):
            raise AuraError('Model identity and attribution must be short printable text.')
    if not re.fullmatch(r'[a-z][a-z0-9_.-]{2,63}',data['id']):raise AuraError('Invalid model ID.')
    size=pair(data['size'],64,2048)
    if any(type(n) is not int for n in size):raise AuraError('Model size must be integer pixels.')
    bones=data['bones'];seen=set();ordered=[]
    if not isinstance(bones,list) or not 1<=len(bones)<=48:raise AuraError('Use 1–48 model joints.')
    for bone in bones:
        if not isinstance(bone,dict) or set(bone)!={'name','parent','position','angle'}:raise AuraError('Invalid joint fields.')
        name=bone['name']
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',name) or name in seen:
            raise AuraError('Joint names must be unique.')
        if bone["parent"] is not None and not isinstance(bone["parent"],str):raise AuraError("Invalid parent joint.")
        if (name=='root' and bone['parent'] is not None) or (name!='root' and bone['parent'] not in seen):
            raise AuraError('Declare root first, then parents before their children. Cycles are not supported.')
        pair(bone['position'],-2048,2048);number(bone['angle'],-360,360)
        seen.add(name);ordered.append(bone)
    if not {'root','chest','head'}<=seen:raise AuraError('A basic model needs root, chest and head joints.')
    sockets=data['sockets']
    if not isinstance(sockets,dict) or len(sockets)>20:raise AuraError('Use at most 20 sockets.')
    for name,socket in sockets.items():
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',name) or not isinstance(socket,dict) or set(socket)!={'bone','position'}:
            raise AuraError('Invalid socket declaration.')
        if not isinstance(socket['bone'],str) or socket['bone'] not in seen:raise AuraError('Socket joint is missing.')
        pair(socket['position'],-2048,2048)
    if not isinstance(data['layers'],list) or not 1<=len(data['layers'])<=48:raise AuraError('Use 1–48 PNG layers.')
    images={};raw={};pixels=0
    for layer in data['layers']:
        if not isinstance(layer,dict) or set(layer)!={'bone','asset','pivot','z'}:raise AuraError('Invalid layer fields.')
        if not isinstance(layer['bone'],str) or layer['bone'] not in seen:raise AuraError('Layer joint is missing.')
        pair(layer['pivot'],-2048,2048);number(layer['z'],-100,100)
        asset=layer['asset']
        if not isinstance(asset,str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.png',asset):
            raise AuraError('PNG assets must use simple filenames beside the manifest; paths and URLs are rejected.')
        resolved=(path.parent/asset).resolve()
        if resolved.parent!=path.parent:raise AuraError('Model assets must stay inside the chosen folder.')
        if asset in images:continue
        if resolved.stat().st_size>4_000_000:raise AuraError('Each PNG must be smaller than 4 MB.')
        content=resolved.read_bytes()
        try:
            with Image.open(io.BytesIO(content)) as source:
                if source.format!='PNG' or max(source.size)>2048:raise AuraError('Use PNG assets at most 2048 pixels per side.')
                pixels+=source.width*source.height
                if pixels>MAX_PIXELS:raise AuraError('Model exceeds the 16 million pixel budget.')
                images[asset]=source.convert('RGBA')
        except (OSError,Image.DecompressionBombError) as exc:raise AuraError('Invalid PNG model asset.') from exc
        raw[asset]=content
        if sum(len(value) for value in raw.values())>32_000_000:raise AuraError("Model files exceed the 32 MB budget.")
    return Model(data,images),raw


class Model:
    def __init__(self,data,images):
        self.data,self.images=data,images
        self.names={b['name'] for b in data['bones']}

    @property
    def capabilities(self):
        caps=['idle','inspect']
        if {'right_upper_arm','right_forearm','right_hand'}<=self.names:caps.append('wave')
        if 'wave' in caps and {'hand_right','holster_right'}<=self.data['sockets'].keys():
            bones={b['name']:b for b in self.data['bones']}
            chain=bones['right_forearm']['parent']=='right_upper_arm' and bones['right_hand']['parent']=='right_forearm' and self.data['sockets']['hand_right']['bone']=='right_hand' and all(bones[name]['position'][0]==0 and bones[name]['position'][1]>0 and bones[name]['angle']==0 for name in ('right_forearm','right_hand'))
            if chain and bones['right_upper_arm']['angle']==0 and self.data['sockets']['hand_right']['position'][0]==0:caps.append('draw')
        return caps

    def pose(self,t,motion='idle'):
        if motion not in self.capabilities:motion='idle'
        angles={'chest':math.sin(t*1.7)*1.1,'head':math.sin(t*.8)*2}
        if motion=='wave':
            blend=max(0,min(1,t/.6,(3.2-t)/.6))
            angles.update(right_upper_arm=-135*blend,right_forearm=(35+math.sin(t*9)*18)*blend,right_hand=math.sin(t*9)*13*blend)
            for i,name in enumerate(('thumb','index','middle','ring')):
                angles['right_'+name]=math.sin(t*8+i*.4)*5*blend
        elif motion=='inspect':angles['head']=math.sin(min(1,t/3)*math.pi)*17
        def evaluate():
            world={}
            for bone in self.data['bones']:
                x,y=bone['position'];angle=bone['angle']+angles.get(bone['name'],0)
                if bone['parent']:
                    px,py,pa=world[bone['parent']];r=math.radians(pa)
                    x,y=px+x*math.cos(r)-y*math.sin(r),py+x*math.sin(r)+y*math.cos(r)
                    angle+=pa
                world[bone['name']]=(x,y,angle)
            return world
        world=evaluate()
        if motion=='draw':
            bones={bone['name']:bone for bone in self.data['bones']}
            fore=bones['right_forearm'];hand=bones['right_hand']
            # Standardized downward bind pose allows a two-bone contact solve.
            length1=fore['position'][1]
            length2=hand['position'][1]+self.data['sockets']['hand_right']['position'][1]
            if length1>0 and length2>0:
                rest=self.socket('hand_right',world);holster=self.socket('holster_right',world)
                shoulder=world['right_upper_arm']
                raised=(shoulder[0]+length1*.85,shoulder[1]+length1*.8)
                points=((0,rest),(.7,holster),(1.4,raised),(2.1,raised),(2.6,holster),(3.2,rest))
                target=rest
                for (start,first),(end,last) in zip(points,points[1:]):
                    if start<=t<=end:
                        k=(t-start)/(end-start);k=k*k*(3-2*k)
                        target=(first[0]+(last[0]-first[0])*k,first[1]+(last[1]-first[1])*k);break
                dx,dy=target[0]-shoulder[0],target[1]-shoulder[1]
                distance=min(length1+length2-.001,max(abs(length1-length2)+.001,math.hypot(dx,dy)))
                elbow=-math.acos(max(-1,min(1,(distance*distance-length1*length1-length2*length2)/(2*length1*length2))))
                upper=math.atan2(dy,dx)-math.atan2(length2*math.sin(elbow),length1+length2*math.cos(elbow))-math.pi/2
                parent=world[bones['right_upper_arm']['parent']][2]
                angles.update(right_upper_arm=math.degrees(upper)-parent,right_forearm=math.degrees(elbow),right_hand=0)
                for name in ('thumb','index','middle','ring'):
                    angles['right_'+name]=45 if .65<t<2.65 else 0
                world=evaluate()
        return world

    def socket(self,name,pose):
        slot=self.data['sockets'].get(name)
        if not slot:return None
        x,y,a=pose[slot['bone']];dx,dy=slot['position'];r=math.radians(a)
        return x+dx*math.cos(r)-dy*math.sin(r),y+dx*math.sin(r)+dy*math.cos(r),a

    def render(self,t,motion='idle',mouth=0,still=False,equipment=(),cast=-1):
        from PIL import ImageDraw
        if still:t=0;motion='idle'
        pose=self.pose(t,motion)
        result=Image.new('RGBA',tuple(self.data['size']))
        for layer in sorted(self.data['layers'],key=lambda l:l['z']):
            source=self.images[layer['asset']]
            x,y,angle=pose[layer['bone']];px,py=layer['pivot']
            a=math.radians(angle);c,s=math.cos(a),math.sin(a)
            corners=[(x+(u-px)*c-(v-py)*s,y+(u-px)*s+(v-py)*c) for u,v in ((0,0),(source.width,0),(0,source.height),(source.width,source.height))]
            left=math.floor(min(v[0] for v in corners));top=math.floor(min(v[1] for v in corners))
            w=math.ceil(max(v[0] for v in corners))-left;h=math.ceil(max(v[1] for v in corners))-top
            tile=source.transform((w,h),Image.Transform.AFFINE,(c,s,c*(left-x)+s*(top-y)+px,-s,c,-s*(left-x)+c*(top-y)+py),Image.Resampling.BICUBIC)
            result.paste(tile,(left,top),tile)
        draw=ImageDraw.Draw(result)
        # The optional mouth socket supplies a simple amplitude-driven aperture.
        point=self.socket('mouth',pose)
        if point and mouth>.08 and not still:
            x,y,_=point;r=2+min(1,mouth)*5
            draw.ellipse((x-8,y-r,x+8,y+r),fill='#17152D',outline='#AC90C6')
        if motion=='draw' and 'draw' in self.capabilities and any(item['kind']=='dagger' for item in equipment):
            point=self.socket('hand_right' if .7<t<2.6 else 'holster_right',pose)
            x,y,a=point;r=math.radians(a)
            def p(dx,dy):return x+dx*math.cos(r)-dy*math.sin(r),y+dx*math.sin(r)+dy*math.cos(r)
            draw.polygon([p(-3,6),p(3,6),p(2,39),p(0,48),p(-2,39)],fill='#BCCFE6',outline='#AA88FF')
            draw.line([p(-7,5),p(7,5)],fill='#BA9BFF',width=3)
            draw.line([p(0,-7),p(0,6)],fill='#3D3555',width=5)
        from .equipment import paint
        anchors={'holster':('holster_right',35,275),'back':('back',35,256),'charm':('charm',-48,190),'spell':('spell_origin',-65,178)}
        scale=self.data['size'][1]/520
        for item in equipment:
            if item['kind']=='dagger' and motion=='draw':continue
            socket_name,ox,oy=anchors[item['slot']]
            point=self.socket(socket_name,pose)
            if point:
                paint(draw,[item],point[0]-ox*scale,point[1]-oy*scale,scale,t,0,cast if not still else -1)
        return result


def draw(canvas):
    from PIL import ImageTk
    import time
    model=canvas.model
    elapsed=canvas.motion.time-getattr(canvas,'model_motion_started',-100)
    motion=getattr(canvas,'model_motion','idle') if elapsed<3.2 else 'idle'
    frame=model.render(canvas.motion.time if motion=='idle' else elapsed,motion,canvas.motion.mouth,
        canvas.paused or canvas.reduced,getattr(canvas,'equipment',()),canvas.motion.time-getattr(canvas,'cast_started',-100))
    w,h=canvas.winfo_width(),canvas.winfo_height()
    scale=min((w-20)/frame.width,(h-20)/frame.height)
    frame=frame.resize((max(1,round(frame.width*scale)),max(1,round(frame.height*scale))),Image.Resampling.LANCZOS)
    canvas.model_photo=ImageTk.PhotoImage(frame,master=canvas)
    key=('model',id(model),w,h)
    if getattr(canvas,'stage_key',None)!=key:
        canvas.delete('all');canvas.stage_key=key
        canvas.body_id=canvas.create_image(w/2,h/2,image=canvas.model_photo,tags='body')
    else:canvas.itemconfigure(canvas.body_id,image=canvas.model_photo)


def import_pack(path,directory):
    model,raw=load_pack(path)
    digest=hashlib.sha256(json.dumps(model.data,sort_keys=True).encode()+b''.join(raw[k] for k in sorted(raw))).hexdigest()[:16]
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    target=directory/(model.data['id']+'-'+digest)
    if not target.exists():
        with tempfile.TemporaryDirectory(dir=directory,prefix='import-') as temp:
            staging=Path(temp)
            for name,content in raw.items():(staging/name).write_bytes(content)
            (staging/'model.json').write_text(json.dumps(model.data,indent=2),encoding='utf-8')
            # Copy only already-validated data, never arbitrary files from a pack folder.
            staging.rename(target)
    return target/'model.json',model
