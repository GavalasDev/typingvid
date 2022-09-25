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
    """
    Remap each character of a word to another layout using a dictionary.

    Parameters
    ----------
    word: string
        The word to be remapped.
    mapping: dict
        The dictionary containing the mapping between the two layouts 
        (e.g. {"A": "ち", "B": "こ", "C": "そ", ...}).
    
    Returns
    -------
    string
        The resulting word after the remapping.
    """
    res = ""
    for c in word:
        c = _remap_special(c)
        res += mapping[c] if c in mapping else c
    return res


def _get_relative_dir(relative_dir):
    """
    Return the full path of a relative directory.

    Parameters
    ----------
    relative_dir: string
        The relative directory name.

    Returns
    -------
    string
        The full path of the directory.
    """
    main_dir_name = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(main_dir_name, relative_dir)


def _set_property(soup, object_id, prop, value):
    """
    Update a property of an object within an svg file.

    Parameters
    ----------
    soup: bs4.BeautifulSoup
        A BeautifulSoup object containing the contents of the svg (modified in place)
    object_id: string
        The id of the svg object to update. Either a single character (e.g. 'A') or
        a special string (e.g. "Space") based on convetion.
    prop: string
        The property to update (e.g. "fill" or "fill-opacity").
    value: string
        The target value of the given property (e.g. "black", "0.1").

    Notes
    -----
    Parameter `soup` is modified in place.
    """
    obj = soup.find(id=object_id)
    obj["style"] = re.sub(f"{prop}:.+?;", f"{prop}:{value};", obj["style"])


def _remap_special(c):
    """
    Remap special characters to valid svg object ids based on convetion.

    Parameters
    ----------
    c: string
        The character to be remapped.

    Returns
    -------
    string
        A valid svg object id. Either the original character `c` or an expressive string
        for special characters.
    """
    m = {
        " ": "space",
        "\n": "enter",
    }

    if c in m:
        c = m[c]

    return c


def _generate_frame(char, soup, properties, temp_dir_name, frame_num):
    """
    Generate a single frame of the (keyboard-only) animation.

    Parameters
    ----------
    char: string
        The character currently being animated.
    soup: bs4.BeautifulSoup
        The BeautifulSoup containing the keyboard svg.
    properties: dict
        A dictionary of property/value pairs to be updated for this frame.
    temp_dir_name: string
        The directory in which the frames are temporary being stored.
    frame_number: int
        The number of the current frame.

    Notes
    -----
    Writes directly to file '{temp_dir_name}/frame{frame_num}.png'
    """
    for prop in properties:
        _set_property(soup, char, prop, properties[prop])
    svg2png(
        bytestring=str(soup),
        write_to=f"{temp_dir_name}/frame{frame_num}.png",
    )


def _create_frames(keyboard_svg, text):
    """
    Generate all frames of keyboard animation and store them in a temporary folder.

    Parameters
    ----------
    keyboard_svg: string
        Path to a keyboard svg file.
    text: string
        The text to be animated onto the keyboard.

    Returns
    -------
    temp_dir: tempfile.TemporaryDirectory
        A reference to the (automatically generated) temporary directory containing all frames.
    """
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
    """
    Combine previously generated keyboard frames to a single MoviePy clip.

    Parameters
    ----------
    temp_dir: tempfile.TemporaryDirectory
        A reference to the (automatically generated) temporary directory containing all frames.
    T: float
        The duration of each frame in seconds.

    Returns
    -------
    moviepy.video.VideoClip.VideoClip
        The resulting MoviePy clip.
    """
    clips = [
        mp.ImageClip(f"{temp_dir.name}/frame{n}.png").set_duration(T)
        for n in range(len(os.listdir(temp_dir.name)))
    ]
    keyboard_clip = mp.concatenate_videoclips(clips)
    return keyboard_clip


def _generate_text_clip(text, T, font):
    """
    Create a simple MoviePy clip of text slowly appearing to be used on the display(s).

    Parameters
    ----------
    text: string
        The string to be animated.
    T: float
        The duration of single keypress.
    font: string
        The font to be used for the text.

    Returns
    -------
    moviepy.video.VideoClip.VideoClip
        The resulting MoviePy clip.
    """
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
    """
    Create the final clip containing the keyboard and either one or two displays.

    Parameters
    ----------
    background_clip: moviepy.video.VideoClip.ImageClip
        A simple image clip of the background to be used for the video.
    keyboard_clip: moviepy.video.VideoClip.VideoClip
        The animated keyboard clip generated by `_generate_keyboard_clip`.
    txt_clips: list
        A list containing either one or two text clips generated by `_generate_text_clip`

    Returns
    -------
    moviepy.video.VideoClip.VideoClip
        The resulting (composite) video clip.
    """
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
    """
    Export a clip to a media file based on its extension.

    Parameters
    ----------
    clip: moviepy.video.VideoClip.VideoClip
        The clip to be written.
    filename: string
        The path to the output file. Extension can be either `.mp4` or `.gif`.
    """
    ext = filename.split(".")[1]
    if ext == "gif":
        clip.write_gif(filename, fps=10, logger=None)
    elif ext == "mp4":
        clip.write_videofile(filename, fps=24, logger=None)


def _create_video(temp_dir, layout, args):
    """
    Create a fully-fledged keyboard animation video using the previously generated keyboard frames.
    
    Parameters
    ----------
    temp_dir: tempfile.TemporaryDirectory
        A reference to the (automatically generated) temporary directory containing all frames.
    layout: dict
        A dictionary resulting from reading an appropriate yaml layout file.
        Should at least include the `file` and `fonts` keys.
    args: argparse.Namespace
        The arguments generated by argparse.
        Required: args.text
    """

    T = 1 / args.speed

    keyboard_clip = _generate_keyboard_clip(temp_dir, T)

    if args.no_display:
        final_clip = keyboard_clip

    elif len(layout["fonts"]) == 2:
        background_clip = mp.ImageClip(f"{_get_relative_dir('assets')}/dual_display_background.png")
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
        background_clip = mp.ImageClip(f"{_get_relative_dir('assets')}/mono_display_background.png")
        txt_clip = _generate_text_clip(
            args.text if not args.force_lowercase else args.text.lower(),
            T,
            layout["fonts"][0],
        )
        final_clip = _generate_composite_clip(
            background_clip, keyboard_clip, [txt_clip]
        )

    if args.invert_colors:
        final_clip = final_clip.fx(vfx.invert_colors)

    if args.hold_last_frame > 0:
        final_clip = final_clip.fx(
            vfx.freeze,
            t="end",
            padding_end=1 / 100,
            freeze_duration=args.hold_last_frame,
        )

    _export_clip(final_clip, args.output)

    temp_dir.cleanup()

def _show_all_layouts():
    layouts = []
    for f in os.listdir(_get_relative_dir("layouts/")):
        if f.endswith(".yml") or f.endswith(".yaml"):
            layouts.append(f)
    print("Available layouts: ", end="")
    print(", ".join([l.split(".")[0] for l in layouts]))


def _parse_arguments():
    """
    Parses the arguments from the command line using argparse.

    Returns
    -------
    args: argparse.Namespace
        The arguments generated by argparse.
        Required: args.text
    """
    parser = argparse.ArgumentParser(
        description="A customizable typing animation generator with multi-layout support."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-t",
        "--text",
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
    group.add_argument(
        "--all-layouts",
        action="store_true",
        help="print all available layouts and exit",
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
    if args.text:
        args.text = args.text.upper() # TODO add support for case-sensitivity (animating the Shift key)

    return args


def animate(layout, args):
    """
    Create a keyboard animation video based on the provided arguments.

    Parameters
    ----------
    layout: dict
        A dictionary resulting from reading an appropriate yaml layout file.
        Should at least include the `file` and `fonts` keys.
    args: argparse.Namespace
        The arguments generated by argparse.
        Required: args.text
    """
    print("Generating frames... ", end="", flush=True)
    asset = os.path.join(_get_relative_dir("assets/"), layout['file'])
    frames_dir = _create_frames(asset, args.text)
    print("frames successfully generated.")
    print("Generating output file... ", end="", flush=True)
    _create_video(frames_dir, layout, args)
    print(f"output file {args.output} successfully generated.")


def main():
    args = _parse_arguments()

    if args.all_layouts:
        _show_all_layouts()
        quit()

    layouts_dir = _get_relative_dir("layouts/")
    layout_file = os.path.join(layouts_dir, args.layout) + ".yml"
    with open(layout_file) as f:
        layout = yaml.safe_load(f)

    animate(layout, args)


if __name__ == "__main__":
    main()

