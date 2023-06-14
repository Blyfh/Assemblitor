import tkinter as tk
import tkinter.ttk as ttk

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
            raise RuntimeError(f"OptionMenu : Can't find default option '{self.default_option}' in given options:\n    {self.options}")
        ttk.OptionMenu.__init__(self, root, self.textvariable, default, *self.options.values(), command = command)
        self.config(**kwargs)

    def current_option(self):
        current_option_displaytext = self.textvariable.get()
        for option in self.options:
            if self.options[option] == current_option_displaytext:
                return option
        raise RuntimeError(f"OptionMenu: Can't find current option for selected displaytext '{current_option_displaytext}'.")


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

        self.waittime = waittime  # in miliseconds, originally 500
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