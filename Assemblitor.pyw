import sys
import os
import pathlib as pl
import tkinter as tk
import tkinter.messagebox as mb


#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


def display_error(name, description):
    win = tk.Tk()
    win.withdraw()
    mb.showerror(name, description)

def display_warning(name, description):
    win = tk.Tk()
    win.withdraw()
    mb.showwarning(name, description)

def ver_str(ver: tuple[int, ...]):
    return ".".join([str(subver) for subver in ver])


min_version = (3, 10)
cur_version = sys.version_info[:3]
min_pil_ver = (10, 0, 0)
dev_mode    = True
is_portable = True
root_dir    = pl.Path(__file__).parent.absolute()


# safely import Editor
try:
    import PIL
except ImportError:
    display_warning("Missing Package", f"Needs Python package Pillow {ver_str(min_pil_ver)}+ to work properly.\n\nYou can install it via the console command 'pip install pillow'.")
    sys.exit()
cur_pil_ver = PIL.__version__.split(".", maxsplit = 2)
cur_pil_ver = tuple(int(subver) for subver in cur_pil_ver)
if cur_pil_ver < min_pil_ver:
    display_warning("Unsupported Version", f"Pillow {ver_str(cur_pil_ver)} is not supported. Please use version {ver_str(min_pil_ver)} or higher.")
    sys.exit()
else:
    from program.source import Editor


if is_portable:
    profile_dir = os.path.join(root_dir, "profile")
else:
    profile_dir = ".../AppData/Assemblitor/profile"  # TODO add feature for installed desktop application


# safely start Editor
if cur_version >= min_version:
    try:
        Editor.startup(profile_dir = profile_dir, root_dir = root_dir, dev_mode = dev_mode)
    except KeyboardInterrupt:  # avoid printing KeyboardInterrupt error
        sys.exit()
    except Exception as e:
        if dev_mode:
            import traceback
            traceback.print_exception(e)
        else:
            display_error("Internal Error", f"{type(e).__name__}: {e}")
        sys.exit()
else:
    display_warning("Unsupported Version", f"Python {ver_str(cur_version)} is not supported. Please use Python {ver_str(min_version)} or higher.")