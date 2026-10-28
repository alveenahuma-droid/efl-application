DROP TABLE IF EXISTS greetings;

CREATE TABLE greeting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL
);

INSERT INTO greeting (message) VALUES ('Hello from the database!');