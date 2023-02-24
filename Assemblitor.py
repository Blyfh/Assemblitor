import sys
import os
import pathlib as pl
import tkinter as tk
import tkinter.messagebox   as mb
from program.source import Editor


min_version = (3, 10)
cur_version = sys.version_info
testing     = True
is_portable = True
root        = pl.Path(__file__).parent.absolute()


if is_portable:
    profile_dir = os.path.join(root, "profile")
else:
    profile_dir = ".../AppData/Assemblitor/profile"  # unfinished

if cur_version >= min_version:
    try:
        Editor.startup(profile_dir = profile_dir, root = root, testing = testing)
    except KeyboardInterrupt:
        pass
    except:
        if testing:
            raise
        else:
            exc_type, exc_desc, tb = sys.exc_info()
            win = tk.Tk()
            win.withdraw()
            mb.showerror("Internal Error", f"{exc_type.__name__}: {exc_desc}")
else:
    win = tk.Tk()
    win.withdraw()
    mb.showerror(lh.ver_win("title"), lh.ver_win("text", min_ver = min_version))