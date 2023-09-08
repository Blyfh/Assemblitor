import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as st
import string
from program.source import Emulator    as emu
from program.source import PackHandler as ph


#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


def gt_img_slider_wheel(): # img_slider_wheel is ideally 5x20 px
    sh = ph.SpriteHandler()
    return sh.gt_sprite("Spinbox", "slider_wheel", 5, 20)


# ASSEMBLITOR WIDGETS

class CodeBlock(tk.Frame):

    def __init__(self, root, editor, **kwargs):
        self.root = root
        self.ed = editor
        tk.Frame.__init__(self, self.root)
        self.SCT = st.ScrolledText(self, bg = self.ed.theme_text_bg, fg = self.ed.theme_text_fg, bd = 0, width = 10, wrap = "none", font = self.ed.gt_code_font(), **kwargs)
        self.xview_SCB = tk.Scrollbar(self, orient = "horizontal", command = self.SCT.xview)
        self.SCT["xscrollcommand"] = self.xview_SCB.set
        self.SCT.pack(side = "top", fill = "both", expand = True)
        self.xview_SCB_flag = False
    # events
        self.SCT.bind(sequence = "<Configure>",  func = lambda event: self.check_for_xvisibility())
        self.SCT.bind(sequence = "<<Modified>>", func = lambda event: self.check_for_xvisibility())

    def check_for_xvisibility(self): # (de-)display xview_SCB if necessary
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
        self.SCT.tag_config("code",        foreground = self.ed.theme_text_fg) # "fg" is an invalid argument
        self.SCT.tag_config("active_code", foreground = self.ed.theme_accent_color) # used by step-by-step mode to highlight the current code line that the PC points to
        self.SCT.tag_config("error",       foreground = self.ed.theme_error_color, wrap = "word")
        self.SCT.config(state = "disabled")

    def display_output(self, code_section1, active_code, code_section2):
        self.SCT.config(state = "normal")
        self.SCT.delete("1.0", "end")
        self.SCT.insert("insert", code_section1, "code")
        if active_code:
            self.SCT.insert("insert", active_code, "active_code")
            self.SCT.yview_moveto(1) # jumps to current command
        self.SCT.insert("insert", code_section2, "code")
        self.SCT.config(state = "disabled")

    def display_error(self, exception_message, prg_state = None):
        print(prg_state)
        self.SCT.config(state = "normal")
        self.SCT.delete("1.0", "end")
        self.SCT.insert("insert", exception_message, "error")
        if prg_state:
            self.SCT.insert("insert", prg_state, "code")
        self.SCT.config(state ="disabled")


class InpCodeBlock(CodeBlock):

    def __init__(self, root, editor):
        super().__init__(root, editor, undo = True)
        self.already_modified = False
        self.SCT.config(insertbackground = self.ed.theme_cursor_color) # necessary because self.ed isn't defined beforehand
    # events
        bindtags = self.SCT.bindtags()
        self.SCT.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3])) # changes bindtag order to let open_file() return "break" before standard class-level binding of <Control-o> that adds a newline
        self.SCT.bind(sequence = "<Control-Shift-z>",   func = lambda event: self.redo()) # automatic edit_redo() bind is <Control-y>
        self.SCT.bind(sequence = "<Control-Shift-Z>",   func = lambda event: self.redo()) # double binds necessary due to capslock overwriting lowercase sequence keys
        self.SCT.bind(sequence = "<Shift-Return>",      func = lambda event: self.regular_newline())
        self.SCT.bind(sequence = "<Return>",            func = lambda event: self.smart_newline())
        self.SCT.bind(sequence = "<Control-BackSpace>", func = lambda event: self.delete_word())
        self.SCT.bind(sequence = "<Key>",               func = lambda event: self.on_key_pressed())
        self.SCT.bind(sequence = "<<Modified>>",        func = lambda event: self.on_inp_modified(), add = "+") # 'add' keyword necessary because CodeBlock already uses bind "<<Modified>>"

    def redo(self):
        try:
            self.SCT.edit_redo()
        except tk.TclError: # when reaching the bottom of the stack and nothing can be redone this error is thrown
            pass
        return "break" # to prevent edit_undo() to trigger when having capslock on

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
        self.change_selected_text(change = +int(self.ed.chng_SBX.gt()))

    def decrement_selected_text(self):
        self.change_selected_text(change = -int(self.ed.chng_SBX.gt()))

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
                self.select_text(sel_range[0], new_text)

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

    def __init__(self, root, command, text:str = None, img_default = None, img_hovering = None, img_clicked = None, img_locked = None, click_display_time:int = 30, locked:bool = False, *args, **kwargs):
        self.root = root
        ttk.Label.__init__(self, self.root, *args, **kwargs)
        self.command = command
        self.hovering = False # mouse is on button
        self.pressing = False # button is getting pressed down
        self.clicked  = False # button got activated
        self.click_display_time = click_display_time
        self.locked = locked
        self.img_default  = None
        self.img_hovering = None
        self.img_clicked  = None
        self.img_locked   = None

        if text:
            self.config(text = text)
        if img_default:
            self.image_flag = True
            self.img_default = img_default
            if img_hovering:
                self.img_hovering = img_hovering
            else:
                self.img_hovering = self.img_default
            if img_clicked:
                self.img_clicked = img_clicked
            else:
                self.img_clicked = self.img_default
            if img_locked:
                self.img_locked = img_locked
            else:
                self.img_locked = self.img_default
            self.set_img(self.img_default) if not self.locked else self.set_img(self.img_locked)
        else:
            self.image_flag = False

        self.bind(sequence = "<Enter>", func = self.on_enter)
        self.bind(sequence = "<Leave>", func = self.on_leave)
        self.bind(sequence = "<ButtonPress-1>",   func = self.on_pressed)
        self.bind(sequence = "<ButtonRelease-1>", func = self.on_released)

    def set_img(self, img):
        if self.image_flag:
            self.config(image = img)

    def lock(self):
        self.locked = True
        self.set_img(self.img_locked)

    def unlock(self):
        self.locked = False
        if self.hovering:
            self.set_img(self.img_hovering)
        else:
            self.set_img(self.img_default)

    def on_enter(self, event = None):
        self.hovering = True
        if not self.locked:
            if not self.pressing:
                self.set_img(self.img_hovering)
            else:
                self.set_img(self.img_clicked)

    def on_leave(self, event = None):
        self.hovering = False
        if not self.clicked and not self.locked:
            self.set_img(self.img_default)

    def on_pressed(self, event = None):
        if not self.locked:
            self.pressing = True
            self.set_img(self.img_clicked)

    def on_released(self, event = None):
        self.pressing = False
        if self.hovering and not self.locked:
            self.clicked = True
            self.root.after(self.click_display_time, self.after_click)
            self.command()

    def after_click(self):
        self.clicked = False
        if not self.locked: # for the rare case that the button gets locked during the click
            if self.hovering:
                self.set_img(self.img_hovering)
            else:
                self.set_img(self.img_default)


class OptionMenu(ttk.OptionMenu):

    def __init__(self, root, textvariable:tk.StringVar, default_option, options:dict, command = lambda event: print(), **kwargs):
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


class Spinbox(tk.Frame):

    def __init__(self, root, abs_root = None, min:int = 0, max:int = 100, default:int = None, textvariable:tk.IntVar = None, threshold:int = 15, bg = None, width:int = None, height = None, wrap = None, *args, **kwargs):
        if default is None:
            default = min
        if min >= 0 and max >= 0 and default >= 0:
            self.min = min
            self.max = max
            self.last_valid_inp = default
        else:
            raise ValueError(f"Spinbox: Either min ({min}), max ({max}) or default ({default}) is negative.")
        self.textvariable = textvariable
        self.root = root
        tk.Frame.__init__(self, self.root, bg = bg)
        width = len(str(max)) if not width else width
        self.text = tk.Text(self, width = width, height = 1, wrap = "none", *args, **kwargs)
        self.text.pack(side = "left")
        abs_root = abs_root if abs_root else self.root
        self.slider = Slider(self, abs_root = abs_root, command = self.update, threshold = threshold)
        self.slider.pack(side = "right")
        self.already_modified = False
        self.st(default)
        if self.textvariable:
            self.textvariable.set(self.gt())
            self.textvariable.trace_add("write", self.on_textvariable_change)
        self.text.bind(sequence = "<<Modified>>", func = lambda event: self.validate_chars())
        self.text.bind(sequence = "<Return>",     func = lambda event: self.focus_out())
        self.text.bind(sequence = "<Escape>",     func = lambda event: self.focus_out())
        self.text.bind(sequence = "<FocusIn>",    func = lambda event: self.select_all())
        self.text.bind(sequence = "<FocusOut>",   func = lambda event: self.update())

    def gt(self):
        return int(self.text.get(1.0, "end-1c"))

    def st(self, value:int):
        self.text.delete(1.0, "end-1c")
        self.text.insert("end-1c", str(value))

    def on_textvariable_change(self, *args):
        self.st(self.textvariable.get())

    def validate_chars(self): # check for nonnumeral characters on <Key>
        if self.already_modified:
            self.already_modified = False
        else:
            inp = self.text.get(1.0, "end-1c")
            if inp.isdigit():
                if inp[0] == "0": # overwriting to avoid "003" instead of "3"
                    i = 0
                    for digit in inp: # find all zeros at front
                        if digit == "0":
                            i += 1
                        else:
                            break
                    if i != len(inp): # cut of zeros at front
                        inp = inp[i:]
                    else: # inp was only zeros
                        inp = 0
                    self.st(inp)
                self.last_valid_inp = int(inp)
            elif inp == "":
                self.last_valid_inp = 0
                self.st(0)
            else: # reset invalid change
                self.st(self.last_valid_inp)
            self.already_modified = True
            self.text.edit_modified(False)

    def focus_out(self):
        self.root.focus_force()
        self.root.lift()
        self.root.update()

    def select_all(self):
        self.text.tag_add("sel", 1.0, "end-1c")

    def update(self, change:int = 0):
        self.validate_range(change)
        if self.textvariable:
            self.textvariable.set(self.gt())

    def validate_range(self, change): # check for invalid numbers on <Enter>, <FocusOut> or Slider change
        inp = self.gt() + change
        if inp < self.min:
            self.st(self.min)
        elif inp > self.max:
            self.st(self.max)
        elif change != 0:
            self.st(inp)


class Slider(tk.Label): # used by Spinbox

    def __init__(self, root, command, abs_root = None, threshold:int = 15, width = 1, *args, **kwargs):
        self.root = root
        img_slider_wheel = gt_img_slider_wheel()
        super().__init__(self.root, height = 16, width = width, image = img_slider_wheel, *args, **kwargs)
        self.image = img_slider_wheel # needs to be assigned for displaying to work
        self.abs_root = abs_root if abs_root else self.root
        self.command = command
        self.threshold = threshold # determines the speed; set to 1 for fastest sliding
        self.hovering = False
        self.pressed = False
        self.click_flag = False
        self.motion_tracker = None
        self.last_y = None
        self.delta_y = 0
        self.bind(sequence = "<Enter>",           func = lambda event: self.on_enter())
        self.bind(sequence = "<Leave>",           func = lambda event: self.on_leave())
        self.bind(sequence = "<ButtonPress-1>",   func = lambda event: self.on_pressed())
        self.bind(sequence = "<ButtonRelease-1>", func = self.on_released)

    def notify_listener(self, change):
        self.click_flag = False # prevent clicks on change by motion
        if self.command:
            self.command(change = change)

    def on_enter(self):
        self.hovering = True
        self.root.config(cursor = "double_arrow")

    def on_leave(self):
        self.hovering = False
        if not self.pressed:
            self.root.config(cursor = "arrow")

    def on_pressed(self):
        self.pressed = True
        self.click_flag = True
        self.root.after(200, self.prevent_click)
        self.motion_tracker = self.abs_root.bind(sequence = "<Motion>", func = self.on_motion) # abs_root is the root where the motion should be tracked (which goes beyond the Slider widget); it is ideally set to tk.Tk()

    def prevent_click(self):
        self.click_flag = False

    def on_released(self, event):
        if self.click_flag:
            self.click_flag = False
            if event.y < 11:
                self.notify_listener(1)
            else:
                self.notify_listener(-1)
        self.pressed = False
        self.abs_root.unbind(sequence = "<Motion>", funcid = self.motion_tracker)
        self.last_y = None
        if not self.hovering:
            self.root.config(cursor = "arrow")

    def on_motion(self, event):
        if self.last_y:
            self.delta_y += self.last_y - event.y
            if self.delta_y >= self.threshold:
                self.delta_y = 0
                self.notify_listener(1)
            elif self.delta_y <= -self.threshold:
                self.delta_y = 0
                self.notify_listener(-1)
        self.last_y = event.y


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

    - Modified slightly by Blyfh

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