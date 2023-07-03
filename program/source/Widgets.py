import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as st
import string
from program.source import Emulator as emu


# ASSEMBLITOR WIDGETS

class CodeBlock(tk.Frame):

    def __init__(self, root, editor, *args, **kwargs):
        self.root = root
        self.ed = editor
        tk.Frame.__init__(self, self.root)
        self.SCT = st.ScrolledText(self, bg = self.ed.theme_text_bg, fg = self.ed.theme_text_fg, bd = 0, width = 10, wrap = "none", font = self.ed.gt_code_font(), *args, **kwargs)
        self.xview_SCB = tk.Scrollbar(self, orient = "horizontal", command = self.SCT.xview)
        self.SCT["xscrollcommand"] = self.xview_SCB.set
        self.SCT.pack(side = "top", fill = "both", expand = True)
        self.xview_SCB_flag = False
    # events
        self.SCT.bind(sequence = "<Configure>",  func = lambda event: self.check_for_xvisibility())
        self.SCT.bind(sequence = "<<Modified>>", func = lambda event: self.check_for_xvisibility())

    def check_for_xvisibility(self): # (un-)display xview_SCB if necessary
        if self.SCT.xview() == (0.0, 1.0):
            if self.xview_SCB_flag:
                self.xview_SCB.pack_forget()
                self.xview_SCB_flag = False
        elif not self.xview_SCB_flag:
            self.xview_SCB.pack(side = "bottom", fill = "x")
            self.xview_SCB_flag = True


class OutCodeBlock(CodeBlock):
    def pack(self, *args, **kwargs):
        tk.Frame.pack(self, *args, **kwargs)
        self.SCT.tag_config("pc_is_here", foreground = self.ed.theme_accent_color)
        self.SCT.config(state = "disabled")

    def display_output(self, out):
        self.SCT.config(state = "normal", fg = self.ed.theme_text_fg)
        self.SCT.delete("1.0", "end")
        self.SCT.insert("insert", out[0][0])
        if out[0][1]:
            self.SCT.insert("insert", out[0][1], "pc_is_here")
            self.SCT.yview_moveto(1) # jumps to current command
        self.SCT.insert("insert", out[0][2])
        self.SCT.config(state = "disabled")

    def display_error(self, exception_message):
        self.SCT.config(state = "normal", fg = self.ed.theme_error_color)
        self.SCT.delete("1.0", "end")
        self.SCT.insert("insert", exception_message)
        self.SCT.config(state = "disabled")


class InpCodeBlock(CodeBlock):

    def __init__(self, root, editor):
        super().__init__(root, editor, undo = True)
        self.already_modified = False
        self.SCT.config(insertbackground = self.ed.theme_cursor_color) # necessary because self.ed isn't defined beforehand
    # events
        bindtags = self.SCT.bindtags()
        self.SCT.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3])) # changes bindtag order to let open_file() return "break" before standard class-level binding of <Control-o> that adds a newline
        self.SCT.bind(sequence = "<Control-Shift-Z>",   func = lambda event: self.edit_redo()) # automatic edit_redo() bind is <Control-y>
        self.SCT.bind(sequence = "<Shift-Return>",      func = lambda event: self.regular_newline())
        self.SCT.bind(sequence = "<Return>",            func = lambda event: self.smart_newline())
        self.SCT.bind(sequence = "<Control-BackSpace>", func = lambda event: self.delete_word())
        self.SCT.bind(sequence = "<Key>",               func = lambda event: self.on_key_pressed())
        self.SCT.bind(sequence = "<<Modified>>",        func = lambda event: self.on_inp_modified(), add = "+") # 'add' keyword necessary because CodeBlock already uses bind "<<Modified>>"

    def regular_newline(self):
        pass # overwrites self.smart_newline()

    def smart_newline(self):
        self.insert_address()
        self.SCT.see("insert") # jump to cursor pos if it gets out of sight (due to newline)
        return "break" # overwrites excessive newline printing

    def insert_address(self):
        last_line = self.SCT.get("insert linestart", "insert")
        last_line_stripped = last_line.lstrip()
        try:
            last_adr = int(last_line_stripped.split()[0])
        except:
            self.SCT.insert("insert", "\n")
            return
        whitespace_wrapping = last_line.split(last_line_stripped)[0]
        new_adr = emu.add_leading_zeros(str(last_adr + 1))
        self.SCT.insert("insert", "\n" + whitespace_wrapping + new_adr + " ")

    def delete_word(self):
        if self.SCT.index("insert") != "1.0": # to prevent deleting word after cursor on position 0
            if self.SCT.get("insert-1c", "insert") != "\n": # to prevent deleting the word of the line above
                self.SCT.delete("insert-1c", "insert") # delete potential space before word
            self.SCT.delete("insert-1c wordstart", "insert") # delete word
            return "break"

    def on_key_pressed(self):
        if self.SCT.get("insert-1c") in string.whitespace:  # last written char is a whitespace
            self.SCT.edit_separator() # add seperator to undo stack so that all actions up to the seperator can be undone -> undoes whole words

    def on_inp_modified(self):
        if not self.already_modified: # because somehow on_inp_modified always gets called twice
            self.SCT.edit_modified(False)
            if self.ed.init_inp == self.SCT.get(1.0, "end-1c"): # checks if code got reverted to last saved instance (to avoid pointless ask-to-save'ing)
                self.ed.set_dirty_flag(False)
            else:
                self.ed.set_dirty_flag(True)
            self.already_modified = True
        else:
            self.already_modified = False

    def increment_selected_text(self):
        self.change_selected_text(change = +int(self.ed.change_amount_VAR.get()))

    def decrement_selected_text(self):
        self.change_selected_text(change = -int(self.ed.change_amount_VAR.get()))

    def change_selected_text(self, change):
        option = self.ed.chng_opt_OMN.current_option() # either "adr", "adr_opr", "opr"
        adrs_flag = "adr" in option
        oprs_flag = "opr" in option
        sel_range = self.SCT.tag_ranges("sel")
        if sel_range:
            text = self.SCT.get(*sel_range)
            if text.strip():
                new_text = self.change_text(text, adrs_flag, oprs_flag, change)
                self.SCT.delete(*sel_range)
                self.SCT.insert(sel_range[0], new_text)
                self.SCT.select_text(sel_range[0], new_text)

    def select_text(self, pos, text):
        self.SCT.tag_add("sel", pos, str(pos) + f"+{len(text)}c")

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

    def gt_input(self):
        return self.SCT.get(1.0, "end-1c")

    def st_input(self, inp_str:str):
        self.SCT.delete("1.0", "end")
        self.SCT.insert("insert", inp_str)


# UNIVERSAL WIDGETS

class Button(ttk.Label):

    def __init__(self, root, command, img_default = None, img_hovering = None, img_clicked = None, click_display_time:int = 30, *args, **kwargs):
        ttk.Label.__init__(self, root, *args, **kwargs)
        self.root = root
        self.command = command
        self.hovering = False # mouse is on button
        self.pressing = False # button is getting pressed down
        self.clicked  = False # button got activated
        self.click_display_time = click_display_time
        self.img_default  = None
        self.img_hovering = None
        self.img_clicked  = None

        if img_default:
            self.image_flag = True
            self.img_default = img_default
            self.on_leave()
            if img_hovering:
                self.img_hovering = img_hovering
            else:
                self.img_hovering = self.img_default
            if img_clicked:
                self.img_clicked = img_clicked
            else:
                self.img_clicked = self.img_default
        else:
            self.image_flag = False

        self.bind(sequence = "<Enter>", func = self.on_enter)
        self.bind(sequence = "<Leave>", func = self.on_leave)
        self.bind(sequence = "<ButtonPress-1>",   func = self.on_pressed)
        self.bind(sequence = "<ButtonRelease-1>", func = self.on_released)

    def set_img(self, img):
        if self.image_flag:
            self.config(image = img)

    def on_enter(self, event = None):
        self.hovering = True
        if not self.pressing:
            self.set_img(self.img_hovering)
        else:
            self.set_img(self.img_clicked)

    def on_leave(self, event = None):
        self.hovering = False
        if not self.clicked:
            self.set_img(self.img_default)

    def on_pressed(self, event = None):
        self.pressing = True
        self.set_img(self.img_clicked)

    def on_released(self, event = None):
        self.pressing = False
        if self.hovering:
            self.clicked = True
            self.root.after(self.click_display_time, self.after_click)
            self.command()

    def after_click(self):
        self.clicked = False
        if self.hovering:
            self.set_img(self.img_hovering)
        else:
            self.set_img(self.img_default)


class OptionMenu(ttk.OptionMenu):

    def __init__(self, root, textvariable:tk.StringVar, default_option, options:dict, command, **kwargs):
        self.root = root
        self.options = options # {"option1_name": "option1_displaytext", "option2_name": "option2_displaytext"}
        self.textvariable = textvariable
        self.default_option = default_option
        try:
            default = self.options[self.default_option]
        except:
            raise RuntimeError(f"OptionMenu: Can't find default option '{self.default_option}' in given options:\n    {self.options}")
        ttk.OptionMenu.__init__(self, root, self.textvariable, default, *self.options.values(), command = command)
        self.config(**kwargs)

    def gt_displaytext(self, option):
        try:
            displaytext = self.options[option]
        except:
            raise RuntimeError(f"OptionMenu: Can't find option '{option}' in given options:\n    {self.options}")
        return displaytext

    def st_option(self, option):
        self.textvariable.set(self.gt_displaytext(option))

    def current_option(self):
        current_option_displaytext = self.textvariable.get()
        for option in self.options:
            if self.options[option] == current_option_displaytext:
                return option
        raise RuntimeError(f"OptionMenu: Can't find current option for selected displaytext '{current_option_displaytext}'.")


class Spinbox(tk.Text):

    def __init__(self, root, min:int = 0, max:int = 100, default:int = 50, *args, **kwargs):
        self.root = root
        self.frame = tk.Frame(self.root)
        if min >= 0 and max >= 0 and default >= 0:
            self.min = min
            self.max = max
            self.last_valid_inp = default
        else:
            raise ValueError(f"Spinbox: Either min {min}, max {max} or default {default} is negative.")
        tk.Text.__init__(self, self.frame, *args, **kwargs)
        self.pack(side = "left", fill = "both", expand = True)
        self.insert("insert", default)

        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack! [copied by ScrolledText, to redirect packing to self.frame]
        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))
        self.bind(sequence = "<<Modified>>", func = self.validate_chars)
        self.bind(sequence = "<FocusOut>",   func = self.validate_range)

    def gt(self):
        return int(self.get(1.0, "end-1c"))

    def st(self, value:int):
        self.delete(1.0, "end-1c")
        self.insert(str(value))

    def validate_chars(self, event): # check for nonnumeral characters on <Key>
        print("hey")
        inp = self.get(1.0, "end-1c")
        if inp.isdecimal():
            self.last_valid_inp = int(inp)
        else: # reset invalid change
            self.st(self.last_valid_inp)

    def validate_range(self): # check for invalid numbers on <Enter> or <FocusOut>
        inp = self.gt()
        if inp < self.min:
            self.st(self.min)
        elif inp > self.max:
            self.st(self.max)


class Tooltip:
    """
    It creates a tooltip for a given widget as the mouse goes on it.

    see:

    http://stackoverflow.com/questions/3221956/
           what-is-the-simplest-way-to-make-tooltips-
           in-tkinter/36221216#36221216

    http://www.daniweb.com/programming/software-development/
           code/484591/a-tooltip-class-for-tkinter

    - Originally written by vegaseat on 2014.09.09.

    - Modified to include a delay time by Victor Zaccardo on 2016.03.25.

    - Modified
        - to correct extreme right and extreme bottom behavior,
        - to stay inside the screen whenever the tooltip might go out on
          the top but still the screen is higher than the tooltip,
        - to use the more flexible mouse positioning,
        - to add customizable background color, padding, waittime and
          wraplength on creation
      by Alberto Vassena on 2016.11.05.

      Tested on Ubuntu 16.04/16.10, running Python 3.5.2

    To-Do: themes styles support
    """

    def __init__(self, widget,
                 *,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='widget info',
                 waittime=600,
                 wraplength=250):

        self.waittime = waittime  # in milliseconds, originally 500
        self.wraplength = wraplength  # in pixels, originally 180
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.onEnter, add = "+")
        self.widget.bind("<Leave>", self.onLeave, add = "+")
        self.widget.bind("<ButtonPress>", self.onLeave, add = "+")
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None

    def update_text(self, new_text:str):
        self.text = new_text

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        def tip_pos_calculator(widget, label,
                               *,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            w = widget

            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])

            mouse_x, mouse_y = w.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                # No further checks will be done.

                # TIP:
                # A further mod might automagically augment the
                # wraplength when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        widget = self.widget

        # creates a toplevel window
        self.tw = tk.Toplevel(widget)

        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)

        win = tk.Frame(self.tw,
                       background=bg,
                       borderwidth=0)
        label = tk.Label(win,
                          text=self.text,
                          justify=tk.LEFT,
                          background=bg,
                          relief=tk.SOLID,
                          borderwidth=0,
                          wraplength=self.wraplength)

        label.grid(padx=(pad[0], pad[2]),
                   pady=(pad[1], pad[3]),
                   sticky=tk.NSEW)
        win.grid()

        x, y = tip_pos_calculator(widget, label)

        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None


root = tk.Tk()
root.config(bg = "red")
root.geometry("200x80")
etr = Spinbox(root, height = 1, width = 20, default = 4)
etr.pack()
root.mainloop()
