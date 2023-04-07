import os
import string
import traceback
import tkinter              as tk
import tkinter.ttk          as ttk
import tkinter.scrolledtext as st
import tkinter.filedialog   as fd
import tkinter.font         as fn
import tkinter.messagebox   as mb
from program.source import CustomGUI as gui
from program.source import PackHandler
from program.source import Emulator

def startup(profile_dir, root, testing = False):
    global ph
    global lh
    global eh
    global sh
    ph = PackHandler.ProfileHandler(profile_dir)
    lh = PackHandler.LangHandler(ph.language())
    eh = PackHandler.ErrorHandler()
    sh = PackHandler.SpriteHandler(ph.is_light_theme())
    Emulator.startup(profile_handler = ph, error_handler = eh)
    ed = Editor(root = root, testing = testing)


class Editor:

    def __init__(self, root, testing = False):
        self.testing    = testing
        self.init_inp   = ""
        self.dirty_flag = False
        self.file_path  = None
        self.last_dir   = root
        self.file_types = ((lh.file_mng("AsmFiles"), "*.asm"), (lh.file_mng("TxtFiles"), "*.txt"))
        self.emu        = Emulator.Emulator()
        self.is_new_pro = False
        self.already_modified = False
        self.tkinter_gui()
        if self.testing:
            self.open_demo_prg()
            self.open_options_win()
        self.root.mainloop()

    def report_callback_exception(self, exc, val, tb): # exc = exception object, val = error message, tb = traceback object
        if exc.__name__ == "Exception": # normal case for Assembly errors caused by user
            self.out_SCT.config(state = "normal", fg = self.theme_error_color)
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.insert("insert", val)
            self.out_SCT.config(state = "disabled")
        else: # special case for internal errors
            if self.testing:
                traceback.print_exception(val)
            else:
                mb.showerror("Internal Error", traceback.format_exception_only(exc, val)[0])

    def tkinter_gui(self):
        self.root = tk.Tk()
        tk.Tk.report_callback_exception = self.report_callback_exception  # overwrite standard Tk method for reporting errors
        self.is_light_theme_VAR = tk.IntVar(   value = int(ph.is_light_theme()))
        self.language_name_VAR  = tk.StringVar(value = lh.gt_lang_name(lh.cur_lang))
        self.code_font_name_VAR = tk.StringVar(value = ph.code_font()[0])
        self.code_font_size_VAR = tk.IntVar(   value = ph.code_font()[1])
        self.min_adr_len_VAR    = tk.IntVar(   value = ph.min_adr_len())
        self.title_font    = ("Segoe", 15, "bold")
        self.subtitle_font = ("Segoe", 13)
        self.set_theme(init = True)
        self.options_WIN   = None
        self.shortcuts_WIN = None
        self.assembly_WIN  = None
        self.about_WIN     = None
        minsize = lh.gui("minsize")
        self.root.minsize(minsize[0], minsize[1])
        self.root.config(bg = self.theme_base_bg)
        self.root.title(lh.gui("title"))
    # style
        self.style = ttk.Style(self.root)
        #self.style.theme_use("winnative")
        self.style.configure("TButton")
        self.style.configure("TFrame",                background = self.theme_base_bg)
        self.style.configure("info.TFrame",           background = self.theme_highlight_base_bg)
        self.style.configure("text.TFrame",           background = self.theme_text_bg)
        self.style.configure("TLabel",                background = self.theme_text_bg,           foreground = self.theme_text_fg)
        self.style.configure("img.TLabel",            background = self.theme_base_bg) # for gui.Button that inherits from ttk.Label
        self.style.configure("info_title.TLabel",     background = self.theme_highlight_base_bg, foreground = self.theme_highlight_text_fg, anchor = "center")
        self.style.configure("info_value.TLabel",     background = self.theme_highlight_text_bg, foreground = self.theme_highlight_text_fg, anchor = "center", font = self.gt_code_font())
        self.style.configure("subtitle.TLabel",       background = self.theme_text_bg,           foreground = self.theme_text_fg, font = self.subtitle_font)
        self.style.configure("TCheckbutton",          background = self.theme_base_bg,           foreground = self.theme_text_fg)  # , relief = "flat", borderwidth = 1)
        self.style.configure("embedded.TCheckbutton", background = self.theme_text_bg,           foreground = self.theme_text_fg)            # , relief = "flat", borderwidth = 1)
    # elements
        self.menubar = tk.Menu(self.root)
        self.root.config(menu = self.menubar)

        self.file_MNU = tk.Menu(self.menubar, tearoff = False)
        self.file_MNU.add_command(label = lh.gui("Open"),     command = self.open_file)
        self.file_MNU.add_command(label = lh.gui("Reload"),   command = self.reload_file)
        self.file_MNU.add_command(label = lh.gui("Save"),     command = self.save_file)
        self.file_MNU.add_command(label = lh.gui("SaveAs"),   command = self.save_file_as)
        self.file_MNU.add_command(label = lh.gui("Options"),  command = self.open_options_win)
        self.file_MNU.add_command(label = lh.gui("Exit"),     command = self.destroy)
        self.menubar.add_cascade(label = lh.gui("File"), menu = self.file_MNU, underline = 0)

        self.help_MNU = tk.Menu(self.menubar, tearoff = False)
        self.help_MNU.add_command(label = lh.gui("Assembly"),  command = self.open_assembly_win)
        self.help_MNU.add_command(label = lh.gui("Shortcuts"), command = self.open_shortcuts_win)
        self.help_MNU.add_command(label = lh.gui("DemoPrg"), command = self.open_demo_prg)
        self.help_MNU.add_command(label = lh.gui("About"),     command = self.open_about_win)
        self.menubar.add_cascade(label = lh.gui("Help"), menu = self.help_MNU, underline = 0)

        self.taskbar_FRM = ttk.Frame(self.root)
        self.taskbar_FRM.pack(fill = "x")

        self.run_BTN = gui.Button(self.taskbar_FRM, style = "img.TLabel", command = self.run_all, img_default = sh.gt_sprite("BTN_run_default"), img_hovering= sh.gt_sprite("BTN_run_hovering"), img_clicked = sh.gt_sprite("BTN_run_clicked"))
        self.run_BTN.pack(side = "left", anchor = "center", padx = (5, 0), pady = 5)
        self.run_TIP = gui.Tooltip(self.run_BTN, text = lh.gui("RunPrg"))

        self.step_BTN = gui.Button(self.taskbar_FRM, style = "img.TLabel", command = self.run_step, img_default = sh.gt_sprite("BTN_run_once_default"), img_hovering= sh.gt_sprite("BTN_run_once_hovering"), img_clicked = sh.gt_sprite("BTN_run_once_clicked"))
        self.step_BTN.pack(side = "left", anchor = "center", padx = (5, 0), pady = 5)
        self.step_TIP = gui.Tooltip(self.step_BTN, text = lh.gui("RunStep"))

        self.incr_BTN = gui.Button(self.taskbar_FRM, style = "img.TLabel", text = "INCR", command = self.change_selected_inp_text)
        self.incr_BTN.pack(side = "left", anchor = "sw", padx = (5, 0), pady = 5)
        self.run_TIP = gui.Tooltip(self.incr_BTN, text = lh.gui("IncrAdrs"))

        self.ireg_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.ireg_title_LBL = ttk.Label(self.ireg_FRM, style = "info_title.TLabel", text = lh.gui("IR:"))
        self.ireg_cmd_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_opr_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_FRM.pack(side = "right", padx = (5, 0), pady = 5)
        self.ireg_title_LBL.grid(row = 0, column = 0, columnspan = 2)
        self.ireg_cmd_LBL.grid(row = 1, column = 0, padx = 1)
        self.ireg_opr_LBL.grid(row = 1, column = 1, padx = 1)

        self.accu_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.accu_title_LBL = ttk.Label(self.accu_FRM, style = "info_title.TLabel", text = lh.gui("ACC:"))
        self.accu_value_LBL = ttk.Label(self.accu_FRM, style = "info_value.TLabel", width = 5)
        self.accu_FRM.pack(side = "right", padx = (5, 0), pady = 5)
        self.accu_title_LBL.pack(side = "top",    fill = "x")
        self.accu_value_LBL.pack(side = "bottom", fill = "x")

        self.prgc_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.prgc_title_LBL = ttk.Label(self.prgc_FRM, style = "info_title.TLabel", text = lh.gui("PC:"))
        self.prgc_value_LBL = ttk.Label(self.prgc_FRM, style ="info_value.TLabel", width = 5)
        self.prgc_FRM.pack(side = "right", padx = (5, 0), pady = 5)
        self.prgc_title_LBL.pack(side = "top",    fill = "x")
        self.prgc_value_LBL.pack(side ="bottom", fill ="x")

        self.text_FRM = ttk.Frame(self.root)
        self.inp_SCT = st.ScrolledText(self.text_FRM, bg = self.theme_text_bg, fg = self.theme_text_fg, bd = 0, width = 10, wrap = "word", font = self.gt_code_font(), insertbackground = self.theme_cursor_color)
        self.out_SCT = st.ScrolledText(self.text_FRM, bg = self.theme_text_bg, fg = self.theme_text_fg, bd = 0, width = 10, wrap = "word", font = self.gt_code_font())
        self.text_FRM.pack(fill = "both", expand = True)
        self.inp_SCT.pack(side = "left",  fill = "both", expand = True, padx = (5, 5), pady = (0, 5))
        self.out_SCT.pack(side = "right", fill = "both", expand = True, padx = (0, 5), pady = (0, 5))
        self.out_SCT.tag_config("pc_is_here", foreground = self.theme_accent_color)
        self.out_SCT.config(state = "disabled")
    # events
        self.root.bind(sequence = "<Control-o>",            func = self.open_file)
        self.root.bind(sequence = "<F5>",                   func = self.run_all)
        self.root.bind(sequence = "<Shift-F5>",             func = self.run_step)
        self.root.bind(sequence = "<Control-r>",            func = self.reload_file)
        self.root.bind(sequence = "<Control-s>",            func = self.save_file)
        self.root.bind(sequence = "<Control-S>",            func = self.save_file_as)
        self.inp_SCT.bind(sequence = "<Return>",            func = self.key_enter)
        self.inp_SCT.bind(sequence = "<Shift-Return>",      func = self.key_shift_enter)
        self.inp_SCT.bind(sequence = "<Control-BackSpace>", func = self.key_ctrl_backspace)
        self.inp_SCT.bind(sequence = "<<Modified>>", func = self.on_inp_modified)
    # protocols
        self.root.protocol(name = "WM_DELETE_WINDOW", func = self.destroy) # when clicking the red x of the window

    def set_theme(self, init = False):
        if self.is_light_theme_VAR.get():
            sh.set_theme(is_light_theme = True)
            self.theme_base_bg = "#DDDDDD"
            self.theme_text_bg = "#FFFFFF"
            self.theme_text_fg = "#000000"
            self.theme_cursor_color = "#222222"
            self.theme_error_color  = "#FF2222"
            self.theme_accent_color = "#00CC00"
            self.theme_highlight_base_bg = "#BBBBFF"
            self.theme_highlight_text_bg = "#CCCCFF"
            self.theme_highlight_text_fg = "#000000"
        else:
            sh.set_theme(is_light_theme = False)
            self.theme_base_bg = "#222222"
            self.theme_text_bg = "#333333"
            self.theme_text_fg = "#FFFFFF"
            self.theme_cursor_color = "#AAAAAA"
            self.theme_error_color  = "#FF5555"
            self.theme_accent_color = "#00FF00"
            self.theme_highlight_base_bg = "#EEEEEE"
            self.theme_highlight_text_bg = "#DDDDDD"
            self.theme_highlight_text_fg = "#000000"
        if not init:
            ph.save_profile_data(key = "is_light_theme", new_value = bool(self.is_light_theme_VAR.get()))
            self.restart_opt_change()

    def set_language(self, new_language_name):
        language = lh.gt_lang(new_language_name)
        ph.save_profile_data(key = "language", new_value = language)
        self.restart_opt_change()

    def update_code_font(self, event = None, win = None):
        if win: # remove focus from code_font_size_SBX
            win.focus()
        ph.save_profile_data(key = "code_font", new_value = (self.code_font_name_VAR.get(), self.code_font_size_VAR.get()))
        self.inp_SCT.config(       font = self.gt_code_font())
        self.out_SCT.config(       font = self.gt_code_font())
        self.ireg_cmd_LBL.config(  font = self.gt_code_font())
        self.ireg_opr_LBL.config(  font = self.gt_code_font())
        self.accu_value_LBL.config(font = self.gt_code_font())
        self.prgc_value_LBL.config(font = self.gt_code_font())
        if self.assembly_WIN:  # restart necessary because unable to access local widget variable text_TXT
            self.close_child_win("self.assembly_WIN")
            self.open_assembly_win()

    def gt_code_font(self):
        return self.code_font_name_VAR.get(), self.code_font_size_VAR.get()

    def update_min_adr_len(self, win = None):
        if win: # remove focus from code_font_size_SBX
            win.focus()
        ph.save_profile_data(key = "min_adr_len", new_value = self.min_adr_len_VAR.get())
        Emulator.update_properties()

    def destroy(self):
        if not self.dirty_flag or self.testing or self.wants_to_save() == True: # "== True" checks if user didn't abort in wants_to_save()
            self.root.destroy()

    def wants_to_save(self):
        is_saving = mb.askyesnocancel(lh.file_mng("UnsavedChanges"), lh.file_mng("Save?")) # returns None when clicking 'Cancel'
        if is_saving:
            self.save_file()
            return not self.dirty_flag # checks if user clicked cancel in save_file_as()
        elif is_saving == None:
            return "abort"
        else:
            return True

    def on_inp_modified(self, event):
        if not self.already_modified: # because somehow on_modified always gets called twice
            self.inp_SCT.edit_modified(False)
            if self.init_inp == self.inp_SCT.get(1.0, "end-1c"): # checks if code got reverted to last saved instance (to avoid pointless wants_to_save()-ing)
                self.set_dirty_flag(False)
            else:
                self.set_dirty_flag(True)
            self.already_modified = True
        else:
            self.already_modified = False

    def set_dirty_flag(self, new_bool):
        if self.dirty_flag != new_bool:
            self.dirty_flag = not self.dirty_flag
            if self.dirty_flag:
                self.root.title("*" + self.root.title())
            else:
                self.root.title(self.root.title()[1:])

    def run(self, execute_all):
        self.prgc_value_LBL.config(text ="")
        self.accu_value_LBL.config(text = "")
        self.ireg_cmd_LBL.config(  text = "")
        self.ireg_opr_LBL.config(  text = "")
        inp = self.inp_SCT.get(1.0, "end-1c")
        if inp:
            out = self.emu.gt_out(inp, execute_all)
            self.prgc_value_LBL.config(text = out[1])
            self.accu_value_LBL.config(text = out[2])
            self.ireg_cmd_LBL.config(  text = out[3][0])
            self.ireg_opr_LBL.config(  text = out[3][1])
            self.out_SCT.config(state = "normal", fg = self.theme_text_fg)
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.insert("insert", out[0][0])
            self.out_SCT.insert("insert", out[0][1], "pc_is_here")
            self.out_SCT.insert("insert", out[0][2])
            self.out_SCT.config(state = "disabled")
        else:
            self.out_SCT.config(state = "normal", fg = self.theme_text_fg)
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.config(state = "disabled")

    def run_all(self, event = None):
        self.run(execute_all = True)

    def run_step(self, event = None):
        self.run(execute_all = False)

    def reload_file(self, event = None):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        if self.file_path:
            self.inp_SCT.delete("1.0", "end")
            with open(self.file_path, "r", encoding = "utf-8") as file:
                self.init_inp = file.read()
            self.inp_SCT.insert("insert", self.init_inp)
            self.set_dirty_flag(False)

    def open_file(self, event = None):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        self.file_path = fd.askopenfilename(title = lh.file_mng("OpenFile"), initialdir = self.last_dir, filetypes = self.file_types)
        if self.file_path:
            self.root.title(self.file_path + " – " + lh.gui("title"))
            file_name = os.path.basename(self.file_path)
            self.last_dir = self.file_path.split(file_name)[0]
            self.set_dirty_flag(False)
            self.reload_file()

    def save_file(self, event = None):
        if self.file_path:
            self.init_inp = self.inp_SCT.get(1.0, "end-1c")
            with open(self.file_path, "w", encoding = "utf-8") as file:
                file.write(self.init_inp)
            self.set_dirty_flag(False)
        else:
            self.save_file_as()

    def save_file_as(self, event = None):
        self.file_path = self.file_path = fd.asksaveasfilename(title = lh.file_mng("SaveFile"), initialdir = self.last_dir, filetypes = self.file_types, defaultextension = ".asm")
        if self.file_path:
            self.save_file()
            self.root.title(self.file_path + " – " + lh.gui("title"))

    def open_options_win(self):
        if self.options_WIN: # set focus on already existing window
            self.set_child_win_focus("self.options_WIN")
            return
        self.options_WIN = tk.Toplevel(self.root)
        self.options_WIN.geometry(lh.opt_win("geometry"))
        self.options_WIN.resizable(False, False)
        self.options_WIN.config(bg = self.theme_base_bg)
        self.options_WIN.title(lh.opt_win("title"))

        options_FRM = ttk.Frame(self.options_WIN, style = "text.TFrame")
        options_FRM.pack(fill="both", expand=True)
        vcmd = (options_FRM.register(self.sbx_input_is_digit)) # used for code_font_size_SBX and min_adr_len_SBX to only allow entered digits
    # appearance
        appearance_subtitle_LBL = ttk.Label(options_FRM, style = "subtitle.TLabel", text = lh.opt_win("Appearance"))
        light_theme_CHB    = ttk.Checkbutton(options_FRM, style = "embedded.TCheckbutton", text = lh.opt_win("LightTheme"), variable = self.is_light_theme_VAR, command = self.set_theme, onvalue = True, offvalue = False)
        if not self.is_light_theme_VAR.get():
            light_theme_CHB.state(["!alternate"])  # deselect the checkbutton
        language_FRM       = ttk.Frame(options_FRM, style = "text.TFrame")
        language_LBL       = ttk.Label(language_FRM, style = "TLabel", text = lh.opt_win("Language"))
        language_MNU       = ttk.OptionMenu(language_FRM, self.language_name_VAR, self.language_name_VAR.get(), *lh.gt_lang_names(), command = self.set_language, style = "TMenubutton")
        code_font_FRM      = ttk.Frame(options_FRM, style = "text.TFrame")
        code_font_LBL      = ttk.Label(code_font_FRM, style = "TLabel", text = lh.opt_win("EditorFont"))
        code_font_size_SBX = ttk.Spinbox(code_font_FRM, textvariable = self.code_font_size_VAR, from_ = 5, to = 30, validate = "all", validatecommand = (vcmd, "%P"), command = self.update_code_font, width = 3, style = "TSpinbox")
        code_font_face_MNU = ttk.OptionMenu(code_font_FRM, self.code_font_name_VAR, self.code_font_name_VAR.get(), *self.gt_fonts(), command = self.update_code_font, style = "TMenubutton")
        appearance_subtitle_LBL.pack(fill = "x", pady = 5, padx = 5)
        light_theme_CHB.pack(   fill = "x",     pady = 5, padx = (20, 5))
        language_FRM.pack(      fill = "x",               padx = (20, 5))
        language_LBL.pack(      side = "left",  pady = 5, padx = (0, 15))
        language_MNU.pack(      side = "right", pady = 5, padx = 5)
        code_font_FRM.pack(     fill = "x",               padx = (20, 5))
        code_font_LBL.pack(     side = "left",  pady = 5, padx = (0, 15))
        code_font_size_SBX.pack(side = "right", pady = 5, padx = 5)
        code_font_face_MNU.pack(side = "right", pady = 5, padx = 5)
    # Assembler
        assembler_subtitle_LBL = ttk.Label(options_FRM, style = "subtitle.TLabel", text = lh.opt_win("Assembler"))
        min_adr_len_FRM = ttk.Frame(options_FRM, style = "text.TFrame")
        min_adr_len_LBL = ttk.Label(min_adr_len_FRM, style = "TLabel", text = lh.opt_win("EditorFont"))
        min_adr_len_SBX = ttk.Spinbox(min_adr_len_FRM, textvariable = self.min_adr_len_VAR, from_ = 1, to = 10, validate = "all", validatecommand = (vcmd, "%P"), command = self.update_min_adr_len, width = 3, style = "TSpinbox")
        assembler_subtitle_LBL.pack(fill = "x", pady = 5, padx = 5)
        min_adr_len_FRM.pack(fill = "x",               padx = (20, 5))
        min_adr_len_LBL.pack(side = "left",  pady = 5, padx = (0, 15))
        min_adr_len_SBX.pack(side = "right", pady = 5, padx = 5)

        code_font_size_SBX.bind(sequence = "<Return>", func = lambda win: self.update_code_font(win = self.options_WIN))
        min_adr_len_SBX.bind(   sequence = "<Return>", func = lambda win: self.update_min_adr_len(self.options_WIN))
        self.set_child_win_focus("self.options_WIN")
        self.options_WIN.protocol("WM_DELETE_WINDOW", lambda: self.close_child_win("self.options_WIN"))

    def restart_opt_change(self):
        print("Save this!\nYou have to restart the program in order to properly apply your changes.")

    def sbx_input_is_digit(self, P): # used for code_font_size_SBX and min_adr_len_SBX to only allow entered digits
        if str.isdigit(P) or P == "":
            return True
        else:
            return False

    def gt_fonts(self):
        fonts = list(fn.families())
        fonts.sort()
        return fonts

    def open_assembly_win(self):
        if self.assembly_WIN: # set focus on already existing window
            self.set_child_win_focus("self.assembly_WIN")
            return
        self.assembly_WIN = tk.Toplevel(self.root)
        minsize = lh.asm_win("minsize")
        self.assembly_WIN.minsize(minsize[0], minsize[1])
        self.assembly_WIN.config(bg = self.theme_base_bg)
        self.assembly_WIN.title(lh.asm_win("title"))

        assembly_FRM = ttk.Frame(self.assembly_WIN, style = "TFrame")
        text_SCB = tk.Scrollbar(assembly_FRM)
        text_TXT = tk.Text(assembly_FRM, bg = self.theme_text_bg, fg = self.theme_text_fg, bd = 5, relief = "flat", wrap = "word", font = ("TkDefaultFont", 10), yscrollcommand = text_SCB.set)
        assembly_FRM.pack(fill = "both", expand = True)
        text_TXT.pack(side = "left",  fill = "both", expand = True)
        text_SCB.pack(side = "right", fill = "y")
        text_TXT.tag_config("asm_code", font = self.gt_code_font())

        text_code_pairs = lh.asm_win("text")
        for text_code_pair in text_code_pairs:
            text_TXT.insert("end", text_code_pair[0])
            text_TXT.insert("end", text_code_pair[1], "asm_code")
        text_SCB.config(command = text_TXT.yview)
        text_TXT.config(state = "disabled")
        self.set_child_win_focus("self.assembly_WIN")
        self.assembly_WIN.protocol("WM_DELETE_WINDOW", lambda: self.close_child_win("self.assembly_WIN"))

    def open_shortcuts_win(self):
        if self.shortcuts_WIN: # set focus on already existing window
            self.set_child_win_focus("self.shortcuts_WIN")
            return
        combos = lh.shc_win("combos")
        actions = lh.shc_win("actions")
        self.shortcuts_WIN = tk.Toplevel(self.root)
        self.shortcuts_WIN.geometry(lh.shc_win("geometry"))
        self.shortcuts_WIN.resizable(False, False)
        self.shortcuts_WIN.config(bg = self.theme_base_bg)
        self.shortcuts_WIN.title(lh.shc_win("title"))

        shortcuts_FRM = ttk.Frame(self.shortcuts_WIN, style = "text.TFrame")
        combos_LBL    = ttk.Label(shortcuts_FRM, style = "TLabel", text = combos,  justify = "left")
        actions_LBL   = ttk.Label(shortcuts_FRM, style = "TLabel", text = actions, justify = "left")
        shortcuts_FRM.pack(fill = "both", expand = True)
        combos_LBL.pack( side = "left",  fill = "both", expand = True, pady = 5, padx = 5)
        actions_LBL.pack(side = "right", fill = "both", expand = True, pady = 5, padx = (0, 5))
        self.set_child_win_focus("self.shortcuts_WIN")
        self.shortcuts_WIN.protocol("WM_DELETE_WINDOW", lambda: self.close_child_win("self.shortcuts_WIN"))

    def open_about_win(self):
        if self.about_WIN: # set focus on already existing window
            self.set_child_win_focus("self.about_WIN")
            return
        self.is_about_win_open = True
        title = lh.gui("title")
        text  = lh.abt_win("text")
        self.about_WIN = tk.Toplevel(self.root)
        self.about_WIN.geometry(lh.abt_win("geometry"))
        self.about_WIN.resizable(False, False)
        self.about_WIN.config(bg = self.theme_base_bg)
        self.about_WIN.title(lh.abt_win("title"))

        about_FRM = ttk.Frame(self.about_WIN, style = "text.TFrame")
        title_LBL = ttk.Label(about_FRM, style = "TLabel", text = title, anchor = "center", justify = "left", font = self.title_font)
        text_LBL  = ttk.Label(about_FRM, style = "TLabel", text = text,  anchor = "w",      justify = "left")
        about_FRM.pack(fill = "both", expand = True)
        title_LBL.pack(fill = "both", expand = True, padx = 5, pady = (5, 0))
        text_LBL.pack( fill = "both", expand = True, padx = 5, pady = (0, 5))
        self.set_child_win_focus("self.about_WIN")
        self.about_WIN.protocol("WM_DELETE_WINDOW", lambda: self.close_child_win("self.about_WIN"))

    def set_child_win_focus(self, win_str):
        eval(win_str + ".focus_force()")
        eval(win_str + ".lift()")
        self.root.update()

    def close_child_win(self, win_str):
        eval(win_str + ".destroy()")
        exec(win_str + " = None")

    def open_demo_prg(self):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        demo = lh.demo()
        self.inp_SCT.delete("1.0", "end")
        self.init_inp = demo
        self.inp_SCT.insert("insert", demo)
        self.set_dirty_flag(False)
        self.root.title(lh.gui("title"))

    def key_enter(self, event):
        self.insert_address()
        return "break" # overwrites the line break printing

    def key_shift_enter(self, event):
        pass # overwrites self.key_enter()

    def key_ctrl_backspace(self, event):
        self.inp_SCT.delete("insert-1c wordstart", "insert wordend")

    def insert_address(self):
        last_line = self.inp_SCT.get("insert linestart", "insert")
        last_line_stripped = last_line.lstrip()
        try:
            last_adr = int(last_line_stripped.split()[0])
        except:
            self.inp_SCT.insert("insert", "\n")
            return
        whitespace_wrapping = last_line.split(last_line_stripped)[0]
        new_adr = self.add_leading_zeros(last_adr + 1)
        self.inp_SCT.insert("insert", "\n" + whitespace_wrapping + new_adr + " ")

    def add_leading_zeros(self, adr):
        adr_str = str(adr)
        if len(adr_str) < Emulator.MIN_ADR_LEN:
            adr_str = (Emulator.MIN_ADR_LEN - len(adr_str)) * "0" + adr_str
        return adr_str

    def change_selected_inp_text(self, change_adrs = True, change_oprs = True, change = 1):
        ranges = self.inp_SCT.tag_ranges("sel")
        if ranges:
            pos_start = self.inp_SCT.index("sel.first")
            pos_end   = self.inp_SCT.index("sel.last")
            text      = self.inp_SCT.get(*ranges)
            new_text  = self.change_text(text, change_adrs, change_oprs, change)
            self.inp_SCT.delete(pos_start, pos_end)
            self.inp_SCT.insert(pos_start, new_text)


    def change_text(self, text, change_adrs = True, change_oprs = True, change = 1):
        lines     = text.split("\n")
        new_text  = ""
        for line in lines:
            cell_comment_pair = line.split(";", maxsplit = 1)
            if len(cell_comment_pair) > 1:
                comment = ";" + cell_comment_pair[1]
            else:
                comment = ""
            cell = cell_comment_pair[0]
            if len(cell):
                if change_adrs:
                    cell = self.change_adr(cell, change)
                if change_oprs:
                    cell = self.change_opr(cell, change)
            new_text += cell + comment + "\n"
        return new_text[0:-1] # 0:-1 to remove line break from last line

    def change_adr(self, cell, change):
        adr_rest_pair = cell.split(maxsplit = 1)
        if len(adr_rest_pair) > 1:
            cell_rest = adr_rest_pair[1]
        else:
            cell_rest = ""
        adr_str = adr_rest_pair[0]
        i = 0
        j = 0
        while i < len(adr_str) and adr_str[i] in string.whitespace:
            i += 1
            j += 1
        while j < len(adr_str) and adr_str[j] in "0123456789":
            j += 1
        old_adr = adr_str[i:j]
        new_adr = int(old_adr) + change
        whitespace_wrapping = adr_str.split(old_adr)
        cell = whitespace_wrapping[0] + self.add_leading_zeros(new_adr) + whitespace_wrapping[1] + " " + cell_rest
        return cell

    def change_opr(self, cell, change):
        toks = cell.split()
        if len(toks) == 3:
            opr_str = toks[2]
            cell_rest = toks[0] + " " + toks[1]
        else:
            return cell
        i = len(opr_str) - 1
        j = len(opr_str) - 1
        while i >= 0 and opr_str[i] in string.whitespace + ")":
            i -= 1
            j -= 1
        while j >= 0 and opr_str[j] in "0123456789":
            j -= 1
        j += 1
        if j - 1 >= 0 and opr_str[j-1] == "#":
            return cell
        if len(opr_str[j:i + 1]):
            old_opr = opr_str[j:i + 1]
            new_opr = int(old_opr) + change
            wrapping = opr_str.split(old_opr)
            cell = cell_rest + " " + wrapping[0] + self.add_leading_zeros(new_opr) + wrapping[1]
        return cell

# TO-DO:
# strg + z
# horizontale SCB, wenn Text in SCT zu lang wird (anstelle von word wrap)
# turn IntVars into BoolVars if necessary
# OPTIONS:
#   reset options (= reset profile)
#   show full error traceback
#   asktosave bei Schließen ausstellbar

# TO-TEST:
# what happens if you only select half of a cell when incrementing operands?

# BUGS:
# error for "05 23 stp" speaks of operands but instead should be talking of allowed number of tokens for value cells
# Kommentare, die eine ganze Zeile besetzen, werden im StepMode mit dem Befehl darüber mitmarkiert
# hold down on gui.Button, drag away from button, drag into button again: button gets executed without displaying img_clicked
# ctrl + del on "09 " deletes "9 "
# change_selected_text() ignores and removes additional whitespaces
# "0 stp \n 01 stp 5" is allowed (+ whole finding-errors-while-executing approach)