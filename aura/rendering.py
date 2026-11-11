"""Limit prop rotation to visible pixels while retaining its original canvas pivot."""
import math
from PIL import Image


def rotate_visible(source,angle):
    box=source.getbbox()
    if not box:return None
    angle%=360
    if angle%90==0:
        rotated=source.rotate(angle,resample=Image.Resampling.BICUBIC)
        box=rotated.getbbox()
        return (rotated.crop(box),box[:2]) if box else None
    width,height=source.size;cx,cy=width/2,height/2
    a=-math.radians(angle);c=round(math.cos(a),15);s=round(math.sin(a),15)
    # Keep transparent interpolation padding on both sides of the transform.
    crop=(max(0,box[0]-4),max(0,box[1]-4),min(width,box[2]+4),min(height,box[3]+4))
    corners=[(cx+c*(u-cx)-s*(v-cy),cy+s*(u-cx)+c*(v-cy))
             for u,v in ((crop[0],crop[1]),(crop[2],crop[1]),(crop[0],crop[3]),(crop[2],crop[3]))]
    left=max(0,math.floor(min(p[0] for p in corners))-4)
    top=max(0,math.floor(min(p[1] for p in corners))-4)
    right=min(width,math.ceil(max(p[0] for p in corners))+4)
    bottom=min(height,math.ceil(max(p[1] for p in corners))+4)
    if right<=left or bottom<=top:return None
    tile=source.crop(crop).transform((right-left,bottom-top),Image.Transform.AFFINE,
        (c,s,c*(left-cx)+s*(top-cy)+cx-crop[0],
         -s,c,-s*(left-cx)+c*(top-cy)+cy-crop[1]),Image.Resampling.BICUBIC)
    return tile,(left,top)
