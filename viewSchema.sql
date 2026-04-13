-- Define views that make queries easier

DROP VIEW IF EXISTS roster;
DROP VIEW IF EXISTS simple_goalie_stats;
DROP VIEW IF EXISTS simple_skater_stats;

-- View that makes it easy to find the rosters of teams in a specific season
CREATE VIEW roster
(
    season,
    team_code,
    team_name,
    player_first_name,
    player_last_name,
    player_position,
    player_birth_date,
    player_headshot,
    city_name_local,
    city_name_english,
    city_state,
    city_state_code,
    city_country,
    city_longitude,
    city_latitude
) AS
SELECT S.season, T.code, T.name, P.first_name, P.last_name, P.position, P.birth_date, P.headshot,
       C.name_local, C.name_english, C.state, C.state_code, C.country, C.longitude, C.latitude
FROM players P
JOIN skater_season_stats S
ON P.id = S.playerID
JOIN teams T
ON S.team = T.code
JOIN cities C
ON P.birth_city = C.name_NHL_API
WHERE S.phase = 'regular' AND S.situation = 'all'

UNION ALL

SELECT G.season, T.code, T.name, P.first_name, P.last_name, P.position, P.birth_date, P.headshot,
       C.name_local, C.name_english, C.state, C.state_code, C.country, C.longitude, C.latitude
FROM players P
JOIN goalie_season_stats G
ON P.id = G.playerID
JOIN teams T
ON G.team = T.code
JOIN cities C
ON P.birth_city = C.name_NHL_API
WHERE G.phase = 'regular' AND G.situation = 'all';

-- Create view for simple goalie stats to find them more easily
-- TODO: Goalie stats are missing the number of wins. Need to get this from NHL API instead of MoneyPuck
CREATE VIEW simple_goalie_stats AS
SELECT G.season AS season,
       G.phase AS phase,
       G.situation AS situation,
       T.code AS team_code,
       T.name AS team_name,
       P.first_name AS first_name,
       P.last_name AS last_name,
       G.games_played AS games_played,
       G.icetime / 60 AS icetime_minutes,
       ROUND(1.0 - (1.0 * G.goals / G.ongoal),3) AS save_percentage,
       ROUND(1.0 - (1.0 * G.xGoals / G.ongoal),3) AS xSave_percentage,
       ROUND(3600.0 * G.goals / G.icetime, 3) AS goals_against_average,
       ROUND(3600.0 * G.xGoals / G.icetime, 3) AS xGoals_against_average,
       ROUND(3600.0 * G.rebounds / G.icetime, 3) AS reboundsPer60,
       ROUND(3600.0 * G.xRebounds / G.icetime, 3) AS xReboundsPer60,
       ROUND(1.0 - (1.0 * G.lowDangerGoals / G.lowDangerShots), 3) AS lowDanger_save_percentage,
       ROUND(1.0 - (G.lowDangerxGoals / G.lowDangerShots), 3) AS xLowDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.mediumDangerGoals / G.mediumDangerShots), 3) AS mediumDanger_save_percentage,
       ROUND(1.0 - (G.mediumDangerxGoals / G.mediumDangerShots), 3) AS xMediumDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.highDangerGoals / G.highDangerShots), 3) AS highDanger_save_percentage,
       ROUND(1.0 - (G.highDangerxGoals / G.highDangerShots), 3) AS xHighDanger_save_percentage,
       G.penaltyMinutes AS penaltyMinutes
FROM players P
JOIN goalie_season_stats G
ON P.id = G.playerID
JOIN teams T
ON G.team = T.code;

-- Create view for simple skater stats to find them more easily
CREATE VIEW simple_skater_stats AS
SELECT S.season AS season,
       S.phase AS phase,
       S.situation AS situation,
       T.code AS team_code,
       T.name AS team_name,
       P.first_name AS first_name,
       P.last_name AS last_name,
       P.position AS position,
       S.games_played AS games_played,
       S.icetime / 60 AS icetime_minutes,
       S.I_F_goals AS goals,
       S.I_F_xGoals AS xGoals,
       S.I_F_primaryAssists + S.I_F_secondaryAssists AS assists,
       S.I_F_goals + S.I_F_primaryAssists + S.I_F_secondaryAssists AS points,
       S.I_F_shotsOnGoal AS shots_on_goal,
       S.I_F_shotAttempts AS shot_attempts,
       S.I_F_hits AS hits,
       CASE WHEN S.faceoffsWon + S.faceoffsLost > 0 THEN ROUND(1.0 * S.faceoffsWon / (S.faceoffsWon + S.faceoffsLost), 3) ELSE 0 END AS faceoff_win_percentage,
       CASE WHEN S.I_F_shotsOnGoal > 0 THEN ROUND(1.0 * S.I_F_goals / S.I_F_shotsOnGoal, 3) ELSE 0 END AS shooting_percentage,
       ROUND(3600.0 * S.I_F_goals / S.icetime, 3) AS goalsPer60,
       ROUND(3600.0 * S.I_F_xGoals / S.icetime, 3) AS xGoalsPer60,
       ROUND(3600.0 * (S.I_F_primaryAssists + S.I_F_secondaryAssists) / S.icetime, 3) AS assistsPer60,
       ROUND(3600.0 * (S.I_F_goals + S.I_F_primaryAssists + S.I_F_secondaryAssists) / S.icetime, 3) AS pointsPer60,
       ROUND(3600.0 * S.I_F_shotsOnGoal / S.icetime, 3) AS shots_on_goal_per60,
       ROUND(3600.0 * S.I_F_shotAttempts / S.icetime, 3) AS shot_attempts_per60,
       ROUND(3600.0 * S.I_F_hits / S.icetime, 3) AS hitsPer60,

       SUM(CASE WHEN S.situation = '5on5' THEN S.OnIce_F_goals - S.OnIce_A_goals ELSE 0 END)
       OVER (PARTITION BY S.playerID, S.season, S.phase) AS "+/-",

       S.penaltyMinutes AS penalty_minutes,
       S.penaltyMinutesDrawn AS penalty_minutes_drawn
FROM players P
JOIN skater_season_stats S
ON P.id = S.playerID
JOIN teams T
ON S.team = T.code
