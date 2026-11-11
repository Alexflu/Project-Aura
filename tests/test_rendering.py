import unittest
from PIL import Image,ImageDraw,ImageChops
from aura.rendering import rotate_visible


class PropRenderingTests(unittest.TestCase):
    def test_empty_props_produce_no_work(self):
        self.assertIsNone(rotate_visible(Image.new('RGBA',(300,300)),21))

    def test_rotation_matches_full_canvas_at_edges_and_off_center(self):
        for size in ((255,255),(300,300),(311,257)):
            source=Image.new('RGBA',size)
            draw=ImageDraw.Draw(source)
            draw.rectangle((3,5,37,75),fill=(120,45,230,170))
            draw.ellipse((70,110,100,143),fill=(32,210,150,240))
            draw.rectangle((size[0]-7,size[1]-35,size[0],size[1]),fill=(240,50,80,255))
            for angle in (0,90,180,270,.1,-.1,13.7,45,87,126,217,359):
                expected=source.rotate(angle,resample=Image.Resampling.BICUBIC)
                actual=Image.new('RGBA',size)
                result=rotate_visible(source,angle)
                if result:
                    tile,offset=result
                    actual.paste(tile,offset)
                for color in ('#10151F','#FFFFFF'):
                    before=Image.new('RGBA',size,color);before.alpha_composite(expected)
                    after=Image.new('RGBA',size,color);after.alpha_composite(actual)
                    delta=ImageChops.difference(before,after)
                    self.assertLessEqual(max(v[1] for v in delta.getextrema()),1,(size,angle))

    def test_sparse_prop_avoids_full_canvas_rotation_output(self):
        source=Image.new('RGBA',(700,700))
        ImageDraw.Draw(source).rectangle((320,320,350,390),fill='#AA88FF')
        tile,_=rotate_visible(source,17)
        self.assertLess(tile.width*tile.height,source.width*source.height/10)
