import string


CMDS        = ["STP", "ADD", "SUB", "MUL", "LDA", "STA", "JMP", "JLE", "JZE"]
CMDS_no_val_opr = ["STA", "JMP", "JLE", "JZE"]
MIN_ADR_LEN = 0
MAX_JMPS    = 0
MAX_CELS    = 0

def startup(profile_handler, error_handler):
    global ph
    global eh
    ph = profile_handler
    eh = error_handler
    update_properties()

def update_properties():
    global MIN_ADR_LEN
    global MAX_JMPS
    global MAX_CELS
    MIN_ADR_LEN = ph.min_adr_len()
    MAX_JMPS    = ph.max_jmps()
    MAX_CELS    = ph.max_cels()

def concatenate(str1, str2): # used by Cell.gt_content() for adding spaces between tokens if necessary
    if len(str1) > 0 and len(str2) > 0 and not str1[-1] in string.whitespace:
        return str1 + " " + str2
    else:
        return str1 + str2

def split_cell_at_comment(cel_cmt_str): # used by Programm.gt_cells() and Editor.change_text() for splitting cell and comment
    i = 0
    while i < len(cel_cmt_str) and cel_cmt_str[i] != ";":
        i += 1
    while i > 1 and cel_cmt_str[i - 1] in string.whitespace and cel_cmt_str[i - 2] in string.whitespace: # move additional whitespaces after cell to comment (first whitespace is appended to cell)
        i -= 1
    return cel_cmt_str[:i], cel_cmt_str[i:]

def add_leading_zeros(adr_str, offset = 0):
    adr_str_stripped = adr_str.strip()
    leading_zeros = (MIN_ADR_LEN - len(adr_str_stripped) + offset) * "0"
    whitespace_wrapping = adr_str.split(adr_str_stripped)
    return whitespace_wrapping[0] + leading_zeros + adr_str_stripped + whitespace_wrapping[1]


class Emulator:

    def __init__(self):
        self.prg_str     = ""
        self.prg         = None
        self.is_new_prg  = True
        self.last_execute_all_flag = None

    def gt_out(self, prg_str, execute_all_flag = True):
        if self.prg_str != prg_str or execute_all_flag != self.last_execute_all_flag or self.prg and self.prg.halted: # program or execution type changed or last execution step reached STP/eh.error.NeverStopped
            self.is_new_prg = True # program reset
            self.last_execute_all_flag = execute_all_flag
        if self.is_new_prg:
            self.create_prg(prg_str)
        if len(self.prg.cells) == 0: # program is empty (can include comments though)
            return self.prg.gt_prg(), "", "", ("", "")
        self.prg.execute(execute_all_flag)
        return self.prg.gt_prg(execute_all_flag), str(self.prg.pc), str(self.prg.accu), self.prg.gt_ireg()

    def create_prg(self, prg_str):
        self.prg_str = prg_str
        self.prg = None # for Editor.format_error() detecting failed program initialisation
        self.prg = Program(prg_str)
        self.is_new_prg = False


class Program:

    def __init__(self, prg_str):
        self.jmps_to_adr = {}  # each element logs how many times the pointer jumped to its cell
        self.top_cmt     = ""
        self.cells       = self.create_cells(prg_str)
        self.accu        = 0
        self.pc          = 0
        self.executing   = False
        self.halted = False

    def __str__(self):
        prg_str = self.top_cmt
        for cell in self.cells:
            prg_str += str(cell)
        return prg_str

    def create_cells(self, prg_str):
        if not prg_str:
            return []
        lines = prg_str.split("\n")
        cells  = []
        for i in range(len(lines)):
            line = split_cell_at_comment(lines[i])
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

    def gt_prg(self, execute_all_flag = False): # returns a tuple with the executing cell in the middle to colorcode it in the output widget
        if not execute_all_flag and len(self.cells) > 0:
            prg_str1      = self.top_cmt
            executed_cell = None
            prg_str2      = ""
            for cell in self.cells:
                if cell.gt_adr() < self.pc:
                    prg_str1 += str(cell)
                elif cell.gt_adr() > self.pc:
                    prg_str2 += str(cell)
                else:
                    executed_cell = cell
            if executed_cell: # current cell exists
                return prg_str1, executed_cell.gt_content(), executed_cell.gt_comment() + "\n" + prg_str2
            else:
                self.executing = False
                self.halted    = True
                raise Exception(eh.error("NeverStopped"))
        else:
            return str(self), "", ""

    def execute(self, execute_all_flag = True):
        # all steps
        if execute_all_flag:
            self.start_executing()
            while self.executing:
                self.execute_cell()
        # one step
        elif self.executing:
            self.execute_cell()
        else:
            self.start_executing()

    def start_executing(self):
        self.executing   = True
        self.halted      = False
        self.accu        = 0
        self.pc          = 0
        self.jmps_to_adr.clear()

    def execute_cell(self):
        if self.pc < len(self.cells):
            self.execute_command(self.pc)
            self.pc += 1
        else:
            self.executing = False
            self.halted = True
            raise Exception(eh.error("NeverStopped"))

    def execute_command(self, adr):
        cmd = self.gt_cel(adr).gt_cmd()
        opr = self.gt_cel(adr).gt_opr()
        eval(f"self.cmd_{cmd}")(opr)

    def fill_empty_cells(self, cells):
        i = 0
        while i < len(cells):
            adr = cells[i].gt_adr()
            if adr > MAX_CELS - 1:
                raise Exception(eh.error("MaxPrgLength", max_adrs = MAX_CELS, adrs = adr + 1))
            if i == adr:
                pass
            elif i < adr:
                cell = Cell(f"{i} ", is_user_generated = False)
                cells.insert(i, cell)
            elif str(cells[adr].toks[1]) == "":
                raise Exception(eh.error("AdrsNotChronological", small_adr = add_leading_zeros(str(adr)), big_adr = add_leading_zeros(str(cells[i - 1].gt_adr())))) # add_leading_zeros() because error message literally refers to address, not the memory cell
            else:
                raise Exception(eh.error("AdrNotUnique", adr = add_leading_zeros(str(adr)))) # add_leading_zeros() because error message literally refers to address, not the memory cell
            i += 1
        return cells

    def gt_ireg(self):
        cmd = self.gt_cel(self.pc).gt_cmd()
        opr = self.gt_cel(self.pc).gt_opr()
        return cmd, str(opr)

    def gt_cel(self, adr):
        if adr > MAX_CELS - 1:
            raise Exception(eh.error("MaxPrgLength", max_adrs = MAX_CELS, adrs = adr + 1))
        while adr >= len(self.cells):
            cell = Cell(f"{len(self.cells)} ", is_user_generated = False)
            self.cells.append(cell)
        return self.cells[adr]

    def gt_final_value(self, opr): # interprets final result of operand pointer as a value (for commands like ADD, SUB, MUL, LDA)
        if opr.type == 0: # normal address
            return self.gt_cel(opr.opr).gt_val()
        elif opr.type == 1: # nested address (e.g. 00 LDA (5))
            adr = self.gt_cel(opr.opr).gt_val()
            return self.gt_cel(adr).gt_val()
        elif opr.type == 2: # value (e.g. 00 LDA #5)
            return opr.opr

    def gt_final_adr(self, opr): # interprets final result of operand pointer as an address (for commands like STA, JMP, JLE, JZE)
        if opr.type == 0: # normal address
            adr = opr.opr
            return adr
        elif opr.type == 1: # nested address (e.g. 00 LDA (5))
            adr = int(self.gt_cel(opr.opr).gt_val())
            return adr
        elif opr.type == 2: # value (e.g. 00 LDA #5)
            raise Exception(eh.error("CmdHasValOpr", opr = opr, adr = opr.cpos))

    def gt_jmps_to_adr(self, adr):
        if adr in self.jmps_to_adr:
            return self.jmps_to_adr[adr]
        else:
            return 0

    def cmd_STP(self, opr):
        self.pc -= 1
        self.executing = False
        self.halted = True

    def cmd_ADD(self, opr):
        self.accu += self.gt_final_value(opr)

    def cmd_SUB(self, opr):
        self.accu -= self.gt_final_value(opr)

    def cmd_MUL(self, opr):
        self.accu *= self.gt_final_value(opr)

    def cmd_LDA(self, opr):
        self.accu = self.gt_final_value(opr)

    def cmd_STA(self, opr):
        adr = self.gt_final_adr(opr)
        self.gt_cel(adr).edit(self.accu)

    def cmd_JMP(self, opr):
        adr = self.gt_final_adr(opr)
        self.pc = adr - 1 # "- 1" because self.pc will increment automatically
        if self.gt_jmps_to_adr(adr) > MAX_JMPS:
            raise Exception(eh.error("MaxIterationDepth", max_jmps = MAX_JMPS, adr = adr))
        else:
            self.jmps_to_adr[adr] = self.gt_jmps_to_adr(adr) + 1 # increment jmps_to_adr for this address

    def cmd_JLE(self, opr):
        if self.accu <= 0:
            self.cmd_JMP(opr)

    def cmd_JZE(self, opr):
        if self.accu == 0:
            self.cmd_JMP(opr)


class Cell:

    def __init__(self, cel_str = "", cmt = "", is_user_generated = True):
        self.is_user_generated = is_user_generated
        self.cmt  = cmt
        self.toks = []
        tok_strs = self.split_cel_str(cel_str)
        self.create_toks(tok_strs)

    def __str__(self):
        if self.is_user_generated or not self.is_empty():
            return self.gt_content() + self.gt_comment() + "\n"
        else:
            return "" # hide empty automatically generated cells to avoid cluttering the program

    def create_toks(self, tok_strs):
        for tpos in range(len(tok_strs)):
            if tpos == 0:
                tok = Token(tok_strs[tpos], tpos)
                self.toks.append(tok)
            else:
                tok = Token(tok_strs[tpos], tpos, self.gt_adr())
                if tok.type == 3: # token is operand
                    if tok.tok.type is None: # empty operand
                        if self.toks[1].type == 1 and self.toks[1].tok != "STP": # command lacks operand
                            raise Exception(eh.error("MissingOpr", cmd = self.gt_cmd(), adr = self.gt_adr()))
                    else:
                        if self.toks[1].type == 2: # operand after a value
                            raise Exception(eh.error("ValCellOpr", opr = tok.tok, adr = self.gt_adr()))
                        elif tpos == 2 and self.toks[1].tok == "STP": # operand after STP
                            raise Exception(eh.error("StpCellOpr", opr = tok.tok, adr = self.gt_adr()))
                        elif tok.tok.type == 2 and self.gt_cmd() in CMDS_no_val_opr: # operand with absolute value for an unsupported command (e.g. STA #5)
                            raise Exception(eh.error("CmdHasValOpr", opr_str = tok.tok_str, adr = self.gt_adr()))
                self.toks.append(tok)

    def split_cel_str(self, cel_str_unstripped):
        cel_str = cel_str_unstripped.lstrip() # remove whitespaces before addres
        lwrapping = cel_str_unstripped.split(cel_str)[0]
        tok_strs = []
        last_split_pos = 0
        for i in range(len(cel_str)):
            if cel_str[i] in string.whitespace and i < len(cel_str) - 1 and cel_str[i+1] not in string.whitespace: # last whitespace between tokens
                tok_str = cel_str[last_split_pos:i+1]
                tok_strs.append(tok_str)
                last_split_pos = i + 1
        tok_str = cel_str[last_split_pos:]
        tok_strs.append(tok_str)
        while len(tok_strs) < 3:
            tok_strs.append("")
        tok_strs[0] = lwrapping + tok_strs[0] # add whitespaces before address
        return tok_strs

    def gt_content(self): # cell content without comment
        cel_str = ""
        for tok in self.toks:
            cel_str = concatenate(cel_str, str(tok))
        return cel_str

    def gt_comment(self):
        return self.cmt

    def edit(self, new_val):
        if type(new_val) is int:
            self.toks[1].edit(new_val)
        else:
            raise Exception(eh.error("ValNotInt_Load", adr = self.gt_adr(), val = new_val))

    def is_empty(self):
        return self.toks[1].is_empty()

    def gt_adr(self):
        return self.toks[0].gt_adr()

    def gt_val(self):
        return self.toks[1].gt_val()

    def gt_cmd(self):
        return self.toks[1].gt_cmd()

    def gt_opr(self):
        return self.toks[2].gt_opr()


class Token:

    def __init__(self, tok_str, tpos, cpos = "NaN"):
        self.tpos    = tpos
        self.cpos    = cpos
        self.tok_str = tok_str
        self.type    = None # 0 = address, 1 = command, 2 = value, 3 = operand
        self.tok     = self.create_tok(self.tok_str)

    def __str__(self):
        return self.add_leading_zeros()

    def create_tok(self, tok_str):
        tok = tok_str.rstrip()
        if self.tpos == 0:
            try:
                tok_int = int(tok.lstrip()) # allow whitespaces before address
            except:
                raise Exception(eh.error("AdrTokNotInt", tok = tok))
            if tok_int >= 0:
                self.type = 0
                self.cpos = tok_int
                return tok_int
            else:
                raise Exception(eh.error("AdrTokIsNegative", tok = tok))
        elif self.tpos == 1:
            try:
                tok_int = int(tok)
            except:
                if tok == "":
                    self.type = 2
                    return 0
                elif tok.upper() in CMDS:
                    self.type = 1
                    return tok.upper()
                else:
                    raise Exception(eh.error("TokNotValOrCmd", adr = self.cpos, tok = tok))
            self.type = 2
            return tok_int
        elif self.tpos == 2:
            self.type = 3
            return Operand(tok, self.cpos)
        else:
            raise Exception(eh.error("MaxCelLength", adr = self.cpos))

    def add_leading_zeros(self):
        if self.type == 0:
            return add_leading_zeros(self.tok_str)
        elif self.type == 3:
            if self.tok.type == 0: # direct operand (e.g. 00 LDA 5)
                return add_leading_zeros(self.tok_str)
            elif self.tok.type == 1:  # indirect operand (e.g. 00 LDA (5))
                return "(" + add_leading_zeros(self.tok_str[1:], offset = 1)
        return self.tok_str

    def edit(self, new_val):
        if self.type == 2:
            self.tok = new_val
            i = 0
            while i < len(self.tok_str) and self.tok_str[i] not in string.whitespace:
                i += 1
            self.tok_str = str(self.tok) + self.tok_str[i:]
        else:
            raise Exception(eh.error("TokNotVal_Overwrite", tpos = self.tpos, adr = self.cpos, tok = self.tok, new_val = new_val))

    def is_empty(self):
        return self.tok_str.strip() == ""

    def gt_val(self):
        if self.type == 2:
            return self.tok
        elif self.type == 1:
            raise Exception(eh.error("TokNotVal_CmdTok", tpos = self.tpos, adr = self.cpos, tok = self.tok))
        else:
            raise Exception(eh.error("TokNotVal", tpos = self.tpos, adr = self.cpos, tok = self.tok))

    def gt_cmd(self):
        if self.type == 1:
            return self.tok
        elif len(self.tok_str) == 0:
            raise Exception(eh.error("TokNotCmd_EmptyTok", tpos = self.tpos, adr = self.cpos))
        elif self.type == 2:
            raise Exception(eh.error("TokNotCmd_ValTok", tpos = self.tpos, adr = self.cpos, tok = self.tok))
        else:
            raise Exception(eh.error("TokNotCmd", tpos = self.tpos, adr = self.cpos, tok = self.tok))

    def gt_opr(self):
        if self.type == 3:
            return self.tok
        else:
            raise Exception(eh.error("TokNotOpr", tpos = self.tpos, adr = self.cpos, tok = self.tok))

    def gt_adr(self):
        if self.type == 0:
            return self.tok
        elif len(self.tok_str) == 0:
            raise Exception(eh.error("TokNotAdr_EmptyTok", tpos = self.tpos, adr = self.cpos))
        else:
            raise Exception(eh.error("TokNotAdr", tpos = self.tpos, adr = self.cpos, tok = self.tok))


class Operand:

    def __init__(self, opr_str, cpos):
        self.cpos = cpos
        if type(opr_str) is str:
            self.opr_str = opr_str
        else:
            raise Exception(eh.error("OprTokNotStr", opr_str = opr_str))
        self.type = None # None = empty, 0 = direct address, 1 = indirect address, 2 = value
        self.opr = self.create_opr(self.opr_str)

    def __str__(self):
        if self.type is None:
            return ""
        elif self.type == 0:
            return add_leading_zeros(str(self.opr))
        elif self.type == 1:
            return f"({add_leading_zeros(str(self.opr))})"
        elif self.type == 2:
            return f"#{self.opr}"

    def create_opr(self, opr_str):
        if len(opr_str) > 0:
            if opr_str[0] == "#":
                try:
                    opr_int = int(opr_str[1:])
                except:
                    raise Exception(eh.error("ValOprNotInt", adr = self.cpos, opr_str = opr_str))
                self.type = 2
                return opr_int
            elif opr_str[0] == "(" and opr_str[-1] == ")":
                try:
                    opr_int = int(opr_str[1:-1])
                except:
                    raise Exception(eh.error("IndOprNotInt", adr = self.cpos, opr_str = opr_str))
                if opr_int >= 0:
                    self.type = 1
                    return opr_int
                else:
                    raise Exception(eh.error("IndOprIsNegative", adr = self.cpos, opr_str = opr_str))
            else:
                try:
                    opr_int = int(opr_str)
                except:
                    raise Exception(eh.error("UnknownOpr", adr = self.cpos, opr_str = opr_str))
                if opr_int >= 0:
                    self.type = 0
                    return opr_int
                else:
                    raise Exception(eh.error("DirOprIsNegative", adr = self.cpos, opr_str = opr_str))