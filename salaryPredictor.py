# Script to predict salaries for NHL players

import sqlite3
import numpy as np
import pandas as pd

import xgboost as xgb
from sklearn.preprocessing import StandardScaler

import matplotlib.pyplot as plt
import seaborn as sns

import torch

import pickle
import json

from pytorchPlayerNetwork import DeepPlayerNetwork
from playerDataFunctions import obtain_stats_for_prediction


def predict_salaries(connection, player_data, xbgoost_model = None, pytorch_model = None, scaler = None):
    """
    Predict the salary for all the players present in player_data
    
    Arguments:
        connection = Connection object to SQLite database from which the season salary cap
        model = Model used for predicting the salaries
        player_data = Data given to the model for prediction
    """
    
    # Remove the player identifying information from the dataframe and make a prediction
    prediction_frame = player_data.drop(columns=["player_id", "first_name", "last_name", "start_season"])
    
    # Predict salary with XGBoost
    if xbgoost_model is not None:
        predictions = xbgoost_model.predict(prediction_frame)
        player_data["xgboost"] = predictions
    else:
        player_data["xgboost"] = 0
        
    # Predict salary with PyTorch
    if pytorch_model is not None and scaler is not None:
        pytorch_model.eval()
        scaled_input = scaler.transform(prediction_frame)
        with torch.no_grad():
            predictions = pytorch_model(torch.from_numpy(scaled_input.astype(np.float32, copy=False)))
        player_data["pytorch"] = predictions
    else:
        player_data["pytorch"] = 0
    
    # Determine the salary cap for 2026 season, for which the predictions are currently being made
    sql_query = "SELECT salary_cap FROM seasons WHERE season = 2026"
    salary_cap_frame = pd.read_sql(sql_query, connection)
    salary_cap = salary_cap_frame.iloc[0,0]
    
    # Loop over all the predictions for player salaries
    for player in player_data.itertuples():
        print("XGBoost salary prediction for {} {} for season 2026 is {:.0f}".format(player.first_name, player.last_name, round(player.xgboost * salary_cap, -3)))
        print("PyTorch salary prediction for {} {} for season 2026 is {:.0f}".format(player.first_name, player.last_name, round(player.pytorch * salary_cap, -3)))
    

def main():
    """
    Main function. Load pretrained models and make predictions using them.
    TODO: Make predictions for all current players with the trained model
            - Store these predictions in the database
    """
    
    # Models are trained separately for forwards, defenders and goalies
    positions = ["forward", "defender", "goalie"]
    position_code = {"forward": ["C","R","L"], "defender": ["D"], "goalie": ["G"]}
    
    # Define the json files that contain all necessary information from the trained models
    xgboost_info_path = {"forward": "models/xgboost_forward_information_2026-06-19.json",
                         "defender": "models/xgboost_defender_information_2026-06-19.json",
                         "goalie": "models/xgboost_goalie_information_2026-06-19.json"}
    pytorch_info_path = {"forward": "models/pytorch_forward_information_2026-06-19.json",
                         "defender": "models/pytorch_defender_information_2026-06-19.json",
                         "goalie": "models/pytorch_goalie_information_2026-06-19.json"}
                         
    # Open all model information files
    xgboost_info = {}
    pytorch_info = {}
    for position in positions:
        with open(xgboost_info_path[position], "r") as xgboost_info_file:
            xgboost_info[position] = json.load(xgboost_info_file)
        with open(pytorch_info_path[position], "r") as pytorch_info_file:
            pytorch_info[position] = json.load(pytorch_info_file)
    
    # ========================== #
    #   Load pretrained models   #
    # ========================== #
    
    xgboost_model = {}
    pytorch_model = {}
    scaler = {}
    
    for position in positions:
    
        # Load the XGBoost model
        xgboost_model[position] = xgb.XGBRegressor()
        xgboost_model[position].load_model(xgboost_info[position]["path"])
    
        # Define the parameters that were used to train the PyTorch neural network
        input_dimension = pytorch_info[position]["input_dimension"]
        hidden_layers = pytorch_info[position]["hidden_layers"]
        dropout_rate = pytorch_info[position]["dropout_rate"]
    
        # Load the PyTorch-based neural network
        pytorch_model[position] = DeepPlayerNetwork(input_dimension, hidden_layers, dropout_rate)
        pytorch_model[position].load_state_dict(torch.load(pytorch_info[position]["path"]))
    
        # Load the scaler for the neural network
        with open(pytorch_info[position]["scaler"], "rb") as scaler_file:
            scaler[position] = pickle.load(scaler_file)
    
    # =================================================================== #
    #   Predict salaries for all players who played in season 2025-2026   #
    # =================================================================== #
    
    # We can find all players that played in a specific season from the roster view
    # Make separate lists for forwards, defenders and goalies
    
    #player_list = {}
    
    #for position in positions:
    
        #sql_query = """SELECT player_id FROM roster
        #              WHERE player_position IN (?) AND season = 2025"""
        #roster = pd.read_sql_query(sql_query, connection, params=(position_code[position]))
    
    # =========================== #
    #   Predicting new salaries   #
    # =========================== #
    
    # Connect to the database that contains player information
    connection = sqlite3.connect("nhlDatabase.db")
    
    # Get the information we need to predict salary for Connor Bedard
    prediction_data = obtain_stats_for_prediction(connection, "Darren Raddysh")
    print(prediction_data.shape[1])
    
    # Predict the salary for Connor Bedard
    predict_salaries(connection, prediction_data, xgboost_model["defender"], pytorch_model["defender"], scaler["defender"])
    
    # Close the connection to the database
    connection.close()
    

# Follow good coding practices
if __name__ == "__main__":
    main()
