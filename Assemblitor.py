import sys
import os
import string
import traceback
import tkinter              as tk
import tkinter.ttk          as ttk
import tkinter.scrolledtext as st
import tkinter.filedialog   as fd
import tkinter.messagebox   as mb
import lang_handler         as lh

lh = lh.LangHandler()

class Emulator:

    def __init__(self, max_jmps = 8192, max_adrs = 8192):
        self.max_jmps   = max_jmps
        self.max_adrs   = max_adrs
        self.pro_str    = ""
        self.pro        = None
        self.is_new_pro = True

    def gt_out(self, pro_str, execute_all = True):
        if pro_str:
            if self.pro_str != pro_str: # program changed
                self.is_new_pro = True
            if self.is_new_pro:
                self.create_pro(pro_str)
                if not execute_all:  # display first step of program
                    return self.pro.gt_pro(), self.pro.pc, self.pro.accu, self.gt_ireg()
            if len(self.pro.cells) == 0: # program is empty
                return
            self.pro.execute(execute_all)
            if self.pro.gt_cel(self.pro.pc).gt_cmd() == "STP":
                self.is_new_pro = True
            return self.pro.gt_pro(execute_all), self.pro.pc, self.pro.accu, self.gt_ireg()
        else:
            return

    def gt_ireg(self): # current command in instruction register
        cell = self.pro.gt_cel(self.pro.pc)
        return str(cell.gt_cmd()), str(cell.gt_opr().opr_str)

    def create_pro(self, pro_str):
        self.is_new_pro = False
        self.pro_str = pro_str
        self.pro = Program(pro_str, self.max_jmps, self.max_adrs)


class Program:

    def __init__(self, pro_str, max_jmps, max_adrs):
        self.max_adrs = max_adrs
        self.max_jmps = max_jmps
        self.jmps_to_adr = {}  # each element logs how many times the pointer jumped to its cell
        self.top_cmt     = ""
        self.cells       = self.gt_cells(pro_str)
        self.accu        = 0
        self.pc          = 0
        self.executing   = False

    def __str__(self):
        pro_str = self.top_cmt
        for cell in self.cells:
            pro_str += str(cell) + "\n"
        return pro_str

    def gt_pro(self, execute_all = False): # returns a tuple with the executing cell in the middle to colorcode it in the output widget
        pro_str1 = self.top_cmt
        cell_that_is_currently_executed = ""
        pro_str2 = ""
        if not execute_all:
            for cell in self.cells:
                if cell.cpos < self.pc:
                    pro_str1 += str(cell) + "\n"
                elif cell.cpos > self.pc:
                    pro_str2 += str(cell) + "\n"
                else:
                    cell_that_is_currently_executed = str(cell) + "\n"
            return pro_str1, cell_that_is_currently_executed, pro_str2
        else:
            return str(self), "", ""

    def execute(self, execute_all = True):
        if len(self.cells) > 0:
            if execute_all:
                self.start_executing()
                while self.executing:
                    self.execute_cell()
            else:
                if not self.executing:
                    self.start_executing()
                self.execute_cell()

    def start_executing(self):
        self.executing   = True
        self.accu        = 0
        self.pc          = 0
        self.jmps_to_adr.clear()

    def execute_cell(self):
        if self.pc < len(self.cells):
            self.execute_command(self.pc)
            self.pc += 1
        else:
            self.executing = False
            raise SyntaxError("Program was never stopped with command 'STP'.")

    def execute_command(self, adr):
        cmd = self.gt_cel(adr).gt_cmd()
        opr = self.gt_cel(adr).gt_opr()
        eval("self.cmd_" + cmd + "(" + str(opr) + ")")

    def gt_cells(self, pro_str):
        if not pro_str:
            return []
        lines = pro_str.split("\n")
        cells  = []
        for i in range(len(lines)):
            line = lines[i].split(";")
            if len(line) < 2:
                line.append("")
            if len(line[1]) > 0:
                line[1] = ";" + line[1]
            if line[0].strip() == "": # no cell in line
                if len(cells) > 0: # not first line; some empty line in between
                    cells[-1].cmt += "\n" + line[0] + line[1]
                elif i == 0:
                    self.top_cmt = line[0] + line[1]
                    if line[1]:
                        self.top_cmt += "\n"
                else:
                    self.top_cmt += line[0] + line[1] + "\n"
            else:
                cell = Cell(line[0], line[1])
                cells.append(cell)
        cells = self.fill_empty_cells(cells)
        return cells

    def gt_cel(self, adr):
        if adr > self.max_adrs - 1:
            raise Exception("Maximum program length exceeded. Can only have up to " + str(self.max_adrs) + " memory cells, not " + str(adr + 1) + ". This can be adjusted in the settings.")
        while adr >= len(self.cells):
            cell = Cell(str(len(self.cells)) + " ")
            self.cells.append(cell)
        return self.cells[adr]

    def fill_empty_cells(self, cells):
        i = 0
        while i < len(cells):
            adr = cells[i].gt_adr()
            if adr > self.max_adrs - 1:
                raise Exception("Maximum program length exceeded. Can only have up to " + str(self.max_adrs) + " memory cells, not " + str(adr + 1) + ". This can be adjusted in the settings.")
            if i == adr:
                pass
            elif i < adr:
                cell = Cell(str(i) + " ")
                cells.insert(i, cell)
            else:
                if str(cells[adr].toks[1]) == "":
                    raise SyntaxError("Address " + str(adr) + " appears after address " + str(cells[i - 1].gt_adr()) + " even though memory cells have to be in chronological order.")
                else:
                    raise SyntaxError("Address " + str(adr) + " appears more than once even though it has to be unique.")
            i += 1
        return cells

    def gt_adr(self, opr_inf, is_lda = False): # opr_inf = (opr.type, opr.opr)
        typ = opr_inf[0]
        opr = opr_inf[1]
        if typ == 0: # normal address
            return opr
        elif typ == 1: # nested address (e.g. 00 LDA (5))
            return int(self.gt_cel(opr).gt_val())
        elif typ == 2: # value (e.g. 00 LDA #5)
            if is_lda:
                return str(opr)
            else:
                raise SyntaxError("Only command 'LDA' supports #<value> format like '#" + str(opr) + "'.")
        else:
            raise ValueError("Unknown operand: '" + str(opr_inf[1]) + "'.")

    def gt_jmps_to_adr(self, adr):
        if adr in self.jmps_to_adr:
            return self.jmps_to_adr[adr]
        else:
            return 0

    def cmd_LDA(self, opr_inf):
        adr = self.gt_adr(opr_inf, True)
        if type(adr) is str: # value (e.g. 00 LDA #5)
            self.accu = int(adr)
        else: # address (e.g. 00 LDA 05)
            self.accu = self.gt_cel(adr).gt_val()

    def cmd_ADD(self, opr_inf):
        adr = self.gt_adr(opr_inf)
        self.accu += self.gt_cel(adr).gt_val()

    def cmd_STP(self):
        self.pc -= 1
        self.executing = False

    def cmd_SUB(self, opr_inf):
        adr = self.gt_adr(opr_inf)
        self.accu -= self.gt_cel(adr).gt_val()

    def cmd_JMP(self, opr_inf):
        self.pc = self.gt_adr(opr_inf) - 1 # "- 1" because self.pc will increment automatically
        if self.gt_jmps_to_adr(self.gt_adr(opr_inf)) > self.max_jmps:
            raise StopIteration("Maximum iteration depth exceeded. Can only jump up to " + str(self.max_jmps) + " times to memory cell " + str(self.gt_adr(opr_inf)) + ". This can be adjusted in the settings.")
        else:
            self.jmps_to_adr[self.gt_adr(opr_inf)] = self.gt_jmps_to_adr(self.gt_adr(opr_inf)) + 1 # increment jmps_to_adr for this address

    def cmd_JLE(self, opr_inf):
        if self.accu <= 0:
            self.cmd_JMP(opr_inf)

    def cmd_JZE(self, opr_inf):
        if self.accu == 0:
            self.cmd_JMP(opr_inf)

    def cmd_MUL(self, opr_inf):
        adr = self.gt_adr(opr_inf)
        self.accu *= self.gt_cel(adr).gt_val()

    def cmd_STA(self, opr_inf):
        adr = self.gt_adr(opr_inf)
        self.gt_cel(adr).edit(self.accu)


class Cell:

    def __init__(self, cel_str = "", cmt = ""):
        tok_strs  = self.split_cel_str(cel_str)
        self.cpos = None
        self.cmt  = cmt
        self.toks = self.gt_toks(tok_strs)

    def __str__(self):
        cel_str = ""
        for tok in self.toks:
            cel_str += str(tok)
        return cel_str + self.cmt

    def gt_toks(self, tok_strs):
        toks = []
        for tpos in range(len(tok_strs)):
            if len(tok_strs[tpos]) == 0 and tpos > 1: # ignore empty operands
                pass
            elif tpos == 0:
                tok = Token(tok_strs[tpos], tpos)
                self.cpos = tok.gt_adr()
                toks.append(tok)
            else:
                tok = Token(tok_strs[tpos], tpos, self.cpos)
                toks.append(tok)
        return toks

    def split_cel_str(self, cel_str):
        tok_strs = []
        last_split_pos = 0
        for i in range(len(cel_str)):
            if cel_str[i] in string.whitespace and i < len(cel_str) - 1 and cel_str[i+1] not in string.whitespace: #last whitespace between tokens
                if i > 0:
                    tok_str = cel_str[last_split_pos:i+1]
                    tok_strs.append(tok_str)
                    last_split_pos = i + 1
                else:
                    pass
        tok_str = cel_str[last_split_pos:]
        tok_strs.append(tok_str)
        while len(tok_strs) < 3:
            tok_strs.append("")
        return tok_strs

    def edit(self, new_val):
        if type(new_val) is int and new_val >= 0:
            self.toks[1].edit(new_val)
        else:
            raise Exception("Unable to load accumulator value in memory cell " + str(self.gt_adr()) + ". Value must be a nonnegative integer, not '" + str(new_val) + "'.")

    def gt_adr(self):
        return self.toks[0].gt_adr()

    def gt_val(self):
        if self.toks[1].tok == "":
            return 0
        else:
            return self.toks[1].tok

    def gt_cmd(self):
        return self.toks[1].gt_cmd()

    def gt_opr(self):
        if len(self.toks) > 2:
            if self.toks[1].tok == "STP":
                raise SyntaxError("Command 'STP' does not take operands. Please remove operand in memory cell " + str(self.gt_adr()) + ".")
            else:
                return self.toks[2].gt_opr()
        elif self.toks[1].tok == "STP":
            return Operand("", self.cpos)
        else:
            raise SyntaxError("Unable to get operand of memory cell " + str(self.gt_adr()) + ". Command '" + self.gt_cmd() + "' requires an operand.")


class Token:

    def __init__(self, tok_str, tpos, cpos = "NaN"):
        self.cmds    = ["LDA", "ADD", "STP", "SUB", "JMP", "JLE", "JZE", "MUL", "STA"]
        self.tpos    = tpos
        self.cpos    = cpos
        self.tok_str = tok_str
        self.type    = None # 0 = address, 1 = command, 2 = value, 3 = operand
        self.tok     = self.create_tok(self.tok_str)

    def __str__(self):
        if len(self.tok_str) > 0 and self.tok_str[-1] != " ":
            self.tok_str += " "
        return self.add_leading_zero(self.tok_str)

    def create_tok(self, tok_str):
        tok = tok_str.rstrip()
        if self.tpos == 0:
            try:
                tok_int = int(tok.lstrip()) # allow whitespaces before address
            except:
                raise ValueError("Expected an address, not '" + str(tok) + "'. An address of a memory cell has to be a nonnegative integer.")
            if tok_int >= 0:
                self.type = 0
                self.cpos = tok_int
                return tok_int
            else:
                raise ValueError("Expected an address, not '" + str(tok) + "'. An address of a memory cell has to be nonnegative.")
        elif self.tpos == 1:
            try:
                tok_int = int(tok)
            except:
                if tok == "":
                    self.type = 2
                    return 0
                elif tok.upper() in self.cmds:
                    self.type = 1
                    return tok.upper()
                else:
                    raise ValueError("Expected a command or a value in memory cell " + str(self.cpos) + ", not '" + str(tok) + "'.")
            self.type = 2
            return tok_int
        elif self.tpos == 2:
            self.type = 3
            return Operand(tok, self.cpos)
        else:
            raise SyntaxError("Memory cell " + str(self.cpos) + " has too many tokens. A memory cell can only have up to 3 tokens (excluding comments): 1. address, 2. command/value, 3. operand")

    def add_leading_zero(self, tok_str):
        tok_str_stripped = tok_str.strip()
        if self.type == 0 and len(tok_str_stripped) == 1:
            whitespace_wrapping = tok_str.split(tok_str_stripped)
            tok_str = whitespace_wrapping[0] + "0" + tok_str_stripped + whitespace_wrapping[1]
        elif self.type == 3:
            if self.tok.type == 0 and len(tok_str_stripped) == 1: # direct operand (e.g. 00 LDA 5)
                tok_str = "0" + tok_str
            elif self.tok.type == 1 and len(tok_str_stripped) == 3: # indirect operand (e.g. 00 LDA (5))
                tok_str = "(0" + tok_str[1:]                
        return tok_str

    def edit(self, new_val):
        if self.type == 2:
            self.tok = new_val
            i = 0
            while i < len(self.tok_str) and self.tok_str[i] not in string.whitespace:
                i += 1
            self.tok_str = str(self.tok) + self.tok_str[i:]
        else:
            raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be a value, not '" + str(self.tok) + "' while trying to overwrite it to " + str(new_val))

    def gt_cmd(self):
        if self.type == 1:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be a command, not '" + str(self.tok) + "'.")
            else:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be a command but it is empty.")

    def gt_opr(self):
        if self.type == 3:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be an operand, not '" + str(self.tok) + "'.")
            else:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be an operand but it is empty.")

    def gt_adr(self):
        if self.type == 0:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be an address, not '" + str(self.tok) + "'.")
            else:
                raise SyntaxError("Expected token " + str(self.tpos) + " of memory cell " + str(self.cpos) + " to be an address but it is empty.")


class Operand:

    def __init__(self, opr_str, cpos):
        self.cpos = cpos
        if type(opr_str) is str:
            self.opr_str = opr_str
        else:
            raise TypeError("Expected to receive a string, not '" + str(opr_str) + "' while trying to get an operand.")
        self.type = 0 # 0 = direct address, 1 = indirect address, 2 = value
        self.opr = self.create_opr(self.opr_str)

    def create_opr(self, opr_str):
        if len(opr_str) > 0:
            if opr_str[0] == "#":
                try:
                    opr_int = int(opr_str[1:])
                except:
                    raise ValueError("Unknown operand in memory cell " + str(self.cpos) + ": '" + opr_str + "'. The value after # has to be an integer.")
                self.type = 2
                return opr_int
            elif opr_str[0] == "(" and opr_str[-1] == ")":
                try:
                    opr_int = int(opr_str[1:-1])
                except:
                    raise ValueError("Unknown operand in memory cell " + str(self.cpos) + ": '" + opr_str + "'. The address nested into brackets has to be a nonnegative integer.")
                if opr_int >= 0:
                    self.type = 1
                    return opr_int
                else:
                    raise ValueError("Unknown operand in memory cell " + str(self.cpos) + ": '" + opr_str + "'. The address nested into brackets has to be nonnegative.")
            else:
                try:
                    opr_int = int(opr_str)
                except:
                    raise ValueError("Unknown operand in memory cell " + str(self.cpos) + ": '" + opr_str + "'. An operand has to be an address (format '<nonnegative int>' or '(<nonnegative int>)') or an absolute value (format '#<int>').")
                self.type = 0
                return opr_int
        else:
            self.type = None
            return None

    def __str__(self):
        if self.type is None:
            return ""
        else:
            return "(" + str(self.type) + ", " + str(self.opr) + ")"
    

class Editor:

    def __init__(self, testing = False):
        self.init_inp   = ""
        self.dirty_flag = False
        self.file_path  = None
        self.last_dir   = os.path.join(os.path.expanduser('~'), "Documents")
        self.file_types = (("Assembler files", "*.asm"), ("Text files", "*.txt"))
        self.code_font  = ("Courier New", 10)
        self.emu        = Emulator()
        self.is_new_pro = False
        self.already_modified = False
        self.tkinter_gui()
        if testing:
            self.open_demo_pro()
            #self.run()
        self.root.mainloop()

    def report_callback_exception(self, exc, val, tb): # exc = exception object, val = error message, tb = traceback object
        self.out_SCT.config(state = "normal", fg = "#FF5555")
        self.out_SCT.delete("1.0", "end")
        self.out_SCT.insert("insert", traceback.format_exception_only(exc, val)[0])
        self.out_SCT.config(state = "disabled")
        print("".join(traceback.format_exception(exc, val, tb = tb)))

    def tkinter_gui(self):
        self.settings_WIN  = None
        self.shortcuts_WIN = None
        self.assembly_WIN  = None
        self.about_WIN     = False
        self.root = tk.Tk()
        tk.Tk.report_callback_exception = self.report_callback_exception # overwrite standard Tk method for reporting errors
        minsize = lh.gui("minsize")
        self.root.minsize(minsize[0], minsize[1])
        self.root.config(bg = "black")
        self.root.title(lh.gui("title"))
        self.only_one_step = tk.IntVar()
    # styles:
        self.style = ttk.Style(self.root)
        self.style.theme_use("winnative")
        self.style.configure("TButton", relief = "flat", borderwidth = 1)
        self.style.configure("TFrame",            background = "#222222")
        self.style.configure("info.TFrame",       background = "#FFFFFF")
        self.style.configure("text.TFrame",       background = "#333333")
        self.style.configure("TLabel",            background = "#333333", foreground = "#FFFFFF")
        self.style.configure("info_title.TLabel", background = "#EEEEEE", foreground = "#000000", anchor = "center")
        self.style.configure("info_value.TLabel", background = "#DDDDDD", foreground = "#000000", anchor = "center", font = self.code_font)
    # elements
        self.menubar = tk.Menu(self.root)
        self.root.config(menu = self.menubar)

        self.file_MNU = tk.Menu(self.menubar, tearoff = False)
        self.file_MNU.add_command(label = lh.gui("Open"),     command = self.open_file)
        self.file_MNU.add_command(label = lh.gui("Reload"),   command = self.reload_file)
        self.file_MNU.add_command(label = lh.gui("Save"),     command = self.save_file)
        self.file_MNU.add_command(label = lh.gui("SaveAs"),   command = self.save_file_as)
        self.file_MNU.add_command(label = lh.gui("Settings"), command = self.open_settings_win)
        self.file_MNU.add_command(label = lh.gui("Exit"),     command = self.destroy)
        self.menubar.add_cascade(label = lh.gui("File"), menu = self.file_MNU, underline = 0)

        self.help_MNU = tk.Menu(self.menubar, tearoff = False)
        self.help_MNU.add_command(label = lh.gui("Assembly"),  command = self.open_assembly_win)
        self.help_MNU.add_command(label = lh.gui("Shortcuts"), command = self.open_shortcuts_win)
        self.help_MNU.add_command(label = lh.gui("DemoPrg"),   command = self.open_demo_pro)
        self.help_MNU.add_command(label = lh.gui("About"),     command = self.open_about_win)
        self.menubar.add_cascade(label = lh.gui("Help"), menu = self.help_MNU, underline = 0)

        self.taskbar_FRM = ttk.Frame(self.root)
        self.taskbar_FRM.pack(fill = "x")

        self.run_BTN = ttk.Button(self.taskbar_FRM, style = "TButton", text = lh.gui("Run"), command = self.run, width = 5)
        self.run_BTN.pack(side = "left", fill = "y", anchor = "center", padx = 5, pady = 5)

        self.step_CHB = ttk.Checkbutton(self.taskbar_FRM, text = lh.gui("StepMode"), variable = self.only_one_step, command = self.reset_pro, onvalue = True, offvalue = False)
        self.step_CHB.pack(side = "left", fill = "y", anchor = "center", padx = 5, pady = 5)
        self.step_CHB.state(["!alternate"]) # deselect the checkbutton

        self.ireg_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.ireg_FRM.pack(side = "right", padx = 5, pady = 5)
        self.ireg_title_LBL = ttk.Label(self.ireg_FRM, style = "info_title.TLabel", text = lh.gui("IR:"))
        self.ireg_cmd_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_opr_LBL   = ttk.Label(self.ireg_FRM, style = "info_value.TLabel", width = 6)
        self.ireg_title_LBL.grid(row = 0, column = 0, columnspan = 2)
        self.ireg_cmd_LBL.grid(row = 1, column = 0, padx = 1)
        self.ireg_opr_LBL.grid(row = 1, column = 1, padx = 1)

        self.accu_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.accu_FRM.pack(side = "right", padx = 5, pady = 5)
        self.accu_title_LBL = ttk.Label(self.accu_FRM, style = "info_title.TLabel", text = lh.gui("ACC:"))
        self.accu_value_LBL = ttk.Label(self.accu_FRM, style = "info_value.TLabel", width = 5)
        self.accu_title_LBL.pack(side = "top",    fill = "x")
        self.accu_value_LBL.pack(side = "bottom", fill = "x")

        self.proc_FRM = ttk.Frame(self.taskbar_FRM, style = "info.TFrame")
        self.proc_FRM.pack(side = "right", padx = 5, pady = 5)
        self.proc_title_LBL = ttk.Label(self.proc_FRM, style = "info_title.TLabel", text = lh.gui("PC:"))
        self.proc_value_LBL = ttk.Label(self.proc_FRM, style = "info_value.TLabel", width = 5)
        self.proc_title_LBL.pack(side = "top",    fill = "x")
        self.proc_value_LBL.pack(side = "bottom", fill = "x")

        self.text_FRM = ttk.Frame(self.root)
        self.text_FRM.pack(fill = "both", expand = True)
        self.inp_SCT = st.ScrolledText(self.text_FRM, bg = "#333333", fg = "white", bd = 0, width = 10, wrap = "word", insertbackground = "#AAAAAA", font = self.code_font)
        self.out_SCT = st.ScrolledText(self.text_FRM, bg = "#333333", fg = "white", bd = 0, width = 10, wrap = "word")
        self.inp_SCT.pack(side = "left",  fill = "both", expand = True, padx = (5, 5), pady = (0, 5))
        self.out_SCT.pack(side = "right", fill = "both", expand = True, padx = (0, 5), pady = (0, 5))
        self.out_SCT.tag_config("pc_is_here", foreground = "#00FF00")
        self.out_SCT.config(state = "disabled")
    # events
        self.root.bind(sequence = "<Control-o>",            func = self.open_file)
        self.root.bind(sequence = "<F5>",                   func = self.reload_file)
        self.root.bind(sequence = "<Control-s>",            func = self.save_file)
        self.root.bind(sequence = "<Control-S>",            func = self.save_file_as)
        self.inp_SCT.bind(sequence = "<Return>",            func = self.key_enter)
        self.inp_SCT.bind(sequence = "<Shift-Return>",      func = self.key_shift_enter)
        self.inp_SCT.bind(sequence = "<Control-Return>",    func = self.key_ctrl_enter)
        self.inp_SCT.bind(sequence = "<Control-BackSpace>", func = self.key_ctrl_backspace)
        self.inp_SCT.bind(sequence = "<<Modified>>",        func = self.on_modified)
    # protocols
        self.root.protocol(name = "WM_DELETE_WINDOW", func = self.destroy) # when clicking the red x of the window

    def wants_to_save(self):
        is_saving = mb.askyesnocancel("Unsaved Changes", "Save program before exiting?") # returns None when clicking 'Cancel'
        if is_saving:
            self.save_file()
            return not self.dirty_flag # checks if user clicked cancel in save_file_as()
        elif is_saving == None:
            return "abort"
        else:
            return True

    def destroy(self):
        if not self.dirty_flag or self.inp_SCT.get(1.0, "end-1c").strip() == "":
            self.root.destroy()
        elif self.wants_to_save() == True: # checks if user didn't abort in wants_to_save()
            self.root.destroy()

    def on_modified(self, event):
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

    def reset_pro(self):
        self.emu.is_new_pro = True

    def run(self):
        self.proc_value_LBL.config(text = "")
        self.accu_value_LBL.config(text = "")
        self.ireg_cmd_LBL.config(text   = "")
        self.ireg_opr_LBL.config(text   = "")
        is_only_one_step = self.only_one_step.get()
        inp = self.inp_SCT.get(1.0, "end-1c")
        out = self.emu.gt_out(inp, not is_only_one_step)
        if out:
            self.proc_value_LBL.config(text = str(out[1]))
            self.accu_value_LBL.config(text = str(out[2]))
            self.ireg_cmd_LBL.config(text   = out[3][0])
            self.ireg_opr_LBL.config(text   = out[3][1])
            self.out_SCT.config(state = "normal", fg = "#FFFFFF")
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.insert("insert", out[0][0])
            self.out_SCT.insert("insert", out[0][1], "pc_is_here")
            self.out_SCT.insert("insert", out[0][2])
            self.out_SCT.config(state = "disabled")
        else:
            self.out_SCT.config(state = "normal", fg = "#FFFFFF")
            self.out_SCT.delete("1.0", "end")
            self.out_SCT.config(state = "disabled")

    def reload_file(self, event = None):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        if self.file_path:
            self.inp_SCT.delete("1.0", "end")
            with open(self.file_path, "r") as file:
                self.init_inp = file.read()
            self.inp_SCT.insert("insert", self.init_inp)
            self.set_dirty_flag(False)

    def open_file(self, event = None):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        self.file_path = fd.askopenfilename(title = "Open File", initialdir = self.last_dir, filetypes = self.file_types)
        if self.file_path:
            self.root.title(self.file_path + " – " + lh.gui("title"))
            file_name = os.path.basename(self.file_path)
            self.last_dir = self.file_path.split(file_name)[0]
            self.set_dirty_flag(False)
            self.reload_file()

    def save_file(self, event = None):
        if self.file_path:
            self.init_inp = self.inp_SCT.get(1.0, "end-1c")
            with open(self.file_path, "w") as file:
                file.write(self.init_inp)
            self.set_dirty_flag(False)
        else:
            self.save_file_as()

    def save_file_as(self, event = None):
        self.file_path = self.file_path = fd.asksaveasfilename(title = "Save File", initialdir = self.last_dir, filetypes = self.file_types, defaultextension = ".asm")
        if self.file_path:
            self.save_file()
            self.root.title(self.file_path + " – " + lh.gui("title"))

    def open_settings_win(self):
        pass

    def open_assembly_win(self):
        if self.assembly_WIN:
            return
        self.assembly_WIN = tk.Toplevel(self.root)
        minsize = lh.asm_win("minsize")
        self.assembly_WIN.minsize(minsize[0], minsize[1])
        self.assembly_WIN.config(bg = "black")
        self.assembly_WIN.title(lh.asm_win("title"))

        assembly_FRM = ttk.Frame(self.assembly_WIN, style = "TFrame")
        text_SCB = tk.Scrollbar(assembly_FRM)
        text_TXT = tk.Text(assembly_FRM, bg = "#333333", fg = "white", bd = 5, relief = "flat", wrap = "word", font = ("TkDefaultFont", 10), yscrollcommand = text_SCB.set)
        assembly_FRM.pack(fill = "both", expand = True)
        text_TXT.pack(side = "left",  fill = "both", expand = True)
        text_SCB.pack(side = "right", fill = "y")
        text_TXT.tag_config("asm_code", font = self.code_font)

        text_code_pairs = lh.asm_win("text")
        for text_code_pair in text_code_pairs:
            text_TXT.insert("end", text_code_pair[0])
            text_TXT.insert("end", text_code_pair[1], "asm_code")
        text_SCB.config(command = text_TXT.yview)
        text_TXT.config(state = "disabled")
        self.assembly_WIN.protocol("WM_DELETE_WINDOW", lambda: self.on_child_win_close("self.assembly_WIN"))

    def open_shortcuts_win(self):
        if self.shortcuts_WIN:
            return
        combos = lh.shc_win("combos")
        actions = lh.shc_win("actions")
        self.shortcuts_WIN = tk.Toplevel(self.root)
        self.shortcuts_WIN.geometry(lh.shc_win("geometry"))
        self.shortcuts_WIN.resizable(False, False)
        self.shortcuts_WIN.config(bg = "black")
        self.shortcuts_WIN.title(lh.shc_win("title"))

        shortcuts_FRM = ttk.Frame(self.shortcuts_WIN, style = "text.TFrame")
        combos_LBL    = ttk.Label(shortcuts_FRM, style = "TLabel", text = combos,  justify = "left")
        actions_LBL   = ttk.Label(shortcuts_FRM, style = "TLabel", text = actions, justify = "left")
        shortcuts_FRM.pack(fill = "both", expand = True)
        combos_LBL.pack( side = "left",  fill = "both", expand = True, pady = 5, padx = 5)
        actions_LBL.pack(side = "right", fill = "both", expand = True, pady = 5, padx = (0, 5))
        self.shortcuts_WIN.protocol("WM_DELETE_WINDOW", lambda: self.on_child_win_close("self.shortcuts_WIN"))

    def open_about_win(self):
        if self.about_WIN:
            return
        self.is_about_win_open = True
        title = lh.gui("title")
        text  = lh.abt_win("text")
        self.about_WIN = tk.Toplevel(self.root)
        self.about_WIN.geometry(lh.abt_win("geometry"))
        self.about_WIN.resizable(False, False)
        self.about_WIN.config(bg = "black")
        self.about_WIN.title(lh.abt_win("title"))

        about_FRM = ttk.Frame(self.about_WIN, style = "text.TFrame")
        title_LBL = ttk.Label(about_FRM, style = "TLabel", text = title, anchor = "center", justify = "left", font = ("Segoe", 15, "bold"))
        text_LBL  = ttk.Label(about_FRM, style = "TLabel", text = text,  anchor = "w",      justify = "left")
        about_FRM.pack(fill = "both", expand = True)
        title_LBL.pack(fill = "both", expand = True, padx = 5, pady = (5, 0))
        text_LBL.pack( fill = "both", expand = True, padx = 5, pady = (0, 5))
        self.about_WIN.protocol("WM_DELETE_WINDOW", lambda: self.on_child_win_close("self.about_WIN"))

    def on_child_win_close(self, win_str):
        eval(win_str + ".destroy()")
        exec(win_str + " = None")

    def open_demo_pro(self):
        if self.dirty_flag:
            if self.wants_to_save() == "abort":
                return
        demo = lh.demo()
        self.inp_SCT.delete("1.0", "end")
        self.init_inp = demo
        self.inp_SCT.insert("insert", demo)

    def key_enter(self, event):
        self.insert_address()
        print(self.inp_SCT.get("end-1c", "end"))
        return "break" # overwrites the line break printing

    def key_shift_enter(self, event):
        pass # overwrites self.key_enter()

    def key_ctrl_enter(self, event):
        self.run()
        return "break" # overwrites the line break printing

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
        new_adr  = str(last_adr + 1)
        if len(new_adr) == 1: # add leading zero
            new_adr = "0" + new_adr
        self.inp_SCT.insert("insert", "\n" + whitespace_wrapping + new_adr + " ")

# TO-DO:
# bei Adressverschiebung alle Adressen anpassen
# strg + z
# horizontale SCB, wenn Text in SCT zu lang wird (anstelle von word wrap)
# SETTINGS:
#   Exception optional in Konsole ausgeben
#   Anzahl Vornullen (Editor.insert_address())
#   asktosave bei Schließen ausstellbar
#   light mode
#   Deutsch (auch Errors?)

# BUGS:
# error for "05 23 stp" speaks of operands but instead should be talking of allowed number of tokens for value cells
# ctrl + enter is printing \n if code has an error (because error occurs before "break "return"" can be executed)
# run() spuckt verschiedene Fehler beim 1. und 2. Mal aus

min_version = (3, 10)
cur_version = sys.version_info

if cur_version >= min_version:
    ed = Editor(testing = True)
else:
    root = tk.Tk()
    root.withdraw()
    title_text_pair = lh.error("PythonVer", min_ver = str(min_version[0]) + "." + str(min_version[1]))
    mb.showerror(title_text_pair[0], title_text_pair[1])