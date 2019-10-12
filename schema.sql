DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS consumption;

CREATE TABLE ingredients (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE NOT NULL,
protein FLOAT,
carbohydrate FLOAT,
fat FLOAT,
kcals FLOAT,
unit TEXT,
serving_size TEXT,
container_name TEXT
);

CREATE TABLE recipes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
composition_string TEXT,
protein FLOAT,
carbohydrate FLOAT,
fat FLOAT,
kcals FLOAT
);

CREATE TABLE consumption (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
amount FLOAT,
unit TEXT,
protein FLOAT,
carbohydrate FLOAT,
fat FLOAT,
kcals FLOAT,
entry_time NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weight (
id INTEGER PRIMARY KEY AUTOINCREMENT,
weighin REAL,
entry_time NOT NULL DEFAULT CURRENT_TIMESTAMP
)