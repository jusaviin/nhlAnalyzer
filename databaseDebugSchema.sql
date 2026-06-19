-- Schema for testing. If we want to recreate some tables from main schema, add them here

-- Drop all already defined tables
DROP TABLE IF EXISTS salary_prediction;

-- Table for seasons
CREATE TABLE salary_prediction
(
    id INTEGER PRIMARY KEY NOT NULL,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    cap_percentage_xgboost REAL NOT NULL,
    cap_percentage_pytorch REAL NOT NULL,
    model_version_xgboost TEXT,
    model_version_pytorch TEXT
);
