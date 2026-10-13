"""Original reproducible procedural artwork; no external imagery or image models."""
from pathlib import Path
from math import sin, cos, pi, sqrt
import random
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'static' / 'img'
PALETTES = [(157,105,236),(227,153,83),(140,160,177),(221,146,193),(167,190,219),(107,135,247),(232,156,124),(211,161,74),(71,188,160),(104,159,181),(225,124,138),(172,157,212),(153,200,210),(203,172,128)]

def artwork(index, variant=0, hero=False):
    rng = random.Random(index * 13 + variant)
    w,h = (1000,1200) if hero else (1000,700)
    color = PALETTES[index % len(PALETTES)]
    im = Image.new('RGB', (w,h))
    pixels = im.load()
    for y in range(h):
        for x in range(w):
            light = max(0, 1-sqrt(((x/w-.5)*1.25)**2 + ((y/h-.45)*1.2)**2)) ** 2
            grain = rng.uniform(-2.7,2.7)
            pixels[x,y] = tuple(int(max(0,min(255,6 + c*.26*light + grain))) for c in color)
    d = ImageDraw.Draw(im)
    horizon = int(h*.77)
    for yy in range(horizon,h):
        t=(yy-horizon)/(h-horizon)
        d.line((0,yy,w,yy),fill=tuple(int(8+c*.09*(1-t)) for c in color))
    glow=Image.new('RGB',(w,h));gd=ImageDraw.Draw(glow)
    gd.ellipse((w*.24,h*.68,w*.78,h*.87),fill=tuple(int(c*.45) for c in color))
    from PIL import ImageChops
    im=ImageChops.screen(im,glow.filter(ImageFilter.GaussianBlur(48)))
    d=ImageDraw.Draw(im)
    if hero or (index+variant)%3==0:
        cx,cy=w*.5,h*.43
        rx,ry=w*.29,h*.27
        # Tilted nested luminous loops produce a sculptural orbital form.
        for k in range(100):
            t=k/100
            pts=[]
            for a in range(361):
                theta=a*pi/180
                xx=rx*(1-t*.25)*cos(theta)
                yy=ry*(1-t*.25)*sin(theta)
                ang=-.34
                pts.append((cx+xx*cos(ang)-yy*sin(ang),cy+xx*sin(ang)+yy*cos(ang)))
            shade=.4+.6*sin(t*pi)
            col=tuple(int(min(255,c*shade+35*sin(t*pi))) for c in color)
            d.line(pts,fill=col,width=2)
        for k in range(16):
            y=h*.81+k*3
            d.ellipse((w*.29,y,w*.73,y+8),outline=tuple(int(c*.10) for c in color),width=1)
    elif (index+variant)%3==1:
        # A stack of polished, impossibly balanced pebbles.
        for n in range(4):
            cx=w*(.5+.09*sin(n*2+index));cy=h*(.69-n*.135)
            rx=w*(.21-n*.025);ry=h*.10
            for k in range(int(ry),0,-1):
                t=k/ry;v=.35+.65*sqrt(max(0,1-t*t))
                d.ellipse((cx-rx*t,cy-k,cx+rx*t,cy+k),fill=tuple(int(min(255,c*v+15)) for c in color))
            d.arc((cx-rx*.82,cy-ry*.85,cx+rx*.82,cy+ry*.5),190,300,fill=tuple(min(255,c+40) for c in color),width=2)
    else:
        # Receding portals, with warm and cool architectural depth.
        for n in range(13):
            t=n/13;left=w*(.11+t*.24);right=w*(.89-t*.24);top=h*(.12+t*.27);bottom=h*.78
            c=tuple(int(c*(.6-t*.28)) for c in color)
            d.rounded_rectangle((left,top,right,bottom),radius=int((right-left)/2),outline=c,width=13)
            d.line((left,bottom,left,top+(right-left)/2),fill=c,width=13)
            d.line((right,bottom,right,top+(right-left)/2),fill=c,width=13)
        d.rectangle((w*.475,h*.55,w*.525,h*.78),fill=(13,11,18))
    # Subtle film grain is already baked into the background.
    return im

if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    artwork(0,hero=True).save(OUT/'hero.jpg',quality=90,optimize=True)
    for i in range(14):
        for j in range(2):
            artwork(i,j).save(OUT/f'demo-{i:02}-{j}.jpg',quality=88,optimize=True)
    print('Generated 29 original local artworks.')
