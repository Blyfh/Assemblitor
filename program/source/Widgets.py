import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as st
import string
from typing import Literal

from program.source import Emulator as emu
from program.source import PackHandler as ph


#          Copyright Blyfh https://github.com/Blyfh
# Distributed under the Boost Software License, Version 1.0.
#     (See accompanying file LICENSE_1_0.txt or copy at
#           http://www.boost.org/LICENSE_1_0.txt)


def gt_img_slider_wheel(height=20):  # img_slider_wheel is ideally 5x20 px
    sh = ph.SpriteHandler()
    return sh.gt_sprite("Spinbox", "slider_wheel", 5, height)


# ASSEMBLITOR WIDGETS

class CodeBlock(tk.Frame):
    
    def __init__(self, root, editor, **kwargs):
        self.root = root
        self.ed = editor
        super().__init__(self.root)
        
        self.x_BAR = AutohideScrollbar(self, orient="horizontal")
        self.y_BAR = AutohideScrollbar(self, orient="vertical")
        self.TXT = tk.Text(self, yscrollcommand=self.y_BAR.set, xscrollcommand=self.x_BAR.set, wrap="none",
                           bg=self.ed.theme_text_bg, fg=self.ed.theme_text_fg, font=self.ed.gt_code_font(),
                           insertbackground=self.ed.theme_cursor_color, width=10, bd=0, **kwargs)
        self.TXT.grid(row=0, column=0, sticky="NSEW")
        
        self.x_BAR.config(command=self.TXT.xview)
        self.y_BAR.config(command=self.TXT.yview)
        
        # make Text widget expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


class OutCodeBlock(CodeBlock):
    
    def __init__(self, root, editor):
        super().__init__(root, editor)
        self.TXT.tag_config("code", foreground=self.ed.theme_text_fg)  # "fg" is an invalid argument
        # used by step-by-step mode to highlight the current code line that the PC points to
        self.TXT.tag_config("active_code", foreground=self.ed.theme_accent_color)
        self.TXT.tag_config("error", foreground=self.ed.theme_error_color, wrap="word")
        self.TXT.config(state="disabled")
    
    def append_text(self, text, tag):
        self.TXT.config(state="normal")
        self.TXT.insert("insert", text, tag)
        self.TXT.config(state="disabled")
    
    def clear_text(self):
        self.TXT.config(state="normal")
        self.TXT.delete("1.0", "end")
        self.TXT.config(state="disabled")
    
    def display_output(self, code_section1, active_code, code_section2):
        self.clear_text()
        self.append_text(code_section1, "code")
        if active_code:
            self.append_text(active_code, "active_code")
            self.TXT.yview_moveto(1)  # jumps to current command
        self.append_text(code_section2, "code")
    
    def display_error(self, exception_message, prg_state=None):
        self.clear_text()
        self.append_text(exception_message, "error")
        if prg_state:
            self.append_text(prg_state, "code")


class InpCodeBlock(CodeBlock):
    
    def __init__(self, root, editor):
        super().__init__(root, editor, undo=True)
        self.already_modified = False
        
        # events
        
        bindtags = self.TXT.bindtags()
        # changes bindtag order to let open_file() return "break" before standard class-level binding of <Control-o>
        # that adds a newline
        self.TXT.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3]))
        # automatic edit_redo() bind is <Control-y>
        # double binds necessary due to capslock overwriting lowercase sequence keys
        self.TXT.bind(sequence="<Control-Shift-z>", func=lambda event: self.redo())
        self.TXT.bind(sequence="<Control-Shift-Z>", func=lambda event: self.redo())
        self.TXT.bind(sequence="<Shift-Return>", func=lambda event: self.regular_newline())
        self.TXT.bind(sequence="<Return>", func=lambda event: self.smart_newline())
        self.TXT.bind(sequence="<Control-BackSpace>", func=lambda event: self.delete_word())
        self.TXT.bind(sequence="<Key>", func=lambda event: self.on_key_pressed())
        # 'add' keyword necessary because CodeBlock already uses bind "<<Modified>>"
        self.TXT.bind(sequence="<<Modified>>", func=lambda event: self.on_inp_modified(), add="+")
    
    def redo(self):
        try:
            self.TXT.edit_redo()
        except tk.TclError:  # when reaching the bottom of the stack and nothing can be redone this error is thrown
            pass
        return "break"  # to prevent edit_undo() to trigger when having capslock on
    
    def regular_newline(self):
        pass  # overwrites self.smart_newline()
    
    def smart_newline(self):
        self.insert_address()
        self.TXT.see("insert")  # jump to cursor pos if it gets out of sight (due to newline)
        return "break"  # overwrites excessive newline printing
    
    def insert_address(self):
        last_line = self.TXT.get("insert linestart", "insert")
        last_line_stripped = last_line.lstrip()
        if last_line_stripped == "":  # empty cell (extra check since split() returns empty list without index 0)
            self.TXT.insert("insert", "\n")
            return
        try:
            last_adr = int(last_line_stripped.split()[0])
        except ValueError:
            self.TXT.insert("insert", "\n")
            return
        whitespace_wrapping = last_line.split(last_line_stripped)[0]
        new_adr = emu.add_leading_zeros(str(last_adr + 1))
        self.TXT.insert("insert", "\n" + whitespace_wrapping + new_adr + " ")
    
    def delete_word(self):
        if self.TXT.index("insert") != "1.0":  # to prevent deleting word after cursor on position 0
            if self.TXT.get("insert-1c", "insert") != "\n":  # to prevent deleting the word of the line above
                self.TXT.delete("insert-1c", "insert")  # delete potential space before word
            self.TXT.delete("insert-1c wordstart", "insert")  # delete word
            return "break"
    
    def on_key_pressed(self):
        if self.TXT.get("insert-1c") in string.whitespace:  # last written char is a whitespace
            # add seperator to undo stack so that all actions up to the seperator can be undone -> undoes whole words
            self.TXT.edit_separator()
    
    def on_inp_modified(self):
        if not self.already_modified:  # because somehow on_inp_modified always gets called twice
            self.TXT.edit_modified(False)
            if self.ed.init_inp == self.TXT.get(1.0, "end-1c"):
                # checks if code got reverted to last saved instance (to avoid pointless ask-to-save'ing)
                self.ed.set_dirty_flag(False)
            else:
                self.ed.set_dirty_flag(True)
            self.already_modified = True
        else:
            self.already_modified = False
    
    def increment_selected_text(self):
        self.change_selected_text(change=int(self.ed.chng_SBX.gt()))
    
    def decrement_selected_text(self):
        self.change_selected_text(change=-int(self.ed.chng_SBX.gt()))
    
    def change_selected_text(self, change):
        option = self.ed.chng_opt_OMN.current_option()  # either "adr", "adr_opr", "opr"
        adrs_flag = "adr" in option
        oprs_flag = "opr" in option
        sel_range = self.TXT.tag_ranges("sel")
        if sel_range:
            text = self.TXT.get(*sel_range)
            if text.strip():
                new_text = self.change_text(text, adrs_flag, oprs_flag, change)
                self.TXT.delete(*sel_range)
                self.TXT.insert(sel_range[0], new_text)
                self.select_text(sel_range[0], new_text)
    
    def select_text(self, pos, text):
        self.TXT.tag_add("sel", pos, str(pos) + f"+{len(text)}c")
    
    def change_text(self, text, adrs_flag, oprs_flag, change=1):
        lines = text.split("\n")
        new_text = ""
        for line in lines:
            cell, comment = emu.split_cell_at_comment(line)
            if len(cell):
                if adrs_flag:
                    cell = self.change_adr(cell, change)
                if oprs_flag:
                    cell = self.change_opr(cell, change)
            new_text += cell + comment + "\n"
        return new_text[:-1]  # :-1 to remove line break from last line
    
    def change_adr(self, cell, change):
        tok_strs = emu.Cell.split_cel_str(self=None, cel_str_unstripped=cell)
        cell_rest = "".join(tok_strs[1:])
        adr_str = tok_strs[0]
        i = 0
        while i < len(adr_str) and adr_str[i] in string.whitespace:  # jump over left wrapping
            i += 1
        j = i
        if j < len(adr_str) and adr_str[j] == "-":
            j += 1
        while j < len(adr_str) and adr_str[j] in "0123456789":  # find end of address
            j += 1
        if j < len(adr_str) and adr_str[j] not in string.whitespace:  # chars after address are not supported
            return cell
        old_adr = adr_str[i:j]
        if old_adr and old_adr != "-":
            wrapping = adr_str.split(old_adr)
            new_adr = wrapping[0] + str(int(old_adr) + change) + wrapping[1]
            cell = emu.add_leading_zeros(new_adr) + cell_rest
        return cell
    
    def change_opr(self, cell, change):
        tok_strs = emu.Cell.split_cel_str(self=None, cel_str_unstripped=cell)
        cell_rest = "".join(tok_strs[:-1])
        opr_str = tok_strs[-1]
        i = len(opr_str) - 1
        while i >= 0 and opr_str[i] in string.whitespace:
            i -= 1
        if i >= 0 and opr_str[i] == ")":  # indirect address
            i -= 1
            j = i
            while j >= 0 and opr_str[j] in "0123456789":
                j -= 1
            if j >= 0 and opr_str[j] != "-":
                j += 1
            if j > 0 and opr_str[j - 1] != "(":
                return cell
            if j > 1 and opr_str[j - 2] not in string.whitespace:
                # chars before indirect address are not supported
                return cell
            offset = 1
        else:  # direct address
            j = i
            while j >= 0 and opr_str[j] in "0123456789":
                j -= 1
            if j >= 0 and opr_str[j] != "-":
                j += 1
            if j > 0 and opr_str[j - 1] not in string.whitespace:
                # absolute values or chars before direct address are not supported
                return cell
            offset = 0
        old_opr = opr_str[j:i + 1]
        if old_opr and old_opr != "-":
            wrapping = opr_str.split(old_opr)
            new_opr = wrapping[0][:-1] + str(int(old_opr) + change) + wrapping[1]  # [:-1] because of "("
            cell = cell_rest + "(" * offset + emu.add_leading_zeros(new_opr, offset)
        return cell
    
    def gt_input(self):
        return self.TXT.get(1.0, "end-1c")
    
    def st_input(self, inp_str: str):
        self.TXT.delete("1.0", "end")
        self.TXT.insert("insert", inp_str)


# UNIVERSAL WIDGETS

class Button(ttk.Label):
    
    def __init__(self, root, command, text: str = None, img_default=None, img_hovering=None, img_clicked=None,
                 img_locked=None, click_display_time: int = 30, locked: bool = False, *args, **kwargs):
        self.root = root
        ttk.Label.__init__(self, self.root, *args, **kwargs)
        self.command = command
        self.hovering = False  # mouse is on button
        self.pressing = False  # button is getting pressed down
        self.clicked  = False  # button got activated
        self.click_display_time = click_display_time
        self.locked = locked
        self.img_default  = None
        self.img_hovering = None
        self.img_clicked  = None
        self.img_locked   = None
        
        if text:
            self.config(text=text)
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
        
        self.bind(sequence="<Enter>", func=self.on_enter)
        self.bind(sequence="<Leave>", func=self.on_leave)
        self.bind(sequence="<ButtonPress-1>",   func=self.on_pressed)
        self.bind(sequence="<ButtonRelease-1>", func=self.on_released)
    
    def set_img(self, img):
        if self.image_flag:
            self.config(image=img)
    
    def lock(self):
        self.locked = True
        self.set_img(self.img_locked)
    
    def unlock(self):
        self.locked = False
        if self.hovering:
            self.set_img(self.img_hovering)
        else:
            self.set_img(self.img_default)
    
    def on_enter(self, event=None):
        self.hovering = True
        if not self.locked:
            if not self.pressing:
                self.set_img(self.img_hovering)
            else:
                self.set_img(self.img_clicked)
    
    def on_leave(self, event=None):
        self.hovering = False
        if not self.clicked and not self.locked:
            self.set_img(self.img_default)
    
    def on_pressed(self, event=None):
        if not self.locked:
            self.pressing = True
            self.set_img(self.img_clicked)
    
    def on_released(self, event=None):
        self.pressing = False
        if self.hovering and not self.locked:
            self.clicked = True
            self.root.after(self.click_display_time, self.after_click)
            self.command()
    
    def after_click(self):
        self.clicked = False
        if not self.locked:  # for the rare case that the button gets locked during the click
            if self.hovering:
                self.set_img(self.img_hovering)
            else:
                self.set_img(self.img_default)


class OptionMenu(ttk.OptionMenu):
    
    def __init__(self, root, textvariable: tk.StringVar, default_option, options: dict, command=lambda event: print(),
                 **kwargs):
        self.root = root
        self.options = options  # {"option1_name": "option1_displaytext", "option2_name": "option2_displaytext"}
        self.textvariable = textvariable
        self.default_option = default_option
        try:
            default = self.options[self.default_option]
        except:
            raise RuntimeError(f"OptionMenu: Can't find default option '{self.default_option}' in given options:"
                               f"\n    {self.options}")
        ttk.OptionMenu.__init__(self, root, self.textvariable, default, *self.options.values(), command=command)
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
        raise RuntimeError(f"OptionMenu: Can't find current option for selected displaytext "
                           f"'{current_option_displaytext}'.")


class Spinbox(tk.Frame):
    
    def __init__(self, root, abs_root=None, min: int = 0, max: int = 100, default: int = None,
                 textvariable: tk.IntVar = None, threshold: int = 15, bg=None, height: int = 19, font_size: int = 10,
                 wrap=None, *args, **kwargs):
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
        abs_root = abs_root if abs_root else self.root
        font = tk.font.Font(family="Segoe", size=font_size)
        width_chars = len(str(max))
        width_text = font.measure("9" * width_chars)
        height_text = font.metrics("linespace")
        padx_text = 1
        pady_text = 0 if (pady_fill := int((height - height_text) / 2)) < 1 else pady_fill
        width_slider = 5
        tk.Frame.__init__(self, self.root, width=width_text + padx_text * 2 + 2 + width_slider, height=height, bg=bg)
        self.text = tk.Text(self, width=width_chars, height=1, wrap="none", font=font, padx=padx_text, pady=pady_text,
                            *args, **kwargs)
        self.slider = Slider(self, abs_root=abs_root, command=self.update, threshold=threshold, width=width_slider,
                             height=height)
        self.text.place(x=0, y=0, height=height)
        self.slider.place(x=width_text + padx_text * 2 + 2, y=0)
        self.already_modified = False
        self.st(default)
        if self.textvariable:
            self.textvariable.set(self.gt())
            self.textvariable.trace_add("write", self.on_textvariable_change)
        self.text.bind(sequence="<<Modified>>", func=lambda event: self.validate_chars())
        self.text.bind(sequence="<Return>",     func=lambda event: self.focus_out())
        self.text.bind(sequence="<Escape>",     func=lambda event: self.focus_out())
        self.text.bind(sequence="<FocusIn>",    func=lambda event: self.select_all())
        self.text.bind(sequence="<FocusOut>",   func=lambda event: self.update())
    
    def gt(self):
        return int(self.text.get(1.0, "end-1c"))
    
    def st(self, value:int):
        self.text.delete(1.0, "end-1c")
        self.text.insert("end-1c", str(value))
    
    def on_textvariable_change(self, *args):
        self.st(self.textvariable.get())
    
    def validate_chars(self):  # check for nonnumeral characters on <Key>
        if self.already_modified:
            self.already_modified = False
        else:
            inp = self.text.get(1.0, "end-1c")
            if inp.isdigit():
                if inp[0] == "0":  # overwriting to avoid "003" instead of "3"
                    i = 0
                    for digit in inp:  # find all zeros at front
                        if digit == "0":
                            i += 1
                        else:
                            break
                    if i != len(inp):  # cut of zeros at front
                        inp = inp[i:]
                    else:  # inp was only zeros
                        inp = 0
                    self.st(inp)
                self.last_valid_inp = int(inp)
            elif inp == "":
                self.last_valid_inp = 0
                self.st(0)
            else:  # reset invalid change
                self.st(self.last_valid_inp)
            self.already_modified = True
            self.text.edit_modified(False)
    
    def focus_out(self):
        self.root.focus_force()
        self.root.lift()
        self.root.update()
    
    def select_all(self):
        self.text.mark_set("insert", "end-1c")  # move cursor to the end
        self.text.tag_add("sel", 1.0, "end-1c")
    
    def update(self, change:int = 0):
        self.validate_range(change)
        if self.textvariable:
            self.textvariable.set(self.gt())
    
    def validate_range(self, change):  # check for invalid numbers on <Enter>, <FocusOut> or Slider change
        inp = self.gt() + change
        if inp < self.min:
            self.st(self.min)
        elif inp > self.max:
            self.st(self.max)
        elif change != 0:
            self.st(inp)


class Slider(tk.Label):  # used by Spinbox
    
    def __init__(self, root, command, abs_root=None, threshold: int = 15, width: int = 5, height: int = 20, *args, **kwargs):
        self.root = root
        img_slider_wheel = gt_img_slider_wheel(height)
        super().__init__(self.root, height=height, width=width, image=img_slider_wheel, borderwidth=0, *args, **kwargs)
        self.image = img_slider_wheel  # needs to be assigned for displaying to work
        self.abs_root = abs_root if abs_root else self.root
        self.command = command
        self.threshold = threshold  # determines the speed; 1 is fastest sliding
        self.hovering = False
        self.pressed = False
        self.click_flag = False
        self.motion_tracker = None
        self.last_y = None
        self.delta_y = 0
        self.bind(sequence="<Enter>",           func=lambda event: self.on_enter())
        self.bind(sequence="<Leave>",           func=lambda event: self.on_leave())
        self.bind(sequence="<ButtonPress-1>",   func=lambda event: self.on_pressed())
        self.bind(sequence="<ButtonRelease-1>", func=self.on_released)
    
    def notify_listener(self, change):
        self.click_flag = False  # prevent clicks on change by motion
        if self.command:
            self.command(change=change)
    
    def on_enter(self):
        self.hovering = True
        self.root.config(cursor="double_arrow")
    
    def on_leave(self):
        self.hovering = False
        if not self.pressed:
            self.root.config(cursor="arrow")
    
    def on_pressed(self):
        self.pressed = True
        self.click_flag = True
        self.root.after(200, self.prevent_click)
        self.motion_tracker = self.abs_root.bind(sequence="<Motion>", func=self.on_motion)
        # abs_root is the root where the motion should be tracked (which goes beyond the Slider widget)
        # it is ideally set to tk.Tk()
    
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
        self.abs_root.unbind(sequence="<Motion>", funcid=self.motion_tracker)
        self.last_y = None
        if not self.hovering:
            self.root.config(cursor="arrow")
    
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
        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.on_leave, add="+")
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None
    
    def update_text(self, new_text: str):
        self.text = new_text
    
    def on_enter(self, event=None):
        self.schedule()
    
    def on_leave(self, event=None):
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


class AutohideScrollbar(tk.Scrollbar):
    
    def __init__(self, root, orient: Literal["vertical", "horizontal"], **kw):
        if orient == "vertical":
            self.grid_kw = {"row": 0, "column": 1, "sticky": "NS"}
        elif orient == "horizontal":
            self.grid_kw = {"row": 1, "column": 0, "sticky": "EW"}
        else:
            raise ValueError(f"AutohideScrollbar: orient takes only 'vertical' or 'horizontal', not '{orient}'")
        self.is_needed = False
        self.orient = orient
        super().__init__(root, orient=orient, **kw)
    
    def set(self, first, last):
        if float(first) > 0.0 or float(last) < 1.0:  # if visible text is not at the bounds of the Text
            if not self.is_needed:
                self.grid(**self.grid_kw)
                self.is_needed = True
        elif self.is_needed:
            self.grid_forget()
            self.is_needed = False
        super().set(first, last)
