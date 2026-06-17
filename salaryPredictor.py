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
    
    # Define the paths for the loaded models
    xgboost_pretrained_path = "models/xgboost_forward_salary_2026-06-17.json"
    pytorch_pretrained_path = "models/pytorch_forward_salary_2026-06-17.pth"
    scaler_pretained_path = "models/standard_scaler_for_pytorch_2026-06-17.pkl"
    
    # Connect to the database that contains player information
    connection = sqlite3.connect("nhlDatabase.db")
    
    # ========================== #
    #   Load pretrained models   #
    # ========================== #
    
    # Load the XGBoost model
    xgboost_model = xgb.XGBRegressor()
    xgboost_model.load_model(xgboost_pretrained_path)
    
    # Define the parameters that were used to train the PyTorch neural network
    # TODO: These should be loaded from some json file, that is saved together with the model
    input_dimension = 16
    hidden_layers = [64, 32, 16]
    dropout_rate = 0.05
    
    # Load the PyTorch-based neural network
    pytorch_model = DeepPlayerNetwork(input_dimension, hidden_layers, dropout_rate)
    pytorch_model.load_state_dict(torch.load(pytorch_pretrained_path))
    
    # Load the scaler for the neural network
    with open(scaler_pretained_path, "rb") as scaler_file:
        scaler = pickle.load(scaler_file)
    
    # ========================== #
    #   Predicting new salaries  #
    # ========================== #
    
    # Get the information we need to predict salary for Connor Bedard
    prediction_data = obtain_stats_for_prediction(connection, "Connor Bedard")
    print(prediction_data.shape[1])
    
    # Predict the salary for Connor Bedard
    predict_salaries(connection, prediction_data, xgboost_model, pytorch_model, scaler)
    
    # Close the connection to the database
    connection.close()
    

# Follow good coding practices
if __name__ == "__main__":
    main()
