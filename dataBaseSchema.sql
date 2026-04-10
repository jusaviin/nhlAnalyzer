-- Schema of the database for predicting NHL contact values and doing some data visualization
-- Version 0.1, debug mode

-- Drop all already defined tables
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS cities;

-- Table for players. Currently only has information needed to make the map visualization
-- In the final version, player should not be associated with a team. This association should come through statistics table that is specific for a season, since a player can change teams. Keep it here for initial testing before statistics tables are implemented.
CREATE TABLE players
(
    id INTEGER PRIMARY KEY NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birth_city TEXT NOT NULL,
    birth_date DATE,
    position CHAR(1),
    handedness CHAR(1),
    headshot TEXT,
    height INTEGER,
    weight INTEGER,
    FOREIGN KEY (birth_city) REFERENCES cities(name_NHL_API),
    FOREIGN KEY (team_code) REFERENCES teams(code)
);

-- Table for teams on NHL
-- Currently the latest arena is listed in the teams table
-- If the project is ever expanded to contain past arenas for teams, the arenas need to go to their own table
-- We might want to also use franchise_id if the project is expanded to historical teams
CREATE TABLE teams
(
    code CHAR(3) PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    logo TEXT,
    arena TEXT,
    arena_capacity INTEGER,
    arena_latitude REAL,
    arena_longitude REAL,
    FOREIGN KEY (city) REFERENCES cities(name_NHL_API)
);

-- Table for cities for map visualizations
CREATE TABLE cities
(
    name_NHL_API TEXT PRIMARY KEY NOT NULL,
    name_local TEXT NOT NULL,
    name_english TEXT NOT NULL,
    country TEXT,
    state TEXT,
    state_code CHAR(2),
    longitude REAL,
    latitude REAL
);

-- Statistics tables are filled directly from MoneyPuck csv files
-- Thus, they are not included in this schema
-- All the information provided by MoneyPuck are included in the said tables
-- Statistics tables include:
--  * skater statistics for regular season and playoffs
--  * goalie statistics for regular season and playoffs
--  * team statistics for regular season and playoffs
-- In future versions, also game-level data should be included
