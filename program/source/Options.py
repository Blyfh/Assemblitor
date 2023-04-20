import os
import tkinter      as tk
import tkinter.ttk  as ttk
import tkinter.font as fn
from program.source import CustomGUI as gui


def startup(profile_handler, language_handler, emulator):
    global ph
    global lh
    global emu
    ph  = profile_handler
    lh  = language_handler
    emu = emulator

def char_is_digit(char): # used by Options.code_font_size_SBX, Options.min_adr_len_SBX to only allow entered digits
    return str.isdigit(char) or char == ""

def gt_font_faces_with_names():
    font_faces_with_names = {}
    for font_face in gt_font_faces():
        font_faces_with_names[font_face] = font_face_name(font_face)
    return font_faces_with_names

def gt_font_faces():
    fonts = list(fn.families())
    fonts.sort()
    return fonts

def font_face_name(font_face):
    return font_face # unfinished


class Options:

    def __init__(self, editor):
        self.ed = editor
        self.changes = {
            "is_light_theme": False,
            "language":       False,
            "code_font_face": False,
            "code_font_size": False,
            "min_adr_len":    False
        }
        self.is_light_theme_VAR = tk.BooleanVar(value = ph.is_light_theme())
        self.language_VAR       = tk.StringVar( value = ph.language())
        self.code_font_face_VAR = tk.StringVar( value = ph.code_font()[0])
        self.code_font_size_VAR = tk.IntVar(    value = ph.code_font()[1])
        self.min_adr_len_VAR    = tk.IntVar(    value = ph.min_adr_len())

        self.init_state = {
            "is_light_theme": self.is_light_theme_VAR.get(),
            "language":       self.language_VAR .get(),
            "code_font_face": self.code_font_face_VAR.get(),
            "code_font_size": self.code_font_size_VAR.get(),
            "min_adr_len":    self.min_adr_len_VAR   .get()
        }

        self.options_WIN = tk.Toplevel(self.ed.root)
        self.options_WIN.geometry(lh.opt_win("geometry"))
        self.options_WIN.resizable(False, False)
        self.options_WIN.config(bg = self.ed.theme_base_bg)
        self.options_WIN.title(lh.opt_win("title"))
        self.options_FRM = ttk.Frame(self.options_WIN, style = "text.TFrame")
        self.options_FRM.pack(fill = "both", expand = True)
        vcmd = self.options_FRM.register(char_is_digit) # used for code_font_size_SBX and min_adr_len_SBX to only allow entered digits
        # appearance
        self.appearance_subtitle_LBL = ttk.Label(self.options_FRM, style = "subtitle.TLabel", text = lh.opt_win("Appearance"))
        self.light_theme_CHB    = ttk.Checkbutton(self.options_FRM, style = "embedded.TCheckbutton", text = lh.opt_win("LightTheme"), variable = self.is_light_theme_VAR, command = lambda: self.change("is_light_theme", restart_required = True), onvalue = True, offvalue = False)
        if not self.is_light_theme_VAR.get():
            self.light_theme_CHB.state(["!alternate"])  # deselect the checkbutton
        self.language_FRM       = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.language_LBL       = ttk.Label(self.language_FRM, style = "TLabel", text = lh.opt_win("Language"))
        self.language_OMN       = gui.OptionMenu(self.language_FRM, textvariable = self.language_VAR, default_option = self.language_VAR.get(), options = lh.gt_langs_with_names(), command = lambda event: self.change("language", restart_required = True), style = "TMenubutton")
        self.code_font_FRM      = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.code_font_LBL      = ttk.Label(self.code_font_FRM, style = "TLabel", text = lh.opt_win("EditorFont"))
        self.code_font_size_SBX = ttk.Spinbox(self.code_font_FRM, textvariable = self.code_font_size_VAR, from_ = 5, to = 30, command = lambda: self.change("code_font_size"), validate = "all", validatecommand = (vcmd, "%P"), width = 3, style = "TSpinbox")
        self.code_font_face_OMN = gui.OptionMenu(self.code_font_FRM, textvariable = self.code_font_face_VAR, default_option = self.code_font_face_VAR.get(), options = gt_font_faces_with_names(), command = lambda event: self.change("code_font_face"), style = "TMenubutton")
        self.appearance_subtitle_LBL.pack(fill = "x", pady = 5, padx = 5)
        self.light_theme_CHB.pack(   fill = "x",     pady = 5, padx = (20, 5))
        self.language_FRM      .pack(fill = "x",               padx = (20, 5))
        self.language_LBL      .pack(side = "left",  pady = 5, padx = (0, 15))
        self.language_OMN      .pack(side = "right", pady = 5, padx = 5)
        self.code_font_FRM     .pack(fill = "x",               padx = (20, 5))
        self.code_font_LBL     .pack(side = "left",  pady = 5, padx = (0, 15))
        self.code_font_size_SBX.pack(side = "right", pady = 5, padx = 5)
        self.code_font_face_OMN.pack(side = "right", pady = 5, padx = 5)
        # Assembler
        self.assembler_subtitle_LBL = ttk.Label(self.options_FRM, style = "subtitle.TLabel", text = lh.opt_win("Assembler"))
        self.min_adr_len_FRM = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.min_adr_len_LBL = ttk.Label(self.min_adr_len_FRM, style = "TLabel", text = lh.opt_win("MinAdrLen"))
        self.min_adr_len_SBX = ttk.Spinbox(self.min_adr_len_FRM, textvariable = self.min_adr_len_VAR, from_ = 1, to = 10, command = lambda: self.change("min_adr_len"), validate = "all", validatecommand = (vcmd, "%P"), width = 3, style = "TSpinbox")
        self.assembler_subtitle_LBL.pack(fill = "x", pady = 5, padx = 5)
        self.min_adr_len_FRM.pack(fill = "x",               padx = (20, 5))
        self.min_adr_len_LBL.pack(side = "left",  pady = 5, padx = (0, 15))
        self.min_adr_len_SBX.pack(side = "right", pady = 5, padx = 5)
        # taskbar
        self.buttons_FRM = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.cancel_BTN  = gui.Button(self.buttons_FRM, text = lh.opt_win("Cancel"),  command = self.close,   style = "TButton")
        self.apply_BTN   = gui.Button(self.buttons_FRM, text = lh.opt_win("Apply"),   command = self.save,    style = "TButton")
        self.ok_BTN      = gui.Button(self.buttons_FRM, text = lh.opt_win("Ok"),      command = self.ok_btn,  style = "TButton")
        self.restart_BTN = gui.Button(self.buttons_FRM, text = lh.opt_win("Restart"), command = self.restart, style = "TButton", state = "disabled")
        self.reset_BTN   = gui.Button(self.buttons_FRM, text = lh.opt_win("Reset"),   command = self.reset,   style = "TButton")
        self.restart_LBL = ttk.Label(self.options_FRM, text = "", foreground = "#FF4444", style = "TLabel")
        self.buttons_FRM.pack(fill = "x", side = "bottom", pady = 5, padx = 5)
        self.cancel_BTN .pack(side = "right", padx = (5, 0))
        self.apply_BTN  .pack(side = "right", padx = (5, 0))
        self.ok_BTN     .pack(side = "right", padx = (5, 0))
        self.ok_BTN     .pack(side = "right", padx = (5, 0))
        self.restart_BTN.pack(side = "right", padx = (5, 0))
        self.reset_BTN  .pack(side = "left")
        self.restart_LBL.pack(fill = "x", side = "bottom", pady = (5, 0), padx = 5)

        self.code_font_size_SBX.bind(sequence = "<Return>", func = lambda event: self.change("code_font_size", win = self.options_WIN))
        self.min_adr_len_SBX.bind(   sequence = "<Return>", func = lambda event: self.change("min_adr_len",    win = self.options_WIN))
        self.set_child_win_focus("self.options_WIN")
        self.options_WIN.protocol("WM_DELETE_WINDOW", lambda: self.close())

    def set_option_vars(self):
        self.is_light_theme_VAR.set(value = ph.is_light_theme())
        self.language_VAR      .set(value = lh.gt_lang_name(lh.cur_lang))
        self.code_font_face_VAR.set(value = ph.code_font()[0])
        self.code_font_size_VAR.set(value = ph.code_font()[1])
        self.min_adr_len_VAR   .set(value = ph.min_adr_len())

    def update_options(self):
        self.set_option_vars()

    def set_child_win_focus(self, win_str): # TODO temp until all child wins migrated to this file
        eval(f"{win_str}.focus_force()")
        eval(f"{win_str}.lift()")
        self.ed.root.update()

    def close(self):
        self.options_WIN.destroy()
        self.ed.close_options_win()

    def ok_btn(self):
        self.save()
        self.close()

    def restart(self):
        self.save()
        self.ed.destroy()
        os.startfile("Assemblitor.pyw")

    def reset(self):
        ph.reset_profile()
        self.update_options()

    def change(self, option, restart_required = False, win = None, event = None):
        if win: # remove focus from code_font_size_SBX
            win.focus()
        if self.init_state[option] != self.current_state(option): # real change
            self.changes[option] = True
            if restart_required:
                self.restart_required()
        else: # just reverted to initial state of option
            self.changes[option] = False
            if restart_required and (option == "is_light_theme" and not self.changes["language"] or option == "language" and not self.changes["is_light_theme"]): # also revert enabling of button when changes get reverted
                self.restart_LBL.config(text = "")
                self.restart_BTN.config(state = "disabled")

    def current_state(self, option):
        if option == "language" or option == "code_font_face":
            return eval(f"self.{option}_OMN.current_option()")
        else:
            return eval(f"self.{option}_VAR.get()")

    def restart_required(self):
        self.restart_LBL.config(text = lh.opt_win("RestartRequired"))
        self.restart_BTN.config(state = "enabled")

    def save(self):
        for option in self.changes:
            if self.changes[option]:
                eval(f"self.save_option_{option}()")
                self.changes[option] = False

    def save_option_is_light_theme(self):
        ph.save_profile_data(key = "is_light_theme", new_value = self.is_light_theme_VAR.get())

    def save_option_language(self):
        ph.save_profile_data(key = "language", new_value = self.language_OMN.current_option())

    def save_option_code_font_face(self):
        ph.save_profile_data(key = "code_font_face", new_value = self.code_font_face_OMN.current_option())
        self.ed.update_code_font()

    def save_option_code_font_size(self):
        ph.save_profile_data(key = "code_font_size", new_value = self.code_font_size_VAR.get())
        self.ed.update_code_font()

    def save_option_min_adr_len(self):
        ph.save_profile_data(key = "min_adr_len", new_value = self.min_adr_len_VAR.get())
        emu.update_properties()