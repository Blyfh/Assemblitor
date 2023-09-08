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


min_version = (3, 10)
cur_version = sys.version_info
min_pil_ver = (10, 0, 0)
dev_mode    = False
is_portable = True
root_dir    = pl.Path(__file__).parent.absolute()


# check if it's safe to import Editor
try:
    import PIL
except ImportError:
    display_warning("Missing Package", f"Needs Python package Pillow {min_pil_ver[0]}.{min_pil_ver[1]}.{min_pil_ver[2]}+ to work properly.\n\nYou can install it via the console command 'pip install pillow'.")
    sys.exit()
cur_pil_ver = PIL.__version__.split(".", maxsplit = 2)
for i in range(3):
    cur_pil_ver[i] = int(cur_pil_ver[i])
cur_pil_ver = tuple(cur_pil_ver)
if cur_pil_ver < min_pil_ver:
    display_warning("Unsupported Version", f"Your version of Pillow is not supported. Please use version {min_pil_ver[0]}.{min_pil_ver[1]}.{min_pil_ver[2]} or higher.")
    sys.exit()
else:
    from program.source import Editor


if is_portable:
    profile_dir = os.path.join(root_dir, "profile")
else:
    profile_dir = ".../AppData/Assemblitor/profile"  # unfinished


if cur_version >= min_version:
    try:
        Editor.startup(profile_dir = profile_dir, root_dir = root_dir, dev_mode = dev_mode)
    except KeyboardInterrupt:
        pass
    except:
        if dev_mode:
            raise
        else:
            exc_type, exc_desc, tb = sys.exc_info()
            display_error("Internal Error", f"{exc_type.__name__}: {exc_desc}")
else:
    display_warning("Unsupported Version", f"Your version of Python is not supported. Please use Python {min_version[0]}.{min_version[1]} or higher.")