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
        names, data = data_series  # unpack the passed arg
        self.ax = self.fig.add_subplot(111)  # add_subplot returns an axes object
        wedges, text, autopct = self.ax.pie(data, autopct=lambda x: f"{int(x)}% ", textprops={"color": "w"})
        # the autopct lambda function gets passed the percentage as an argument
        self.ax.legend(wedges, names)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)


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
            self.caldata = caldata

        days = mdates.DayLocator()
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("kcals")

        ax2 = self.ax.twinx()  # make a "twinned" axis to have two scales on the same plot
        ax2.set_ylabel("weight/kg")
        p1, = self.ax.plot(xdata, caldata, "s-b")
        p2, = ax2.plot(xdata2, weightdata, "o-r")
        self.ax.yaxis.label.set_color(p1.get_color())
        ax2.yaxis.label.set_color(p2.get_color())
        self.ax.xaxis.set_minor_locator(days)
        self.ax.xaxis.set_minor_formatter(mdates.DateFormatter("%D"))
        self.ax.grid(True)

        self.fig.autofmt_xdate()


        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)




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

        days = mdates.DayLocator()
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("macronutrient/grams")

        lines = []

        keys = [x for x in ydata[0].keys()]  # get the keys from the first dict and use for all subsequent
        series = {x:[] for x in keys}
        for i in ydata:
            for j in keys:
                series[j].append(i[j])  # assemble a dict of {key1: [value1, value2...]}
        for x in keys:
            a, = self.ax.plot(xdata, series[x], label=x)  # then plot using the dict we just made
            lines.append(a)  # hold a reference to the lines to build the legend

        self.ax.legend(lines, [x.get_label() for x in lines])

        self.ax.xaxis.set_minor_locator(days)
        self.ax.xaxis.set_minor_formatter(mdates.DateFormatter("%D"))
        self.ax.grid(True)
        self.fig.autofmt_xdate()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        widget = self.canvas.get_tk_widget()
        widget.pack(side=TOP, fill=BOTH, expand=YES)

    def set_title(self, title):

        self.ax.set_title(title)