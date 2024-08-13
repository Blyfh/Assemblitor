import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as fn
from program.source import Widgets as wdg


#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


def startup(profile_handler, language_handler, sprite_handler, emulator):
    global ph
    global lh
    global sh
    global emu
    ph = profile_handler
    lh = language_handler
    sh = sprite_handler
    emu = emulator

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
    return font_face  # unfinished


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
        else:  # set focus on already existing window
            self.focus()
    
    def build_gui(self):  # different for each Subwindow
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
        self.is_light_theme_VAR  = tk.BooleanVar()
        self.language_VAR        = tk.StringVar()
        self.code_font_face_VAR  = tk.StringVar()
        self.code_font_size_VAR  = tk.IntVar()
        self.min_adr_len_VAR     = tk.IntVar()
        self.max_cels_VAR        = tk.IntVar()
        self.max_jmps_VAR        = tk.IntVar()
        self.closing_unsaved_VAR = tk.StringVar()
        self.dev_mode_VAR        = tk.BooleanVar()
        self.set_option_vars()
        self.init_state = {
            "theme":           self.gt_theme(),
            "language":        ph.language(),
            "code_font_face":  ph.code_font_face(),
            "code_font_size":  self.code_font_size_VAR.get(),
            "min_adr_len":     self.min_adr_len_VAR.get(),
            "max_cels":        self.max_cels_VAR.get(),
            "max_jmps":        self.max_jmps_VAR.get(),
            "closing_unsaved": ph.closing_unsaved(),
            "dev_mode":        self.dev_mode_VAR.get()
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
        self.subroot.config(bg=self.ed.theme_base_bg)
        self.subroot.title(lh.opt_win("title"))
        self.options_FRM = ttk.Frame(self.subroot, style="text.TFrame")
        self.options_FRM.pack(fill="both", expand=True)
        
        # appearance
        
        self.appearance_subtitle_LBL = ttk.Label(self.options_FRM, style="subtitle.TLabel",
                                                 text=lh.opt_win("Appearance"))
        self.light_theme_CHB = ttk.Checkbutton(self.options_FRM, style="embedded.TCheckbutton",
                                               text=lh.opt_win("LightTheme"), variable=self.is_light_theme_VAR,
                                               command=lambda: self.update_on_restart_required_change(), onvalue=True,
                                               offvalue=False)
        if not self.is_light_theme_VAR.get():
            self.light_theme_CHB.state(["!alternate"])  # deselect the checkbutton
        self.language_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.language_LBL = ttk.Label(self.language_FRM, style="TLabel", text=lh.opt_win("Language"))
        self.language_OMN = wdg.OptionMenu(self.language_FRM, textvariable=self.language_VAR,
                                           default_option=ph.language(), options=lh.gt_langs_with_names(),
                                           command=lambda event: self.update_on_restart_required_change(),
                                           style="TMenubutton")
        self.code_font_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.code_font_LBL = ttk.Label(self.code_font_FRM, style="TLabel", text=lh.opt_win("EditorFont"))
        self.code_font_size_SBX = wdg.Spinbox(self.code_font_FRM, self.subroot, textvariable=self.code_font_size_VAR,
                                              min=5, max=30, default=self.code_font_size_VAR.get(), height=23)
        self.code_font_face_OMN = wdg.OptionMenu(self.code_font_FRM, textvariable=self.code_font_face_VAR,
                                                 default_option=ph.code_font_face(), options=gt_font_faces_with_names(),
                                                 style="TMenubutton")
        self.appearance_subtitle_LBL.pack(fill="x", pady=5, padx=10)
        self.light_theme_CHB   .pack(fill="x",     pady=5, padx=(20, 5))
        self.language_FRM      .pack(fill="x",             padx=(20, 5))
        self.language_LBL      .pack(side="left",  pady=5, padx=(0, 15))
        self.language_OMN      .pack(side="right", pady=5, padx=5)
        self.code_font_FRM     .pack(fill="x",             padx=(20, 5))
        self.code_font_LBL     .pack(side="left",  pady=5, padx=(0, 15))
        self.code_font_size_SBX.pack(side="right", pady=5, padx=5)
        self.code_font_face_OMN.pack(side="right", pady=5, padx=5)
        
        # Assembler
        
        # not using ttk.Seperator because width and color can't be customized
        self.seperator1_FRM = tk.Frame(self.options_FRM, height=2,
                                       bg=self.ed.theme_base_fg)
        self.assembler_subtitle_LBL = ttk.Label(self.options_FRM, style="subtitle.TLabel", text=lh.opt_win("Assembler"))
        self.min_adr_len_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.min_adr_len_LBL = ttk.Label(self.min_adr_len_FRM, style="TLabel", text=lh.opt_win("MinAdrLen"))
        self.min_adr_len_SBX = wdg.Spinbox(self.min_adr_len_FRM, self.subroot, textvariable=self.min_adr_len_VAR, min=1,
                                           max=10, default=self.min_adr_len_VAR.get(), height=23)
        self.max_cels_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.max_cels_LBL = ttk.Label(self.max_cels_FRM, style="TLabel", text=lh.opt_win("MaxCels"))
        self.max_cels_SBX = wdg.Spinbox(self.max_cels_FRM, self.subroot, textvariable=self.max_cels_VAR, min=1,
                                        max=1048576, default=self.max_cels_VAR.get(), threshold=1, height=23)
        self.max_jmps_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.max_jmps_LBL = ttk.Label(self.max_jmps_FRM, style="TLabel", text=lh.opt_win("MaxJmps"))
        self.max_jmps_SBX = wdg.Spinbox(self.max_jmps_FRM, self.subroot, textvariable=self.max_jmps_VAR, min=1,
                                        max=1048576, default=self.max_jmps_VAR.get(), threshold=1, height=23)
        self.seperator1_FRM.pack(anchor="center", fill="x", pady=5, padx=10)
        self.assembler_subtitle_LBL.pack(fill="x", pady=5, padx=10)
        self.min_adr_len_FRM.pack(fill="x",             padx=(20, 5))
        self.min_adr_len_LBL.pack(side="left",  pady=5, padx=(0, 15))
        self.min_adr_len_SBX.pack(side="right", pady=5, padx=5)
        self.max_cels_FRM   .pack(fill="x",             padx=(20, 5))
        self.max_cels_LBL   .pack(side="left",  pady=5, padx=(0, 15))
        self.max_cels_SBX   .pack(side="right", pady=5, padx=5)
        self.max_jmps_FRM   .pack(fill="x",     padx=(20, 5))
        self.max_jmps_LBL   .pack(side="left",  pady=5, padx=(0, 15))
        self.max_jmps_SBX   .pack(side="right", pady=5, padx=5)
        
        # File
        
        # not using ttk.Seperator because width and color can't be customized
        self.seperator2_FRM = tk.Frame(self.options_FRM, height=2,
                                       bg=self.ed.theme_base_fg)
        self.file_subtitle_LBL = ttk.Label(self.options_FRM, style="subtitle.TLabel", text=lh.opt_win("File"))
        self.closing_unsaved_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.closing_unsaved_LBL = ttk.Label(self.closing_unsaved_FRM, style="TLabel",
                                             text=lh.opt_win("ClosingUnsaved"))
        self.closing_unsaved_OMN = wdg.OptionMenu(self.closing_unsaved_FRM, textvariable=self.closing_unsaved_VAR,
                                                  default_option=ph.closing_unsaved(),
                                                  options=lh.opt_win("ClosingUnsavedOptions"), style="TMenubutton")
        self.seperator2_FRM.pack(anchor="center", fill="x", pady=5, padx=10)
        self.file_subtitle_LBL.pack(fill="x", pady=5, padx=10)
        self.closing_unsaved_FRM.pack(fill="x",             padx=(20, 5))
        self.closing_unsaved_LBL.pack(side="left",  pady=5, padx=(0, 15))
        self.closing_unsaved_OMN.pack(side="right", pady=5, padx=5)
        
        # Advanced
        
        # not using ttk.Seperator because width and color can't be customized
        self.seperator3_FRM = tk.Frame(self.options_FRM, height=2,
                                       bg=self.ed.theme_base_fg)
        self.advanced_subtitle_LBL = ttk.Label(self.options_FRM, style="subtitle.TLabel", text=lh.opt_win("Advanced"))
        self.dev_mode_CHB = ttk.Checkbutton(self.options_FRM, style="embedded.TCheckbutton", text=lh.opt_win("DevMode"),
                                            variable=self.dev_mode_VAR, onvalue=True, offvalue=False)
        if not self.dev_mode_VAR.get():
            self.dev_mode_CHB.state(["!alternate"])  # deselect the checkbutton
        self.dev_mode_TIP = wdg.Tooltip(self.dev_mode_CHB, text=lh.opt_win("DevModeTip"))
        self.seperator3_FRM.pack(anchor="center", fill="x", pady=5, padx=10)
        self.advanced_subtitle_LBL.pack(fill="x", pady=5, padx=10)
        self.dev_mode_CHB.pack(fill="x", pady=5, padx=(20, 5))
        
        # taskbar
        
        self.buttons_FRM = ttk.Frame(self.options_FRM, style="text.TFrame")
        self.cancel_BTN  = ttk.Button(self.buttons_FRM, text=lh.opt_win("Cancel"),  command=self.close,   style="TButton")
        self.apply_BTN   = ttk.Button(self.buttons_FRM, text=lh.opt_win("Apply"),   command=self.save,    style="TButton")
        self.ok_BTN      = ttk.Button(self.buttons_FRM, text=lh.opt_win("Ok"),      command=self.ok_btn,  style="TButton")
        self.restart_BTN = ttk.Button(self.buttons_FRM, text=lh.opt_win("Restart"), command=self.restart, style="TButton", state="disabled")
        self.reset_BTN   = ttk.Button(self.buttons_FRM, text=lh.opt_win("Reset"),   command=self.reset,   style="TButton")
        self.restart_LBL = ttk.Label(self.options_FRM, text="", foreground="#FF4444", style="TLabel")
        self.buttons_FRM.pack(fill="x", side="bottom", pady=5, padx=5)
        self.cancel_BTN .pack(side="right", padx=(5, 0))
        self.apply_BTN  .pack(side="right", padx=(5, 0))
        self.ok_BTN     .pack(side="right", padx=(5, 0))
        self.ok_BTN     .pack(side="right", padx=(5, 0))
        self.restart_BTN.pack(side="right", padx=(5, 0))
        self.reset_BTN  .pack(side="left")
        self.restart_LBL.pack(fill="x", side="bottom", pady=(5, 0), padx=5)
        if self.restart_required_flag():
            self.restart_required()
        super().build_gui()
    
    def set_option_vars(self):
        self.is_light_theme_VAR .set(value=ph.theme() == "light")
        # has language dependent displaytext
        self.language_VAR       .set(value=lh.gt_lang_name(ph.language()))
        # has language dependent displaytext
        self.code_font_face_VAR .set(value=font_face_name(ph.code_font_face()))
        self.code_font_size_VAR .set(value=ph.code_font_size())
        self.min_adr_len_VAR    .set(value=ph.min_adr_len())
        self.max_cels_VAR       .set(value=ph.max_cels())
        self.max_jmps_VAR       .set(value=ph.max_jmps())
        # has language dependent displaytext
        self.closing_unsaved_VAR.set(value=lh.opt_win("ClosingUnsavedOptions")[ph.closing_unsaved()])
        self.dev_mode_VAR       .set(value=ph.dev_mode())
    
    def restart_required_flag(self):
        return (self.ed.active_theme    != self.current_state("theme") or
                self.ed.active_language != self.current_state("language"))
    
    def update_options(self):
        self.set_option_vars()  # reset
        self.update_on_restart_required_change()
    
    def ok_btn(self):
        self.save()
        self.close()
    
    def restart(self):
        self.save()
        self.ed.destroy()
        os.startfile(self.ed.root_dir / "Assemblitor.pyw")
    
    def reset(self):
        ph.reset_profile()
        self.update_options()
    
    def update_on_restart_required_change(self):
        if self.restart_required_flag():
            self.restart_required()
        else:
            # also revert displaying restart_BTN & restart_LBL when changes got reverted
            self.restart_no_longer_required()
    
    def option_changed(self, option: str):
        return self.init_state[option] != self.current_state(option)
    
    def current_state(self, option: str):
        if option == "language" or option == "code_font_face" or option == "closing_unsaved":
            return getattr(self, f"{option}_OMN").current_option()
        elif option == "theme":
            return self.gt_theme()
        else:
            return getattr(self, f"{option}_VAR").get()
    
    def restart_required(self):
        self.restart_LBL.config(text=lh.opt_win("RestartRequired"))
        self.restart_BTN.config(state="enabled")
    
    def restart_no_longer_required(self):
        self.restart_LBL.config(text="")
        self.restart_BTN.config(state="disabled")
    
    def save(self):
        for option in self.init_state:
            if self.option_changed(option):
                ph.save_profile_data(key=option, new_value=self.current_state(option))
                self.init_state[option] = self.current_state(option)
                getattr(self, f"save_option_{option}")()  # individual saving methods
    
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
    
    def save_option_closing_unsaved(self):
        self.ed.action_on_closing_unsaved_prg = self.current_state("closing_unsaved")
    
    def save_option_dev_mode(self):
        self.ed.dev_mode = self.dev_mode_VAR.get()


class Assembly(Subwindow):
    
    def build_gui(self):
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.minsize(*lh.asm_win("minsize"))
        self.subroot.config(bg=self.ed.theme_base_bg)
        self.subroot.title(lh.asm_win("title"))
        
        self.assembly_FRM = ttk.Frame(self.subroot, style="TFrame")
        self.text_BAR = tk.Scrollbar(self.assembly_FRM)
        self.text_TXT = tk.Text(self.assembly_FRM, bg=self.ed.theme_text_bg, fg=self.ed.theme_text_fg, bd=5,
                                relief="flat", wrap="word", font=("TkDefaultFont", 10),
                                yscrollcommand=self.text_BAR.set)
        self.assembly_FRM.pack(fill="both", expand=True)
        self.text_TXT.pack(side="left",  fill="both", expand=True)
        self.text_BAR.pack(side="right", fill="y")
        self.set_code_font()
        
        text_code_pairs = lh.asm_win("text")
        for text_code_pair in text_code_pairs:
            self.text_TXT.insert("end", text_code_pair[0])
            self.text_TXT.insert("end", text_code_pair[1], "asm_code")
        self.text_BAR.config(command=self.text_TXT.yview)
        self.text_TXT.config(state="disabled")
        super().build_gui()
    
    def set_code_font(self):
        if self.active:
            self.text_TXT.tag_config("asm_code", font=ph.code_font())


class Shortcuts(Subwindow):
    
    def build_gui(self):
        combos = lh.shc_win("combos")
        actions = lh.shc_win("actions")
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.geometry(lh.shc_win("geometry"))
        self.subroot.resizable(False, False)
        self.subroot.config(bg=self.ed.theme_base_bg)
        self.subroot.title(lh.shc_win("title"))
        
        self.shortcuts_FRM = ttk.Frame(self.subroot, style="text.TFrame")
        self.combos_LBL    = ttk.Label(self.shortcuts_FRM, style="TLabel", text=combos,  justify="left")
        self.actions_LBL   = ttk.Label(self.shortcuts_FRM, style="TLabel", text=actions, justify="left")
        self.shortcuts_FRM.pack(fill="both", expand=True)
        self.combos_LBL .pack(side="left",  fill="both", expand=True, pady=5, padx=5)
        self.actions_LBL.pack(side="right", fill="both", expand=True, pady=5, padx=(0, 5))
        super().build_gui()


class About(Subwindow):
    
    def build_gui(self):
        title = lh.gui("title")
        text = lh.abt_win("text")
        self.subroot = tk.Toplevel(self.ed.root)
        self.subroot.geometry(lh.abt_win("geometry"))
        #self.subroot.resizable(False, False)
        self.subroot.config(bg=self.ed.theme_text_bg)
        self.subroot.title(lh.abt_win("title"))
        
        self.about_FRM = ttk.Frame(self.subroot, style="text.TFrame")
        self.title_TXT = tk.Text(self.about_FRM, height=1, font=self.ed.title_font, bg=self.ed.theme_text_bg,
                                 fg=self.ed.theme_text_fg, bd=0)
        self.title_TXT.insert("1.0", title)
        self.title_TXT.config(state="disabled")
        icon = sh.gt_sprite("Assemblitor", "icon", 90, 90)
        self.icon_LBL = ttk.Label(self.about_FRM, image=icon)
        self.icon_LBL.image = icon
        self.text_TXT = tk.Text(self.about_FRM, height=6, font=("TkDefaultFont", 10), bg=self.ed.theme_text_bg,
                                fg=self.ed.theme_text_fg, bd=0)
        self.text_TXT.insert("1.0", text)
        self.text_TXT.config(state="disabled")
        self.about_FRM.pack(expand=True, anchor="center")
        self.title_TXT.pack(side="top",   padx=5, pady=5)
        self.icon_LBL .pack(side="left",  padx=5, pady=5, anchor="center", )
        self.text_TXT .pack(side="right", padx=5, pady=5)
        super().build_gui()
