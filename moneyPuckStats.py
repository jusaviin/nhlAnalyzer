# Visualize some stats from moneypuck

# Note: available keys in the dictionary can be printed with the command
# print(moneyPuckReader.fieldnames)
# They are:
# ['team', 'season', 'name', 'team', 'position', 'situation', 'games_played', 'xGoalsPercentage', 'corsiPercentage', 'fenwickPercentage', 'iceTime', 'xOnGoalFor', 'xGoalsFor', 'xReboundsFor', 'xFreezeFor', 'xPlayStoppedFor', 'xPlayContinuedInZoneFor', 'xPlayContinuedOutsideZoneFor', 'flurryAdjustedxGoalsFor', 'scoreVenueAdjustedxGoalsFor', 'flurryScoreVenueAdjustedxGoalsFor', 'shotsOnGoalFor', 'missedShotsFor', 'blockedShotAttemptsFor', 'shotAttemptsFor', 'goalsFor', 'reboundsFor', 'reboundGoalsFor', 'freezeFor', 'playStoppedFor', 'playContinuedInZoneFor', 'playContinuedOutsideZoneFor', 'savedShotsOnGoalFor', 'savedUnblockedShotAttemptsFor', 'penaltiesFor', 'penalityMinutesFor', 'faceOffsWonFor', 'hitsFor', 'takeawaysFor', 'giveawaysFor', 'lowDangerShotsFor', 'mediumDangerShotsFor', 'highDangerShotsFor', 'lowDangerxGoalsFor', 'mediumDangerxGoalsFor', 'highDangerxGoalsFor', 'lowDangerGoalsFor', 'mediumDangerGoalsFor', 'highDangerGoalsFor', 'scoreAdjustedShotsAttemptsFor', 'unblockedShotAttemptsFor', 'scoreAdjustedUnblockedShotAttemptsFor', 'dZoneGiveawaysFor', 'xGoalsFromxReboundsOfShotsFor', 'xGoalsFromActualReboundsOfShotsFor', 'reboundxGoalsFor', 'totalShotCreditFor', 'scoreAdjustedTotalShotCreditFor', 'scoreFlurryAdjustedTotalShotCreditFor', 'xOnGoalAgainst', 'xGoalsAgainst', 'xReboundsAgainst', 'xFreezeAgainst', 'xPlayStoppedAgainst', 'xPlayContinuedInZoneAgainst', 'xPlayContinuedOutsideZoneAgainst', 'flurryAdjustedxGoalsAgainst', 'scoreVenueAdjustedxGoalsAgainst', 'flurryScoreVenueAdjustedxGoalsAgainst', 'shotsOnGoalAgainst', 'missedShotsAgainst', 'blockedShotAttemptsAgainst', 'shotAttemptsAgainst', 'goalsAgainst', 'reboundsAgainst', 'reboundGoalsAgainst', 'freezeAgainst', 'playStoppedAgainst', 'playContinuedInZoneAgainst', 'playContinuedOutsideZoneAgainst', 'savedShotsOnGoalAgainst', 'savedUnblockedShotAttemptsAgainst', 'penaltiesAgainst', 'penalityMinutesAgainst', 'faceOffsWonAgainst', 'hitsAgainst', 'takeawaysAgainst', 'giveawaysAgainst', 'lowDangerShotsAgainst', 'mediumDangerShotsAgainst', 'highDangerShotsAgainst', 'lowDangerxGoalsAgainst', 'mediumDangerxGoalsAgainst', 'highDangerxGoalsAgainst', 'lowDangerGoalsAgainst', 'mediumDangerGoalsAgainst', 'highDangerGoalsAgainst', 'scoreAdjustedShotsAttemptsAgainst', 'unblockedShotAttemptsAgainst', 'scoreAdjustedUnblockedShotAttemptsAgainst', 'dZoneGiveawaysAgainst', 'xGoalsFromxReboundsOfShotsAgainst', 'xGoalsFromActualReboundsOfShotsAgainst', 'reboundxGoalsAgainst', 'totalShotCreditAgainst', 'scoreAdjustedTotalShotCreditAgainst', 'scoreFlurryAdjustedTotalShotCreditAgainst']

# As a first example, make a scatter plot with actual goas vs. expected goals from each team this season
teams = []
goals = []
expectedGoals = []

# The input is in csv format, use Python reader for csv
import csv
with open('moneyPuck/teams_season2526_2026-03-16.csv', newline='') as csvfile:

    # Since the file as column labels in the first row and values in the following rows, DictReader work well
    # Each row return a dictionary with keys defined by the strings in the first row
    moneyPuckReader = csv.DictReader(csvfile)
    for row in moneyPuckReader:
    
        # In this example, we want to get all stituation goals and expected goals for each team
        if row["situation"] == "all":
            teams.append(row["team"])
            goals.append(float(row["goalsFor"])) # Note that csv reader returns each value as string
            expectedGoals.append(float(row["xGoalsFor"])) # Note that csv reader returns each value as string

# Once we have the data extracted from the csv file, put it to pandas DataFrame
import pandas
goalData = {"goalsFor": goals, "xGoalsFor": expectedGoals}
goalDataFrame = pandas.DataFrame(goalData, index = teams)

# Illustrate the data as a scatter plot
import matplotlib.pyplot as plt
goalPlot, goalAxes = plt.subplots()
goalDataFrame.plot("goalsFor", "xGoalsFor", kind='scatter', ax=goalAxes)

# Associate a team for each point
for teamIndex, teamName in goalDataFrame.iterrows():
    print("Index: {}, name: {}".format(teamIndex, teamName))
    goalAxes.annotate(teamIndex, teamName, xytext=(-10,5), textcoords='offset points',
                family='sans-serif', fontsize=10, color='darkslategrey')

# Add a line to the figure to mark the line where goals match expected goals
plt.plot([160,250], [160,250])
plt.show()

# Derive a new column to the DataFrame
goalDataFrame["goalsAboveExpected"] = goalDataFrame["goalsFor"] - goalDataFrame["xGoalsFor"]

# Make a histogram for goals above expected
hist = goalDataFrame["goalsAboveExpected"].hist(bins=8)

# Adding title and labels
plt.title('Team scoring efficiency')
plt.xlabel('Goals above expected')
plt.ylabel('Couns')

# Display the histogram
plt.show()
