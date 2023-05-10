import os
import tkinter      as tk
import tkinter.ttk  as ttk
import tkinter.font as fn
from program.source import Widgets as wdg


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


class Subwindow:

    def __init__(self, editor):
        self.ed = editor
        self.subroot = None
        self.active = False

    def open(self):
        if not self.active:
            self.active = True
            self.build_gui()
            self.focus()
        else: # set focus on already existing window
            self.focus()

    def build_gui(self): # different for each Subwindow
        self.subroot.protocol("WM_DELETE_WINDOW", self.close)

    def focus(self):
        if self.active:
            self.subroot.focus_force()
            self.subroot.lift()
            self.ed.root.update()
        else:
            raise RuntimeError(f"Can't focus on Subwindow if it isn't opened.")

    def close(self):
        if self.active:
            self.active = False
            self.subroot.destroy()
        else:
            raise RuntimeError(f"Can't close Subwindow if it isn't opened.")


class Options(Subwindow):

    def open(self):
        self.is_light_theme_VAR = tk.BooleanVar(value = ph.theme() == "light")
        self.language_VAR       = tk.StringVar( value = lh.gt_lang_name(ph.language())) # do not use to get current option as this StringVar is language-dependent; use self.language_OMN.current_option()
        self.code_font_face_VAR = tk.StringVar( value = font_face_name(ph.code_font_face())) # do not use to get current option as this StringVar is language-dependent; use self.code_font_face_OMN.current_option()
        self.code_font_size_VAR = tk.IntVar(    value = ph.code_font_size())
        self.min_adr_len_VAR    = tk.IntVar(    value = ph.min_adr_len())
        self.max_cels_VAR       = tk.IntVar(    value = ph.max_cels())
        self.max_jmps_VAR       = tk.IntVar(    value = ph.max_jmps())
        self.init_state = {
            "theme":          self.gt_theme(),
            "language":       ph.language(),
            "code_font_face": ph.code_font_face(),
            "code_font_size": self.code_font_size_VAR.get(),
            "min_adr_len":    self.min_adr_len_VAR.get(),
            "max_cels":       self.max_cels_VAR.get(),
            "max_jmps":       self.max_jmps_VAR.get()
        }

        super().open()

    def gt_theme(self):
        if self.is_light_theme_VAR.get():
            return "light"
        else:
            return "dark"

    def build_gui(self):

        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.geometry(lh.opt_win("geometry"))
        self.subroot.resizable(False, False)
        self.subroot.config(bg = self.ed.theme_base_bg)
        self.subroot.title(lh.opt_win("title"))
        self.options_FRM = ttk.Frame(self.subroot, style ="text.TFrame")
        self.options_FRM.pack(fill = "both", expand = True)
        vcmd = self.options_FRM.register(char_is_digit) # used for code_font_size_SBX and min_adr_len_SBX to only allow entered digits

        # appearance
        self.appearance_subtitle_LBL = ttk.Label(self.options_FRM, style = "subtitle.TLabel", text = lh.opt_win("Appearance"))
        self.light_theme_CHB    = ttk.Checkbutton(self.options_FRM, style = "embedded.TCheckbutton", text = lh.opt_win("LightTheme"), variable = self.is_light_theme_VAR, command = lambda: self.change(restart_required = True), onvalue = True, offvalue = False)
        if not self.is_light_theme_VAR.get():
            self.light_theme_CHB.state(["!alternate"])  # deselect the checkbutton
        self.language_FRM       = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.language_LBL       = ttk.Label(self.language_FRM, style = "TLabel", text = lh.opt_win("Language"))
        self.language_OMN       = wdg.OptionMenu(self.language_FRM, textvariable = self.language_VAR, default_option = ph.language(), options = lh.gt_langs_with_names(), command = lambda event: self.change(restart_required = True), style = "TMenubutton")
        self.code_font_FRM      = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.code_font_LBL      = ttk.Label(self.code_font_FRM, style = "TLabel", text = lh.opt_win("EditorFont"))
        self.code_font_size_SBX = ttk.Spinbox(self.code_font_FRM, textvariable = self.code_font_size_VAR, from_ = 5, to = 30, command = lambda: self.change(focus_flag = True), validate = "all", validatecommand = (vcmd, "%P"), width = 3, style = "TSpinbox")
        self.code_font_face_OMN = wdg.OptionMenu(self.code_font_FRM, textvariable = self.code_font_face_VAR, default_option = ph.code_font_face(), options = gt_font_faces_with_names(), command = lambda event: self.change(), style = "TMenubutton")
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
        self.min_adr_len_SBX = ttk.Spinbox(self.min_adr_len_FRM, textvariable = self.min_adr_len_VAR, from_ = 1, to = 10, command = lambda: self.change(focus_flag = True), validate = "all", validatecommand = (vcmd, "%P"), width = 3, style = "TSpinbox")
        self.max_cels_FRM    = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.max_cels_LBL    = ttk.Label(self.max_cels_FRM, style = "TLabel", text = lh.opt_win("MaxCels"))
        self.max_cels_SBX    = ttk.Spinbox(self.max_cels_FRM, textvariable = self.max_cels_VAR, from_ = 1, to = 1048576, command = lambda: self.change(focus_flag = True), validate = "all", validatecommand = (vcmd, "%P"), width = 6, style = "TSpinbox")
        self.max_jmps_FRM    = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.max_jmps_LBL    = ttk.Label(self.max_jmps_FRM, style = "TLabel", text = lh.opt_win("MaxJmps"))
        self.max_jmps_SBX    = ttk.Spinbox(self.max_jmps_FRM, textvariable = self.max_jmps_VAR, from_ = 1, to = 1048576, command = lambda: self.change(focus_flag = True), validate = "all", validatecommand = (vcmd, "%P"), width = 6, style = "TSpinbox")
        self.assembler_subtitle_LBL.pack(fill = "x", pady = 5, padx = 5)
        self.min_adr_len_FRM.pack(fill = "x",               padx = (20, 5))
        self.min_adr_len_LBL.pack(side = "left",  pady = 5, padx = (0, 15))
        self.min_adr_len_SBX.pack(side = "right", pady = 5, padx = 5)
        self.max_cels_FRM   .pack(fill = "x",               padx = (20, 5))
        self.max_cels_LBL   .pack(side = "left",  pady = 5, padx = (0, 15))
        self.max_cels_SBX   .pack(side = "right", pady = 5, padx = 5)
        self.max_jmps_FRM   .pack(fill = "x",     padx = (20, 5))
        self.max_jmps_LBL   .pack(side = "left",  pady = 5, padx = (0, 15))
        self.max_jmps_SBX   .pack(side = "right", pady = 5, padx = 5)

        # taskbar
        self.buttons_FRM = ttk.Frame(self.options_FRM, style = "text.TFrame")
        self.cancel_BTN  = ttk.Button(self.buttons_FRM, text = lh.opt_win("Cancel"),  command = self.close,   style = "TButton")
        self.apply_BTN   = ttk.Button(self.buttons_FRM, text = lh.opt_win("Apply"),   command = self.save,    style = "TButton")
        self.ok_BTN      = ttk.Button(self.buttons_FRM, text = lh.opt_win("Ok"),      command = self.ok_btn,  style = "TButton")
        self.restart_BTN = ttk.Button(self.buttons_FRM, text = lh.opt_win("Restart"), command = self.restart, style = "TButton", state = "disabled")
        self.reset_BTN   = ttk.Button(self.buttons_FRM, text = lh.opt_win("Reset"),   command = self.reset,   style = "TButton")
        self.restart_LBL = ttk.Label(self.options_FRM, text = "", foreground = "#FF4444", style = "TLabel")
        self.buttons_FRM.pack(fill = "x", side = "bottom", pady = 5, padx = 5)
        self.cancel_BTN .pack(side = "right", padx = (5, 0))
        self.apply_BTN  .pack(side = "right", padx = (5, 0))
        self.ok_BTN     .pack(side = "right", padx = (5, 0))
        self.ok_BTN     .pack(side = "right", padx = (5, 0))
        self.restart_BTN.pack(side = "right", padx = (5, 0))
        self.reset_BTN  .pack(side = "left")
        self.restart_LBL.pack(fill = "x", side = "bottom", pady = (5, 0), padx = 5)
        if self.restart_required_flag():
            self.restart_required()

        # events
        self.code_font_size_SBX.bind(sequence = "<Return>", func = lambda event: self.change(focus_flag = True))
        self.min_adr_len_SBX.bind(   sequence = "<Return>", func = lambda event: self.change(focus_flag = True))
        self.max_cels_SBX.bind(      sequence = "<Return>", func = lambda event: self.change(focus_flag = True))
        self.max_jmps_SBX.bind(      sequence = "<Return>", func = lambda event: self.change(focus_flag = True))

        super().build_gui()

    def set_option_vars(self):
        self.is_light_theme_VAR.set(value = ph.theme() == "light")
        self.language_VAR      .set(value = lh.gt_lang_name(lh.cur_lang))
        self.code_font_face_VAR.set(value = font_face_name(ph.code_font_face()))
        self.code_font_size_VAR.set(value = ph.code_font_size())
        self.min_adr_len_VAR   .set(value = ph.min_adr_len())
        self.max_cels_VAR      .set(value = ph.max_cels())
        self.max_jmps_VAR      .set(value = ph.max_jmps())

    def restart_required_flag(self):
        return self.ed.active_theme != self.current_state("theme") or self.ed.active_language != self.current_state("language")

    def update_options(self):
        self.set_option_vars() # reset
        if self.restart_required_flag():
            self.restart_required()
        else:
            self.restart_no_longer_required()

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

    def change(self, restart_required = False, focus_flag = False, event = None):
        if focus_flag: # remove focus from spinboxes (to remove cursor in the spinbox)
            self.focus()
        if restart_required:
            if self.restart_required_flag():
                self.restart_required()
            else:
                self.restart_no_longer_required() # also revert displaying restart_BTN & restart_LBL when changes got reverted

    def option_changed(self, option:str):
        return self.init_state[option] != self.current_state(option)

    def current_state(self, option:str):
        if option == "language" or option == "code_font_face":
            return eval(f"self.{option}_OMN.current_option()")
        elif option == "theme":
            return self.gt_theme()
        else:
            return eval(f"self.{option}_VAR.get()")

    def restart_required(self):
        self.restart_LBL.config(text = lh.opt_win("RestartRequired"))
        self.restart_BTN.config(state = "enabled")

    def restart_no_longer_required(self):
        self.restart_LBL.config(text = "")
        self.restart_BTN.config(state = "disabled")

    def save(self):
        for option in self.init_state:
            if self.option_changed(option): # TODO also saves unchanged options?
                ph.save_profile_data(key = option, new_value = self.current_state(option))
                self.init_state[option] = self.current_state(option)
                eval(f"self.save_option_{option}()") # individual saving methods

    def save_option_theme(self):
        pass

    def save_option_language(self):
        pass

    def save_option_code_font_face(self):
        self.ed.update_code_font()

    def save_option_code_font_size(self):
        self.ed.update_code_font()

    def save_option_min_adr_len(self):
        emu.update_properties()

    def save_option_max_cels(self):
        emu.update_properties()

    def save_option_max_jmps(self):
        emu.update_properties()


class Assembly(Subwindow):

    def build_gui(self):
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.minsize(*lh.asm_win("minsize"))
        self.subroot.config(bg = self.ed.theme_base_bg)
        self.subroot.title(lh.asm_win("title"))

        self.assembly_FRM = ttk.Frame(self.subroot, style = "TFrame")
        self.text_SCB = tk.Scrollbar(self.assembly_FRM)
        self.text_TXT = tk.Text(self.assembly_FRM, bg = self.ed.theme_text_bg, fg = self.ed.theme_text_fg, bd = 5, relief = "flat", wrap = "word", font = ("TkDefaultFont", 10), yscrollcommand = self.text_SCB.set)
        self.assembly_FRM.pack(fill = "both", expand = True)
        self.text_TXT.pack(side = "left",  fill = "both", expand = True)
        self.text_SCB.pack(side = "right", fill = "y")
        self.set_code_font()

        text_code_pairs = lh.asm_win("text")
        for text_code_pair in text_code_pairs:
            self.text_TXT.insert("end", text_code_pair[0])
            self.text_TXT.insert("end", text_code_pair[1], "asm_code")
        self.text_SCB.config(command = self.text_TXT.yview)
        self.text_TXT.config(state = "disabled")

        super().build_gui()

    def set_code_font(self):
        if self.active:
            self.text_TXT.tag_config("asm_code", font = ph.code_font())

class Shortcuts(Subwindow):

    def build_gui(self):
        combos = lh.shc_win("combos")
        actions = lh.shc_win("actions")
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.geometry(lh.shc_win("geometry"))
        self.subroot.resizable(False, False)
        self.subroot.config(bg = self.ed.theme_base_bg)
        self.subroot.title(lh.shc_win("title"))

        self.shortcuts_FRM = ttk.Frame(self.subroot, style ="text.TFrame")
        self.combos_LBL    = ttk.Label(self.shortcuts_FRM, style = "TLabel", text = combos,  justify = "left")
        self.actions_LBL   = ttk.Label(self.shortcuts_FRM, style = "TLabel", text = actions, justify = "left")
        self.shortcuts_FRM.pack(fill = "both", expand = True)
        self.combos_LBL.pack( side = "left",  fill = "both", expand = True, pady = 5, padx = 5)
        self.actions_LBL.pack(side = "right", fill = "both", expand = True, pady = 5, padx = (0, 5))

        super().build_gui()


class About(Subwindow):

    def build_gui(self):
        title = lh.gui("title")
        text  = lh.abt_win("text")
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.geometry(lh.abt_win("geometry"))
        self.subroot.resizable(False, False)
        self.subroot.config(bg = self.ed.theme_base_bg)
        self.subroot.title(lh.abt_win("title"))

        self.about_FRM = ttk.Frame(self.subroot, style ="text.TFrame")
        self.title_LBL = ttk.Label(self.about_FRM, style = "TLabel", text = title, anchor = "center", justify = "left", font = self.ed.title_font)
        self.text_LBL  = ttk.Label(self.about_FRM, style = "TLabel", text = text,  anchor = "w",      justify = "left")
        self.about_FRM.pack(fill = "both", expand = True)
        self.title_LBL.pack(fill = "both", expand = True, padx = 5, pady = (5, 0))
        self.text_LBL.pack( fill = "both", expand = True, padx = 5, pady = (0, 5))

        super().build_gui()