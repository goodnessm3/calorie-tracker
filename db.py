import sqlite3
import csv


def get_db_connection():

    a = sqlite3.connect("db.sqlite3")
    a.row_factory = sqlite3.Row
    return a


# first connect to the database then load everything else using this connection as the default arg
CONN = get_db_connection()


def add_ingredient(adict, conn=CONN):

    """takes rows from reading the CSV and inserts them into the DB. This function expects dictionaries
    with the same keys as the SQL column names"""

    k = ["protein", "carbohydrate", "fat", "kcals", "unit", "serving_size", "container_name"]
    v = (adict["name"].lower(),) + tuple(adict[x] for x in k)

    conn.execute('''INSERT INTO ingredients (name,protein,carbohydrate,fat,kcals,unit,serving_size, container_name)
                    VALUES (?,?,?,?,?,?,?,?)''', v)
    conn.commit()


def add_recipe(recipe_name, list_of_tups, portions, conn=CONN):

    """takes the ingredient list from the main windw, which is a list of tuples of (name, amount, unit). Look
    up the nutritional info for all the ingredient amounts and make an entry in the recipes DB under
    the recipe name. Total nutritional info of all the ingredients is summed and then divided by the
    number of portions, these are the values stored for the meal."""

    comp_string = ""  # to record the recipe content
    pro = 0
    carb = 0
    fat = 0
    kcal = 0
    portions = float(portions)
    for tup in list_of_tups:
        info = calc_nutritional_content(tup)
        pro += float(info["protein"])
        carb += float(info["carbohydrate"])
        fat += float(info["fat"])
        kcal += float(info["kcals"])

        name, amt, unit = tup
        comp_string += f"{name}|{amt}|{unit}$"

    vals = (recipe_name, comp_string, pro/portions, carb/portions, fat/portions, kcal/portions)

    conn.execute('''INSERT INTO recipes (name, composition_string, protein, carbohydrate, fat, kcals)
                    VALUES (?,?,?,?,?,?)''', vals)
    conn.commit()


def calc_nutritional_content(tup):

    """takes a tuple of (name, amount, unit), looks up the unit, multiplies it by the ingredient
    per-100-unit stats and returns a dictionary with the protein, carbs etc content"""

    name, amount, unit = tup
    # unit might be grams, each, or the container name e.g. can, bottle, we need to check. Get all
    # info here, also for the purposes of computing the calories and macros

    amount = float(amount)  # TODO: proper type affininty from sqlite
    row = get_ingredient(name)
    if not row:
        row = get_recipe(name)

    ks = ["protein", "carbohydrate", "fat", "kcals"]
    if "unit" not in row.keys():
        # entering a whole meal, nutritional values pre-calculated
        vals = [row[x] * amount for x in ks]
    elif unit == row["unit"]:
        if not unit == "each":
            amount = amount/100.0  # nutritional info is always per 100 mL/g
        vals = [row[x]*amount for x in ks]  # compute total value
    elif unit == row["container_name"]:
        siz = float(row["serving_size"])/100.0
        vals = [row[x]*siz*amount for x in ks]
    else:
        raise KeyError("unrecognised measurement unit")

    vals = tuple(vals)
    to_output = tup + vals
    ks2 = ["name", "amount", "unit"] + ks  # full key list for the output dictionary
    return {x: y for x, y in zip(ks2, to_output)}  # compile a dictionary


def record_consumption(tup, conn=CONN):

    """record consumption of a food item. Comes as a tuple of (name, amount, unit). Makes a timestamped entry.
    returns the database row for displaying the info in the UI."""

    nutritional_info = calc_nutritional_content(tup)
    ks = ["name", "amount", "unit", "protein", "carbohydrate", "fat", "kcals"]
    vals = [nutritional_info[x] for x in ks]  # make sure the values come in the right order
    vals = tuple(vals)
    to_enter = vals  # concatenate the tuples now we have computed the total nutritional contents
    conn.execute('''INSERT INTO consumption (name, amount, unit, protein, carbohydrate, fat, kcals)
                    VALUES (?,?,?,?,?,?,?)''', to_enter)
    conn.commit()

    return nutritional_info


def ingest_csv(path):

    with open(path, "r") as f:
        rd = csv.DictReader(f)
        for line in rd:
            add_ingredient(line)


def get_all_ingredient_names(conn=CONN):

    """returns a list of name strings for use by the autocompleter"""

    a = conn.execute('''SELECT name from ingredients''')
    return [b["name"] for b in a.fetchall()]


def get_all_recipe_names(conn=CONN):

    a = conn.execute('''SELECT name from recipes''')
    return [b["name"] for b in a.fetchall()]


def get_ingredient(name, conn=CONN):

    """returns the single SQlite row, addressable as a dictionary, matching the name"""
    a = conn.execute('''SELECT * from ingredients WHERE name = ?''', (name,))
    return a.fetchone()


def get_recipe(name, conn=CONN):

    a = conn.execute('''SELECT * from recipes WHERE name = ?''', (name,))
    return a.fetchone()


def enter_weight(weight, conn=CONN):

    conn.execute('''INSERT INTO weight (weighin) VALUES (?)''', (weight,))
    conn.commit()


def get_daily_totals(date=None, date_mod=None, conn=CONN):

    """return the last 30 days' totals of protein, carb, fat, kcals, for plotting on the main
    window graph, or a single day's totals if the date argument is specified. Date
    must be a string like YYYY-MM-DD or 'now' for today's date"""

    if date:
        if date_mod:
            a = conn.execute('''select date(entry_time), 
                                sum(protein), 
                                sum(carbohydrate), 
                                sum(fat), 
                                sum(kcals) 
                                from consumption 
                                where date(entry_time) = date(?, ?)''', (date, date_mod))
        else:

            a = conn.execute('''select date(entry_time), 
                                sum(protein), 
                                sum(carbohydrate), 
                                sum(fat), 
                                sum(kcals) 
                                from consumption 
                                where date(entry_time) = date(?)''', (date,))
    else:
        a = conn.execute('''select date(entry_time), 
                            sum(protein), 
                            sum(carbohydrate), 
                            sum(fat), 
                            sum(kcals) 
                            from consumption 
                            group by date(entry_time)''')

    ret = a.fetchall()
    if ret[0]["sum(kcals)"]:
        # check that the row actually contains values, if not, the user is asking for a date with no entry
        # and instead we will return zero values (below)
        return ret
    else:
        return [{"sum(protein)": 0,
                "sum(carbohydrate)": 0,
                "sum(fat)": 0,
                "sum(kcals)": 0}]

        # dict of dummy values to populate the interface, instead of a sqlite row. When the user starts entering
        # data, it will be written to the db and can be returned by this function in future calls.
        # TODO: probably this is better to take care of in SQL


def get_daily_weighins(conn=CONN):

    """return the last 30 day's worth of weight measurements."""

    a = conn.execute('''select date(entry_time), weighin from weight''')
    return a.fetchall()
