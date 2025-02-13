from gi.repository import Gtk, Adw
import copy
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.backends.backend_gtk4agg import (
    FigureCanvasGTK4Agg as FigureCanvas)
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)
from . import datman, utilities, rename_label
from matplotlib.widgets import SpanSelector
from cycler import cycler
import matplotlib.font_manager
import time 

def define_highlight(self, span=None):
    self.highlight = SpanSelector(
        self.canvas.top_right_axis,
        on_select,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.3, facecolor = "tab:blue", linewidth = 0),
        handle_props=dict(linewidth=0),
        interactive=True,
        drag_from_anywhere=True)
    if span is not None:
        self.highlight.extents = span
        self.highlight.set_visible(True)
        self.highlight.set_active(True)

def on_select(self, xmin):
    pass

def hide_highlight(self):
    win = self.props.active_window
    button = win.select_data_button
    self.highlight.set_visible(False)
    self.highlight.set_active(False)
    button.set_active(False)

def toggle_highlight(shortcut, _, self):
    win = self.props.active_window
    button = win.select_data_button
    if self.highlight == None:
        define_highlight(self)    
    if button.get_active():
        hide_highlight(self)
    else:
        button.set_active(True)
        self.highlight.set_visible(True)
        self.highlight.set_active(True)
    self.canvas.draw()


def plot_figure(self, canvas, X, Y, filename="", xlim=None, linewidth = 2, title="", scale="log",marker=None, linestyle="solid",
                     revert = False, color = None, marker_size = 10, y_axis = "left", x_axis = "bottom"):
    if y_axis == "left":
        if x_axis == "bottom":
            canvas.ax.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_left_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
    elif y_axis == "right":
        if x_axis == "bottom":
            canvas.right_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_right_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
    set_legend(self, canvas)

def set_legend(self, canvas):
    if self.plot_settings.legend:
        canvas.legends = []
        lines, labels = canvas.ax.get_legend_handles_labels()
        lines2, labels2 = canvas.right_axis.get_legend_handles_labels()
        lines3, labels3 = canvas.top_left_axis.get_legend_handles_labels()
        lines4, labels4 = canvas.top_right_axis.get_legend_handles_labels()
        canvas.top_right_axis.legend(lines + lines2 + lines3 + lines4, labels + labels2 + labels3 + labels4, loc=0)

def set_canvas_limits_axis(self, canvas, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
    left_datadict = dict()
    right_datadict = dict()
    top_datadict = dict()
    bottom_datadict = dict()
    graph_limits = limits
    for axis in [canvas.ax, canvas.right_axis, canvas.top_left_axis, canvas.top_right_axis]:
        graph_limits_new = find_limits(self, axis, canvas, self.datadict)
        if graph_limits_new["xmin"] is not None:
            graph_limits = graph_limits_new
            set_canvas_limits(self, graph_limits, axis)
            
def set_canvas_limits(self, graph_limits, axis, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
    for key, item in limits.items():
        if item is not None:
            graph_limits[key] = item
    x_span = (graph_limits["xmax"] - graph_limits["xmin"])
    y_span = (graph_limits["ymax"] - graph_limits["ymin"]) 
    if axis.get_xscale() == "linear":
        graph_limits["xmin"] -= 0.015*x_span
        graph_limits["xmax"] += 0.015*x_span
    if axis.get_yscale() == "linear":
        if y_span != 0:
            if graph_limits["ymin"] > 0:
                graph_limits["ymin"] *= 0.95
            else:
                graph_limits["ymin"] *= 1.05
            graph_limits["ymax"] *= 1.05        
        else:
            graph_limits["ymax"] +=  abs(graph_limits["ymax"]*0.05)            
            graph_limits["ymin"] -=  abs(graph_limits["ymin"]*0.05)
    else:
        graph_limits["ymin"] *= 0.5
        graph_limits["ymax"] *= 2
    try:
        axis.set_xlim(graph_limits["xmin"], graph_limits["xmax"])
        axis.set_ylim(graph_limits["ymin"], graph_limits["ymax"])
    except ValueError:
        print("Could not set limits, one of the values was probably infinite")
        
def find_limits(self, axis, canvas, datadict):
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None
    if axis == canvas.ax:
        xaxis = "bottom"
        yaxis = "left"
    elif axis == canvas.right_axis:
        xaxis = "bottom"
        yaxis = "right"
    elif axis == canvas.top_left_axis:
        xaxis = "top"
        yaxis = "left"
    elif axis == canvas.top_right_axis:
        xaxis = "top"
        yaxis = "right"    

    for key, item in datadict.items():
        if item is not None and len(item.xdata) > 0 and item.plot_Y_position == yaxis and item.plot_X_position == xaxis:
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)
            if len(nonzero_ydata) > 0:
                ymin_item = min(nonzero_ydata)
            else:
                ymin_item = min(item.ydata)
            ymax_item = max(item.ydata)

            if xmin_all == None:
                xmin_all = xmin_item
            if xmax_all == None:
                xmax_all = xmax_item
            if ymin_all == None:
                ymin_all = ymin_item
            if ymax_all == None:
                ymax_all = ymax_item

            if xmin_item < xmin_all:
                xmin_all = xmin_item
            if xmax_item > xmax_all:
                xmax_all = xmax_item
            if (ymin_item < ymin_all):
                ymin_all = ymin_item
            if ymax_item > ymax_all:
                ymax_all = ymax_item
    return {"xmin":xmin_all, "xmax":xmax_all, "ymin":ymin_all, "ymax":ymax_all}


def reload_plot(self, from_dictionary = True):
    win = self.props.active_window
    datman.clear_layout(self)
    datman.load_empty(self)
    if len(self.datadict) > 0:
        define_highlight(self)
        hide_highlight(self)
        hide_unused_axes(self, self.canvas)
        datman.open_selection(self, None, from_dictionary)
        set_canvas_limits_axis(self, self.canvas)
    self.canvas.grab_focus()


def refresh_plot(self, canvas = None, from_dictionary = True, set_limits = True):
    if canvas == None:
        canvas = self.canvas
    for line in canvas.ax.lines:
        line.remove()
    for line in canvas.right_axis.lines:
        line.remove()
    for line in canvas.top_left_axis.lines:
        line.remove()
    for line in canvas.top_right_axis.lines:
        line.remove()
    if len(self.datadict) > 0:
        hide_unused_axes(self, canvas)
    datman.open_selection(self, None, from_dictionary, canvas = canvas)
    if set_limits and len(self.datadict) > 0:
        set_canvas_limits_axis(self, canvas)
    self.canvas.draw()

def hide_unused_axes(self, canvas):
    #Double check the code here, seems to work but this is too messy
    for axis in [canvas.ax, canvas.right_axis, canvas.top_left_axis, canvas.top_right_axis]:
        axis.get_xaxis().set_visible(True)
        axis.get_yaxis().set_visible(True)
    left = False
    right = False
    top = False
    bottom = False
    for key, item in self.datadict.items():
        if item.plot_Y_position == "left":
            left = True
        if item.plot_Y_position == "right":
            right = True
        if item.plot_X_position == "top":
            top = True
        if item.plot_X_position == "bottom":
            bottom = True
    if not left:
        canvas.top_left_axis.get_yaxis().set_visible(False)
        canvas.ax.get_yaxis().set_visible(False)
    if not right:
        canvas.top_right_axis.get_yaxis().set_visible(False)
        canvas.right_axis.get_yaxis().set_visible(False)
    if not top:
        canvas.top_right_axis.get_xaxis().set_visible(False)
        canvas.top_left_axis.get_xaxis().set_visible(False)
    if not bottom:
        canvas.ax.get_xaxis().set_visible(False)
        canvas.right_axis.get_xaxis().set_visible(False)

    canvas.top_right_axis.get_xaxis().set_visible(False)
    canvas.right_axis.get_xaxis().set_visible(False)
    canvas.top_right_axis.get_yaxis().set_visible(False)
    canvas.top_left_axis.get_yaxis().set_visible(False)

    
def get_next_color(self):
    color_list = self.canvas.color_cycle
    used_colors = []
    item_rows = copy.copy(self.item_rows)
    color_length = len(color_list)
    if len(item_rows) >= color_length:
        item_rows_list = list(item_rows.items())
        item_rows_list = item_rows_list[-color_length+1:]
        item_rows = dict(item_rows_list)
    for key, item in item_rows.items():
        used_colors.append(item.color_picker.color)
    for color in color_list:
        if color not in used_colors:
            return color

def load_fonts(self):
    font_list = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    for font in font_list:
        try:
            matplotlib.font_manager.fontManager.addfont(font)
        except:
            print(f"Could not load {font}")
            
class PlotSettings:
    def __init__(self, parent):
        self.font_string = parent.preferences.config["plot_font_string"]
        self.xlabel = parent.preferences.config["plot_X_label"]
        self.right_label = parent.preferences.config["plot_right_label"]
        self.top_label = parent.preferences.config["plot_top_label"]
        self.ylabel = parent.preferences.config["plot_Y_label"]
        self.xscale = parent.preferences.config["plot_X_scale"]
        self.yscale = parent.preferences.config["plot_Y_scale"]
        self.right_scale = parent.preferences.config["plot_right_scale"]
        self.top_scale = parent.preferences.config["plot_top_scale"]
        self.title = parent.preferences.config["plot_title"]
        self.font_weight = parent.preferences.config["plot_font_weight"]
        self.font_family = parent.preferences.config["plot_font_family"]
        self.font_size = parent.preferences.config["plot_font_size"]
        self.font_style = parent.preferences.config["plot_font_style"]
        self.tick_direction = parent.preferences.config["plot_tick_direction"]
        self.major_tick_length = parent.preferences.config["plot_major_tick_length"]
        self.minor_tick_length = parent.preferences.config["plot_minor_tick_length"]
        self.major_tick_width = parent.preferences.config["plot_major_tick_width"]
        self.minor_tick_width = parent.preferences.config["plot_minor_tick_width"]
        self.tick_top = parent.preferences.config["plot_tick_top"]
        self.tick_bottom = parent.preferences.config["plot_tick_bottom"]
        self.tick_left = parent.preferences.config["plot_tick_left"]
        self.tick_right = parent.preferences.config["plot_tick_right"]
        self.legend = parent.preferences.config["plot_legend"]
        if Adw.StyleManager.get_default().get_dark(): 
            self.plot_style = parent.preferences.config["plot_style_dark"]
        else:
            self.plot_style = parent.preferences.config["plot_style_light"]

        
class PlotWidget(FigureCanvas):
    def __init__(self, parent=None, xlabel="", ylabel="", yscale = "log", title="", scale="linear", style = "seaborn-whitegrid"):
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvas(self.figure)
        self.one_click_trigger = False
        self.time_first_click  = 0
        self.parent = parent
        self.canvas.mpl_connect('button_release_event', self)
        self.set_style(parent)
        self.ax = self.figure.add_subplot(111)
        self.right_axis = self.ax.twinx()
        self.top_left_axis = self.ax.twiny()
        self.top_right_axis = self.top_left_axis.twinx()
        self.set_ax_properties(parent)
        self.set_save_properties(parent)
        self.set_color_cycle(parent)
        super(PlotWidget, self).__init__(self.figure)

    def set_save_properties(self, parent):
        plt.rcParams["savefig.format"] = parent.preferences.config["savefig_filetype"]
        if parent.preferences.config["savefig_transparent"]:
            plt.rcParams["savefig.transparent"] = True

    def set_ax_properties(self, parent):
        self.title = self.ax.set_title(parent.plot_settings.title)
        self.bottom_label = self.ax.set_xlabel(parent.plot_settings.xlabel, fontweight = parent.plot_settings.font_weight)
        self.right_label = self.right_axis.set_ylabel(parent.plot_settings.right_label, fontweight = parent.plot_settings.font_weight)
        self.top_label = self.top_left_axis.set_xlabel(parent.plot_settings.top_label, fontweight = parent.plot_settings.font_weight)
        self.left_label = self.ax.set_ylabel(parent.plot_settings.ylabel, fontweight = parent.plot_settings.font_weight)
        self.ax.set_yscale(parent.plot_settings.yscale)
        self.right_axis.set_yscale(parent.plot_settings.right_scale)
        self.top_left_axis.set_xscale(parent.plot_settings.top_scale)
        self.top_right_axis.set_xscale(parent.plot_settings.top_scale)
        self.ax.set_xscale(parent.plot_settings.xscale)
        self.set_ticks(parent)

    def set_ticks(self, parent):
        for axis in [self.top_right_axis, self.top_left_axis, self.ax, self.right_axis]:
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.major_tick_length, width=parent.plot_settings.major_tick_width, which="major")
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.minor_tick_length, width=parent.plot_settings.minor_tick_width, which="minor")
            axis.tick_params(axis='x',which='minor')
            axis.tick_params(axis='y',which='minor')
            axis.minorticks_on()
            top = False
            bottom = False
            left = False
            right = False
            for key in parent.datadict.keys():
                if parent.datadict[key].plot_X_position == "top":
                    top = True
                if parent.datadict[key].plot_X_position == "bottom":
                    bottom = True
                if parent.datadict[key].plot_Y_position == "left":
                    left = True
                if parent.datadict[key].plot_Y_position == "right":
                    right = True
            if not (top and bottom):
                axis.tick_params(which = "both", bottom=parent.plot_settings.tick_bottom, top=parent.plot_settings.tick_top)
            if not (left and right):
                axis.tick_params(which = "both", left=parent.plot_settings.tick_left, right=parent.plot_settings.tick_right)

    def set_style(self, parent):
        plt.rcParams.update(plt.rcParamsDefault)
        if Adw.StyleManager.get_default().get_dark():
            self.figure.patch.set_facecolor("#242424")
            params = {"ytick.color" : "w",
            "xtick.color" : "w",
            "axes.labelcolor" : "w",
            "font.family": "sans-serif",
            "font.weight": parent.plot_settings.font_weight,
            "font.sans-serif": parent.plot_settings.font_family,
            "font.size": parent.plot_settings.font_size,
            "font.style": parent.plot_settings.font_style,
            "mathtext.default": "regular"
            }
            plt.style.use(parent.plot_settings.plot_style)
        else:
            self.figure.patch.set_facecolor("#fafafa")
            params = {"ytick.color" : "black",
            "xtick.color" : "black",
            "axes.labelcolor" : "black",
            "font.family": "sans-serif",
            "font.weight": parent.plot_settings.font_weight,
            "font.sans-serif": parent.plot_settings.font_family,
            "font.size": parent.plot_settings.font_size,
            "font.style": parent.plot_settings.font_style,
            "mathtext.default": "regular"
            }
            plt.style.use(parent.plot_settings.plot_style)
        plt.rcParams.update(params)

    def set_color_cycle(self, parent):
        cmap = parent.preferences.config["plot_color_cycle"]
        reverse_dark = parent.preferences.config["plot_invert_color_cycle_dark"]
        if Adw.StyleManager.get_default().get_dark() and reverse_dark:
            cmap += "_r"
        color_cycle = cycler(color=plt.get_cmap(cmap).colors)
        self.color_cycle = color_cycle.by_key()['color']

    def __call__(self, event):
        double_click = False
        if self.one_click_trigger == False:
            self.one_click_trigger = True
            self.time_first_click = time.time()
        else:
            double_click_interval = time.time() - self.time_first_click
            if double_click_interval > 0.5:
                self.one_click_trigger = True
                self.time_first_click = time.time()
            else:
                self.one_click_trigger = False
                self.time_first_click = 0 
                double_click = True
                
        if self.title.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.title)
        if self.top_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.top_label)
        if self.bottom_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.bottom_label)
        if self.left_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.left_label)
        if self.right_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.right_label)



