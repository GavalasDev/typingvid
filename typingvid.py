#!/usr/bin/env python3
"""
A simple python script for generating customizable typing videos and gifs.
"""

import argparse
import os
import re
import tempfile

import moviepy.editor as mp
import moviepy.video.fx.all as vfx
import yaml
from bs4 import BeautifulSoup
from cairosvg import svg2png


def _layout_remap(word, mapping):
    res = ""
    for c in word:
        res += mapping[c]
    return res


def _set_property(soup, object_id, prop, value):
    obj = soup.find(id=object_id)
    obj["style"] = re.sub(f"{prop}:.+?;", f"{prop}:{value};", obj["style"])


def _remap_special(c):
    m = {
        " ": "Space",
        "\n": "Enter",
        "`": "backtick",
        "-": "minus",
        "=": "equals",
        "[": "open_square",
        "]": "closed_square",
        "\\": "backslash",
        ";": "semicolon",
        "'": "tick",
        ",": "comma",
        ".": "period",
        "/": "forwardslash",
    }

    if c in m:
        c = m[c]
    else:
        c = c
    return c


def _generate_frame(char, soup, properties, temp_dir_name, frame_num):
    for prop in properties:
        _set_property(soup, char, prop, properties[prop])
    svg2png(
        bytestring=str(soup),
        write_to=f"{temp_dir_name}/frame{frame_num}.png",
    )


def _create_frames(keyboard_svg, text):
    with open(keyboard_svg) as f:
        data = f.read()
    keyboard_soup = BeautifulSoup(data, "xml")

    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_name = temp_dir.name

    frame_num = 0

    _generate_frame(None, keyboard_soup, {}, temp_dir_name, frame_num)

    frame_num += 1

    for char in text:
        char = _remap_special(char)

        _generate_frame(
            char,
            keyboard_soup,
            {"fill": "black", "fill-opacity": "0.2"},
            temp_dir_name,
            frame_num,
        )

        frame_num += 1

        _generate_frame(
            char,
            keyboard_soup,
            {"fill": "none", "fill-opacity": "1"},
            temp_dir_name,
            frame_num,
        )

        frame_num += 1

    return temp_dir


def _generate_keyboard_clip(temp_dir, T):
    clips = [
        mp.ImageClip(f"{temp_dir.name}/frame{n}.png").set_duration(T)
        for n in range(len(os.listdir(temp_dir.name)))
    ]
    keyboard_clip = mp.concatenate_videoclips(clips)
    return keyboard_clip


def _generate_text_clip(text, T, font):
    return mp.concatenate_videoclips(
        [
            mp.TextClip(
                f"> {text[:i]}|",
                color="black",
                kerning=5,
                fontsize=31,
                font=font,
            ).set_duration(2 * T)
            for i in range(0, len(text) + 1)
        ]
    )


def _generate_composite_clip(background_clip, keyboard_clip, txt_clips):
    if len(txt_clips) == 2:
        cvc = mp.CompositeVideoClip(
            [
                background_clip,
                keyboard_clip.resize(0.69).set_pos(("center", 0.4), relative=True),
                txt_clips[0].set_pos((351, 230)),
                txt_clips[1].set_pos((351, 335)),
            ]
        ).set_duration(keyboard_clip.duration)

        cvc = vfx.crop(cvc, x1=247.72, y1=132.38, width=1424.56, height=815.24)
    elif len(txt_clips) == 1:
        cvc = mp.CompositeVideoClip(
            [
                background_clip,
                keyboard_clip.resize(0.69).set_pos(("center", 380)),
                txt_clips[0].set_pos((351, 282)),
            ]
        ).set_duration(keyboard_clip.duration)
        cvc = vfx.crop(cvc, x1=269.5, y1=199.5, width=1381, height=681)
    return cvc


def _export_clip(clip, filename):
    ext = filename.split(".")[1]
    if ext == "gif":
        clip.write_gif(filename, fps=10, logger=None)
    elif ext == "mp4":
        clip.write_videofile(filename, fps=24, logger=None)


def create_video(temp_dir, layout, args):

    T = 1 / args.speed

    keyboard_clip = _generate_keyboard_clip(temp_dir, T)

    if args.no_display:
        final_clip = keyboard_clip

    elif len(layout["fonts"]) == 2:
        background_clip = mp.ImageClip("assets/dual_display_background.png")
        upper_text_clip = _generate_text_clip(
            args.text if not args.force_lowercase else args.text.lower(),
            T,
            layout["fonts"][0],
        )

        remapped_text = _layout_remap(args.text, layout["mapping"])

        lower_text_clip = _generate_text_clip(
            remapped_text if not args.force_lowercase else remapped_text.lower(),
            T,
            layout["fonts"][1],
        )

        final_clip = _generate_composite_clip(
            background_clip, keyboard_clip, [upper_text_clip, lower_text_clip]
        )

    elif len(layout["fonts"]) == 1:
        background_clip = mp.ImageClip("assets/mono_display_background.png")
        txt_clip = _generate_text_clip(
            args.text if not args.force_lowercase else args.text.lower(),
            T,
            layout["fonts"][0],
        )
        final_clip = _generate_composite_clip(background_clip, keyboard_clip, [txt_clip])

    if args.invert_colors:
        final_clip = final_clip.fx(vfx.invert_colors)

    if args.hold_last_frame > 0:
        final_clip = final_clip.fx(vfx.freeze, t='end', padding_end=1/100, freeze_duration=args.hold_last_frame)

    _export_clip(final_clip, args.output)

    temp_dir.cleanup()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A customizable typing animation generator with multi-layout support."
    )
    parser.add_argument(
        "-t",
        "--text",
        required=True,
        help="the text (only in the first language) to be typed",
    )
    parser.add_argument(
        "-l",
        "--layout",
        default="en",
        help="the layout to use for the keyboard (default: en)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.mp4",
        help="location of output file (default: output.mp4)",
    )
    parser.add_argument(
        "-s",
        "--speed",
        default=5.0,
        type=float,
        help="speed of output media file (default: 5.0)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="keep only the keyboard for final animation",
    )
    parser.add_argument(
        "--invert-colors", action="store_true", help="invert colors of final media file"
    )
    parser.add_argument(
        "--force-lowercase",
        action="store_true",
        help="show display text in lowercase (instead of uppercase)",
    )
    parser.add_argument(
        "--hold-last-frame",
        default=-1,
        type=float,
        metavar="N",
        help="keep last frame on screen for N seconds, 0 for normal screen time (default: 0)",
    )

    args = parser.parse_args()
    args.text = args.text.upper() # TODO add support for case-sensitivity (animating the Shift key)

    with open(f"layouts/{args.layout}.yml") as f:
        layout = yaml.safe_load(f)

    print("Generating frames... ", end="", flush=True)
    frames_dir = _create_frames(f"assets/{layout['file']}", args.text)
    print("frames successfully generated.")
    print("Generating output file... ", end="", flush=True)
    create_video(frames_dir, layout, args)
    print(f"output file {args.output} successfully generated.")
