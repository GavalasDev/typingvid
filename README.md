# Typingvid

![PyPI](https://img.shields.io/pypi/v/typingvid) ![PyPI - Status](https://img.shields.io/pypi/status/typingvid) ![PyPI - Downloads](https://img.shields.io/pypi/dm/typingvid) ![PyPI - License](https://img.shields.io/pypi/l/typingvid)

Typingvid is a command line utility that allows users to quickly generate typing animation videos using different keyboard layouts and themes. To read more about the inner workings of the tool visit https://www.gavalas.dev/projects/typingvid.

## Installation

### Using a package installer

![](https://www.gavalas.dev/assets/images/typingvid/gifs/pipinstall.gif)

The latest stable version of the script is available on the Python Package Index (PyPI) and can easily be installed using your favorite Python package installer (e.g. pip):

    pip install typingvid

or:

    python3 -m pip install typingvid

To check If everything went smoothly, you can try running:

    typingvid --help

### From source

Another option is to clone the entire GitHub repository of the project as follows:

    git clone https://github.com/GavalasDev/typingvid
    cd typingvid
    chmod +x typingvid.py
    ./typingvid.py --help

## Usage

The standard format of a typingvid command is the following:

    typingvid -t TEXT [-l LAYOUT] [-o OUTPUT] [OPTIONS]

To see all available options, use:

    typingvid --help

For example:

    typingvid -t "hello world"

will generate an animation video using the default layout (en) and store it at the default output location (output.mp4).

The extension of the `OUTPUT` variable (option `-o`) defines the type of the output file. For example, to generate a simple GIF:

    typingvid -t "lorem ipsum" -o "/path/to/file.gif"

For more examples, check out the [official page](https://www.gavalas.dev/projects/typingvid/#examples) of the tool.

## License

Licensed under the MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT).


## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, shall be licensed as above, without any additional terms or conditions.

