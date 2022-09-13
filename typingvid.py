import argparse
import yaml
from bs4 import BeautifulSoup
import re
import tempfile
import os
from cairosvg import svg2png
import moviepy.editor as mp
from moviepy.video.tools.segmenting import findObjects
import moviepy.video.fx.all as vfx

def layout_remap(word, mapping):
    res = ""
    for c in word:
        res += (mapping[c])
    return res

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

    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_name = temp_dir.name
    
    frame_num = 0
    svg2png(bytestring=str(keyboard_soup), write_to="{}/frame{}.png".format(temp_dir_name,frame_num))
    frame_num += 1
    for c in text:
        c = remap_special(c)
        set_property(keyboard_soup, c, 'fill', 'black')
        set_property(keyboard_soup, c, 'fill-opacity', '0.2')
        svg2png(bytestring=str(keyboard_soup), write_to="{}/frame{}.png".format(temp_dir_name,frame_num))
        frame_num += 1
        set_property(keyboard_soup, c, 'fill', 'none')
        set_property(keyboard_soup, c, 'fill-opacity', '1')
        svg2png(bytestring=str(keyboard_soup), write_to="{}/frame{}.png".format(temp_dir_name, frame_num))
        frame_num += 1
    return temp_dir


def generate_keyboard_clip(temp_dir, T):
    clips = [mp.ImageClip("{}/frame{}.png".format(temp_dir.name, n)).set_duration(T) for n in range(len(os.listdir(temp_dir.name)))]
    keyboard_clip = mp.concatenate_videoclips(clips)
    return keyboard_clip

def generate_text_clip(text, T, font):
    return mp.concatenate_videoclips([mp.TextClip('> {}|'.format(text[:i].upper()),color='black',
        kerning = 5, fontsize=31, font=font).set_duration(2*T) for i in range(0, len(text)+1)])
    
def generate_composite_clip(background_clip, keyboard_clip, txt_clips):
    if len(txt_clips) == 2:
        cvc = mp.CompositeVideoClip( [background_clip, keyboard_clip.resize(0.69).set_pos(("center",0.4), relative=True) , txt_clips[0].set_pos((351, 230)), txt_clips[1].set_pos((351, 335))]).set_duration(keyboard_clip.duration)

        cvc = vfx.crop(cvc, x1=247.72, y1=132.38, width=1424.56, height=815.24)
    elif len(txt_clips) == 1:
        cvc = mp.CompositeVideoClip([background_clip, keyboard_clip.resize(0.69).set_pos(("center", 380)), txt_clips[0].set_pos((351, 282))]).set_duration(keyboard_clip.duration)
        cvc = vfx.crop(cvc, x1=269.5, y1=199.5, width=1381, height=681)
    return cvc

def export_clip(clip, filename):
    ext = filename.split(".")[1]
    if ext == 'gif':
        clip.write_gif(filename, fps=10, logger=None)
    elif ext == 'mp4':
        clip.write_videofile(filename, fps=24, logger=None)


def create_video(temp_dir, filename, text, speed, layout, no_display=False, invert_colors=False):

    T = 1/speed

    keyboard_clip = generate_keyboard_clip(temp_dir, T)

    if no_display:
        final_clip = keyboard_clip
    elif len(layout['fonts']) == 2:
        background_clip = mp.ImageClip("assets/dual_display_background.png")
        upperTxtClip = generate_text_clip(text, T, layout['fonts'][0])

        lowerTxtClip = generate_text_clip(layout_remap(text, layout['mapping']), T, layout['fonts'][1])

        final_clip = generate_composite_clip(background_clip, keyboard_clip, [upperTxtClip, lowerTxtClip])
    elif len(layout['fonts']) == 1:
        background_clip = mp.ImageClip("assets/mono_display_background.png")
        txt_clip = generate_text_clip(text, T, layout['fonts'][0])
        final_clip = generate_composite_clip(background_clip, keyboard_clip, [txt_clip])

    if invert_colors:
        final_clip = final_clip.fx(vfx.invert_colors)

    export_clip(final_clip, filename)

    temp_dir.cleanup()


parser = argparse.ArgumentParser(description="A customizable typing animation generator with multi-layout support.")
parser.add_argument('-l', '--layout', default='engr', help='the layout to use for the keyboard (default: engr)')
parser.add_argument('--no-display', action='store_true')
parser.add_argument('-t', '--text', required=True)
parser.add_argument('-o', '--output', default='output.mp4')
parser.add_argument('-s', '--speed', default=5, type=int)
parser.add_argument('--invert-colors', action='store_true')

args = parser.parse_args()
args.text = args.text.upper() # TODO add support for case-sensitivity (animating the Shift key)

with open("layouts/{}.yml".format(args.layout)) as f:
    layout = yaml.safe_load(f)

print("Generating frames... ", end="", flush=True)
frames_dir = create_frames("assets/{}".format(layout['file']), args.text)
print("frames successfully generated.")
print("Generating output file... ", end="", flush=True)
create_video(frames_dir, args.output, args.text, args.speed, layout, args.no_display, args.invert_colors)
print("output file {} successfully generated.".format(args.output))
