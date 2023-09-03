import sys
import os
import pathlib as pl
import tkinter as tk
import tkinter.messagebox   as mb
from program.source import Editor


#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


min_version = (3, 10)
cur_version = sys.version_info
dev_mode    = False
is_portable = True
root_dir    = pl.Path(__file__).parent.absolute()


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
            win = tk.Tk()
            win.withdraw()
            mb.showerror("Internal Error", f"{exc_type.__name__}: {exc_desc}")
else:
    win = tk.Tk()
    win.withdraw()
    mb.showerror("Version Error", f"Your version of Python is not supported. Please use Python {min_version[0]}.{min_version[1]} or higher.")