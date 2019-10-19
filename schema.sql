DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS consumption;
DROP TABLE IF EXISTS weight;

CREATE TABLE ingredients (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE NOT NULL,
protein REAL,
carbohydrate REAL,
fat REAL,
kcals REAL,
unit TEXT,
serving_size TEXT,
container_name TEXT
);

CREATE TABLE recipes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
composition_string TEXT,
protein REAL,
carbohydrate REAL,
fat REAL,
kcals REAL
);

CREATE TABLE consumption (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
amount REAL,
unit TEXT,
protein REAL,
carbohydrate REAL,
fat REAL,
kcals REAL,
entry_time NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weight (
id INTEGER PRIMARY KEY AUTOINCREMENT,
weighin REAL,
entry_time NOT NULL DEFAULT CURRENT_TIMESTAMP
)