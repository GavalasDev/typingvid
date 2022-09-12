from bs4 import BeautifulSoup
import re
import os, shutil
from cairosvg import svg2png
import moviepy.editor as mp
from moviepy.video.tools.segmenting import findObjects
from moviepy.video.fx.all import crop

def set_property(soup, object_id, prop, value):
    obj = soup.find(id=object_id)
    obj['style'] = re.sub("{}:.+?;".format(prop), "{}:{};".format(prop, value), obj['style'])

def remap_special(c):
    m = {' ': 'Space', '\n': 'Enter', '`': 'backtick', '-': 'minus', '=': 'equals', '[': 'open_square', ']': 'closed_square', '\\': 'backslash', ';': 'semicolon', '\'': 'tick', ',': 'comma', '.': 'period', '/': 'forwardslash'}
    if c in m:
        c = m[c]
    else:
        c = c.upper()
    return c

def create_frames(keyboard_svg, text):
    with open(keyboard_svg) as f:
        data = f.read()
    keyboard_soup = BeautifulSoup(data, 'xml')

    shutil.rmtree('temp')
    os.makedirs('temp')
    
    frame_num = 0
    svg2png(bytestring=str(keyboard_soup), write_to="temp/frame{}.png".format(frame_num))
    frame_num += 1
    for c in text:
        c = remap_special(c)
        set_property(keyboard_soup, c, 'fill', 'black')
        set_property(keyboard_soup, c, 'fill-opacity', '0.2')
        svg2png(bytestring=str(keyboard_soup), write_to="temp/frame{}.png".format(frame_num))
        frame_num += 1
        set_property(keyboard_soup, c, 'fill', 'none')
        set_property(keyboard_soup, c, 'fill-opacity', '1')
        svg2png(bytestring=str(keyboard_soup), write_to="temp/frame{}.png".format(frame_num))
        frame_num += 1

def create_video(filename, text1, text2):
    background_clip = mp.ImageClip("keyboard_video_background.png")

    T = 0.2

    clips = [mp.ImageClip("temp/frame{}.png".format(n)).set_duration(T) for n in range(len(os.listdir("temp")))]
    keyboard_clip = mp.concatenate_videoclips(clips)

    upperTxtClip = mp.concatenate_videoclips([mp.TextClip('> {}|'.format(text1[:i].upper()),color='black',
                   kerning = 5, fontsize=31, font='Noto-Sans-Mono').set_duration(2*T) for i in range(0, len(text1)+1)])

    lowerTxtClip = mp.concatenate_videoclips([mp.TextClip('> {}|'.format(text2[:i].upper()),color='black',
                   kerning = 5, fontsize=31, font='Noto-Sans-Mono-CJK-JP').set_duration(2*T) for i in range(0, len(text2)+1)])

    cvc = mp.CompositeVideoClip( [background_clip, keyboard_clip.resize(0.69).set_pos(("center",0.4), relative=True) , upperTxtClip.set_pos((351, 230)), lowerTxtClip.set_pos((351, 335))]).set_duration(keyboard_clip.duration)

    cvc = crop(cvc, x1=247.72, y1=132.38, width=1424.56, height=815.24)

    ext = filename.split(".")[1]

    if ext == 'gif':
        cvc.write_gif(filename, fps=10)
    elif ext == 'mp4':
        cvc.write_videofile(filename, fps=24)


create_frames("keyboard-jp.svg", "BYTE")
create_video("test.mp4", "BYTE", "こんかい")
