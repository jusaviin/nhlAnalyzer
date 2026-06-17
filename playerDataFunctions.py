# Functions to retrieve data needed for model training and predictions from the SQL database

import sqlite3
import numpy as np
import pandas as pd

def get_weight(season, contract_year, weights):
    """
    Get a weight factor for the season stats based on how far in the past the season was played

    Arguments:
        season = Season these stats were produced
        contract_year = First season for the new contract
        weights = List of weights that tell how different career years are weighted
                    * Index[0] = Any year farther in past than length or array
                    * Index[n] = Season n years before the first year in current contract

    Return:
        Weight factor for the season to be used to make weighted average
    """
    season_gap = contract_year - season
    if season_gap >= len(weights):
        return weights[0]
    return weights[season_gap]


def get_weighted_average(df, target_column, weight_columns):
    """
    Calculate weighted average from target column using weight column values as weights
    
    Arguments:
        df = pandas dataframe used for the calculation
        target_column = column name for which the weighted average is calculated
        weight_columns = columns that are used as weights for the weighted average.
 
    Return:
        Weighted avare of the target column
    """

    # Make sure the weight_columns is a list
    if not isinstance(weight_columns, list):
        weight_columns = [weight_columns]

    # Calculate weighted average
    numerator = df[target_column] * df[weight_columns[0]]
    denominator = df[weight_columns[0]]
    for column_name in weight_columns[1:]:
        numerator = numerator * df[column_name]
        denominator = denominator * df[column_name]
    return numerator.sum() / denominator.sum()


def find_all_stats(connection, training_frame, played_ids, weights):
    """
    Actually go and get all the stats needed for training and predictions
    
    Arguments:
        connection = Connection object to SQLite database from which the player information is read 
        training_frame = Frame to which the stats are attached
        played_ids = All the player IDs for which the stats are searched for
    """
    
    # The stats used in training are currently combined from two different sources. First read the data from simple_skater_stats view
    sql_query = f"""SELECT player_id, season, icetime_minutes, goalsPer60, xGoalsPer60, 
                      assistsPer60, shots_on_goal_per60, hitsPer60, "+/-"
                   FROM simple_skater_stats
                   WHERE phase = 'regular' AND Situation = 'all'
                      AND player_id IN ({played_ids})"""
    simple_stats = pd.read_sql(sql_query, connection)
    
    # Query more advanced stats from the database
    sql_query = f"""SELECT playerId, season, icetime, games_played, onIce_xGoalsPercentage,
                      offIce_xGoalsPercentage, onIce_fenwickPercentage, offIce_fenwickPercentage, 
                      I_F_takeaways, I_F_giveaways, shotsBlockedByPlayer
                   FROM skater_season_stats
                   WHERE phase = 'regular' AND Situation = 'all'
                      AND playerId IN ({played_ids})"""
    advanced_stats = pd.read_sql(sql_query, connection)
    
    # Once we have all the needed stats loaded, combine these into a single DataFrame
    # First, we define all the stats that will be present in the final DataFrame
    training_dict = {"icetime_per_game": [], "games_played": [], "goals_per60": [], "goals_above_expected_per60": [], "assists_per60": [], "shots_on_goal_per60": [], "hits_per60": [], "+/-": [], "onIce_xGoalsPercentage": [], "xGoalsSurplus": [], "onIce_fenwickPercentage": [], "fenwickSurplus": [], "takeawaysPer60": [], "giveawaysPer60": [], "shotsBlockedPer60": []}
    
    # Loop over all the relevant contracts that are in the training_frame
    for contract in training_frame.itertuples():
    
        # Find the player_id and contract_season from the data
        player_id = contract.player_id
        contract_season = contract.start_season
        
        # Read the relevant stat information for this contract
        contract_advanced_stats = advanced_stats[(advanced_stats["playerId"] == player_id) & (advanced_stats["season"] < contract_season)]
        contract_simple_stats = simple_stats[(simple_stats["player_id"] == player_id) & (simple_stats["season"] < contract_season)]
        
        # If we have no stats for the player, fill the stats with NaN
        # We can clean these rows from the table before model training
        if contract_simple_stats.shape[0] == 0:
            for key in list(training_dict.keys()):
                training_dict[key].append(np.nan)
            continue
            
        # Add a weight column to contract_stats by checking the how many seasons before the contract started the stats were obtained
        contract_advanced_stats["weight"] = contract_advanced_stats["season"].apply(get_weight, args=[contract_season, weights])
        contract_simple_stats["weight"] = contract_simple_stats["season"].apply(get_weight, args=[contract_season, weights])
        
        # To get proper season-by-season weighted averages, we need to calculate derived stats for each season
        contract_advanced_stats["icetime_per_game"] = contract_advanced_stats["icetime"] / contract_advanced_stats["games_played"]
        contract_advanced_stats["takeaways_per60"] = 3600 * contract_advanced_stats["I_F_takeaways"] / contract_advanced_stats["icetime"]
        contract_advanced_stats["giveaways_per60"] = 3600 * contract_advanced_stats["I_F_giveaways"] / contract_advanced_stats["icetime"]
        contract_advanced_stats["shotsBlockedPer60"] = 3600 * contract_advanced_stats["shotsBlockedByPlayer"] / contract_advanced_stats["icetime"]
        
        
        # Calcuate everything we want to use from simple stats
        training_dict["goals_per60"].append(get_weighted_average(contract_simple_stats, "goalsPer60", ["weight", "icetime_minutes"]))
        training_dict["goals_above_expected_per60"].append(training_dict["goals_per60"][-1] - get_weighted_average(contract_simple_stats, "xGoalsPer60", ["weight", "icetime_minutes"]))
        training_dict["assists_per60"].append(get_weighted_average(contract_simple_stats, "assistsPer60", ["weight", "icetime_minutes"]))
        training_dict["shots_on_goal_per60"].append(get_weighted_average(contract_simple_stats, "shots_on_goal_per60", ["weight", "icetime_minutes"]))
        training_dict["hits_per60"].append(get_weighted_average(contract_simple_stats, "hitsPer60", ["weight", "icetime_minutes"]))
        training_dict["+/-"].append(get_weighted_average(contract_simple_stats, "+/-", ["weight", "icetime_minutes"]))
        
        # Calculate everything we want to use from advanced stats
        training_dict["games_played"].append(get_weighted_average(contract_advanced_stats, "games_played", ["weight"]))
        training_dict["icetime_per_game"].append(get_weighted_average(contract_advanced_stats, "icetime_per_game", ["weight"]))
        training_dict["onIce_xGoalsPercentage"].append(get_weighted_average(contract_advanced_stats, "onIce_xGoalsPercentage", ["weight", "icetime"]))
        training_dict["xGoalsSurplus"].append(training_dict["onIce_xGoalsPercentage"][-1] - get_weighted_average(contract_advanced_stats, "offIce_xGoalsPercentage", ["weight", "icetime"]))
        training_dict["onIce_fenwickPercentage"].append(get_weighted_average(contract_advanced_stats, "onIce_fenwickPercentage", ["weight", "icetime"]))
        training_dict["fenwickSurplus"].append(training_dict["onIce_fenwickPercentage"][-1] - get_weighted_average(contract_advanced_stats, "offIce_fenwickPercentage", ["weight", "icetime"]))
        training_dict["takeawaysPer60"].append(get_weighted_average(contract_advanced_stats, "takeaways_per60", ["weight", "icetime"]))
        training_dict["giveawaysPer60"].append(get_weighted_average(contract_advanced_stats, "giveaways_per60", ["weight", "icetime"]))
        training_dict["shotsBlockedPer60"].append(get_weighted_average(contract_advanced_stats, "shotsBlockedPer60", ["weight", "icetime"]))
        
    # Once we have all the information we need, construct a new DataFrame from the dictionary
    stats_frame = pd.DataFrame(training_dict)

    # Concatenate this with training_frame
    training_frame_with_stats = pd.concat([training_frame, stats_frame], axis=1)
    
    # Clean any rows with NaN values
    training_frame_with_stats.dropna(how="any", inplace=True, ignore_index=True)
    
    # Return the frame with all the stats attached to it
    return training_frame_with_stats
    

def obtain_stats_for_prediction(connection, player, weights = [0.01, 1, 0.8, 0.6, 0.3, 0.1]):
    """
    Get the information needed to predict new contract for a specific player assuming the contract is signed today
    
    Arguments:
        connection = Connection object to SQLite database from which the player information is read 
        player = A player name for whom this prediction is done
    """
    
    # Split the player name into first name and last name
    name_tokens = player.split()
    first_name = name_tokens[0]
    last_name = " ".join(name_tokens[1:]) # Support surnames with several parts
    
    # Make a query to find the player information from the database
    # CAST(strftime('%Y.%m%d', C.signing_date) - strftime('%Y.%m%d', P.birth_date) AS int) AS age,
    sql_query = f"""SELECT id, first_name, last_name,
                   CAST(strftime('%Y.%m%d', date('now')) - strftime('%Y.%m%d', birth_date) AS int) AS age
                   FROM players
                   WHERE first_name = \"{first_name}\"
                      AND last_name = \"{last_name}\""""
                
                 
    player_frame = pd.read_sql(sql_query, connection)
    
    # We need to modify a couple of columns in the player_frame in order to properly use the find_all_stats function
    player_frame.rename(columns={"id": "player_id"}, inplace=True)
    player_frame["start_season"] = 2026
    
    # Find the player ID for filtering other queries
    player_id = player_frame.loc[0,"player_id"]
    
    # Find the stats needed for predictions
    prediction_frame = find_all_stats(connection, player_frame, player_id, weights)
    
    # Return the prediction frame. Keep the id and player name information for now, such that it can be used for printouts even though it need to be disabled for prediction
    return prediction_frame


def obtain_training_data(connection, weights = [0.01, 1, 0.8, 0.6, 0.3, 0.1]):
    """
    Function to collect from database all the necessary data that is needed to train the salary predictor model
    
    Arguments:
        connection = Connection object to SQLite database from which the player information is read 
    
    Return:
        DataFrame with all the necessary data to train a salary predictor model
    """
    
    # Read all the contracts that need stats from skater_training_data view
    sql_query = "SELECT player_id, start_season, age, salary_cap_fraction FROM skater_training_data"
    training_frame = pd.read_sql(sql_query, connection)
    
    training_frame_with_stats = find_all_stats(connection, training_frame, "SELECT DISTINCT(player_id) FROM skater_training_data", weights)
    
    # Remove information not necessary for training that was used to find the correct stats
    training_frame_with_stats.drop(columns=["player_id", "start_season"], inplace=True)
    
    # Return the cleaned training frame
    return training_frame_with_stats
