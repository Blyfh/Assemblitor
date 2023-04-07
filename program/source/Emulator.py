import string


CMDS        = ["LDA", "ADD", "STP", "SUB", "JMP", "JLE", "JZE", "MUL", "STA"]
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


class Emulator:

    def __init__(self):
        self.prg_str     = ""
        self.prg         = None
        self.is_new_prg  = True

    def gt_out(self, prg_str, execute_all = True):
        if self.prg_str != prg_str: # program changed
            self.is_new_prg = True
        if self.is_new_prg:
            self.create_prg(prg_str)
            if not execute_all:  # display first step of program
                return self.prg.gt_prg(), str(self.prg.pc), str(self.prg.accu), self.gt_ireg()
        if len(self.prg.cells) == 0: # program is empty (can include comments though)
            return self.prg.gt_prg(), 0, 0, ("", "")
        self.prg.execute(execute_all)
        if self.cur_cmd() == "STP": # program reset when reaching end of single-step executing
            self.is_new_prg = True
        return self.prg.gt_prg(execute_all), str(self.prg.pc), str(self.prg.accu), self.gt_ireg()

    def gt_ireg(self): # current command in instruction register
        return self.cur_cmd(), self.cur_opr_str()

    def cur_cell(self): # current cell
        return self.prg.gt_cel(self.prg.pc)

    def cur_cmd(self):
        return self.cur_cell().gt_cmd()

    def cur_opr_str(self):
        return self.cur_cell().gt_opr().opr_str

    def create_prg(self, prg_str):
        self.prg_str = prg_str
        self.prg = Program(prg_str)
        self.is_new_prg = False


class Program:

    def __init__(self, prg_str):
        self.jmps_to_adr = {}  # each element logs how many times the pointer jumped to its cell
        self.top_cmt     = ""
        self.cells       = self.gt_cells(prg_str)
        self.accu        = 0
        self.pc          = 0
        self.executing   = False

    def __str__(self):
        prg_str = self.top_cmt
        for cell in self.cells:
            prg_str += str(cell) + "\n"
        return prg_str

    def gt_prg(self, execute_all = False): # returns a tuple with the executing cell in the middle to colorcode it in the output widget
        prg_str1 = self.top_cmt
        cell_that_is_currently_executed = ""
        prg_str2 = ""
        if not execute_all:
            for cell in self.cells:
                if cell.cpos < self.pc:
                    prg_str1 += str(cell) + "\n"
                elif cell.cpos > self.pc:
                    prg_str2 += str(cell) + "\n"
                else:
                    cell_that_is_currently_executed = str(cell) + "\n"
            return prg_str1, cell_that_is_currently_executed, prg_str2
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
            raise Exception(eh.error("NeverStopped"))

    def execute_command(self, adr):
        cmd = self.gt_cel(adr).gt_cmd()
        opr = self.gt_cel(adr).gt_opr()
        eval("self.cmd_" + cmd + "(" + str(opr) + ")")

    def gt_cells(self, prg_str):
        if not prg_str:
            return []
        lines = prg_str.split("\n")
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
        if adr > MAX_CELS - 1:
            raise Exception(eh.error("MaxPrgLength", max_adrs = MAX_CELS, adrs =adr + 1))
        while adr >= len(self.cells):
            cell = Cell(str(len(self.cells)) + " ")
            self.cells.append(cell)
        return self.cells[adr]

    def fill_empty_cells(self, cells):
        i = 0
        while i < len(cells):
            adr = cells[i].gt_adr()
            if adr > MAX_CELS - 1:
                raise Exception(eh.error("MaxPrgLength", max_adrs = MAX_CELS, adrs =adr + 1))
            if i == adr:
                pass
            elif i < adr:
                cell = Cell(str(i) + " ")
                cells.insert(i, cell)
            else:
                if str(cells[adr].toks[1]) == "":
                    raise Exception(eh.error("AdrsNotChronological", small_adr = adr, big_adr = str(cells[i - 1].gt_adr())))
                else:
                    raise Exception(eh.error("AdrNotUnique", adr = adr))
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
                raise Exception(eh.error("CmdHasValOpr", opr = opr))
        else:
            raise Exception(eh.error("UnknownOprTyp", opr = opr))

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
        if self.gt_jmps_to_adr(self.gt_adr(opr_inf)) > MAX_JMPS:
            raise Exception(eh.error("MaxIterationDepth", max_jmps = MAX_JMPS, adr = self.gt_adr(opr_inf)))
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
        if type(new_val) is int:
            self.toks[1].edit(new_val)
        else:
            raise Exception(eh.error("ValNotInt_Load", adr = self.gt_adr(), val = new_val))

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
                raise Exception(eh.error("CmdStpHasOpr", adr = self.gt_adr()))
            else:
                return self.toks[2].gt_opr()
        elif self.toks[1].tok == "STP":
            return Operand("", self.cpos)
        else:
            raise Exception(eh.error("MissingOpr", cmd = self.gt_cmd(), adr = self.gt_adr()))


class Token:

    def __init__(self, tok_str, tpos, cpos = "NaN"):
        self.tpos    = tpos
        self.cpos    = cpos
        self.tok_str = tok_str
        self.type    = None # 0 = address, 1 = command, 2 = value, 3 = operand
        self.tok     = self.create_tok(self.tok_str)

    def __str__(self):
        if len(self.tok_str) > 0 and self.tok_str[-1] != " ":
            self.tok_str += " "
        return self.add_leading_zeros(self.tok_str)

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

    def add_leading_zeros(self, tok_str):
        tok_str_stripped = tok_str.strip()
        if self.type == 0 and len(tok_str_stripped) < MIN_ADR_LEN:
            whitespace_wrapping = tok_str.split(tok_str_stripped)
            tok_str = whitespace_wrapping[0] + (MIN_ADR_LEN - len(tok_str_stripped)) * "0" + tok_str_stripped + whitespace_wrapping[1]
        elif self.type == 3:
            if self.tok.type == 0 and len(tok_str_stripped) < MIN_ADR_LEN: # direct operand (e.g. 00 LDA 5)
                tok_str = (MIN_ADR_LEN - len(tok_str_stripped)) * "0" + tok_str
            elif self.tok.type == 1 and len(tok_str_stripped) < MIN_ADR_LEN + 2: # indirect operand (e.g. 00 LDA (5))
                tok_str = "(" + (MIN_ADR_LEN - len(tok_str_stripped)) * "0" + tok_str[1:]
        return tok_str

    def edit(self, new_val):
        if self.type == 2:
            self.tok = new_val
            i = 0
            while i < len(self.tok_str) and self.tok_str[i] not in string.whitespace:
                i += 1
            self.tok_str = str(self.tok) + self.tok_str[i:]
        else:
            raise Exception(eh.error("TokNotVal_Overwrite", tpos = self.tpos, adr = self.cpos, tok = self.tok, new_val = new_val))

    def gt_cmd(self):
        if self.type == 1:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise Exception(eh.error("TokNotCmd", tpos = self.tpos, adr = self.cpos, tok = self.tok))
            else:
                raise Exception(eh.error("TokNotCmd_EmptyTok", tpos = self.tpos, adr = self.cpos))

    def gt_opr(self):
        if self.type == 3:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise Exception(eh.error("TokNotOpr", tpos = self.tpos, adr = self.cpos, tok = self.tok))
            else:
                raise Exception(eh.error("TokNotOpr_EmptyTok", tpos = self.tpos, adr = self.cpos))

    def gt_adr(self):
        if self.type == 0:
            return self.tok
        else:
            if len(self.tok_str) > 0:
                raise Exception(eh.error("TokNotAdr", tpos = self.tpos, adr = self.cpos, tok = self.tok))
            else:
                raise Exception(eh.error("TokNotAdr_EmptyTok", tpos = self.tpos, adr = self.cpos))


class Operand:

    def __init__(self, opr_str, cpos):
        self.cpos = cpos
        if type(opr_str) is str:
            self.opr_str = opr_str
        else:
            raise Exception(eh.error("OprTokNotStr", opr_str = opr_str))
        self.type = 0 # 0 = direct address, 1 = indirect address, 2 = value
        self.opr = self.create_opr(self.opr_str)

    def create_opr(self, opr_str):
        if len(opr_str) > 0:
            if opr_str[0] == "#":
                try:
                    opr_int = int(opr_str[1:])
                except:
                    raise Exception(eh.error("ValOprNotInt", adr = self.cpos, opr = opr_str))
                self.type = 2
                return opr_int
            elif opr_str[0] == "(" and opr_str[-1] == ")":
                try:
                    opr_int = int(opr_str[1:-1])
                except:
                    raise Exception(eh.error("IndOprNotInt", adr = self.cpos, opr = opr_str))
                if opr_int >= 0:
                    self.type = 1
                    return opr_int
                else:
                    raise Exception(eh.error("IndOprIsNegative", adr = self.cpos, opr = opr_str))
            else:
                try:
                    opr_int = int(opr_str)
                except:
                    raise Exception(eh.error("UnknownOpr", adr = self.cpos, opr = opr_str))
                if opr_int >= 0:
                    self.type = 0
                    return opr_int
                else:
                    raise Exception(eh.error("DirOprIsNegative", adr = self.cpos, opr = opr_str))
        else:
            self.type = None
            return None

    def __str__(self):
        if self.type is None:
            return ""
        else:
            return "(" + str(self.type) + ", " + str(self.opr) + ")"