import sys
import os
import string
import traceback
import tkinter              as tk
import tkinter.scrolledtext as st
import tkinter.filedialog   as fd
import tkinter.messagebox   as mb


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
                if len(cells) > 0: # not first line = some empty line in between
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
            if cel_str[i] in string.whitespace and i < len(cel_str) - 1 and cel_str[i+1] not in string.whitespace: # split at last whitespace between tokens
                tok_str = cel_str[last_split_pos:i] + cel_str[i]
                tok_strs.append(tok_str)
                last_split_pos = i + 1
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
                tok_int = int(tok)
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
        if self.type == 0 and len(self.tok_str.strip()) == 1:
            tok_str = "0" + tok_str
        elif self.type == 3:
            if self.tok.type == 0 and len(self.tok_str.strip()) == 1: # direct operand (e.g. 00 LDA 5)
                tok_str = "0" + tok_str
            elif self.tok.type == 1 and len(self.tok_str.strip()) == 3: # indirect operand (e.g. 00 LDA (5))
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

    def __init__(self, test_str = ""):
        self.is_saved   = False
        self.file_path  = None
        self.last_dir   = os.path.join(os.path.expanduser('~'), "Documents")
        self.file_types = (("Assembler files", "*.asm"), ("Text files", "*.txt"))
        self.code_font  = ("Courier New", 10)
        self.emu        = Emulator()
        self.is_new_pro = False
        self.tkinter_gui()
        if test_str != "":
            self.inp_SCT.insert(tk.INSERT, test_str)
            self.run()
        self.root.mainloop()

    def report_callback_exception(self, exc, val, tb): # exc = exception object, val = error message, tb = traceback object
        self.out_SCT.configure(state = "normal", fg = "#FF5555")
        self.out_SCT.delete("1.0", tk.END)
        self.out_SCT.insert(tk.INSERT, traceback.format_exception_only(exc, val)[0])
        self.out_SCT.configure(state = "disabled")

    def tkinter_gui(self):
        self.settings_WIN  = None
        self.shortcuts_WIN = None
        self.assembly_WIN  = None
        self.about_WIN     = False
        self.root = tk.Tk()
        #tk.Tk.report_callback_exception = self.report_callback_exception # overwrite standard Tk method for reporting errors
        self.root.minsize(642, 500)
        self.root.config(bg = "black")
        self.root.title("Assemblitor")
        self.only_one_step = tk.IntVar()
    # elements
        self.menubar = tk.Menu(self.root)
        self.root.config(menu = self.menubar)

        self.file_MNU = tk.Menu(self.menubar, tearoff = False)
        self.file_MNU.add_command(label = "Open",     command = self.open_file)
        self.file_MNU.add_command(label = "Reload",   command = self.reload_file)
        self.file_MNU.add_command(label = "Save",     command = self.save_file)
        self.file_MNU.add_command(label = "Save As",  command = self.save_file_as)
        self.file_MNU.add_command(label = "Settings", command = self.open_settings_win)
        self.file_MNU.add_command(label = "Exit",     command = self.exit)
        self.menubar.add_cascade(label = "File", menu = self.file_MNU, underline = 0)

        self.help_MNU = tk.Menu(self.menubar, tearoff = False)
        self.help_MNU.add_command(label = "Assembly",     command = self.open_assembly_win)
        self.help_MNU.add_command(label = "Shortcuts",    command = self.open_shortcuts_win)
        self.help_MNU.add_command(label = "Demo Program", command = self.open_demo_pro)
        self.help_MNU.add_command(label = "About",        command = self.open_about_win)
        self.menubar.add_cascade(label = "Help", menu = self.help_MNU, underline = 0)

        self.taskbar_FRM = tk.Frame(self.root, bg = "#222222")
        self.taskbar_FRM.pack(fill = "x")

        self.run_BTN = tk.Button(self.taskbar_FRM, text = "Run", command = self.run, width = 5)
        self.run_BTN.pack(side = tk.LEFT, fill = "y", anchor = "n", padx = 5, pady = 5)

        self.step_CHB = tk.Checkbutton(self.taskbar_FRM, text = "Step-By-Step Mode", variable = self.only_one_step, command = self.reset_pro, onvalue = True, offvalue = False)
        self.step_CHB.pack(side = tk.LEFT, fill = "y", anchor = "n", padx = 5, pady = 5)
        self.step_CHB.deselect()

        self.ireg_FRM = tk.Frame(self.taskbar_FRM, bg = "white")
        self.ireg_FRM.pack(side = tk.RIGHT, padx = 5, pady = 5)
        self.ireg_title_LBL = tk.Label(self.ireg_FRM, bg = "#EEEEEE", fg = "black", text = "Instruction Register:")
        self.ireg_cmd_LBL   = tk.Label(self.ireg_FRM, bg = "#DDDDDD", fg = "black", font = self.code_font, width = 6)
        self.ireg_opr_LBL   = tk.Label(self.ireg_FRM, bg = "#DDDDDD", fg = "black", font = self.code_font, width = 6)
        self.ireg_title_LBL.grid(row = 0, column = 0, columnspan = 2)
        self.ireg_cmd_LBL.grid(row = 1, column = 0, padx = 1)
        self.ireg_opr_LBL.grid(row = 1, column = 1, padx = 1)

        self.accu_FRM = tk.Frame(self.taskbar_FRM, bg = "white")
        self.accu_FRM.pack(side = tk.RIGHT, padx = 5, pady = 5)
        self.accu_title_LBL = tk.Label(self.accu_FRM, bg = "#EEEEEE", fg = "black", text = "Accumulator:")
        self.accu_value_LBL = tk.Label(self.accu_FRM, bg = "#DDDDDD", fg = "black", font = self.code_font, width = 5)
        self.accu_title_LBL.pack(side = tk.TOP,    fill = "x")
        self.accu_value_LBL.pack(side = tk.BOTTOM, fill = "x")

        self.proc_FRM = tk.Frame(self.taskbar_FRM, bg = "white")
        self.proc_FRM.pack(side = tk.RIGHT, padx = 5, pady = 5)
        self.proc_title_LBL = tk.Label(self.proc_FRM, bg = "#EEEEEE", fg = "black", text = "Program Counter:")
        self.proc_value_LBL = tk.Label(self.proc_FRM, bg = "#DDDDDD", fg = "black", font = self.code_font, width = 5)
        self.proc_title_LBL.pack(side = tk.TOP,    fill = "x")
        self.proc_value_LBL.pack(side = tk.BOTTOM, fill = "x")

        self.text_FRM = tk.Frame(self.root, bg = "#222222")
        self.text_FRM.pack(fill = "both", expand = True)
        self.inp_SCT = st.ScrolledText(self.text_FRM, bg = "#333333", fg = "white", width = 10, wrap = "word", insertbackground = "#AAAAAA", font = self.code_font)
        self.out_SCT = st.ScrolledText(self.text_FRM, bg = "#333333", fg = "white", width = 10, wrap = "word")
        self.inp_SCT.pack(side = tk.LEFT,  fill = "both", expand = True, padx = 5)
        self.out_SCT.pack(side = tk.RIGHT, fill = "both", expand = True, padx = 5)
        self.out_SCT.tag_configure("pc_is_here", foreground = "#00FF00")
        self.out_SCT.configure(state = "disabled")
    # events
        self.root.bind(sequence = "<Return>",         func = self.key_enter)
        self.root.bind(sequence = "<Shift-Return>",   func = self.key_shift_enter)
        self.root.bind(sequence = "<Control-Return>", func = self.key_ctrl_enter)
        self.root.bind(sequence = "<Control-o>",      func = self.open_file)
        self.root.bind(sequence = "<F5>",             func = self.reload_file)
        self.root.bind(sequence = "<Control-s>",      func = self.save_file)
        self.root.bind(sequence = "<Control-S>",      func = self.save_file_as)
        self.inp_SCT.bind(sequence="<Key>",           func = self.writing)
    # protocols
        self.root.protocol(name = "WM_DELETE_WINDOW", func = self.exit) # when clicking the red x of the window

    def exit(self):
        if self.is_saved or self.inp_SCT.get(1.0, "end-1c").strip() == "":
            self.root.destroy()
        else:
            is_saving = mb.askyesnocancel("Unsaved Changes", "Save program before exiting?") # returns None when clicking 'Cancel'
            if is_saving:
                self.save_file()
                self.root.destroy()
            elif is_saving == False:
                self.root.destroy()

    def writing(self, event = None):
        if self.is_saved:
            self.is_saved = False
            print(self.root.title())
            self.root.title("*" + self.root.title())

    def reset_pro(self):
        self.emu.is_new_pro = True

    def run(self):
        is_only_one_step = self.only_one_step.get()
        pro_str = self.inp_SCT.get(1.0, "end-1c")
        out = self.emu.gt_out(pro_str, not is_only_one_step)
        if out:
            self.proc_value_LBL.configure(text = str(out[1]))
            self.accu_value_LBL.configure(text = str(out[2]))
            self.ireg_cmd_LBL.configure(text   = out[3][0])
            self.ireg_opr_LBL.configure(text   = out[3][1])
            self.out_SCT.configure(state = "normal", fg = "#FFFFFF")
            self.out_SCT.delete("1.0", tk.END)
            self.out_SCT.insert(tk.INSERT, out[0][0])
            self.out_SCT.insert(tk.INSERT, out[0][1], "pc_is_here")
            self.out_SCT.insert(tk.INSERT, out[0][2])
            self.out_SCT.configure(state = "disabled")
        else:
            self.out_SCT.configure(state = "normal", fg = "#FFFFFF")
            self.out_SCT.delete("1.0", tk.END)
            self.out_SCT.configure(state = "disabled")

    def reload_file(self, event = None):
        if self.file_path:
            self.inp_SCT.delete("1.0", tk.END)
            self.inp_SCT.insert(tk.INSERT, open(self.file_path).read())
            if not self.is_saved:
                self.is_saved = True
                self.root.title(self.root.title()[1:])

    def open_file(self, file_path = None, event = None):
        if file_path:
            self.file_path = file_path
        else:
            self.file_path = fd.askopenfilename(title = "Open File", initialdir = self.last_dir, filetypes = self.file_types)
        print(self.file_path)
        if self.file_path:
            self.root.title(self.file_path + " – Assemblitor")
            file_name = os.path.basename(self.file_path)
            self.last_dir = self.file_path.split(file_name)[0]
            self.is_saved = True
            self.reload_file()

    def save_file(self, event = None):
        if self.file_path:
            file = open(self.file_path, "w")
            file.write(self.inp_SCT.get(1.0, "end-1c"))
            file.close()
            if not self.is_saved:
                self.is_saved = True
                self.root.title(self.root.title()[1:])
        else:
            self.save_file_as()

    def save_file_as(self, event = None):
        self.file_path = self.file_path = fd.asksaveasfilename(title = "Save File", initialdir = self.last_dir, filetypes = self.file_types, defaultextension = ".asm")
        self.root.title(self.file_path + " – Assemblitor")
        if self.file_path:
            self.save_file()

    def open_settings_win(self):
        pass

    def open_assembly_win(self):
        if self.assembly_WIN:
            return
        text1 = """[Assembly Dialect] is a very low-level column-oriented programming language that is close to machine code. It is not case sensitive.

It consists of a sequence of 'memory cells' that can store values or commands. Each memory cell starts with its address and ends with a line break. The memory cells have to be in increasing order but empty memory cells don't have to be displayed. A value has to be stored after the address as an integer. An empty memory cell will be interpreted as having a value of 0. A command is also stored after the address. There are many commands and some of them require operands to work.
Comments can be made with a semicolon. All text between the semicolon and the next line break will be ignored by the computer.

The program orients itself to the architecture of a Von-Neumann processor. This means it takes usage of the program counter (PC), the accumulator (ACC) and the instruction register (IR). The PC is set to 0 by default. If the program is executed, the command at the address stored in the PC will be loaded into the IR. There the command can be executed. After its execution the PC gets increased by one (excluding jumps and stops) and the next command can be loaded.


A simple program may look like this:
<code>
    00 LDA 04 ; load the value of the 4th memory cell into the ACC
    01 STA 05 ; store the value of the ACC into the 5th memory cell
    02 STP    ; stop the program
    04 42     ; a stored value
</code>
    
This would be the result after executing the program:
<code>
    00 LDA 04
    01 STA 05
    02 STP 
    03        ; <--- Notice how the formerly hidden 3rd memory cell is now displayed
    04 42
    05 42
</code>
"""
        text2 = "\n\nA list of all accepted commands:\n"
        text3 = """    STP     - stops the program
    LDA n   - loads the value at memory cell n into the ACC
    LDA #n  - loads the value n into the ACC
    LDA (n) - loads the value of the memory cell that has the address that is stored in memory cell n
    STA n   - stores the value of the ACC into memory cell n
    ADD n   - adds the value at memory cell n to the value of the ACC and stores the result into the ACC
    SUB n   - subtracts the value at memory cell n from the value of the ACC and stores the result into the ACC
    MUL n   - multiplies the value at memory cell n by the value of the ACC and stores the result into the ACC
    JMP n   - jumps to memory cell n by setting the PC to n
    JZE n   - jumps to memory cell n by setting the PC to n if the value of the ACC is equal to zero
    JLE n   - jumps to memory cell n by setting the PC to n if the value of the ACC is less or equal to zero"""

        self.assembly_WIN = tk.Toplevel(self.root)
        self.assembly_WIN.minsize(710, 200)
        self.assembly_WIN.config(bg = "black")
        self.assembly_WIN.title("Assembly")

        assembly_FRM = tk.Frame(self.assembly_WIN, bg = "#222222", bd = 5)
        text_SCB = tk.Scrollbar(assembly_FRM)
        text_TXT = tk.Text(assembly_FRM, bg = "#333333", fg = "white", bd = 0, wrap = tk.WORD, font = ("TkDefaultFont", 10), yscrollcommand = text_SCB.set)
        #text_SCT = st.ScrolledText(assembly_FRM, bg = "#333333", fg = "white", bd = 0, wrap = tk.WORD, font = ("TkDefaultFont", 10))
        assembly_FRM.pack(fill = tk.BOTH, expand = True)
        text_TXT.pack(side = tk.LEFT,  fill = tk.BOTH, expand = True)
        text_SCB.pack(side = tk.RIGHT, fill = tk.Y)
        text_TXT.tag_configure("asm_code", font = self.code_font)

        for foo in text1.split("</code>\n"):
            if foo:
                text_TXT.insert(tk.END, foo.split("<code>\n")[0])
                text_TXT.insert(tk.END, foo.split("<code>\n")[1], "asm_code")
        text_TXT.insert(tk.END, text2)
        for line in text3.split("\n"):
            text_TXT.insert(tk.END, line.split(" -")[0], "asm_code")
            text_TXT.insert(tk.END, line.split(" -")[1] + "\n")
        text_SCB.config(command = text_TXT.yview)
        #text_SCT.pack(    fill = "both", expand = True)
        #text_SCT.insert(tk.INSERT, text)
        #text_SCT.configure(state = "disabled")
        self.assembly_WIN.protocol("WM_DELETE_WINDOW", self.on_assembly_win_close)

    def on_assembly_win_close(self):
        self.assembly_WIN.destroy()
        self.assembly_WIN = None

    def open_shortcuts_win(self):
        if self.shortcuts_WIN:
            return
        combos = """Ctrl + Enter
Shift + Enter
Ctrl + O
F5
Ctrl + S
Ctrl + Shift + S"""
        actions = """Run program
Line break without new address
Open file
Reload file
Save file
Save file as"""
        self.shortcuts_WIN = tk.Toplevel(self.root)
        self.shortcuts_WIN.geometry("275x120")
        self.shortcuts_WIN.resizable(False, False)
        self.shortcuts_WIN.config(bg = "black")
        self.shortcuts_WIN.title("Shortcuts")

        shortcuts_FRM = tk.Frame(self.
                shortcuts_WIN, bg = "#222222", bd = 5)
        #title_LBL    = tk.Label(shortcuts_FRM, bg = "#222222", fg = "white", text = title,   justify = tk.LEFT, font = ("Segoe", 15, "bold"))
        combos_LBL    = tk.Label(shortcuts_FRM, bg = "#333333", fg = "white", text = combos,  justify = tk.LEFT)
        actions_LBL   = tk.Label(shortcuts_FRM, bg = "#333333", fg = "white", text = actions, justify = tk.LEFT)
        shortcuts_FRM.pack(fill = "both", expand = True)
        #title_LBL.pack( side = "top",   fill = "x", expand = True)
        combos_LBL.pack( side = tk.LEFT,  fill = "both", expand = True, padx = (0, 5))
        actions_LBL.pack(side = tk.RIGHT, fill = "both", expand = True)
        self.shortcuts_WIN.protocol("WM_DELETE_WINDOW", self.on_shortcuts_win_close)


    def on_shortcuts_win_close(self):
        self.shortcuts_WIN.destroy()
        self.shortcuts_WIN = None

    def open_demo_pro(self):
        demo = """; A simple countdown program
00 JMP 03
01 5
02 1
03 LDA 01
04 SUB 02
05 JLE 08
06 STA 01
07 JMP 04
08 STP"""
        self.inp_SCT.delete("1.0", tk.END)
        self.inp_SCT.insert(tk.INSERT, demo)
        print("heyy")
        self.is_saved = True
        self.writing()

    def open_about_win(self):
        if self.about_WIN:
            return
        self.is_about_win_open = True
        title = "Assemblitor"
        text  = """
    A simple emulator and editor for [Assembly Dialect]
    Version: 0.1 Alpha
    Made by Blyfh in 2022
        
    Created with love in Berlin <3
        """
        self.about_WIN = tk.Toplevel(self.root)
        self.about_WIN.geometry("275x130")
        self.about_WIN.resizable(False, False)
        self.about_WIN.config(bg = "black")
        self.about_WIN.title("About")

        about_FRM = tk.Frame(self.about_WIN, bg ="#222222", bd = 5)
        title_LBL = tk.Label(about_FRM, bg = "#333333", fg = "white", text = title, anchor = tk.CENTER, justify = tk.LEFT, font = ("Segoe", 15, "bold"))
        text_LBL  = tk.Label(about_FRM, bg = "#333333", fg = "white", text = text,  anchor = tk.W, justify = tk.LEFT)
        about_FRM.pack(fill = "both", expand = True)
        title_LBL.pack(fill = "both", expand = True)
        text_LBL.pack( fill = "both", expand = True)
        self.about_WIN.protocol("WM_DELETE_WINDOW", self.on_about_win_close)

    def on_about_win_close(self):
        self.about_WIN.destroy()
        self.about_WIN = None

    def key_enter(self, event):
        self.insert_address()

    def key_shift_enter(self, event):
        pass # overwrites self.key_enter()

    def key_ctrl_enter(self, event):
        txt = self.inp_SCT.get(1.0, "end-1c")
        txt = txt[:len(txt) - 1]
        self.inp_SCT.delete(1.0, tk.END)
        self.inp_SCT.insert(tk.INSERT, txt)
        self.run()

    def insert_address(self):
        txt = self.inp_SCT.get(1.0, "end-1c")
        txt = txt[:len(txt) - 1]
        pos = int(float(self.inp_SCT.index(tk.INSERT))) - 2
        lines = txt.split("\n")
        try:
            last_adr = int(lines[pos].split()[0])
        except:
            return
        new_adr  = str(last_adr + 1)
        if len(new_adr) == 1: # add leading zero
            new_adr = "0" + new_adr
        self.inp_SCT.insert(tk.INSERT, new_adr + " ")

# TO-DO:
# bei Adressverschiebung alle Adressen anpassen
# Demo-Programm
# ask to save altes Programm, wenn man neue Datei/Demo öffnen möchte
# SETTINGS:
# Exception optional in Konsole ausgeben
# strg + del löscht ganzes Wort

# BUGS:
# Editor schließt sich ungespeichert, wenn man nach askToSave->yes beim Speichern auf cancel drückt

min_version = (3, 10)
cur_version = sys.version_info

if cur_version >= min_version:
    ed = Editor()
else:
    root = tk.Tk()
    root.withdraw()
    mb.showerror("Error", "Your version of Python is not supported. Please use Python 3.10 or higher.")
