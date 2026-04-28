-- Schema for testing. If we want to recreate some tables from main schema, add them here

-- Drop all already defined tables
DROP TABLE IF EXISTS seasons;

-- Table for seasons
CREATE TABLE seasons
(
    season INTEGER PRIMARY KEY NOT NULL,
    salary_cap INTEGER NOT NULL,
    cap_floor INTEGER NOT NULL
);
