from tkinter import *
import db
import re

class App:

    def __init__(self, master):

        self.container0 = Frame(master)
        self.container0.pack()
        self.container = Frame(self.container0)
        self.container.pack(side=LEFT)
        self.container3 = Frame(self.container0)
        self.container3.pack(side=LEFT, padx=20)

        self.recipe_name_container = Frame(self.container)
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

        self.entry_boxes = MyEntryBoxes(self.container, parent=self)
        self.entry_boxes.pack(side=TOP)

        self.running_totals = RunningTotals(self.container3)
        self.running_totals.pack(side=TOP)

        self.ingredient_adder = IngredientAdder(self.container3, parent=self)
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
            self.entry_boxes.log_message(f"Added {i}: {j} {k} to speculative running total.\n")
            self.entry_boxes.clear_all()
            return  # return early to stop the db adding code running

        if rname:
            # adding a new recipe
            self.inglist.append(content)
            self.entry_boxes.log_message(f"Added {i}: {j} {k} to the recipe for {rname}.\n")
        else:
            # recording what was eaten today
            nutritional_info = db.record_consumption(content)
            self.running_totals.increment_displayed_values(nutritional_info)
            self.entry_boxes.log_message(f"Consumed {i}: {j} {k}.\n")
        self.entry_boxes.clear_all()

    def add_recipe(self):

        nm = self.recipe_name_input.get()
        portions = self.recipe_portion_input.get()
        if not portions:
            self.entry_boxes.log_message("Portion size not entered\n")
            return
        db.add_recipe(nm, self.inglist, portions)
        self.recipe_name_input.delete(0, END)
        self.recipe_portion_input.delete(0, END)
        self.inglist = []
        self.entry_boxes.log_message(f"Added recipe for {nm} to the database.\n")
        self.entry_boxes.refresh_autocompletes()


class RunningTotals():

    def __init__(self, parent_container):

        self.container = Frame(parent_container)
        self.title = Label(self.container, text="Running totals for consumption")
        self.title.pack(side=TOP)
        self.readings = {}
        self.reading_values = {}

        self.label_con = Frame(self.container)
        self.label_con.pack(side=TOP)

        for x in ["protein", "carbohydrate", "fat", "kcals"]:
            con = Frame(self.label_con)
            lab = Label(con, text=f"{x}:")
            lab.pack(side=LEFT)
            lab2 = Label(con, text = 0)
            lab2.pack(side=RIGHT)
            self.readings[x] = lab2  # dictionary to look up label and change the displayed value
            self.reading_values[x] = 0.0
            con.pack(side=TOP, fill=BOTH)

    def pack(self, side):

        self.container.pack(side=side, pady=60)

    def increment_displayed_values(self, adict):

        """pass in a dict containing protein, carbohydrate, fat, kcals"""

        for k in ["protein", "carbohydrate", "fat", "kcals"]:
            old_val = self.reading_values[k]
            new_val = old_val + float(adict[k])
            self.readings[k].configure(text=round(new_val, 2))
            self.reading_values[k] = new_val


class IngredientAdder:

    def __init__(self, parent_container, parent):

        self.container = Frame(parent_container)
        self.parent = parent
        title = Label(self.container, text="Enter new ingredient:")
        title.pack(side=TOP)
        self.entries = {}  # dict to look up values in the entry boxes
        for x in ["name", "kcals", "fat", "carbohydrate", "protein", "unit", "serving_size", "container_name"]:
            con = Frame(self.container)
            lab = Label(con, text=x)
            lab.pack(side=LEFT)
            entry = Entry(con)
            entry.pack(side=RIGHT)
            self.entries[x] = entry
            con.pack(side=TOP, fill=BOTH, expand=YES)
        self.confirm_button = Button(self.container, text="Confirm",command=self.add_ingredient)
        self.confirm_button.pack(side=TOP, pady=20)

    def pack(self, side):

        self.container.pack(side=side)

    def add_ingredient(self):

        out = {}

        for x in ["name", "kcals", "fat", "carbohydrate", "protein", "unit", "serving_size", "container_name"]:
            value = self.entries[x].get()
            out[x] = value
            self.entries[x].delete(0, END)
            if x == "name":
                ingname = value

        db.add_ingredient(out)
        self.parent.entry_boxes.log_message(f"Added ingredient {ingname} to the database.\n")
        self.parent.entry_boxes.refresh_autocompletes()


class MyEntryBoxes():

    """three text entry boxes, item name, amount, and unit"""

    def __init__(self, cont, parent):

        self.parent = parent
        self.container = Frame(cont)
        self.container2 = Frame(self.container)
        self.container3 = Frame(self.container)
        self.ingredient_autocompletes = db.get_all_ingredient_names()
        self.recipe_autocompletes = db.get_all_recipe_names()

        for label in ("name", "amount", "unit"):
            l = Label(self.container3)
            l.configure(text=label)
            l.pack(side=LEFT, fill=BOTH, expand=YES)
        self.container3.pack(side=TOP, fill=BOTH, expand=YES)

        self.name_entry = Entry(self.container2)
        self.name_entry.pack(side=LEFT)
        self.name_entry.bind("<KeyRelease>", self.te_function)
        #self.name_entry.bind("<Tab>", lambda e: "break")
        self.name_entry.bind("<Tab>", self.te_tab_down)
        self.name_entry.bind("<Up>", self.te_arrow)
        self.name_entry.bind("<Down>", self.te_arrow)
        # override behaviour where tab selects the next widget
        # returning "break" stops the event from propagating

        self.amount_entry = Entry(self.container2)
        self.amount_entry.pack(side=LEFT)

        self.unit_entry = Entry(self.container2)
        self.unit_entry.pack(side=LEFT)
        self.unit_entry.bind("<Return>", self.parent.add_entry)
        # NOTE: "<Enter>" means when the mouse enters the widget
        self.unit_entry.bind("<Tab>", self.unit_tab_down)

        self.container2.pack(side=TOP)

        self.checkbox_var = IntVar()
        self.speculative_container = Frame(self.container)
        self.spec_label = Label(self.speculative_container, text="Speculative")
        self.spec_label.pack(side=LEFT)
        self.spec_checkbox = Checkbutton(self.speculative_container, variable=self.checkbox_var)
        self.spec_checkbox.pack(side=LEFT)
        self.speculative_container.pack(side=TOP)

        self.content = ""
        self.unit = None
        self.container_name = None

        self.lb = Listbox(self.container, exportselection=0)
        self.lb.pack(side=TOP, fill=BOTH, expand=YES, pady=10)
        for word in self.ingredient_autocompletes:
            self.lb.insert(0, word)
        self.lb.selection_set(0)

        self.recipe_box = Listbox(self.container, exportselection=0)
        self.recipe_box.pack(side=TOP, fill=BOTH, expand=YES)
        for word in db.get_all_recipe_names():
            self.recipe_box.insert(0, word)
        self.recipe_box.selection_set(0)
        # !!ONLY ONE LIST BOX CAN HAVE AN ACTIVE SELECTION AT ONE TIME!! #
        # exportselection=0 overrides this behaviour

        self.console = Text(self.container, height=20, width=30)
        self.console.config(state=DISABLED)
        self.console.pack(side=TOP, fill=BOTH, expand=YES, pady=10)



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

    def pack(self, side):

        self.container.pack(side=side)

    def log_message(self, msg):

        self.console.config(state=NORMAL)
        self.console.insert("1.0", msg)
        # insert in line 1, column 0 (lines start from 1)
        # this makes sure the new message comes at the top
        self.console.delete("20.0", END)
        # make sure it doesn't fill up forever
        self.console.config(state=DISABLED)

    def te_function(self, e):

        #print(e.keycode)
        #self.log_message(f"got {e.keycode}\n")

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
            self.container = row["container_name"]
        else:
            row = db.get_recipe(name)
            self.unit = "meal"
            self.container = None

        if not row:
            raise KeyError("ingredient or recipe not in db")

        self.unit_entry.delete(0, END)  # clear it in case there's something in there
        self.unit_entry.insert(0, self.unit)

    def unit_tab_down(self, e):

        """tab between unit or container name e.g. grams or can"""
        displayed = self.unit_entry.get()
        self.unit_entry.delete(0, END)
        if displayed == self.unit:
            if self.container:
                # sometimes there is no container specified, in which case, do nothing
                self.unit_entry.insert(0, self.container)
        elif displayed == self.container or not displayed:
            self.unit_entry.insert(0, self.unit)

        return "break"  # suppress moving the focus to the next field


    def te_arrow(self, e):

        current = self.lb.curselection()  # a tuple of indexes, so the first item is (0,)
        ind = current[0]
        all_items = list(self.lb.get(0, END))
        self.lb.selection_clear(0, END)
        if e.keycode == 38:
            # up
            ind -=1
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


root = Tk()
root.title("Calorie counter")
app = App(root)
root.mainloop()
