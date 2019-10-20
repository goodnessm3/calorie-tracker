from tkinter import *
import db
import re
from graphs import *
import datetime


class LoggingMixIn:

    """provides a method to send a message, via the application root object, to a console that
    prints the text output."""

    _root = None
    # this method is provided by all other tkinter classes that will be mixed in
    # it gets a reference to the app root object

    def log(self, msg):

        self._root().log(msg)


class App(Frame, LoggingMixIn):

    """top level window containing everything else"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.cont1 = Frame(self)
        self.cont1.pack(side=LEFT)
        self.cont2 = Frame(self, relief=RIDGE)
        self.cont2.pack(side=LEFT, padx=20)

        self.graph_window = GraphWindow(self)
        self.graph_window.pack(side=LEFT, fill=BOTH, expand=YES)

        self.recipe_name_container = Frame(self.cont1)
        self.recipe_name_container.pack(side=TOP, pady=20)
        self.recipe_name_label = Label(self.recipe_name_container, text="Recipe name")
        self.recipe_name_label.pack(side=LEFT)
        self.recipe_name_input = Entry(self.recipe_name_container)
        # if this has text in it, add new entries to the recipe. Else just add entries
        # to the daily record.
        self.recipe_name_input.pack(side=LEFT)

        self.recipe_portion_label = Label(self.recipe_name_container, text="Portions:")
        self.recipe_portion_label.pack(side=LEFT)
        self.recipe_portion_input = Entry(self.recipe_name_container, width=2)
        self.recipe_portion_input.pack(side=LEFT)

        self.commit_recipe_button = Button(self.recipe_name_container,
                                           text="Commit recipe",
                                           command=self.add_recipe)
        self.commit_recipe_button.pack(side=RIGHT)

        self.entry_boxes = MyEntryBoxes(self.cont1)
        self.entry_boxes.pack(side=TOP)

        self.console = LoggingConsole(self.cont1, height=20, width=30)
        # this receives messages from the root object
        self.console.pack(side=TOP, fill=BOTH, expand=YES)

        self.running_totals = RunningTotals(self.cont2, borderwidth=5, relief=RIDGE)
        self.running_totals.pack(side=TOP)

        self.ingredient_adder = IngredientAdder(self.cont2, borderwidth=5, relief=RIDGE)
        self.ingredient_adder.pack(side=TOP)

        self.inglist = []  # the list of ingredients currently accumulating for a new recipe

    def add_entry(self, e):

        rname = self.recipe_name_input.get()
        content = self.entry_boxes.get_content()
        i, j, k = content
        if self.entry_boxes.checkbox_var.get():
            # "speculative" checkbox is ticked and user just wants to make a plan, not enter into db
            nutritional_info = db.calc_nutritional_content(content)
            self.running_totals.increment_displayed_values(nutritional_info)
            self.log(f"Added {i}: {j} {k} to speculative running total.\n")
            self.entry_boxes.clear_all()
            return  # return early to stop the db adding code running

        if rname:
            # adding a new recipe
            self.inglist.append(content)
            self.log(f"Added {i}: {j} {k} to the recipe for {rname}.\n")
        else:
            # recording what was eaten today
            nutritional_info = db.record_consumption(content)
            self.running_totals.increment_displayed_values(nutritional_info)
            self.log(f"Consumed {i}: {j} {k}.\n")
        self.entry_boxes.clear_all()

    def add_recipe(self):

        nm = self.recipe_name_input.get()
        portions = self.recipe_portion_input.get()
        if not portions:
            self.log("Portion size not entered\n")
            return
        db.add_recipe(nm, self.inglist, portions)
        self.recipe_name_input.delete(0, END)
        self.recipe_portion_input.delete(0, END)
        self.inglist = []
        self.log(f"Added recipe for {nm} to the database.\n")
        self.entry_boxes.refresh_autocompletes()


class GraphWindow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.pie_container = Frame(self)
        self.graph_container = Frame(self)
        self.config(bg="white")

        self.today_pie = Frame()
        self.yesterday_pie = Frame()
        # these are overwritten when new pie charts are displayed and are immediately destroyed

        self.show_calorie_split_chart("now")
        self.show_macro_split_chart("now")  # set up pie charts with today's data

        historical_info = db.get_daily_totals()
        line_graph_data = self.prepare_line_data_series(historical_info)

        weight_info = db.get_daily_weighins()
        weight_data = self.prepare_line_data_series(weight_info)
        i, j = weight_data

        a, b = line_graph_data
        self.line_graph = DateGraphWidget(self.graph_container, xdata=a,
                                          caldata=[x["sum(kcals)"] for x in b],
                                          xdata2=i,
                                          weightdata=[x["weighin"] for x in j])
        self.line_graph.set_title("Daily kcals/weight")

        macronutrient_info = self.prepare_macronutrient_data_series(historical_info)
        a, b = macronutrient_info
        self.macro_graph = MultiDateGraphWidget(self.graph_container, xdata=a, ydata=b)
        self.macro_graph.set_title("Daily macronutrients")

        self.pie_container.pack(side=TOP, fill=BOTH, expand=YES)
        self.today_pie.pack(side=LEFT, fill=BOTH, expand=YES)
        self.yesterday_pie.pack(side=LEFT, fill=BOTH, expand=YES)
        self.graph_container.pack(side=TOP, fill=BOTH, expand=YES)
        self.graph_container.config(bg="white")
        self.line_graph.pack(side=LEFT, fill=BOTH, expand=YES, padx=30)
        self.macro_graph.pack(side=LEFT, fill=BOTH, expand=YES)

    def prepare_pie_data_series(self, row):

        """converts the sqlite row to a pair of lists suitable for the pie chart widget"""

        names = []
        values = []
        for k in ["sum(protein)", "sum(carbohydrate)", "sum(fat)"]:
            names.append(k)
            values.append(row[k])
        return names, values

    def prepare_calorie_data_series(self, dc):

        """converts the sqlite row to a pair of lists suitable for the pie chart widget"""

        names = []
        values = []
        for k in dc.keys():
            names.append(k)
            values.append(dc[k])
        return names, values

    def show_calorie_split_chart(self, date):

        items = db.get_day_consumption(date)
        self.today_pie.destroy()
        chart = PieChartWidget(self.pie_container, data_series=self.prepare_calorie_data_series(items))
        chart.set_title(f"Calorie split for {date}")
        self.today_pie = chart
        self.today_pie.pack(side=LEFT, fill=BOTH, expand=YES)

    def show_macro_split_chart(self, date):

        info = db.get_daily_totals(date=date)[0]
        self.yesterday_pie.destroy()
        chart = PieChartWidget(self.pie_container,
                                data_series=self.prepare_pie_data_series(info))
        chart.set_title(f"Macronutrient split for {date}")
        self.yesterday_pie = chart
        self.yesterday_pie.pack(side=LEFT, fill=BOTH, expand=YES)

    def prepare_line_data_series(self, rowlist):

        """converts the sqlite query for the last 30 days into a pair of lists
        [date1, date2..], [value1, value2...]"""

        dates = []
        vals = []
        for x in rowlist:
            dates.append(datetime.datetime.strptime(x["date(entry_time)"], "%Y-%m-%d"))
            # the graph needs to be given datetime objects rather than date strings, otherwise it will
            # plot the x-axis as categories rather than a continuous scale
            vals.append(x)
        return dates, vals

    def prepare_macronutrient_data_series(self, rowlist):

        """converts the historical sqlite query into a dict of protein, carbs, fat per day"""
        # TODO: refactor this as a variant of prepare_line_data, pass desired keys

        dates = []
        values = []
        for x in rowlist:
            dates.append(datetime.datetime.strptime(x["date(entry_time)"], "%Y-%m-%d"))
            tmp = {}
            for k in ["protein", "carbohydrate", "fat"]:
                v = x[f"sum({k})"]
                tmp[k] = v
            values.append(tmp)

        return dates, values


class RunningTotals(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.weighin = WeighIn(self)
        self.weighin.pack(side=TOP, expand=YES, fill=BOTH)
        self.title = Label(self, text="Today's consumption")
        self.title.pack(side=TOP)
        self.readings = {}
        self.reading_values = {}

        self.label_con = Frame(self)
        self.label_con.pack(side=TOP)

        for x in ["protein", "carbohydrate", "fat", "kcals"]:
            con = Frame(self.label_con)
            lab = Label(con, text=f"{x}:")
            lab.pack(side=LEFT)
            lab2 = Label(con, text=0)
            lab2.pack(side=RIGHT)
            self.readings[x] = lab2  # dictionary to look up label and change the displayed value
            self.reading_values[x] = 0.0
            con.pack(side=TOP, fill=BOTH)

        today_info = db.get_daily_totals(date="now")[0]  # read in the day's entries already made

        tmp = {}
        for x in ["protein", "carbohydrate", "fat", "kcals"]:
            val = today_info[f"sum({x})"]  # keys are different because we used and SQL sum query
            tmp[x] = val
        self.increment_displayed_values(tmp)

    def increment_displayed_values(self, adict):

        """pass in a dict containing protein, carbohydrate, fat, kcals"""

        for k in ["protein", "carbohydrate", "fat", "kcals"]:
            old_val = self.reading_values[k]
            new_val = old_val + float(adict[k])
            self.readings[k].configure(text=round(new_val, 2))
            self.reading_values[k] = new_val


class WeighIn(Frame, LoggingMixIn):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        lab = Label(self, text="Today's weight (kg):")
        self.entry = Entry(self, width=4)
        button = Button(self, text="Enter", command=self.submit_weight)
        lab.pack(side=LEFT)
        self.entry.pack(side=LEFT)
        button.pack(side=LEFT)

    def submit_weight(self):

        val = self.entry.get()
        db.enter_weight(val)
        self.log(f"entered weigh-in {val} kg into the db")
        self.entry.delete(0, END)


class IngredientAdder(Frame, LoggingMixIn):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        title = Label(self, text="Enter new ingredient:")
        title.pack(side=TOP)
        self.entries = {}  # dict to look up values in the entry boxes
        for x in ["name", "kcals", "fat", "carbohydrate", "protein", "unit", "serving_size", "container_name"]:
            con = Frame(self)
            lab = Label(con, text=x)
            lab.pack(side=LEFT)
            entry = Entry(con)
            entry.pack(side=RIGHT)
            self.entries[x] = entry
            con.pack(side=TOP, fill=BOTH, expand=YES)
        self.confirm_button = Button(self, text="Confirm", command=self.add_ingredient)
        self.confirm_button.pack(side=TOP, pady=20)

    def add_ingredient(self):

        out = {}

        for x in ["name", "kcals", "fat", "carbohydrate", "protein", "unit", "serving_size", "container_name"]:
            value = self.entries[x].get()
            out[x] = value
            self.entries[x].delete(0, END)
            if x == "name":
                ingname = value

        db.add_ingredient(out)
        self.log(f"Added ingredient {ingname} to the database.\n")
        self.master.master.entry_boxes.refresh_autocompletes()  # master is the top level frame


class MyEntryBoxes(Frame):

    """three text entry boxes, item name, amount, and unit"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.cont1 = Frame(self)
        self.cont2 = Frame(self)
        self.ingredient_autocompletes = db.get_all_ingredient_names()
        self.recipe_autocompletes = db.get_all_recipe_names()

        for label in ("name", "amount", "unit"):
            la = Label(self.cont2)
            la.configure(text=label)
            la.pack(side=LEFT, fill=BOTH, expand=YES)
        self.cont2.pack(side=TOP, fill=BOTH, expand=YES)

        self.name_entry = Entry(self.cont1)
        self.name_entry.pack(side=LEFT)
        self.name_entry.bind("<KeyRelease>", self.te_function)
        self.name_entry.bind("<Tab>", self.te_tab_down)
        self.name_entry.bind("<Up>", self.te_arrow)
        self.name_entry.bind("<Down>", self.te_arrow)
        # override behaviour where tab selects the next widget
        # returning "break" stops the event from propagating

        self.amount_entry = Entry(self.cont1)
        self.amount_entry.pack(side=LEFT)

        self.unit_entry = Entry(self.cont1)
        self.unit_entry.pack(side=LEFT)

        self.unit_entry.bind("<Return>", self.master.master.add_entry)
        # NOTE: "<Enter>" means when the mouse enters the widget
        self.unit_entry.bind("<Tab>", self.unit_tab_down)

        self.cont1.pack(side=TOP)

        self.checkbox_var = IntVar()
        self.speculative_container = Frame(self)
        self.spec_label = Label(self.speculative_container, text="Speculative")
        self.spec_label.pack(side=LEFT)
        self.spec_checkbox = Checkbutton(self.speculative_container, variable=self.checkbox_var)
        self.spec_checkbox.pack(side=LEFT)
        self.speculative_container.pack(side=TOP)

        self.content = ""
        self.unit = None
        self.vessel = None

        self.lb = Listbox(self, exportselection=0)
        self.lb.pack(side=TOP, fill=BOTH, expand=YES, pady=10)
        for word in self.ingredient_autocompletes:
            self.lb.insert(0, word)
        self.lb.selection_set(0)

        self.recipe_box = Listbox(self, exportselection=0)
        self.recipe_box.pack(side=TOP, fill=BOTH, expand=YES)
        for word in db.get_all_recipe_names():
            self.recipe_box.insert(0, word)
        self.recipe_box.selection_set(0)
        # !!ONLY ONE LIST BOX CAN HAVE AN ACTIVE SELECTION AT ONE TIME!! #
        # exportselection=0 overrides this behaviour

    def refresh(self, listbox, lst, partial):

        """fill a listbox with items from list only if they contain the string partial"""

        listbox.delete(0, END)
        for x in lst:
            if re.search(partial, x):
                listbox.insert(0, x)
        listbox.selection_set(0)

    def refresh_autocompletes(self):

        self.ingredient_autocompletes = db.get_all_ingredient_names()
        self.recipe_autocompletes = db.get_all_recipe_names()

    def te_function(self, e):

        if e.keycode == 40 or e.keycode == 38:
            # up is 38, dn is 40
            return

        if not e.keycode == 9:  # tab
            self.content = e.widget.get()
            for box, lst in zip((self.lb, self.recipe_box),
                                (self.ingredient_autocompletes, self.recipe_autocompletes)):
                self.refresh(box, lst, self.content)

            options = self.lb.get(0, END) + self.recipe_box.get(0, END)

            if not e.keycode == 8:  # backspace
                if len(options) == 1:
                    e.widget.delete(0, END)
                    e.widget.insert(0, options[0])

    def te_tab_down(self, e):

        """autocompletes the selected ingredient, and fills in the unit option in the unit field"""

        index = self.lb.curselection()  # it's a tuple of indexes always of length 1, so get the first
        if index:
            name = self.lb.get(0, END)[index[0]]  # get all items, then look up by index
        else:
            # index is an empty tuple if no selection i.e. the list has been filtered so there is nothing
            # displayed and the user wants something from the recipe list
            name = self.recipe_box.get(0, END)[0]  # just get the first thing from the recipe list

        e.widget.delete(0, END)
        e.widget.insert(0, name)
        row = db.get_ingredient(name)  # to get the unit
        if row:
            self.unit = row["unit"]
            self.vessel = row["container_name"]
        else:
            row = db.get_recipe(name)
            self.unit = "meal"
            self.vessel = None

        if not row:
            raise KeyError("ingredient or recipe not in db")

        self.unit_entry.delete(0, END)  # clear it in case there's something in there
        self.unit_entry.insert(0, self.unit)

    def unit_tab_down(self, e):

        """tab between unit or container name e.g. grams or can"""
        displayed = self.unit_entry.get()
        self.unit_entry.delete(0, END)
        if displayed == self.unit:
            if self.vessel:
                # sometimes there is no container specified, in which case, do nothing
                self.unit_entry.insert(0, self.vessel)
        elif displayed == self.vessel or not displayed:
            self.unit_entry.insert(0, self.unit)

        return "break"  # suppress moving the focus to the next field

    def te_arrow(self, e):

        current = self.lb.curselection()  # a tuple of indexes, so the first item is (0,)
        ind = current[0]
        all_items = list(self.lb.get(0, END))
        self.lb.selection_clear(0, END)
        if e.keycode == 38:
            # up
            ind -= 1
            if ind < 0:
                ind = len(all_items) - 1
        elif e.keycode == 40:
            # down
            ind += 1
            if ind >= len(all_items):
                ind = 0
        self.lb.selection_set(ind)

    def get_content(self):

        """return the contents of the text widgets"""
        a = self.name_entry.get()
        b = self.amount_entry.get()
        c = self.unit_entry.get()

        return a, b, c

    def clear_all(self):

        for x in self.name_entry, self.unit_entry, self.amount_entry:
            x.delete(0, END)
        self.name_entry.focus_set()


class LoggingConsole(Text):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.config(state=DISABLED)  # user can't type in here
        self._root().console = self
        # put a reference in our custom root object so it can direct logging messages here

    def log_message(self, msg):

        self.config(state=NORMAL)  # temporarily re-enable so we can add text
        self.insert("1.0", f"{msg}\n")
        # insert in line 1, column 0 (lines start from 1)
        # this makes sure the new message comes at the top
        self.delete("20.0", END)  # trim old messages
        self.config(state=DISABLED)


class MyRoot(Tk):

    """custom root class that contains top-level functions for the application, like redirecting log
    messages to the logging console"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.title("Calorie counter")
        self.console = None  # when a console is created, it registers itself with the root object
        self.app = App(self)  # the main window frame containing all other frames
        self.app.pack()

    def log(self, msg):

        """redirect a message to the registered logging console"""

        if self.console:
            self.console.log_message(msg)

    def show_pie_charts(self, date):

        self.app.graph_window.show_calorie_split_chart(date)
        self.app.graph_window.show_macro_split_chart(date)


root = MyRoot()
#root.title("Calorie counter")
#app = App(root)
#app.pack()
root.mainloop()
