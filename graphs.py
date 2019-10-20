from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure


class LineGraphWidget(Frame):

    """more straightforward way to have a custom graph widget by embedding the graph and canvas object in
    a frame, then using the parent frame to do the packing, etc, in the UI. This is probably the best way."""

    def __init__(self, *args, xdata=None, ydata=None, **kwargs):

        super().__init__(*args, **kwargs)
        if not(xdata and ydata):
            raise ValueError("must provide x and y data arrays")
        else:
            self.xdata = xdata
            self.ydata = ydata

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.add_subplot(111).plot(xdata, ydata)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def refresh(self):

        self.fig.clear()
        self.fig.add_subplot(111).plot(self.xdata, self.ydata)
        self.canvas.draw()


class PieChartWidget(Frame):

    """custom frame containing a pie chart"""

    def __init__(self, *args, data_series=None, **kwargs):

        """data_series is a pair of lists [name1, name2...], [value1, value2...]"""

        super().__init__(*args, **kwargs)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = None  # this will be defined the first time the redraw function is called

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)
        self.canvas.draw()

    def redraw(self, data_series):

        names, data = data_series
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)  # add_subplot returns an axes object
        wedges, text, autopct = self.ax.pie(data, autopct=lambda x: f"{int(x)}% ", textprops={"color": "w"})
        # the autopct lambda function gets passed the percentage as an argument
        self.ax.legend(wedges, names)
        self.canvas.draw()


class DateGraphWidget(Frame):

    """line graph that expects a pair of data series: two lists
    of values, one for calories per day, the other for weigh-in per day, to plot kcals and weight
    on the same chart"""

    def __init__(self, *args, xdata=None, caldata=None, xdata2=None, weightdata=None, **kwargs):

        super().__init__(*args, **kwargs)
        if not(xdata and caldata):
            raise ValueError("must provide x and y data arrays")
        else:
            self.xdata = xdata
            self.xdata2 = xdata2
            self.caldata = caldata
            self.weightdata = weightdata

        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("weight/kg")

        self.ax2 = self.ax.twinx()  # make a "twinned" axis to have two scales on the same plot
        self.ax2.set_ylabel("kcals")

        p1, = self.ax.plot(xdata2, weightdata, "o-r")
        # pickable data with a tolerance of 5 pixels
        p2, = self.ax2.plot(xdata, caldata, "s-b", picker=5)
        # can only "pick" data from the most recent axis to be plotted

        self.ax.yaxis.label.set_color(p1.get_color())
        self.ax2.yaxis.label.set_color(p2.get_color())
        self.ax.grid(True)
        self.fig.autofmt_xdate()

        self.selected = None
        self.picked = False   # variables for data point picking behaviour

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.mpl_connect("pick_event", self.onpick)
        self.canvas.mpl_connect("button_press_event", self.onmouse)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)

    def onmouse(self, e):

        """function for if the user clicks on the graph canvas but not on a data point, this
        deselects the currently selected data point if there is one."""

        # print("on mouse")
        if not self.picked and len(self.ax2.lines) > 1:
            self.ax2.lines.pop()  # remove the last Line2D object that we plotted
            self.selected = None
        self.canvas.draw()
        self.picked = False

    def onpick(self, e):

        """even for picking a data point with the mouse, note this is run FIRST before the
        mouseevent that generates the pick event"""

        # print("picked")
        # print(e.mouseevent)
        # print(vars(e))
        if self.selected:
            self.ax2.lines.pop()  # remove the last Line2D object that we plotted
            self.selected = None
        if e.mouseevent.button == 1:
            self.selected = self.ax2.plot([self.xdata[e.ind[0]]], [self.caldata[e.ind[0]]], "go", ms=15)
            # the event has an "index" of the data point, but it's returned as a single value list
            # ms is "marker size" for the plot, "go" is green circles
        self.canvas.draw()  # need to refresh the canvas

        self.picked = True
        ret = self.xdata[e.ind[0]].date()
        # the date we get from the graph is "DD-MM-YYYY hh:mm:ss" and we only want the date
        self._root().show_pie_charts(ret)
        # this sends the date of the selected point to the root object, so it can plot a pie charts of
        # data from that date


class MultiDateGraphWidget(Frame):

    """expects one list of date objects and one list of dictionaries, plots each dict
    key on a separate line"""

    def __init__(self, *args, xdata=None, ydata=None, **kwargs):

        super().__init__(*args, **kwargs)
        if not(xdata and ydata):
            raise ValueError("must provide x and y data arrays")
        else:
            self.xdata = xdata
            self.ydata = ydata

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("macronutrient/grams")

        lines = []

        keys = [x for x in ydata[0].keys()]  # get the keys from the first dict and use for all subsequent
        series = {x: [] for x in keys}
        for i in ydata:
            for j in keys:
                series[j].append(i[j])  # assemble a dict of {key1: [value1, value2...]}
        for x in keys:
            a, = self.ax.plot(xdata, series[x], label=x)  # then plot using the dict we just made
            lines.append(a)  # hold a reference to the lines to build the legend

        self.ax.legend(lines, [x.get_label() for x in lines])
        self.ax.grid(True)
        self.fig.autofmt_xdate()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)
