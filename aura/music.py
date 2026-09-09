"""Opt-in level-reactive rig poses; no recording, genre inference or beat detection."""
import math

MODES={'Off':'off','Gentle nod':'gentle','Dance + speakers':'dance',
       'Headbang':'headbang','Headphones + book':'read'}


class Transition:
    """Return to neutral before changing styles; keep pose and props in sync."""
    def __init__(self):
        self.mode='off'
        self.amount=0.0

    def update(self,target,dt,energy):
        dt=max(0,min(.2,dt))
        if target!=self.mode:
            self.amount=max(0,self.amount-dt/.35)
            if self.amount==0:self.mode=target
        elif target!='off':
            self.amount=min(1,self.amount+dt/.65)
        weight=self.amount*self.amount*(3-2*self.amount)
        return (self.mode,energy,weight) if self.mode!='off' and weight>0 else None

    def reset(self):
        self.mode='off';self.amount=0.0


def unpack(reaction):
    mode,energy=reaction[:2]
    return mode,energy,max(0,min(1,reaction[2] if len(reaction)>2 else 1))


class Reaction:
    def __init__(self):
        self.energy=0.0

    def update(self,level,dt,active=True):
        if not active:
            self.energy=0.0
            return 0.0
        level=float(level)
        target=max(0,min(1,(level-.025)*1.8)) if math.isfinite(level) else 0
        dt=max(0,min(.2,dt))
        self.energy+=(target-self.energy)*(1-math.exp(-dt/(.15 if target>self.energy else .65)))
        return self.energy


def angles(mode,energy,clock):
    energy=max(0,min(1,energy))
    pulse=math.sin(clock*math.tau*1.5)
    sway=math.sin(clock*math.tau*.75)
    if mode=='read':
        return dict(head=12,chest=2,left_upper_arm=30,left_forearm=-150,
                    right_upper_arm=-30,right_forearm=150)
    if mode=='gentle':return dict(head=pulse*5*energy,chest=sway*1.5*energy)
    if mode=='headbang':return dict(head=pulse*17*energy,chest=pulse*6*energy)
    if mode=='dance':
        return dict(head=-sway*5*energy,chest=sway*7*energy,
                    left_upper_arm=(15+pulse*10)*energy,right_upper_arm=(-15+pulse*10)*energy,
                    left_forearm=-25*energy,right_forearm=25*energy,
                    left_thigh=sway*3*energy,right_thigh=sway*3*energy,
                    left_shin=-sway*2*energy,right_shin=-sway*2*energy)
    return {}


def props(image,model,pose,mode,energy,clock):
    from PIL import ImageDraw
    draw=ImageDraw.Draw(image)
    scale=model.data['size'][1]/800
    color='#B6A0FF'
    if mode=='dance' and energy>.04:
        x,y,_=pose['root'];floor=min(image.height-15*scale,y+390*scale)
        for sign in (-1,1):
            cx=max(28*scale,min(image.width-28*scale,x+sign*145*scale))
            draw.rounded_rectangle((cx-24*scale,floor-85*scale,cx+24*scale,floor),radius=5*scale,fill='#202A3D',outline=color,width=max(1,round(scale)))
            for cy,r in ((floor-61*scale,10),(floor-25*scale,17)):
                radius=(r+energy*2*math.sin(clock*9))*scale
                draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill='#10151F',outline=color,width=max(1,round(scale)))
    if mode!='read':return
    # Head-layer coordinates keep headphones attached across differently sized art.
    layer=next((v for v in model.data['layers'] if v['bone']=='head'),None)
    if layer:
        art=model.images[layer['asset']];px,py=layer['pivot']
        x,y,a=pose['head'];r=math.radians(a)
        def p(u,v):
            u-=px;v-=py
            return x+u*math.cos(r)-v*math.sin(r),y+u*math.sin(r)+v*math.cos(r)
        points=[p(art.width*(.5+.37*math.cos(t)),art.height*(.49-.36*math.sin(t))) for t in [i*math.pi/24 for i in range(25)]]
        draw.line(points,fill='#24283E',width=max(3,round(7*scale)))
        draw.line(points,fill=color,width=max(1,round(2*scale)))
        for u in (.13,.87):
            draw.polygon([p(art.width*(u+dx),art.height*v) for dx,v in ((-.045,.40),(.045,.40),(.045,.60),(-.045,.60))],fill='#24283E',outline=color)
    if {'left_hand','right_hand'}<=pose.keys():
        left,right=sorted((pose['left_hand'],pose['right_hand']),key=lambda p:p[0])
        x=(left[0]+right[0])/2;y=(left[1]+right[1])/2
        dx,dy=right[0]-left[0],right[1]-left[1]
        angle=math.atan2(dy,dx);c,s=math.cos(angle),math.sin(angle)
        w=math.hypot(dx,dy)/2+8*scale;h=48*scale
        def book(u,v):return x+u*c-v*s,y+u*s+v*c
        draw.polygon([book(-w,-h),book(0,-h+8*scale),book(w,-h),book(w,0),book(0,8*scale),book(-w,0)],fill='#DBD5C5',outline=color)
        draw.line([book(0,-h+8*scale),book(0,8*scale)],fill='#665E78',width=max(1,round(scale)))
        for offset in range(4):
            cy=-h+(17+offset*7)*scale
            for sign in (-1,1):draw.line([book(sign*8*scale,cy),book(sign*(w-8*scale),cy-4*scale)],fill='#8B8298',width=max(1,round(scale)))
