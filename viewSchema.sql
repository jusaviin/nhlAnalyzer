-- Define views that make queries easier

DROP VIEW IF EXISTS roster;
DROP VIEW IF EXISTS simple_goalie_stats;
DROP VIEW IF EXISTS simple_skater_stats;
DROP VIEW IF EXISTS goalie_cumulative_career_stats;
DROP VIEW IF EXISTS goalie_training_data;
DROP VIEW IF EXISTS skater_cumulative_career_stats;
DROP VIEW IF EXISTS skater_training_data;


-- View that makes it easy to find the rosters of teams in a specific season
CREATE VIEW roster
(
    season,
    team_code,
    team_name,
    player_id,
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
SELECT S.season, T.code, T.name, P.id, P.first_name, P.last_name, P.position, P.birth_date, P.headshot,
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

SELECT G.season, T.code, T.name, P.id, P.first_name, P.last_name, P.position, P.birth_date, P.headshot,
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
       P.id AS player_id,
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
       P.id AS player_id,
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
       S.penaltyMinutesDrawn AS penalty_minutes_drawn,
       ROUND(3600.0 * S.penaltyMinutes / S.icetime, 3) AS penalty_minutes_per60,
       ROUND(3600.0 * S.penaltyMinutesDrawn / S.icetime, 3) AS penalty_minutes_drawn_per60
FROM players P
JOIN skater_season_stats S
  ON P.id = S.playerID
JOIN teams T
  ON S.team = T.code;


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
       ROUND(SUM(xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xGoals,
       SUM(goals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_goals,
       SUM(unblocked_shot_attempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_unblocked_shot_attempts,
       ROUND(SUM(xRebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xRebounds,
       SUM(rebounds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_rebounds,
       ROUND(SUM(xFreeze) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xFreeze,
       SUM(freeze) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_freeze,
       ROUND(SUM(xOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xOnGoal,
       SUM(ongoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_ongoal,
       ROUND(SUM(xPlayStopped) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xPlayStopped,
       SUM(playStopped) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playStopped,
       ROUND(SUM(xPlayContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xPlayContinuedInZone,
       SUM(playContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playContinuedInZone,
       ROUND(SUM(xPlayContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xPlayContinuedOutsideZone,
       SUM(playContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_playContinuedOutsideZone,
       ROUND(SUM(flurryAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_flurryAdjustedxGoals,
       SUM(lowDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_lowDangerShots,
       SUM(mediumDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_mediumDangerShots,
       SUM(highDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_highDangerShots,
       ROUND(SUM(lowDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_lowDangerxGoals,
       ROUND(SUM(mediumDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_mediumDangerxGoals,
       ROUND(SUM(highDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_highDangerxGoals,
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
       ROUND(1.0 - (1.0 * G.xGoals / G.ongoal),4) AS xSave_percentage,
       ROUND(1.0 - (1.0 * GCS.career_xGoals / GCS.career_ongoal),4) AS career_xSave_percentage,
       ROUND(3600.0 * G.goals / G.icetime, 3) AS goals_against_average,
       ROUND(3600.0 * GCS.career_goals / GCS.career_icetime, 3) AS career_goals_against_average,
       ROUND(3600.0 * G.xGoals / G.icetime, 4) AS xGoals_against_average,
       ROUND(3600.0 * GCS.career_xGoals / GCS.career_icetime, 4) AS career_xGoals_against_average,
       ROUND(3600.0 * G.rebounds / G.icetime, 3) AS reboundsPer60,
       ROUND(3600.0 * GCS.career_rebounds / GCS.career_icetime, 3) AS career_reboundsPer60,
       ROUND(3600.0 * G.xRebounds / G.icetime, 4) AS xReboundsPer60,
       ROUND(3600.0 * GCS.career_xRebounds / GCS.career_icetime, 4) AS career_xReboundsPer60,
       ROUND(1.0 - (1.0 * G.lowDangerGoals / G.lowDangerShots), 3) AS lowDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_lowDangerGoals / GCS.career_lowDangerShots), 3) AS career_lowDanger_save_percentage,
       ROUND(1.0 - (G.lowDangerxGoals / G.lowDangerShots), 4) AS xLowDanger_save_percentage,
       ROUND(1.0 - (GCS.career_lowDangerxGoals / GCS.career_lowDangerShots), 4) AS career_xLowDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.mediumDangerGoals / G.mediumDangerShots), 3) AS mediumDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_mediumDangerGoals / GCS.career_mediumDangerShots), 3) AS career_mediumDanger_save_percentage,
       ROUND(1.0 - (G.mediumDangerxGoals / G.mediumDangerShots), 4) AS xMediumDanger_save_percentage,
       ROUND(1.0 - (GCS.career_mediumDangerxGoals / GCS.career_mediumDangerShots), 4) AS career_xMediumDanger_save_percentage,
       ROUND(1.0 - (1.0 * G.highDangerGoals / G.highDangerShots), 3) AS highDanger_save_percentage,
       ROUND(1.0 - (1.0 * GCS.career_highDangerGoals / GCS.career_highDangerShots), 3) AS career_highDanger_save_percentage,
       ROUND(1.0 - (G.highDangerxGoals / G.highDangerShots), 4) AS xHighDanger_save_percentage,
       ROUND(1.0 - (GCS.career_highDangerxGoals / GCS.career_highDangerShots), 4) AS career_xHighDanger_save_percentage
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

-- Create cumulatiteve career statistics for each skater
-- In the model training, we want to use the career statistics up to the point where new contract starts
-- Thus we want the cumulatite statistics for each season in the skaters' careers
-- Use window functions to achieve this
CREATE VIEW skater_cumulative_career_stats AS
SELECT playerId,
       season,
       phase,
       SUM(games_played) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_games_played,
       SUM(icetime) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_icetime,
       SUM(shifts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_shifts,
       ROUND(SUM(gameScore) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_gameScore,
       ROUND(SUM(onIce_xGoalsPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_onIce_xGoalsPercentage,
       ROUND(SUM(offIce_xGoalsPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_offIce_xGoalsPercentage,
       ROUND(SUM(onIce_corsiPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_onIce_corsiPercentage,
       ROUND(SUM(offIce_corsiPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_offIce_corsiPercentage,
       ROUND(SUM(onIce_fenwickPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_onIce_fenwickPercentage,
       ROUND(SUM(offIce_fenwickPercentage) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_offIce_fenwickPercentage,
       ROUND(SUM(I_F_xOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xOnGoal,
       ROUND(SUM(I_F_xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoals,
       ROUND(SUM(I_F_xRebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xRebounds,
       ROUND(SUM(I_F_xFreeze) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xFreeze,
       ROUND(SUM(I_F_xPlayStopped) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xPlayStopped,
       ROUND(SUM(I_F_xPlayContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xPlayContinuedInZone,
       ROUND(SUM(I_F_xPlayContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xPlayContinuedOutsideZone,
       ROUND(SUM(I_F_flurryAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_flurryAdjustedxGoals,
       ROUND(SUM(I_F_scoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_scoreVenueAdjustedxGoals,
       ROUND(SUM(I_F_flurryScoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_flurryScoreVenueAdjustedxGoals,
       SUM(I_F_primaryAssists) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_primaryAssists,
       SUM(I_F_secondaryAssists) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_secondaryAssists,
       SUM(I_F_shotsOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_shotsOnGoal,
       SUM(I_F_missedShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_missedShots,
       SUM(I_F_blockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_blockedShotAttempts,
       SUM(I_F_shotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_shotAttempts,
       SUM(I_F_points) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_points,
       SUM(I_F_goals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_goals,
       SUM(I_F_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_rebounds,
       SUM(I_F_reboundGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_reboundGoals,
       SUM(I_F_freeze) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_freeze,
       SUM(I_F_playStopped) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_playStopped,
       SUM(I_F_playContinuedInZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_playContinuedInZone,
       SUM(I_F_playContinuedOutsideZone) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_playContinuedOutsideZone,
       SUM(I_F_savedShotsOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_savedShotsOnGoal,
       SUM(I_F_savedUnblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_savedUnblockedShotAttempts,
       SUM(penalties) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penalties,
       SUM(I_F_faceOffsWon) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_faceOffsWon,
       SUM(I_F_hits) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_hits,
       SUM(I_F_takeaways) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_takeaways,
       SUM(I_F_giveaways) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_giveaways,
       SUM(I_F_lowDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_lowDangerShots,
       SUM(I_F_mediumDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_mediumDangerShots,
       SUM(I_F_highDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_highDangerShots,
       ROUND(SUM(I_F_lowDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_lowDangerxGoals,
       ROUND(SUM(I_F_mediumDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_mediumDangerxGoals,
       ROUND(SUM(I_F_highDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_highDangerxGoals,
       SUM(I_F_lowDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_lowDangerGoals,
       SUM(I_F_mediumDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_mediumDangerGoals,
       SUM(I_F_highDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_highDangerGoals,
       ROUND(SUM(I_F_scoreAdjustedShotsAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_scoreAdjustedShotsAttempts,
       SUM(I_F_unblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_unblockedShotAttempts,
       ROUND(SUM(I_F_scoreAdjustedUnblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_scoreAdjustedUnblockedShotAttempts,
       SUM(I_F_dZoneGiveaways) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_dZoneGiveaways,
       ROUND(SUM(I_F_xGoalsFromxReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoalsFromxReboundsOfShots,
       ROUND(SUM(I_F_xGoalsFromActualReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoalsFromActualReboundsOfShots,
       ROUND(SUM(I_F_reboundxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_reboundxGoals,
       ROUND(SUM(I_F_xGoals_with_earned_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoals_with_earned_rebounds,
       ROUND(SUM(I_F_xGoals_with_earned_rebounds_scoreAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoals_with_earned_rebounds_scoreAdjusted,
       ROUND(SUM(I_F_xGoals_with_earned_rebounds_scoreFlurryAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_I_F_xGoals_with_earned_rebounds_scoreFlurryAdjusted,
       SUM(I_F_oZoneShiftStarts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_oZoneShiftStarts,
       SUM(I_F_dZoneShiftStarts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_dZoneShiftStarts,
       SUM(I_F_neutralZoneShiftStarts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_neutralZoneShiftStarts,
       SUM(I_F_flyShiftStarts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_flyShiftStarts,
       SUM(I_F_oZoneShiftEnds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_oZoneShiftEnds,
       SUM(I_F_dZoneShiftEnds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_dZoneShiftEnds,
       SUM(I_F_neutralZoneShiftEnds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_neutralZoneShiftEnds,
       SUM(I_F_flyShiftEnds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_I_F_flyShiftEnds,
       SUM(faceoffsWon) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_faceoffsWon,
       SUM(faceoffsLost) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_faceoffsLost,
       SUM(timeOnBench) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_timeOnBench,
       SUM(penaltyMinutes) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penaltyMinutes,
       SUM(penaltyMinutesDrawn) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penaltyMinutesDrawn,
       SUM(penaltiesDrawn) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_penaltiesDrawn,
       SUM(shotsBlockedByPlayer) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_shotsBlockedByPlayer,
       ROUND(SUM(OnIce_F_xOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xOnGoal,
       ROUND(SUM(OnIce_F_xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoals,
       ROUND(SUM(OnIce_F_flurryAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_flurryAdjustedxGoals,
       ROUND(SUM(OnIce_F_scoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_scoreVenueAdjustedxGoals,
       ROUND(SUM(OnIce_F_flurryScoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_flurryScoreVenueAdjustedxGoals,
       SUM(OnIce_F_shotsOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_shotsOnGoal,
       SUM(OnIce_F_missedShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_missedShots,
       SUM(OnIce_F_blockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_blockedShotAttempts,
       SUM(OnIce_F_shotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_shotAttempts,
       SUM(OnIce_F_goals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_goals,
       SUM(OnIce_F_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_rebounds,
       SUM(OnIce_F_reboundGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_reboundGoals,
       SUM(OnIce_F_lowDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_lowDangerShots,
       SUM(OnIce_F_mediumDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_mediumDangerShots,
       SUM(OnIce_F_highDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_highDangerShots,
       ROUND(SUM(OnIce_F_lowDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_lowDangerxGoals,
       ROUND(SUM(OnIce_F_mediumDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_mediumDangerxGoals,
       ROUND(SUM(OnIce_F_highDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_highDangerxGoals,
       SUM(OnIce_F_lowDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_lowDangerGoals,
       SUM(OnIce_F_mediumDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_mediumDangerGoals,
       SUM(OnIce_F_highDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_highDangerGoals,
       ROUND(SUM(OnIce_F_scoreAdjustedShotsAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_scoreAdjustedShotsAttempts,
       SUM(OnIce_F_unblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_F_unblockedShotAttempts,
       ROUND(SUM(OnIce_F_scoreAdjustedUnblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_scoreAdjustedUnblockedShotAttempts,
       ROUND(SUM(OnIce_F_xGoalsFromxReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoalsFromxReboundsOfShots,
       ROUND(SUM(OnIce_F_xGoalsFromActualReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoalsFromActualReboundsOfShots,
       ROUND(SUM(OnIce_F_reboundxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_reboundxGoals,
       ROUND(SUM(OnIce_F_xGoals_with_earned_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoals_with_earned_rebounds,
       ROUND(SUM(OnIce_F_xGoals_with_earned_rebounds_scoreAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoals_with_earned_rebounds_scoreAdjusted,
       ROUND(SUM(OnIce_F_xGoals_with_earned_rebounds_scoreFlurryAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_F_xGoals_with_earned_rebounds_scoreFlurryAdjusted,
       ROUND(SUM(OnIce_A_xOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xOnGoal,
       ROUND(SUM(OnIce_A_xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoals,
       ROUND(SUM(OnIce_A_flurryAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_flurryAdjustedxGoals,
       ROUND(SUM(OnIce_A_scoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_scoreVenueAdjustedxGoals,
       ROUND(SUM(OnIce_A_flurryScoreVenueAdjustedxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_flurryScoreVenueAdjustedxGoals,
       SUM(OnIce_A_shotsOnGoal) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_shotsOnGoal,
       SUM(OnIce_A_missedShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_missedShots,
       SUM(OnIce_A_blockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_blockedShotAttempts,
       SUM(OnIce_A_shotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_shotAttempts,
       SUM(OnIce_A_goals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_goals,
       SUM(OnIce_A_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_rebounds,
       SUM(OnIce_A_reboundGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_reboundGoals,
       SUM(OnIce_A_lowDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_lowDangerShots,
       SUM(OnIce_A_mediumDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_mediumDangerShots,
       SUM(OnIce_A_highDangerShots) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_highDangerShots,
       ROUND(SUM(OnIce_A_lowDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_lowDangerxGoals,
       ROUND(SUM(OnIce_A_mediumDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_mediumDangerxGoals,
       ROUND(SUM(OnIce_A_highDangerxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_highDangerxGoals,
       SUM(OnIce_A_lowDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_lowDangerGoals,
       SUM(OnIce_A_mediumDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_mediumDangerGoals,
       SUM(OnIce_A_highDangerGoals) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_highDangerGoals,
       ROUND(SUM(OnIce_A_scoreAdjustedShotsAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_scoreAdjustedShotsAttempts,
       SUM(OnIce_A_unblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OnIce_A_unblockedShotAttempts,
       ROUND(SUM(OnIce_A_scoreAdjustedUnblockedShotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_scoreAdjustedUnblockedShotAttempts,
       ROUND(SUM(OnIce_A_xGoalsFromxReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoalsFromxReboundsOfShots,
       ROUND(SUM(OnIce_A_xGoalsFromActualReboundsOfShots) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoalsFromActualReboundsOfShots,
       ROUND(SUM(OnIce_A_reboundxGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_reboundxGoals,
       ROUND(SUM(OnIce_A_xGoals_with_earned_rebounds) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoals_with_earned_rebounds,
       ROUND(SUM(OnIce_A_xGoals_with_earned_rebounds_scoreAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoals_with_earned_rebounds_scoreAdjusted,
       ROUND(SUM(OnIce_A_xGoals_with_earned_rebounds_scoreFlurryAdjusted) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OnIce_A_xGoals_with_earned_rebounds_scoreFlurryAdjusted,
       ROUND(SUM(OffIce_F_xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OffIce_F_xGoals,
       ROUND(SUM(OffIce_A_xGoals) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_OffIce_A_xGoals,
       SUM(OffIce_F_shotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OffIce_F_shotAttempts,
       SUM(OffIce_A_shotAttempts) OVER (PARTITION BY playerId, phase ORDER BY season) AS career_OffIce_A_shotAttempts,
       ROUND(SUM(xGoalsForAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xGoalsForAfterShifts,
       ROUND(SUM(xGoalsAgainstAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_xGoalsAgainstAfterShifts,
       ROUND(SUM(corsiForAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_corsiForAfterShifts,
       ROUND(SUM(corsiAgainstAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_corsiAgainstAfterShifts,
       ROUND(SUM(fenwickForAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_fenwickForAfterShifts,
       ROUND(SUM(fenwickAgainstAfterShifts) OVER (PARTITION BY playerId, phase ORDER BY season), 4) AS career_fenwickAgainstAfterShifts
FROM skater_season_stats
WHERE situation = 'all';

-- All the relevant contracts are defined here in skater_training_data
-- The season stats for the players still need to be read from
-- simple_season_stats or skater_season_stats
-- Eventually when statistics combination scheme is finalized
-- the combination can be done directly in this view
CREATE VIEW skater_training_data AS
WITH selectedPlayers AS (SELECT DISTINCT(player_id) FROM contracts
    WHERE type LIKE 'Entry%'
    AND start_season > 2007)
SELECT P.first_name AS first_name,
       P.last_name AS last_name,
       CAST(strftime('%Y.%m%d', C.signing_date) - strftime('%Y.%m%d', P.birth_date) AS int) AS age,
       P.position AS position,
       P.id AS player_id,
       C.type AS type,
       C.start_season AS start_season,
       S.salary_cap AS salary_cap,
       C.cap_hit AS cap_hit,
       ROUND(1.0 * C.cap_hit / S.salary_cap, 5) AS salary_cap_fraction
FROM players P
JOIN contracts C
  ON P.id = C.player_id
JOIN seasons S
  ON S.season = C.start_season
WHERE C.type NOT LIKE 'Entry%'
  AND P.id IN (SELECT player_id FROM selectedPlayers)
  AND P.position <> 'G'
