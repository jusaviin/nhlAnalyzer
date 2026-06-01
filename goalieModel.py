# Teach a machine learning model to predict goalie contract value

import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Read the data to a dataframe
connection = sqlite3.connect('nhlDatabase.db')
sql_query = "SELECT * FROM goalie_training_data"
goalie_training_data = pd.read_sql(sql_query, connection)

# Require at least 10 games from the previous season
cleaned_goalie_data = goalie_training_data[goalie_training_data["games_played"] > 10].reset_index(drop=True)

# Select a subset of columns for training
training_features = cleaned_goalie_data[['age', 'games_played',
       'career_games_played', 'save_percentage', 'career_save_percentage', 'xSave_percentage',
       'career_xSave_percentage', 'goals_against_average',
       'career_goals_against_average', 'xGoals_against_average',
       'career_xGoals_against_average', 'reboundsPer60',
       'career_reboundsPer60', 'xReboundsPer60', 'career_xReboundsPer60']]
training_labels = cleaned_goalie_data["salary_cap_fraction"]

# Use 75% of data for training and 25% for testing
train_features, test_features, train_salary, test_salary = train_test_split(training_features, training_labels, test_size=0.25, random_state=42)

# Train a linear regression model with the training data
simple_regression = LinearRegression().fit(train_features, train_salary)

# Print the R^2 score for training and testing sets
print("Linear regression: R^2 score on training data: {}".format(simple_regression.score(train_features, train_salary)))
print("Linear regression: R^2 score on testing data: {}".format(simple_regression.score(test_features, test_salary)))

# Do the same with xgboost
gradient_boost = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, random_state=42)

gradient_boost.fit(train_features, train_salary)
boosted_prediction_train = gradient_boost.predict(train_features)
boosted_prediction = gradient_boost.predict(test_features)

print("XGBoost: R^2 score on training data: {}".format(r2_score(train_salary, boosted_prediction_train)))
print("XGBoost: R^2 score on testing data: {}".format(r2_score(test_salary, boosted_prediction)))

# Make a kernel density function from testing data and predictions
predicted_salary = simple_regression.predict(test_features)

fig, ax = plt.subplots()

sns.kdeplot(x=test_salary, ax=ax, label='True salaries')
sns.kdeplot(x=predicted_salary, ax=ax, label='Prediction: linear regression')
sns.kdeplot(x=boosted_prediction, ax=ax, label='Prediction: XGBoost')

plt.legend()
plt.show()
