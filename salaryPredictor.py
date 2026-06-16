# Script to predict salaries for NHL players

import sqlite3
import numpy as np
import pandas as pd

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from datetime import date

class PlayerDataset(Dataset):
    """
    Class that handles data feeding to PyTorch-based naural network model
    Inherits from the PyTorch Dataset class
    """
    
    def __init__(self, features, salary):
        """
        Class constructor. Initializes the features to predict the salary and salary itself.
        
        Arguments:
            features = Features in form of numpy.ndarray
            salary = Salary in form of pandas.Series
        """
        self.features = torch.from_numpy(features.astype(np.float32, copy=False))
        self.salary = torch.from_numpy(salary.to_numpy().astype(np.float32, copy=True)).unsqueeze(1)
        
    def __getitem__(self,index):
        """
        Implement indexing for the PlayerDataset
        """
        return self.features[index], self.salary[index]
        
    def __len__(self):
        """
        Define length for the PlayerDataset
        """
        return len(self.features)


class PlayerNetwork(nn.Module):
    """
    Class defining the neural network structure for predicting player salaries.
    Inherits from Module in PyTorch
    """

    def __init__(self,input_dimension,hidden1,hidden2):
        """
        Initilization of network.
        """
        super(PlayerNetwork,self).__init__()
        self.linear1=nn.Linear(input_dimension,hidden1)
        self.relu1 = nn.ReLU()
        self.linear2=nn.Linear(hidden1,hidden2)
        self.relu2 = nn.ReLU()
        self.linear3=nn.Linear(hidden2,1)
        
    def forward(self,x):
        """
        Definition of forward pass.
        """
        x = self.relu1(self.linear1(x))
        x = self.relu2(self.linear2(x))
        x = self.linear3(x)
        return x
        
class DeepPlayerNetwork(nn.Module):
    """
    Class defining a deep neural network structure for predicting player salaries.
    Inherits from Module in PyTorch
    """

    def __init__(self,input_dimension,hidden_dimensions,dropout_rate):
        """
        Initilization of network.
        """
        super(DeepPlayerNetwork,self).__init__()
        
        # Define a ModuleList to hold all the hidden layers
        self.layers = nn.ModuleList()
        previous_dimension = input_dimension
        
        # Add fully connected layers to the network
        for hidden_dimension in hidden_dimensions:
            self.layers.append(nn.Linear(previous_dimension, hidden_dimension))
            previous_dimension = hidden_dimension
        
        # Add the output layer
        self.layers.append(nn.Linear(previous_dimension, 1))
        
        # Define ReLU activation and dropout layer
        self.dropout = nn.Dropout(dropout_rate)
        self.relu = nn.ReLU()
        
    def forward(self,x):
        """
        Definition of forward pass.
        """
        
        # Loop through hidden layers and add ReLU activation and Dropout
        for layer in self.layers[:-1]:
            x = layer(x)
            x = self.relu(x)
            x = self.dropout(x)
            
        # Output layer without activation or Dropout
        x = self.layers[-1](x)
        return x
    
    
def train_pytorch_model(model, criterion, optimizer, train_loader, test_loader, nEpoch, patience=10, save_path='pytorch_model.pth'):
    """
    Function for training a PyTorch neural network model

    Arguments:
        model = The model that needs training
        criterion = Used loss function to evaluate the performance of the model
        optimizer = Optimizer object performing the gradient descent
        train_loader = DataLoader providing the training data for the model
        test_loader = DataLoader providing the validation data for the model
        nEpoch = Number of epochs to train the model
        patience = Number of epochs to wait for improvement before early stopping
        save_path = Path to save the best model

    Return:
        Dictionaries describing total loss and R^2 score after each epoch for training and validation data
    """

    # Initialize loss and R^2 collection
    loss_epoch = {"train": [], "validation": []}
    rsquared_score_epoch = {"train": [], "validation": []}

    # Initialize early stopping variables
    best_validation_loss = float('inf')
    patience_counter = 0

    for epoch in range(nEpoch):
    
        if epoch % (nEpoch//10) == 0:
            print("PyTorch training, epoch {}/{}".format(epoch, nEpoch))

        # ====================================== #
        #   Implement the PyTorch training loop  #
        # ====================================== #
        
        # Put the model to training mode
        model.train()

        # Initialize the total loss to 0
        total_loss=0

        # Load the training data in batches
        for x,y in train_loader:

            # Clear the gradients from previous iteration
            optimizer.zero_grad()

            # Make a forward pass through the model
            yhat=model(x)

            # Calculate the loss based on the forward pass
            loss=criterion(yhat,y)

            # Prepare the gradients by making a backward pass
            loss.backward()
            
            optimizer.step()

            # Add the loss from this batch to the total loss value
            total_loss+=loss.item()
            
        # Append the total loss from this epoch to the loss per epoch list
        loss_epoch["train"].append(total_loss)

        # ======================================================= #
        #   Collect loss and R^2 information for validation data  #
        # ======================================================= #
        
        # Put the model to evaluation mode
        model.eval()

        # Loop over data from test loader and collect losses and predictions
        all_predictions = []
        all_targets = []
        total_loss=0
        with torch.no_grad():
            for x, y in test_loader:

                # Collect predictions
                yhat = model(x)
                all_predictions.append(yhat.cpu().numpy())
                all_targets.append(y.cpu().numpy())

                # Collect losses
                loss=criterion(yhat,y)
                total_loss+=loss.item()

        # Append the total loss from this epoch to the loss per epoch list
        # Scale it to the same scale as the training set
        loss_epoch["validation"].append(total_loss * (len(train_loader) / len(test_loader)))

        # Compile all predictions together from validation data
        pytorch_prediction = np.concatenate(all_predictions, axis=0)

        # Squeeze the predictions into one dimension
        pytorch_prediction = pytorch_prediction.squeeze()

        # Do the make for truth targets
        pytorch_targets = np.concatenate(all_targets, axis=0)
        pytorch_targets = pytorch_targets.squeeze()

        # Add the goodness of the current model to the per epoch list
        rsquared_score_epoch["validation"].append(r2_score(pytorch_targets, pytorch_prediction))

        # ============================================ #
        #   Collect R^2 information for training data  #
        # ============================================ #
        
        # We cannot calculate predictions for R^2 score in training mode, since dropout/batch normalization layers might be active
        # Thus, we will do it here when the model is turned to evaluation mode
        all_predictions = []
        all_targets = []
        with torch.no_grad():
            for x, y in train_loader:
                yhat = model(x)
                all_predictions.append(yhat.cpu().numpy())
                all_targets.append(y.cpu().numpy())
        pytorch_prediction = np.concatenate(all_predictions, axis=0)
        pytorch_prediction = pytorch_prediction.squeeze()
        pytorch_targets = np.concatenate(all_targets, axis=0)
        pytorch_targets = pytorch_targets.squeeze()
        rsquared_score_epoch["train"].append(r2_score(pytorch_targets, pytorch_prediction))
        
        # ================================ #
        #  Early Stopping & Checkpointing  #
        # ================================ #
        
        # Remember the model that minimizes validation loss
        if loss_epoch["validation"][-1] < best_validation_loss:
            best_validation_loss = loss_epoch["validation"][-1]
            patience_counter = 0
            
            # Save best model
            torch.save(model.state_dict(), save_path)
        else:
            # If we do not improve, increment the patience counter
            patience_counter += 1
            
        # Break from the training loop if the model is not improving for a while
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    # Restore the best parameters for the model
    model.load_state_dict(torch.load(save_path))

    # After we have trained the model with the desired number of epochs, return the loss and R^2 dictionaries
    return loss_epoch, rsquared_score_epoch
   
   
def visualize_training(loss_epoch, r_squared_epoch):
    """
    Visualize the neural network training performance by plotting loss and R^2 curves for training and validation datasets
    
    Arguments:
        loss_epoch = Dictionary containing loss value per epoch for training and validation
        r_squared_epoch = Dictionary containing R^2 value per epoch for training and validation
    """

    # Plot the loss and R^2 curves for training and validation datasets
    fig=plt.figure(figsize=(12, 6))
    
    # Create axes for loss and R^2
    ax0 = fig.add_subplot(1, 2, 1) # Subplot for loss
    ax1 = fig.add_subplot(1 ,2, 2) # Subplot for R^2

    # Plots for loss
    sns.lineplot(data=loss_epoch["train"][1:], ax=ax0, label='Training loss')
    sns.lineplot(data=loss_epoch["validation"][1:], ax=ax0, label='Validation loss')
    ax0.set_xlabel('Epoch')
    ax0.set_ylabel('Total loss')
    ax0.set_title('Total loss as a function of epoch')
    ax0.legend()

    # Plots for R^2
    sns.lineplot(data=r_squared_epoch["train"][1:], ax=ax1, label='Training $R^2$ score')
    sns.lineplot(data=r_squared_epoch["validation"][1:], ax=ax1, label='Validation $R^2$ score')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('$R^2$ score')
    ax1.set_title('$R^2$ score as a function of epoch')
    ax1.legend()
    
    # Draw the plots
    plt.tight_layout()
    plt.show()
    

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


def evaluate_models(true_salary, model_predictions, plot_kde=True):
    """
    Evaluate models by calculating their R^2 score and plotting kernel density estimates
    
    Arguments:
        true_salary = List containing true salaries
        model_predictions = Dictionary containing predictions for different models
        plot_kde = Plot kernel density estimates for true and predicted salaries
        
    Return: 
        Trained XGBoost model
    """
    
    # Start by printing the R^2 scores
    for model, prediction in model_predictions.items():
        print("{}: R^2 score on testing data: {}".format(model, r2_score(true_salary, prediction)))
        
    if plot_kde:
        
        # Initialize the residual and salary in numpy format
        residuals = {}
        numpy_salary = np.array(true_salary)
        
        # Calculate prediction residuals for plotting
        for model, prediction in model_predictions.items():
            numpy_prediction = np.array(prediction)
            residuals[model] = numpy_salary - numpy_prediction
        
        # Define nice colors for plotting
        colors = sns.color_palette("deep")
        
        # Figure
        fig=plt.figure(figsize=(12, 6))
    
        # Make two different plots
        ax0 = fig.add_subplot(1, 2, 1) # Subplot for salaries
        ax1 = fig.add_subplot(1 ,2, 2) # Subplot for salary residuals
    
        # Salary plot
        sns.kdeplot(x=true_salary, ax=ax0, label="True salaries", color=colors[0])
        for i, (model, prediction) in enumerate(model_predictions.items()):
            sns.kdeplot(x=prediction, ax=ax0, label=f"Prediction: {model}", color=colors[i+1])
        ax0.set_xlabel("Salary cap fraction")
        ax0.set_ylabel("Density")
        ax0.set_title("Predicted salary cap fraction distribution")
        ax0.legend()

        # Residual plot
        for i, (model, residual) in enumerate(residuals.items()):
            sns.kdeplot(x=residual, ax=ax1, label=f"{model} accuracy", color=colors[i+1])
        ax1.axvline(x=0, color="red", linestyle="--")
        ax1.set_xlabel("Difference from true salary")
        ax1.set_ylabel("Density")
        ax1.set_title("Prediction difference from truth")
        ax1.legend()
    
        plt.tight_layout()
        plt.show()


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
    Main function. We can either use pre-trained model, or train the model based on optimized hyperparameters and use that.
    """
    
    # Variables defining if we should save/load models from file
    save_xgboost = False
    xgboost_pretrained_model = "xgboost_forward_salary_2026-06-12.json"
    
    # Today's data for model saving
    today = date.today().strftime('%Y-%m-%d')
    
    # Connect to the database that contains player information
    connection = sqlite3.connect("nhlDatabase.db")
    
    # ========================= #
    #   Prepare training data   #
    # ========================= #
    
    print("Preparing training data")
    
    # Find the training data for the model
    training_data = obtain_training_data(connection)
    
    # Split training data into training and testing to have consistent datasets if training multiple models
    features = training_data.drop(columns=["salary_cap_fraction"])
    salary = training_data["salary_cap_fraction"]
    features_train, features_test, salary_train, salary_test = train_test_split(features, salary, test_size=0.25, random_state=42)
    
    # =========================== #
    #   Model training: XGBoost   #
    # =========================== #
    
    print("Training XGBoost model")
    
    # Train an XGBoost model with training data
    xgboost_model = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100, random_state=42, reg_alpha=0.1, reg_lambda=10, max_depth=4, min_child_weight=2, subsample=0.7)
    
    # Option to use pretrained model instead of training a new model
    if xgboost_pretrained_model != "":
        xgboost_model.load_model(xgboost_pretrained_model)
    else:
        xgboost_model.fit(features_train, salary_train)
    
    # Save XGBoost model to a file
    if save_xgboost:
        xgboost_model.save_model(f"xgboost_forward_salary_{today}.json")
        
    # Get the prediction from the XGBoost model
    xgboost_prediction = xgboost_model.predict(features_test)
        
    # =========================== #
    #   Model training: PyTorch   #
    # =========================== #
    
    print("Training PyTorch model")
    torch.manual_seed(42)
    
    # Unlike decision trees, neural networks are sensitive to absolute feature scales
    # Thus, for PyTorch we need to scale the input features in order to achieve good performance
    # Use the StandardScaler from scikit-learn to do this
    # This scales the mean of each feature to 0 and standard deviation to 1
    # Note that scaling is only learned from training features
    scaler = StandardScaler()
    features_train_scaled = scaler.fit_transform(features_train)
    features_test_scaled = scaler.transform(features_test)
    
    # Convert datasets into tensors that can be consumed by PyTorch
    tensor_train_data = PlayerDataset(features_train_scaled, salary_train)
    tensor_test_data = PlayerDataset(features_test_scaled, salary_test)
    
    # Define the number of neurons in the neural network
    pytorch_model = DeepPlayerNetwork(features_train_scaled.shape[1],[64,32,16],0.05)
    
    # Define criterion for the loss function and optimizer
    learning_rate = 0.0001
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(pytorch_model.parameters(), lr=learning_rate)
    
    # Define batch sizes for training and testing
    train_loader = DataLoader(dataset=tensor_train_data, batch_size=32, shuffle=True)
    test_loader = DataLoader(dataset=tensor_test_data, batch_size=128, shuffle=False)
    
    # Train the PyTorch model while collecting loss and R^2 information during training
    nEpoch = 200
    patience = 20
    pytorch_model_path = f"pytorch_forward_salary_{today}.pth"
    
    loss_epoch, r_squared_epoch = train_pytorch_model(pytorch_model, criterion, optimizer, train_loader, test_loader, nEpoch, patience, pytorch_model_path)
    visualize_training(loss_epoch, r_squared_epoch)

    # Get the prediction from the model
    pytorch_model.eval()
    all_predictions = []
    with torch.no_grad():
        for x, y in test_loader:
            yhat = pytorch_model(x)
            all_predictions.append(yhat.cpu().numpy())
    pytorch_prediction = np.concatenate(all_predictions, axis=0)
    pytorch_prediction = pytorch_prediction.squeeze()
    
    # ===================== #
    #   Model evaluations   #
    # ===================== #
    
    # Run the model evaluation function
    model_predictions = {"XGBoost": xgboost_prediction, "PyTorch": pytorch_prediction}
    evaluate_models(salary_test, model_predictions)
    
    # ========================== #
    #   Predicting new salaries  #
    # ========================== #
    
    # Get the information we need to predict salary for Connor Bedard
    prediction_data = obtain_stats_for_prediction(connection, "Connor Bedard")
    
    # Predict the salary for Connor Bedard
    predict_salaries(connection, prediction_data, xgboost_model, pytorch_model, scaler)
    
    # Close the connection to the database
    connection.close()
    

# Follow good coding practices
if __name__ == "__main__":
    main()
