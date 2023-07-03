import os
import string
import traceback
import tkinter              as tk
import tkinter.ttk          as ttk
import tkinter.scrolledtext as st
import tkinter.filedialog   as fd
import tkinter.messagebox   as mb
from program.source import Emulator    as emu
from program.source import Widgets     as wdg
from program.source import Subwindows  as sub
from program.source import PackHandler as pck

def startup(profile_dir, root, dev_mode = False):
    global ph
    global lh
    global eh
    global sh
    ph = pck.ProfileHandler(profile_dir)
    lh = pck.LangHandler(ph.language())
    eh = pck.ErrorHandler()
    sh = pck.SpriteHandler(ph.theme())
    emu.startup(profile_handler = ph, error_handler = eh)
    sub.startup(profile_handler = ph, language_handler = lh, emulator = emu)

    ph.save_profile_data("dev_mode", dev_mode)
    ed = Editor(root = root)


class Editor:

    def __init__(self, root):
        self.dev_mode   = ph.dev_mode()
        self.init_inp   = ""
        self.dirty_flag = False
        self.file_path  = None
        self.last_dir   = root
        self.file_types = ((lh.file_mng("AsmFiles"), "*.asm"), (lh.file_mng("TxtFiles"), "*.txt"))
        self.emu        = emu.Emulator()
        self.action_on_closing_unsaved_prg = ph.closing_unsaved()
        self.build_gui()
        if self.dev_mode: # special startup for developers
            pass
        self.root.mainloop()

    def report_callback_exception(self, exc, val, tb): # exc = exception object, val = error message, tb = traceback object
        if self.dev_mode:
            traceback.print_exception(val)
        if exc.__name__ == "Exception" or self.dev_mode: # Exceptions are Assembly errors caused by user
            self.out_CDB.display_error(self.format_exception_message(val))
        else: # internal errors caused by program will be displayed in a small pop-up window if developer mode isn't enabled
            mb.showerror("Internal Error", traceback.format_exception_only(exc, val)[0])

    def format_exception_message(self, val):
        if self.dev_mode: # full traceback
            error_msg = "".join(traceback.format_exception(val))
        else: # only error
            error_msg = str(val)
        if self.emu.prg is None: # program initialisation exception
            self.emu.creating_new_prg_flag = False
            return error_msg
        else: # runtime exception
            return error_msg + eh.prg_state_msg() + str(self.emu.prg)

    def build_gui(self):
        self.root = tk.Tk()
        tk.Tk.report_callback_exception = self.report_callback_exception  # overwrite standard Tk method for reporting errors
        self.change_amount_VAR  = tk.StringVar(value = "1")
        self.change_options_VAR = tk.StringVar() # do not use to get current option as this StringVar is language dependent; use self.chng_opt_OMN.current_option()
        self.active_theme    = ph.theme() # won't change without restart
        self.active_language = ph.language() # won't change without restart
        self.title_font    = ("Segoe", 15, "bold")
        self.subtitle_font = ("Segoe", 13)
        self.set_theme(theme = self.active_theme)
        self.options_SUB   = sub.Options(  editor = self)
        self.shortcuts_SUB = sub.Shortcuts(editor = self)
        self.assembly_SUB  = sub.Assembly( editor = self)
        self.about_SUB     = sub.About(    editor = self)
        self.root.minsize(*lh.gui("minsize"))
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
        self.style.configure("TCheckbutton",          background = self.theme_base_bg,           foreground = self.theme_text_fg) # , relief = "flat", borderwidth = 1)
        self.style.configure("embedded.TCheckbutton", background = self.theme_text_bg,           foreground = self.theme_text_fg) # , relief = "flat", borderwidth = 1)

    # elements
        self.menubar = tk.Menu(self.root)
        self.root.config(menu = self.menubar)

        self.file_MNU = tk.Menu(self.menubar, tearoff = False)
        self.file_MNU.add_command(label = lh.gui("New"),      command = self.open_prg)
        self.file_MNU.add_command(label = lh.gui("Open"),     command = self.open_file)
        self.file_MNU.add_command(label = lh.gui("Reload"),   command = self.reload_file)
        self.file_MNU.add_command(label = lh.gui("Save"),     command = self.save_file)
        self.file_MNU.add_command(label = lh.gui("SaveAs"),   command = self.save_file_as)
        self.file_MNU.add_command(label = lh.gui("Options"),  command = self.options_SUB.open)
        self.file_MNU.add_command(label = lh.gui("Exit"),     command = self.destroy)
        self.menubar.add_cascade(label = lh.gui("File"), menu = self.file_MNU, underline = 0)

        self.help_MNU = tk.Menu(self.menubar, tearoff = False)
        self.help_MNU.add_command(label = lh.gui("Assembly"),  command = self.assembly_SUB.open)
        self.help_MNU.add_command(label = lh.gui("Shortcuts"), command = self.shortcuts_SUB.open)
        self.help_MNU.add_command(label = lh.gui("DemoPrg"),   command = self.open_demo_prg)
        self.help_MNU.add_command(label = lh.gui("About"),     command = self.about_SUB.open)
        self.menubar.add_cascade(label = lh.gui("Help"), menu = self.help_MNU, underline = 0)

        self.taskbar_FRM = ttk.Frame(self.root)
        self.text_FRM    = ttk.Frame(self.root)
        self.taskbar_FRM.pack(fill = "x",    padx = 5, pady = 5)
        self.text_FRM.pack(   fill = "both", padx = 5, pady = (0, 5), expand = True)

        self.inp_CDB = wdg.InpCodeBlock(self.text_FRM, self)
        self.out_CDB = wdg.OutCodeBlock(self.text_FRM, self)
        self.inp_CDB.pack(side = "left",  fill = "both", expand = True, padx = (0, 5))
        self.out_CDB.pack(side = "right", fill = "both", expand = True)

        self.run_BTN = wdg.Button(self.taskbar_FRM, style = "img.TLabel", command = self.run_all, img_default = sh.gt_sprite("BTN_run_default"), img_hovering = sh.gt_sprite("BTN_run_hovering"), img_clicked = sh.gt_sprite("BTN_run_clicked"))
        self.run_BTN.pack(side = "left", anchor = "center")
        self.run_TIP = wdg.Tooltip(self.run_BTN, text = lh.gui("RunPrg"))

        self.step_BTN = wdg.Button(self.taskbar_FRM, style = "img.TLabel", command = self.run_step, img_default = sh.gt_sprite("BTN_run_once_default"), img_hovering = sh.gt_sprite("BTN_run_once_hovering"), img_clicked = sh.gt_sprite("BTN_run_once_clicked"))
        self.step_BTN.pack(side = "left", anchor = "center", padx = (5, 0))
        self.step_TIP = wdg.Tooltip(self.step_BTN, text = lh.gui("RunStep"))

        self.seperator_FRM = tk.Frame(self.taskbar_FRM, width = 2, bg = self.theme_text_bg) # not using ttk.Seperator because width and color can't be customized
        self.seperator_FRM.pack(side = "left", anchor = "center", fill = "y", padx = (5, 0), pady = 3)

        self.chng_FRM = ttk.Frame(self.taskbar_FRM)
        self.incr_BTN = wdg.Button(self.chng_FRM, style = "img.TLabel", command = self.inp_CDB.increment_selected_text, img_default = sh.gt_sprite("BTN_increment_default", x = 17, y = 17), img_hovering = sh.gt_sprite("BTN_increment_hovering", x = 17, y = 17), img_clicked = sh.gt_sprite("BTN_increment_clicked", x = 17, y = 17))
        self.decr_BTN = wdg.Button(self.chng_FRM, style = "img.TLabel", command = self.inp_CDB.decrement_selected_text, img_default = sh.gt_sprite("BTN_decrement_default", x = 17, y = 17), img_hovering = sh.gt_sprite("BTN_decrement_hovering", x = 17, y = 17), img_clicked = sh.gt_sprite("BTN_decrement_clicked", x = 17, y = 17))
        self.chng_FRM.pack(side = "left", anchor = "center", padx = (5, 0))
        self.incr_BTN.pack()
        self.decr_BTN.pack()
        self.incr_TIP = wdg.Tooltip(self.incr_BTN, text = lh.gui("IncrAdrs"))
        self.decr_TIP = wdg.Tooltip(self.decr_BTN, text = lh.gui("DecrAdrs"))

        self.chng_adjust_FRM = ttk.Frame(self.taskbar_FRM)
        vcmd = self.chng_adjust_FRM.register(self.char_is_digit)
        self.chng_ETR = ttk.Entry(self.chng_adjust_FRM, validate = "key", validatecommand = (vcmd, "%P"), textvariable = self.change_amount_VAR, width = 1)
        self.chng_opt_OMN = wdg.OptionMenu(self.chng_adjust_FRM, options = lh.gui("ChngOptions"), default_option = "adr", textvariable = self.change_options_VAR, width = 20, command = self.update_incr_decr_tooltips)
        self.chng_adjust_FRM.pack(side = "left", anchor = "center", padx = (5, 0))
        self.chng_ETR.pack(anchor = "nw")
        self.chng_opt_OMN.pack()

        self.ireg_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.ireg_title_LBL = ttk.Label(self.ireg_FRM, style = "info_title.TLabel", text = lh.gui("IR:"))
        self.ireg_cmd_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_opr_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_FRM.pack(side = "right", padx = (5, 0))
        self.ireg_title_LBL.grid(row = 0, column = 0, columnspan = 2)
        self.ireg_cmd_LBL.grid(row = 1, column = 0, padx = 1)
        self.ireg_opr_LBL.grid(row = 1, column = 1, padx = 1)

        self.accu_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.accu_title_LBL = ttk.Label(self.accu_FRM, style = "info_title.TLabel", text = lh.gui("ACC:"))
        self.accu_value_LBL = ttk.Label(self.accu_FRM, style = "info_value.TLabel", width = 5)
        self.accu_FRM.pack(side = "right", padx = (5, 0))
        self.accu_title_LBL.pack(side = "top",    fill = "x")
        self.accu_value_LBL.pack(side = "bottom", fill = "x")

        self.prgc_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.prgc_title_LBL = ttk.Label(self.prgc_FRM, style = "info_title.TLabel", text = lh.gui("PC:"))
        self.prgc_value_LBL = ttk.Label(self.prgc_FRM, style ="info_value.TLabel", width = 5)
        self.prgc_FRM.pack(side = "right", padx = (5, 0))
        self.prgc_title_LBL.pack(side = "top",    fill = "x")
        self.prgc_value_LBL.pack(side = "bottom", fill = "x")

    # events
        self.root.bind(sequence = "<F5>",                   func = lambda event: self.run_all())
        self.root.bind(sequence = "<Shift-F5>",             func = lambda event: self.run_step())
        self.root.bind(sequence = "<Control-n>",            func = lambda event: self.open_prg())
        self.root.bind(sequence = "<Control-N>",            func = lambda event: self.open_prg()) # double binds necessary due to capslock overwriting lowercase sequence keys
        self.root.bind(sequence = "<Control-o>",            func = lambda event: self.open_file())
        self.root.bind(sequence = "<Control-O>",            func = lambda event: self.open_file())
        self.root.bind(sequence = "<Control-r>",            func = lambda event: self.reload_file())
        self.root.bind(sequence = "<Control-R>",            func = lambda event: self.reload_file())
        self.root.bind(sequence = "<Control-s>",            func = lambda event: self.save_file())
        self.root.bind(sequence = "<Control-S>",            func = lambda event: self.save_file())
        self.root.bind(sequence = "<Control-Shift-s>",      func = lambda event: self.save_file_as())
        self.root.bind(sequence = "<Control-Shift-S>",      func = lambda event: self.save_file_as()) # again: necessary due to capslock
        self.root.bind(sequence = "<Shift-Tab>",            func = lambda event: self.switch_change_option())
        self.root.bind(sequence = "<Shift-MouseWheel>",     func = self.on_shift_mousewheel)

    # protocols
        self.root.protocol(name = "WM_DELETE_WINDOW", func = self.destroy) # when clicking the red x of the window

    def char_is_digit(self, char): # used by Editor.chng_ETR to only allow entered digits
        return str.isdigit(char) or char == ""

    def gt_code_font(self):
        return ph.code_font()

    def set_theme(self, theme):
        if theme == "light":
            sh.set_theme(theme = "light")
            self.theme_base_bg = "#DDDDDD"
            self.theme_text_bg = "#FFFFFF"
            self.theme_text_fg = "#000000"
            self.theme_cursor_color = "#222222"
            self.theme_error_color  = "#FF2222"
            self.theme_accent_color = "#00CC00"
            self.theme_highlight_base_bg = "#BBBBFF"
            self.theme_highlight_text_bg = "#CCCCFF"
            self.theme_highlight_text_fg = "#000000"
        elif theme == "dark":
            sh.set_theme(theme = "dark")
            self.theme_base_bg = "#222222"
            self.theme_text_bg = "#333333"
            self.theme_text_fg = "#FFFFFF"
            self.theme_cursor_color = "#AAAAAA"
            self.theme_error_color  = "#FF5555"
            self.theme_accent_color = "#00FF00"
            self.theme_highlight_base_bg = "#EEEEEE"
            self.theme_highlight_text_bg = "#DDDDDD"
            self.theme_highlight_text_fg = "#000000"

    def update_code_font(self):
        code_font = self.gt_code_font()
        self.inp_CDB.SCT.config(font = code_font)
        self.out_CDB.SCT.config(font = code_font)
        self.ireg_cmd_LBL.config(  font = code_font)
        self.ireg_opr_LBL.config(  font = code_font)
        self.accu_value_LBL.config(font = code_font)
        self.prgc_value_LBL.config(font = code_font)
        self.assembly_SUB.set_code_font()

    def update_incr_decr_tooltips(self):
        option = self.chng_opt_OMN.current_option()  # either "adr", "adr_opr", "opr"
        if option == "adr":
            self.incr_TIP.update_text(lh.gui("IncrAdrs"))
            self.decr_TIP.update_text(lh.gui("DecrAdrs"))
        elif option == "adr_opr":
            self.incr_TIP.update_text(lh.gui("IncrAdrsOprs"))
            self.decr_TIP.update_text(lh.gui("DecrAdrsOprs"))
        elif option == "opr":
            self.incr_TIP.update_text(lh.gui("IncrOprs"))
            self.decr_TIP.update_text(lh.gui("DecrOprs"))

    def destroy(self):
        if not self.dirty_flag or self.dev_mode or self.can_close_unsaved_prg():
            self.root.destroy()

    def can_close_unsaved_prg(self): # returns if it is okay to continue
        if self.action_on_closing_unsaved_prg == "ask":
            is_saving = mb.askyesnocancel(lh.file_mng("UnsavedChanges"), lh.file_mng("Save?")) # returns None when clicking 'Cancel'
            if is_saving:
                self.save_file()
                return not self.dirty_flag # checks if user clicked cancel in save_file_as()
            else:
                return is_saving is not None
        elif self.action_on_closing_unsaved_prg == "save":
            self.save_file()
            return not self.dirty_flag  # checks if user clicked cancel in save_file_as()
        elif self.action_on_closing_unsaved_prg == "discard":
            return True

    def set_dirty_flag(self, new_bool):
        if self.dirty_flag != new_bool:
            self.dirty_flag = not self.dirty_flag
            if self.dirty_flag:
                self.root.title(f"*{self.root.title()}")
            else:
                self.root.title(self.root.title()[1:])

    def run(self, execute_all):
        inp = self.inp_CDB.gt_input()
        out = self.emu.gt_out(inp, execute_all)
        self.prgc_value_LBL.config(text = out[1])
        self.accu_value_LBL.config(text = out[2])
        self.ireg_cmd_LBL.config(  text = out[3][0])
        self.ireg_opr_LBL.config(  text = out[3][1])
        self.out_CDB.display_output(out)

    def run_all(self):
        self.run(execute_all = True)

    def run_step(self):
        self.run(execute_all = False)

    def open_file(self):
        if self.dirty_flag:
            if not self.can_close_unsaved_prg():
                return
        self.file_path = fd.askopenfilename(title = lh.file_mng("OpenFile"), initialdir = self.last_dir, filetypes = self.file_types)
        if self.file_path:
            file_name = os.path.basename(self.file_path)
            self.last_dir = self.file_path.split(file_name)[0]
            self.set_dirty_flag(False)
            self.reload_file()
        return "break"

    def reload_file(self):
        if self.file_path:
            with open(self.file_path, "r", encoding = "utf-8") as file:
                prg_str = file.read()
            self.open_prg(prg_str = prg_str, win_title = f"{self.file_path} – {lh.gui('title')}")

    def save_file(self):
        if self.file_path:
            self.init_inp = self.inp_CDB.gt_input()
            with open(self.file_path, "w", encoding = "utf-8") as file:
                file.write(self.init_inp)
            self.set_dirty_flag(False)
        else:
            self.save_file_as()

    def save_file_as(self):
        self.file_path = self.file_path = fd.asksaveasfilename(title = lh.file_mng("SaveFile"), initialdir = self.last_dir, filetypes = self.file_types, defaultextension = ".asm")
        if self.file_path:
            self.save_file()
            self.root.title(self.file_path + " – " + lh.gui("title"))

    def open_prg(self, prg_str = "", win_title = None):
        if self.dirty_flag:
            if not self.can_close_unsaved_prg():
                return
        self.inp_CDB.st_input(prg_str)
        self.init_inp = prg_str
        self.set_dirty_flag(False)
        if not win_title:
            self.root.title(lh.gui("title"))

    def open_demo_prg(self):
        self.open_prg(lh.demo())

    def on_shift_mousewheel(self, event):
        if event.delta > 0:
            self.inp_CDB.increment_selected_text()
        else:
            self.inp_CDB.decrement_selected_text()

    def switch_change_option(self):
        cur_option = self.chng_opt_OMN.current_option()
        if cur_option == "adr":
            new_option = "adr_opr"
        elif cur_option == "adr_opr":
            new_option = "opr"
        else:
            new_option = "adr"
        self.chng_opt_OMN.st_option(new_option)


# TO-DO:
# OPTIONS:
#   last dir fixed (choose path) or automatic
# rework output coloring

# BUGS:
# will default to save_as() when using save() after aborting one save_as()
# askyesnocancel buttons don't adjust to language

# SUGGESTIONS
# ALU anzeigen
# break points for debugging
# farbige markierung der Sprache
# strg + h