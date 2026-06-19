# Script to tune and save models that are used to predict player salaries

import sqlite3
import numpy as np
import pandas as pd

import xgboost as xgb
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import optuna
from optuna.pruners import MedianPruner

from datetime import date
import pickle
import os
import json

from pytorchPlayerNetwork import PlayerDataset, DeepPlayerNetwork
from playerDataFunctions import obtain_training_data


def train_pytorch_kfold(features, salary, k, hidden_dimensions, dropout_rate, learning_rate, batch_size, nEpoch, patience):
    """
    Do a k-fold validation to get a realistic estimate of the model performance.
    
    Arguments:
        features = Features used for k-fold validation
        salary = Target salaries for the k-flod validation
        k = Number of folds for the validation
        hidden_dimensions = A list defining the number of neurons in each fully connected hidden layer
        dropout_rate = Dropout rate applied to each hidden layer
        learning_rate = Learning rate for the Adam optimizer
        batch_size = Batch size for training
        nEpoch = Maximum number of epochs to train each fold
        patience = Stop the training if validation loss doesn't improve over patience epochs
        
    Return:
        Best loss and R^2 values for each fold
        Average number of epochs it takes to find the optimal solution
    """
    
    # Print the parameters used
    print("Training with parameters: ")
    print("Hidden layers: {}".format(hidden_dimensions))
    print("Dropout: {}".format(dropout_rate))
    print("Learning rate: {}".format(learning_rate))
    
    # Make the folds
    kfold = KFold(n_splits=k, shuffle=True, random_state=42)
    
    # Initialize loss and R^2 collections
    fold_loss = []
    fold_rsquared = []
    fold_results = {
        "train_losses": [],
        "validation_losses": [],
        "train_rsquared": [],
        "validation_rsquared": []
    }
    optimal_epoch = []
    
    # Loop over all the folds and retrain the model in each case
    fold_number = 1
    for iTrain, iValidation in kfold.split(features):
        print(f"\n{'='*50}")
        print(f"Training Fold {fold_number}/{k}")
        print(f"{'='*50}")
        
        # Split data for this fold
        features_train_fold = features[iTrain]
        salary_train_fold = salary[iTrain]
        features_validation_fold = features[iValidation]
        salary_validation_fold = salary[iValidation]
        
        # Normalize features
        scaler = StandardScaler()
        features_train_fold = scaler.fit_transform(features_train_fold)
        features_validation_fold = scaler.transform(features_validation_fold)
        
        # Create datasets and dataloaders
        train_loader = DataLoader(
            PlayerDataset(features_train_fold, salary_train_fold),
            batch_size=batch_size, shuffle=True
        )
        val_loader = DataLoader(
            PlayerDataset(features_validation_fold, salary_validation_fold),
            batch_size=128, shuffle=False
        )
        
        # Create fresh model for this fold
        model = DeepPlayerNetwork(features_train_fold.shape[1], hidden_dimensions, dropout_rate)
        
        # Train the model
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        
        loss_epoch, rsquared_epoch, best_epoch = train_pytorch_model(
            model, criterion, optimizer,
            train_loader, val_loader, 
            nEpoch, early_stopping = True,
            patience=patience, save_path="temp_model.pth"
        )
        
        # Store results
        fold_loss.append(loss_epoch)
        fold_rsquared.append(rsquared_epoch)
        optimal_epoch.append(best_epoch)
        
        fold_results["train_losses"].append(loss_epoch["train"][best_epoch])
        fold_results["validation_losses"].append(loss_epoch["validation"][best_epoch])
        fold_results["train_rsquared"].append(rsquared_epoch["train"][best_epoch])
        fold_results["validation_rsquared"].append(rsquared_epoch["validation"][best_epoch])
        
        fold_number += 1
    
    
    # Print summary from folds
    print(f"\n{'='*50}")
    print(f"k-fold result summary with {k} folds")
    print(f"{'='*50}")
    print(f"Average Validation Loss: {np.mean(fold_results['validation_losses']):.6f} ± {np.std(fold_results['validation_losses']):.6f}")
    print(f"Average Validation R²: {np.mean(fold_results['validation_rsquared']):.4f} ± {np.std(fold_results['validation_rsquared']):.4f}")
    print(f"Average Training R²: {np.mean(fold_results['train_rsquared']):.4f}")
    
    # Return the fold results and the average of the optimal epochs
    return fold_results, int(np.mean(optimal_epoch))
    
    
def train_pytorch_model(model, criterion, optimizer, train_loader, test_loader, nEpoch, early_stopping = True, patience=10, save_path="pytorch_model.pth"):
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
        The epoch that produces the best result
    """
    
    # We cannot do early stopping if there is no test_loader. Enforce this behavior here.
    if test_loader is None:
        early_stopping = False

    # Initialize loss and R^2 collection
    loss_epoch = {"train": [], "validation": []}
    rsquared_score_epoch = {"train": [], "validation": []}

    # Initialize early stopping variables
    best_validation_loss = float('inf')
    best_epoch = 0
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
        
        # We can also train without validation data. In this case, skip this part
        if test_loader is not None:
        
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

            # Do the same for truth targets
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
        
        # Only do early stopping if instructed
        if early_stopping:
        
            # Remember the model that minimizes validation loss
            if loss_epoch["validation"][-1] < best_validation_loss:
                best_validation_loss = loss_epoch["validation"][-1]
                best_epoch = epoch
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

    # Restore the best parameters for the model when doing early stopping
    if early_stopping:
        model.load_state_dict(torch.load(save_path))
        
        # Delete the saved model file. We do not want to keep temporaty files.
        os.remove(save_path)

    # After we have trained the model with the desired number of epochs, return the loss and R^2 dictionaries
    return loss_epoch, rsquared_score_epoch, best_epoch
   
   
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
    sns.lineplot(data=loss_epoch["train"][1:], ax=ax0, label="Training loss")
    sns.lineplot(data=loss_epoch["validation"][1:], ax=ax0, label="Validation loss")
    ax0.set_xlabel("Epoch")
    ax0.set_ylabel("Total loss")
    ax0.set_title("Total loss as a function of epoch")
    ax0.legend()

    # Plots for R^2
    sns.lineplot(data=r_squared_epoch["train"][1:], ax=ax1, label="Training $R^2$ score")
    sns.lineplot(data=r_squared_epoch["validation"][1:], ax=ax1, label="Validation $R^2$ score")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("$R^2$ score")
    ax1.set_title("$R^2$ score as a function of epoch")
    ax1.legend()
    
    # Draw the plots
    plt.tight_layout()
    plt.show()
    
    
def visualize_feature_importances(feature_names, feature_importances):
    """
    Make a bar chart showing how XGBoost ranks different features in the model
    
    Arguments:
        feature_names = Names of features used to fit the model
        feature_importances = Importance of each feature as decided by XGBoost
    """
    
    # Sort the importance scores
    importances_with_scores = zip(feature_names, feature_importances)
    sorted_importances = sorted(importances_with_scores, key=lambda x: x[1], reverse=True)
    features_for_plot, importance_scores = zip(*sorted_importances)

    # Make a bar plot with seaborn to visualize the feature importances
    fig, ax = plt.subplots(figsize=(6, 7))
    sns.barplot(x=features_for_plot, y=importance_scores, ax=ax)
    ax.set_ylabel("Feature importances")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()
    

def plot_feature_correlations(feature_frame, position):
    """
    Plot pairwise correlations for all features and for salary
    """
    
    # Order the columns in the feature_frame such that the target salary is the first column
    ordered_frame = pd.concat([feature_frame[["salary_cap_fraction"]], feature_frame.drop(columns=["salary_cap_fraction"])], axis=1)
    
    # Plot the pairwise correlations for all features
    correlation_plot = sns.pairplot(ordered_frame)
    correlation_plot.savefig(f"feature_correlations_{position}.png", dpi=100, bbox_inches='tight')
    
    # Do not show the figure on the screen
    plt.close()
    
  
def objective(trial, features, targets, batch_size):
    """
    Objective function for Optuna to optimize.
    
    Arguments:
        trial: Optuna trial class, handled internally by the optimizer
        features = Features used in neural network training
        targets = Values the network tries to learn
        
    Return:
        Average R^2 score from the 5 folds used to evaluate the hyperparameters
    """
    
    # Suggest hyperparameters
    hidden1 = trial.suggest_int("hidden1", 16, 64, step=16)
    hidden2 = trial.suggest_int("hidden2", 8, min(hidden1,32))
    hidden3 = trial.suggest_int("hidden3", 4, min(hidden2,16))
    dropout = trial.suggest_float("dropout", 0.01, 0.3)
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1e-3, log=True)
    
    # Collect the hidden dimensions to an array
    hidden_dimensions = [hidden1, hidden2, hidden3]
    
    # Run k-fold validation
    kfold_results, _ = train_pytorch_kfold(
        features, targets, k=5,
        hidden_dimensions=hidden_dimensions,
        dropout_rate=dropout,
        learning_rate=learning_rate,
        batch_size=batch_size,
        nEpoch=1000,
        patience=25
    )
    
    # Return the average validation r squared value
    return np.mean(kfold_results["validation_rsquared"])
  
  
def evaluate_models(true_salary, model_predictions, model_json, plot_kde=True):
    """
    Evaluate models by calculating their R^2 score and plotting kernel density estimates
    
    Arguments:
        true_salary = List containing true salaries
        model_predictions = Dictionary containing predictions for different models
        model_json = Json file for recording the r2 score for each model
        plot_kde = Plot kernel density estimates for true and predicted salaries
    """
    
    # Start by printing the R^2 scores
    for model, prediction in model_predictions.items():
        rsquared = r2_score(true_salary, prediction)
        print("{}: R^2 score on testing data: {}".format(model, rsquared))
        
        # If json file for the model is provided, add r2 value to the file
        if model in model_json:
            with open(model_json[model], "r") as model_file:
                info_dict = json.load(model_file)
                
            info_dict["r2_score"] = rsquared
            
            with open(model_json[model], "w") as model_file:
                json.dump(info_dict, model_file, indent=4)
        
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
    

def main():
    """
    Main function. Train models for XGBoost and PyTorch-based neural network for forward data.
    The trained models can be saved to files for predictions in other macros.
    """
    
    # ======================= #
    #   Basic configuration   #
    # ======================= #
    
    # Today's data for model saving
    today = date.today().strftime("%Y-%m-%d")
    
    # Define the position for which the training is done
    selected_positions = ["forward", "defender", "goalie"]
    
    # Sanity check for position
    for position in selected_positions:
        if position not in ["forward", "defender", "goalie"]:
            print(f"ERROR! Unknown position: {position}")
            print("Available positions are forward, defender and goalie")
            exit()
    
    # Variables defining if we should save models to file
    save_xgboost = True
    save_pytorch = True
    
    # Variables defining which tuning steps should be made
    xgboost_tune_hyperparameters = False
    pytorch_tune_hyperparameters = False
    n_trials_optuna = 300
    draw_feature_importances = False
    draw_feature_correlations = False
    draw_pytorch_training_qa = False
    
    # ============================================ #
    #   Model hyperparameters and data selection   #
    # ============================================ #
    
    # Include minimum icetime of three full games for goalies to be included in the training
    icetime_variable = {"forward": "games_played", "defender": "games_played", "goalie": "icetime"}
    minimum_icetime = {"forward": 0, "defender": 0, "goalie": 180*60}
        
    # Default XGBoost configuration if not doing hyperparameter tuning
    xgb_n_estimators = {"forward": 100, "defender": 100, "goalie": 100}
    xbg_reg_alpha = {"forward": 0, "defender": 0, "goalie": 0.1}
    xgb_reg_lambda = {"forward": 10, "defender": 10, "goalie": 10}
    xgb_max_depth = {"forward": 4, "defender": 8, "goalie": 8}
    xgb_min_child_weight = {"forward": 2, "defender": 3, "goalie": 1}
    xgb_subsample = {"forward": 0.85, "defender": 1, "goalie": 0.85}
        
    # Default PyTorch configuration if not doing hyperparameter tuning
    hidden_layers = {"forward": [64, 31, 12], "defender": [64, 25, 12], "goalie": [64, 32, 6]}
    dropout_rate = {"forward": 0.0645, "defender": 0.0333, "goalie": 0.057}
    learning_rate = {"forward": 0.00048, "defender": 0.00032, "goalie": 0.00086}
    batch_size = 32
    
    # Connect to the database that contains player information
    connection = sqlite3.connect("nhlDatabase.db")
    
    # Loop over all selected positions and train the models
    for position in selected_positions:
    
        # Files containing model versioning information
        xgboost_model_information = f"models/xgboost_{position}_information_{today}.json"
        pytorch_model_information = f"models/pytorch_{position}_information_{today}.json"
    
        # Naming for saved models
        xgboost_model_name = f"models/xgboost_{position}_salary_{today}.json"
        pytorch_model_name = f"models/pytorch_{position}_salary_{today}.pth"
        pytorch_architecture_name = f"models/architecture_for_pytorch_{position}_{today}.json"
        scaler_file_name = f"models/scaler_for_pytorch_{position}_{today}.pkl"
    
        # ========================= #
        #   Prepare training data   #
        # ========================= #
    
        print("Preparing training data")
    
        # Find the training data for the model for forwards
        training_data = obtain_training_data(connection, position)
    
        # Cut for minimum icetime
        training_data = training_data[training_data[icetime_variable[position]] > minimum_icetime[position]]
    
        # Split training data into training and testing to have consistent datasets if training multiple models
        features = training_data.drop(columns=["salary_cap_fraction"]).to_numpy()
        salary = training_data["salary_cap_fraction"].to_numpy()
        features_train, features_test, salary_train, salary_test = train_test_split(features, salary, test_size=0.25, random_state=42)
    
        # Draw the correlations between different features
        if draw_feature_correlations:
            plot_feature_correlations(training_data, position)
    
        # =========================== #
        #   Model training: XGBoost   #
        # =========================== #
    
        print("Training XGBoost model")
    
        # Optional: hyperparameter tuning for XGBoost
        if xgboost_tune_hyperparameters:
            
            # Define the XGBoost model
            xgboost_tuning = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100, random_state=42)

            # Define hyperparameters to be scanned
            param_grid = {
                "max_depth": [4, 6, 8],         # Tree depth. Default: 6
                "min_child_weight": [1, 2, 3],  # Min samples per leaf. Default: 1
                "subsample": [0.7, 0.85, 1],    # Row sampling. Default: 1
                "lambda": [0.1, 1.0, 10],       # L2 regularization. Default: 1
                "alpha": [0, 0.1, 1.0]          # L1 regularization. Default: 0
            }
            
            # Perform the scan with 5 folds
            grid_search = GridSearchCV(xgboost_tuning, param_grid, cv=5,scoring='r2', verbose=1)
            grid_search.fit(features_train, salary_train)
            
            # Find the best parameters
            xbg_reg_alpha[position] = grid_search.best_params_["alpha"]
            xgb_reg_lambda[position] = grid_search.best_params_["lambda"]
            xgb_max_depth[position] = grid_search.best_params_["max_depth"]
            xgb_min_child_weight[position] = grid_search.best_params_["min_child_weight"]
            xgb_subsample[position] = grid_search.best_params_["subsample"]
            
            # Print the best parameters to console
            print(f"\nBest XGBoost configuration:")
            print(f"  reg_alpha: {xbg_reg_alpha[position]}")
            print(f"  reg_lambda: {xgb_reg_lambda[position]}")
            print(f"  max_depth: {xgb_max_depth[position]}")
            print(f"  min_child_weight: {xgb_min_child_weight[position]}")
            print(f"  subsample: {xgb_subsample[position]}")
    
        # Train an XGBoost model with training data
        xgboost_model = xgb.XGBRegressor(
                            objective = "reg:squarederror",
                            n_estimators = xgb_n_estimators[position],
                            random_state = 42,
                            reg_alpha = xbg_reg_alpha[position],
                            reg_lambda = xgb_reg_lambda[position],
                            max_depth = xgb_max_depth[position],
                            min_child_weight = xgb_min_child_weight[position],
                            subsample = xgb_subsample[position]
                        )
        xgboost_model.fit(features_train, salary_train)
        
        # Get the prediction from the XGBoost model
        xgboost_prediction = xgboost_model.predict(features_test)
    
        # Save XGBoost model trained with the full dataset into a file
        if save_xgboost:
    
            # Train XGBoost model with the full dataset for final predictions
            xgboost_full_model = xgb.XGBRegressor(
                                     objective = "reg:squarederror",
                                     n_estimators = xgb_n_estimators[position],
                                     random_state = 42,
                                     reg_alpha = xbg_reg_alpha[position],
                                     reg_lambda = xgb_reg_lambda[position],
                                     max_depth = xgb_max_depth[position],
                                     min_child_weight = xgb_min_child_weight[position],
                                     subsample = xgb_subsample[position]
                                 )
            xgboost_full_model.fit(features, salary)
    
            # Save to file
            xgboost_full_model.save_model(xgboost_model_name)
            
            # Create an information file with all necessary information to use the model
            xgboost_info = {
                "version": f"xgboost_{position}_{today}",
                "path": xgboost_model_name
            }
            
            with open(xgboost_model_information, "w") as xgb_info_file:
                json.dump(xgboost_info, xgb_info_file, indent=4)
      
        # Visualize how important each feature is for XGBoost model
        if draw_feature_importances:
            visualize_feature_importances(training_data.drop(columns=["salary_cap_fraction"]).columns.tolist(), xgboost_model.feature_importances_)
      
        # =========================== #
        #   Model training: PyTorch   #
        # =========================== #
    
        print("Training PyTorch model")
        torch.manual_seed(42)
    
        # Optional: hyperparameter tuning for PyTorch
        if pytorch_tune_hyperparameters:
    
            # Run optuna optimization study where we maximize the R^2 value of the model
            study = optuna.create_study(
                direction="maximize",
                pruner=MedianPruner()
            )
    
            # Set manually parameters we know to be good for the first trial
            # This ensures that the hyperparameter tuning result is at least as good as the default result
            study.enqueue_trial({
                "hidden1": hidden_layers[position][0],
                "hidden2": hidden_layers[position][1],
                "hidden3": hidden_layers[position][2],
                "dropout": dropout_rate[position],
                "learning_rate": learning_rate[position]
            })

            # Run the study with only training data. Testing data is reserved for final evaluation
            study.optimize(
                lambda trial: objective(trial, features_train, salary_train, batch_size),
                n_trials=n_trials_optuna
            )
    
            # Get the best trial
            best_trial = study.best_trial
            print(f"\n{'='*60}")
            print(f"Best R²: {best_trial.value:.4f}")
            print(f"Best params: {best_trial.params}")
            print(f"{'='*60}")

            # Extract best hyperparameters
            hidden_layers[position] = [
                best_trial.params["hidden1"],
                best_trial.params["hidden2"],
                best_trial.params["hidden3"]
            ]
            dropout_rate[position] = best_trial.params["dropout"]
            learning_rate[position] = best_trial.params["learning_rate"]

            # Print the best parameters to console
            print(f"\nBest PyTorch configuration:")
            print(f"  Hidden layers: {hidden_layers[position]}")
            print(f"  Dropout: {dropout_rate[position]}")
            print(f"  Learning rate: {learning_rate[position]}")
        
    
        # Train a model with training set and obtain a prediction from the testing set to evaluate the model
    
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
        pytorch_model = DeepPlayerNetwork(features_train_scaled.shape[1], hidden_layers[position], dropout_rate[position])
    
        # Define criterion for the loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(pytorch_model.parameters(), lr=learning_rate[position])
    
        # Define batch sizes for training and testing
        train_loader = DataLoader(dataset=tensor_train_data, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(dataset=tensor_test_data, batch_size=128, shuffle=False)
    
        # Train the PyTorch model while collecting loss and R^2 information during training
        nEpoch = 1000
        patience = 25
        pytorch_model_path = f"pytorch_training_model.pth"
    
        loss_epoch, r_squared_epoch, _ = train_pytorch_model(pytorch_model, criterion, optimizer, train_loader, test_loader, nEpoch, early_stopping=True, patience=patience, save_path=pytorch_model_path)
        
        if draw_pytorch_training_qa:
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
    
        # Train PyTorch model with full dataset and save the resulting model to a file
        if save_pytorch:
    
            # Do a k-fold validation for the PyTorch model to determine nepoch for the full model:
            k = 5
            _, nEpoch = train_pytorch_kfold(features, salary, k, hidden_layers[position], dropout_rate[position], learning_rate[position], batch_size, nEpoch, patience)
        
            # Use the full dataset to train the final model for predictions
            # We use here DataFrame to fit intead of features numpy-array since later
            # the column names can be used as sanity check that fitting is done correctly
            # In the numpy-array the column name information is lost
            scaler = StandardScaler()
            features_full = scaler.fit_transform(training_data.drop(columns=["salary_cap_fraction"]))
    
            # Convert the full dataset into tensors that can be consumed by PyTorch
            tensor_full_data = PlayerDataset(features_full, salary)
    
            # Define the number of neurons in the neural network
            pytorch_full_model = DeepPlayerNetwork(features_full.shape[1], hidden_layers[position], dropout_rate[position])
    
            # Define criterion for the loss function and optimizer
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(pytorch_full_model.parameters(), lr=learning_rate[position])
    
            # Define batch size for training the model
            full_train_loader = DataLoader(dataset=tensor_full_data, batch_size=batch_size, shuffle=True)
        
            # Train the model
            train_pytorch_model(pytorch_full_model, criterion, optimizer, full_train_loader, None, nEpoch, early_stopping=False)
        
            # Save the model and the used standard scaler to a file for predictions
            torch.save(pytorch_full_model.state_dict(), pytorch_model_name)
            
            # Save the standard scaler that needs to be used with the model
            with open(scaler_file_name,"wb") as scaler_file:
                pickle.dump(scaler, scaler_file)
                
            # Create an information file with all necessary information to use the model
            pytorch_info = {
                "version": f"pytorch_{position}_{today}",
                "input_dimension": features_full.shape[1],
                "hidden_layers": hidden_layers[position],
                "dropout_rate": dropout_rate[position],
                "learning_rate": learning_rate[position],
                "batch_size": batch_size,
                "path": pytorch_model_name,
                "scaler": scaler_file_name
            }
            
            with open(pytorch_model_information, "w") as pytorch_info_file:
                json.dump(pytorch_info, pytorch_info_file, indent=4)
    
        # ===================== #
        #   Model evaluations   #
        # ===================== #
    
        # Combine models and use the one for which the kernel density function is closer to true salary
        # combined_prediction = np.where((pytorch_prediction < 0.0215) & (xgboost_prediction < 0.0215), xgboost_prediction, pytorch_prediction)
    
        # Run the model evaluation function
        model_predictions = {"XGBoost": xgboost_prediction, "PyTorch": pytorch_prediction}
        model_json = {}
        if save_xgboost:
            model_json["XGBoost"] = xgboost_model_information
        if save_pytorch:
            model_json["PyTorch"] = pytorch_model_information
            
        evaluate_models(salary_test, model_predictions, model_json)
    
    
    # Close the connection to the database
    connection.close()
    

# Follow good coding practices
if __name__ == "__main__":
    main()
