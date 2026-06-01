-- Define views that make queries easier

DROP VIEW IF EXISTS goalie_cumulative_career_stats;
DROP VIEW IF EXISTS goalie_training_data;

-- Create cumulatiteve career statistics for each goalie
-- In the model training, we want to use the career statistics up to the point where new contract starts
-- Thus we want the cumulatite statistics for each season in the goalies' careers
-- Use window functions to achieve this
CREATE VIEW goalie_cumulative_career_stats AS
SELECT playerId,
       season,
       phase,
       SUM(games_played) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_games_played,
       SUM(icetime) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_icetime,
       ROUND(SUM(xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xGoals,
       SUM(goals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_goals,
       SUM(unblocked_shot_attempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_unblocked_shot_attempts,
       ROUND(SUM(xRebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xRebounds,
       SUM(rebounds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_rebounds,
       ROUND(SUM(xFreeze) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xFreeze,
       SUM(freeze) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_freeze,
       ROUND(SUM(xOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xOnGoal,
       SUM(ongoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_ongoal,
       ROUND(SUM(xPlayStopped) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xPlayStopped,
       SUM(playStopped) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playStopped,
       ROUND(SUM(xPlayContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xPlayContinuedInZone,
       SUM(playContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playContinuedInZone,
       ROUND(SUM(xPlayContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_xPlayContinuedOutsideZone,
       SUM(playContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playContinuedOutsideZone,
       ROUND(SUM(flurryAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_flurryAdjustedxGoals,
       SUM(lowDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_lowDangerShots,
       SUM(mediumDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_mediumDangerShots,
       SUM(highDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_highDangerShots,
       ROUND(SUM(lowDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_lowDangerxGoals,
       ROUND(SUM(mediumDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_mediumDangerxGoals,
       ROUND(SUM(highDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 2) AS career_highDangerxGoals,
       SUM(lowDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_lowDangerGoals,
       SUM(mediumDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_mediumDangerGoals,
       SUM(highDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_highDangerGoals,
       SUM(blocked_shot_attempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_blocked_shot_attempts,
       SUM(penaltyMinutes) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penaltyMinutes,
       SUM(penalties) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penalties
FROM goalie_season_stats
WHERE situation = 'all';

-- Create view for data we want to use to train the model for goalies
-- Use the stats from simple_goelie_stats for first guess
-- Include the stats from the year before the new contract starts
-- Also include the cumulative career stats before the contract starts
-- Exclude entry-level contracts, those have standard value
CREATE VIEW goalie_training_data AS
WITH selectedPlayers AS (SELECT DISTINCT(player_id) FROM contracts
    WHERE type LIKE 'Entry%'
    AND start_season > 2007)
SELECT P.first_name AS first_name,
       P.last_name AS last_name,
       CAST(strftime('%Y.%m%d', C.signing_date) - strftime('%Y.%m%d', P.birth_date) AS int) AS age,
       P.id AS player_id,
       C.type AS type,
       C.start_season AS start_season,
       S.salary_cap AS salary_cap,
       C.cap_hit AS cap_hit,
       ROUND(1.0 * C.cap_hit / S.salary_cap, 5) AS salary_cap_fraction,
       G.games_played AS games_played,
       GCS.career_games_played AS career_games_played,
       G.icetime / 60 AS icetime_minutes,
       GCS.career_icetime / 60 AS career_icetime_minutes,
       ROUND(1.0 - (1.0 * G.goals / G.ongoal),3) AS save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_goals / GCS.career_ongoal),3) AS career_save_percentage,
       ROUND(1.0 - (1.0 * G.xGoals / G.ongoal),3) AS xSave_percentage,
       ROUND(1.0 - (1.0 * GCS.career_xGoals / GCS.career_ongoal),3) AS career_xSave_percentage,
       ROUND(3600.0 * G.goals / G.icetime, 3) AS goals_against_average,
       ROUND(3600.0 * GCS.career_goals / GCS.career_icetime, 3) AS career_goals_against_average,
       ROUND(3600.0 * G.xGoals / G.icetime, 3) AS xGoals_against_average,
       ROUND(3600.0 * GCS.career_xGoals / GCS.career_icetime, 3) AS career_xGoals_against_average,
       ROUND(3600.0 * G.rebounds / G.icetime, 3) AS reboundsPer60,
       ROUND(3600.0 * GCS.career_rebounds / GCS.career_icetime, 3) AS career_reboundsPer60,
       ROUND(3600.0 * G.xRebounds / G.icetime, 3) AS xReboundsPer60,
       ROUND(3600.0 * GCS.career_xRebounds / GCS.career_icetime, 3) AS career_xReboundsPer60,
       ROUND(1.0 - (1.0 * G.lowDangerGoals / G.lowDangerShots), 3) AS lowDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_lowDangerGoals / GCS.career_lowDangerShots), 3) AS career_lowDanger_save_percentage,
       ROUND(1.0 - (G.lowDangerxGoals / G.lowDangerShots), 3) AS xLowDanger_save_percentage,
       ROUND(1.0 - (GCS.career_lowDangerxGoals / GCS.career_lowDangerShots), 3) AS career_xLowDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.mediumDangerGoals / G.mediumDangerShots), 3) AS mediumDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_mediumDangerGoals / GCS.career_mediumDangerShots), 3) AS career_mediumDanger_save_percentage,
       ROUND(1.0 - (G.mediumDangerxGoals / G.mediumDangerShots), 3) AS xMediumDanger_save_percentage,
       ROUND(1.0 - (GCS.career_mediumDangerxGoals / GCS.career_mediumDangerShots), 3) AS career_xMediumDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.highDangerGoals / G.highDangerShots), 3) AS highDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_highDangerGoals / GCS.career_highDangerShots), 3) AS career_highDanger_save_percentage,
       ROUND(1.0 - (G.highDangerxGoals / G.highDangerShots), 3) AS xHighDanger_save_percentage,
       ROUND(1.0 - (GCS.career_highDangerxGoals / GCS.career_highDangerShots), 3) AS career_xHighDanger_save_percentage
FROM players P
JOIN contracts C
  ON P.id = C.player_id
JOIN seasons S
  ON S.season = C.start_season
JOIN goalie_season_stats G
  ON P.id = G.playerID
  AND C.start_season - 1 = G.season
JOIN goalie_cumulative_career_stats GCS
  ON GCS.playerId = P.id
  AND C.start_season - 1 = GCS.season
WHERE C.type NOT LIKE 'Entry%'
  AND P.id IN (SELECT player_id FROM selectedPlayers)
  AND P.position = 'G'
  AND G.situation = 'all'
  AND G.phase = 'regular'
  AND GCS.phase = 'regular';
