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
        self.already_modified = False
        self.build_gui()
        if self.dev_mode: # special startup for developers
            pass
        self.root.mainloop()

    def report_callback_exception(self, exc, val, tb): # exc = exception object, val = error message, tb = traceback object
        if self.dev_mode:
            traceback.print_exception(val)
        if exc.__name__ == "Exception" or self.dev_mode: # Exceptions are Assembly errors caused by user
            self.out_SCT.config(state = "normal", fg = self.theme_error_color)
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.insert("insert", self.format_exception_message(val))
            self.out_SCT.config(state = "disabled")
        else: # internal errors caused by program will be displayed in a window if developer mode isn't enabled
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
        self.change_options_VAR = tk.StringVar() # do not use to get current option as this StringVar is language-dependent; use self.chng_opt_OMN.current_option()
        self.active_theme    = ph.theme() # won't change without restart
        self.active_language = ph.language() # won't change without restart
        self.title_font    = ("Segoe", 15, "bold")
        self.subtitle_font = ("Segoe", 13)
        self.set_theme(theme = self.active_theme)
        self.options_SUB   = sub.Options(editor = self)
        self.shortcuts_SUB = sub.Shortcuts(editor = self)
        self.assembly_SUB  = sub.Assembly(editor = self)
        self.about_SUB     = sub.About(editor = self)
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
        self.style.configure("info_value.TLabel",     background = self.theme_highlight_text_bg, foreground = self.theme_highlight_text_fg, anchor = "center", font = ph.code_font())
        self.style.configure("subtitle.TLabel",       background = self.theme_text_bg,           foreground = self.theme_text_fg, font = self.subtitle_font)
        self.style.configure("TCheckbutton",          background = self.theme_base_bg,           foreground = self.theme_text_fg)  # , relief = "flat", borderwidth = 1)
        self.style.configure("embedded.TCheckbutton", background = self.theme_text_bg,           foreground = self.theme_text_fg)  # , relief = "flat", borderwidth = 1)

    # elements
        self.menubar = tk.Menu(self.root)
        self.root.config(menu = self.menubar)

        self.file_MNU = tk.Menu(self.menubar, tearoff = False)
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
        self.help_MNU.add_command(label = lh.gui("DemoPrg"), command = self.open_demo_prg)
        self.help_MNU.add_command(label = lh.gui("About"),     command = self.about_SUB.open)
        self.menubar.add_cascade(label = lh.gui("Help"), menu = self.help_MNU, underline = 0)

        self.taskbar_FRM = ttk.Frame(self.root)
        self.taskbar_FRM.pack(fill = "x", padx = 5, pady = 5)

        self.run_BTN = wdg.Button(self.taskbar_FRM, style ="img.TLabel", command = self.run_all, img_default = sh.gt_sprite("BTN_run_default"), img_hovering= sh.gt_sprite("BTN_run_hovering"), img_clicked = sh.gt_sprite("BTN_run_clicked"))
        self.run_BTN.pack(side = "left", anchor = "center")
        self.run_TIP = wdg.Tooltip(self.run_BTN, text = lh.gui("RunPrg"))

        self.step_BTN = wdg.Button(self.taskbar_FRM, style ="img.TLabel", command = self.run_step, img_default = sh.gt_sprite("BTN_run_once_default"), img_hovering= sh.gt_sprite("BTN_run_once_hovering"), img_clicked = sh.gt_sprite("BTN_run_once_clicked"))
        self.step_BTN.pack(side = "left", anchor = "center", padx = (5, 0))
        self.step_TIP = wdg.Tooltip(self.step_BTN, text = lh.gui("RunStep"))

        self.chng_FRM = ttk.Frame(self.taskbar_FRM)
        self.incr_BTN = wdg.Button(self.chng_FRM, style ="img.TLabel", command = self.increment_selected_inp_text, img_default = sh.gt_sprite("BTN_increment_default", x = 17, y = 17), img_hovering= sh.gt_sprite("BTN_increment_hovering", x = 17, y = 17), img_clicked = sh.gt_sprite("BTN_increment_clicked", x = 17, y = 17))
        self.decr_BTN = wdg.Button(self.chng_FRM, style ="img.TLabel", command = self.decrement_selected_inp_text, img_default = sh.gt_sprite("BTN_decrement_default", x = 17, y = 17), img_hovering= sh.gt_sprite("BTN_decrement_hovering", x = 17, y = 17), img_clicked = sh.gt_sprite("BTN_decrement_clicked", x = 17, y = 17))
        self.chng_FRM.pack(side = "left", anchor = "center", padx = (5, 0))
        self.incr_BTN.pack()
        self.decr_BTN.pack()
        self.incr_TIP = wdg.Tooltip(self.incr_BTN, text = lh.gui("IncrAdrs"))
        self.decr_TIP = wdg.Tooltip(self.decr_BTN, text = lh.gui("DecrAdrs"))

        self.chng_adjust_FRM = ttk.Frame(self.taskbar_FRM)
        vcmd = self.chng_adjust_FRM.register(self.char_is_digit)
        self.chng_ETR = ttk.Entry(self.chng_adjust_FRM, validate = "key", validatecommand = (vcmd, "%P"), textvariable = self.change_amount_VAR, width = 3)
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

        self.text_FRM = ttk.Frame(self.root)
        self.inp_SCT = st.ScrolledText(self.text_FRM, bg = self.theme_text_bg, fg = self.theme_text_fg, bd = 0, width = 10, wrap = "word", font = ph.code_font(), insertbackground = self.theme_cursor_color)
        self.out_SCT = st.ScrolledText(self.text_FRM, bg = self.theme_text_bg, fg = self.theme_text_fg, bd = 0, width = 10, wrap = "word", font = ph.code_font())
        self.text_FRM.pack(fill = "both", expand = True, padx = 5, pady = (0, 5))
        self.inp_SCT.pack(side = "left",  fill = "both", expand = True, padx = (0, 5))
        self.out_SCT.pack(side = "right", fill = "both", expand = True)
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

    def char_is_digit(self, char): # used by Editor.chng_ETR to only allow entered digits
        return str.isdigit(char) or char == ""

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
        self.inp_SCT.config(       font = ph.code_font())
        self.out_SCT.config(       font = ph.code_font())
        self.ireg_cmd_LBL.config(  font = ph.code_font())
        self.ireg_opr_LBL.config(  font = ph.code_font())
        self.accu_value_LBL.config(font = ph.code_font())
        self.prgc_value_LBL.config(font = ph.code_font())
        self.assembly_SUB.set_code_font()

    def update_incr_decr_tooltips(self, event = None):
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

    def on_inp_modified(self, event):
        if not self.already_modified: # because somehow on_modified always gets called twice
            self.inp_SCT.edit_modified(False)
            if self.init_inp == self.inp_SCT.get(1.0, "end-1c"): # checks if code got reverted to last saved instance (to avoid pointless ask-to-save'ing)
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
                self.root.title(f"*{self.root.title()}")
            else:
                self.root.title(self.root.title()[1:])

    def run(self, execute_all):
        inp = self.inp_SCT.get(1.0, "end-1c")
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

    def run_all(self, event = None):
        self.run(execute_all = True)

    def run_step(self, event = None):
        self.run(execute_all = False)

    def reload_file(self, event = None):
        if self.file_path:
            with open(self.file_path, "r", encoding = "utf-8") as file:
                prg_str = file.read()
            self.open_prg(prg_str = prg_str, win_title = f"{self.file_path} – {lh.gui('title')}")

    def open_file(self, event = None):
        if self.dirty_flag:
            if not self.can_close_unsaved_prg():
                return
        self.file_path = fd.askopenfilename(title = lh.file_mng("OpenFile"), initialdir = self.last_dir, filetypes = self.file_types)
        if self.file_path:
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

    def open_prg(self, prg_str = "", win_title = None):
        if self.dirty_flag:
            if not self.can_close_unsaved_prg():
                return
        self.inp_SCT.delete("1.0", "end")
        self.init_inp = prg_str
        self.inp_SCT.insert("insert", prg_str)
        self.set_dirty_flag(False)
        if not win_title:
            self.root.title(lh.gui("title"))

    def open_demo_prg(self):
        self.open_prg(lh.demo())

    def key_enter(self, event):
        self.insert_address()
        return "break" # overwrites the line break printing

    def key_shift_enter(self, event):
        pass # overwrites self.key_enter()

    def key_ctrl_backspace(self, event):
        if self.inp_SCT.index("insert") != "1.0": # to prevent deleting word after cursor on position 0
            if self.inp_SCT.get("insert-1c", "insert") != "\n": # to prevent deleting the word of the line above
                self.inp_SCT.delete("insert-1c", "insert") # delete potential space before word
            self.inp_SCT.delete("insert-1c wordstart", "insert") # delete word
            return "break"

    def insert_address(self):
        last_line = self.inp_SCT.get("insert linestart", "insert")
        last_line_stripped = last_line.lstrip()
        try:
            last_adr = int(last_line_stripped.split()[0])
        except:
            self.inp_SCT.insert("insert", "\n")
            return
        whitespace_wrapping = last_line.split(last_line_stripped)[0]
        new_adr = emu.add_leading_zeros(str(last_adr + 1))
        self.inp_SCT.insert("insert", "\n" + whitespace_wrapping + new_adr + " ")

    def increment_selected_inp_text(self):
        self.change_selected_inp_text(change = +int(self.change_amount_VAR.get()))

    def decrement_selected_inp_text(self):
        self.change_selected_inp_text(change = -int(self.change_amount_VAR.get()))

    def change_selected_inp_text(self, change):
        option = self.chng_opt_OMN.current_option() # either "adr", "adr_opr", "opr"
        adrs_flag = "adr" in option
        oprs_flag = "opr" in option
        sel_range = self.inp_SCT.tag_ranges("sel")
        if sel_range:
            text = self.inp_SCT.get(*sel_range)
            if text.strip():
                new_text = self.change_text(text, adrs_flag, oprs_flag, change)
                self.inp_SCT.delete(*sel_range)
                self.inp_SCT.insert(sel_range[0], new_text)
                self.select_text(self.inp_SCT, sel_range[0], new_text)

    def select_text(self, text_widget, pos, text):
        text_widget.tag_add("sel", pos, str(pos) + f"+{len(text)}c")

    def change_text(self, text, adrs_flag, oprs_flag, change = 1):
        lines    = text.split("\n")
        new_text = ""
        for line in lines:
            cell, comment = emu.split_cell_at_comment(line)
            if len(cell):
                if adrs_flag:
                    cell = self.change_adr(cell, change)
                if oprs_flag:
                    cell = self.change_opr(cell, change)
            new_text += cell + comment + "\n"
        print(f"new'{new_text}'")
        return new_text[:-1] # :-1 to remove line break from last line

    def change_adr(self, cell, change):
        tok_strs  = emu.Cell.split_cel_str(self = None, cel_str_unstripped = cell)
        cell_rest = "".join(tok_strs[1:])
        adr_str   = tok_strs[0]
        i = 0
        while i < len(adr_str) and adr_str[i] in string.whitespace: # jump over left wrapping
            i += 1
        j = i
        if j < len(adr_str) and adr_str[j] == "-":
            j += 1
        while j < len(adr_str) and adr_str[j] in "0123456789": # find end of address
            j += 1
        if j < len(adr_str) and adr_str[j] not in string.whitespace: # chars after address are not supported
            return cell
        old_adr  = adr_str[i:j]
        if old_adr and old_adr != "-":
            wrapping = adr_str.split(old_adr)
            new_adr  = wrapping[0] + str(int(old_adr) + change) + wrapping[1]
            cell = emu.add_leading_zeros(new_adr) + cell_rest
        return cell

    def change_opr(self, cell, change):
        tok_strs  = emu.Cell.split_cel_str(self = None, cel_str_unstripped = cell)
        cell_rest = "".join(tok_strs[:-1])
        opr_str   = tok_strs[-1]
        i = len(opr_str) - 1
        while i >= 0 and opr_str[i] in string.whitespace:
            i -= 1
        if i >= 0 and opr_str[i] == ")": # indirect address
            i -= 1
            j = i
            while j >= 0 and opr_str[j] in "0123456789":
                j -= 1
            if j >= 0 and opr_str[j] != "-":
                j += 1
            if j > 0 and opr_str[j - 1] != "(":
                return cell
            if j > 1 and opr_str[j - 2] not in string.whitespace: # chars before indirect address are not supported
                return cell
            offset = 1
        else: # direct address
            j = i
            while j >= 0 and opr_str[j] in "0123456789":
                j -= 1
            if j >= 0 and opr_str[j] != "-":
                j += 1
            if j > 0 and opr_str[j - 1] not in string.whitespace: # absolute values or chars before direct address are not supported
                return cell
            offset = 0
        old_opr = opr_str[j:i + 1]
        if old_opr and old_opr != "-":
            wrapping = opr_str.split(old_opr)
            new_opr = wrapping[0][:-1] + str(int(old_opr) + change) + wrapping[1] # [:-1] because of "("
            cell = cell_rest + "(" * offset + emu.add_leading_zeros(new_opr, offset)
        return cell

# TO-DO:
# strg + z
# horizontale SCB, wenn Text in SCT zu lang wird (anstelle von word wrap)
# turn IntVars into BoolVars if necessary
# OPTIONS:
#   last dir fixed or automatic
# rework output coloring

# BUGS:
# change_selected_inp_text adds \n for empty inp or input with empty lines

# SUGGESTIONS
# ALU anzeigen
# (single step) execution scrolls to the top of the prg (option)
# break points for debugging
# farbige markierung der Sprache
# strg + h
# "neu" als Dateioption