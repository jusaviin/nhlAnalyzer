# Macro to analyze and visualize goalie statistics
# Combine data from MoneyPuck and NHL API for this
# Maybe at some point I will create my own SQL database with all the information
# But for now, these will suffice

import pandas
from nhlpy import NHLClient

# Make a scatter plot with goalie data using pyplot
#
#  Arguments:
#   goalieData = pandas DataFrame containing studied goalie data
#   xAxis = Label in the DataFrame to be used as x-axis
#   yAxis = Label in the DataFrame to be used as y-axis
#   hoverText = Show the goalie names when hovering mouse over points in the plot. Default = True
#   printNames = Print the goalie names next to the data points. Default = True
#   diagonalLine = Draw a diagonal line to the plot. Default = False
#   minGamesPlayed = Minimum number of games played to be included in the plot. Default = 20
def scatterWithPyplot(goalieData, xAxis, yAxis, hoverText = True, printNames = True, diagonalLine = False, minGamesPlayed = 20):

    import matplotlib.pyplot as plt
    import mplcursors

    # Use the filter for minimum number of games played
    filteredGoalies = goalieData[goalieData["gamesPlayed"] >= minGamesPlayed]

    # Illustrate the data as a scatter plot
    goaliePlot, ax = plt.subplots()
    filteredGoalies.plot(xAxis, yAxis, kind='scatter', ax=ax)

    # Create list of goalie names in same order as scatter points
    goalieNames = filteredGoalies.index.tolist()

    # Use mplcursors with custom annotations
    if hoverText:
        mplcursors.cursor(goaliePlot, hover=True).connect("add", lambda sel: sel.annotation.set_text(goalieNames[sel.index]))
  
    # Associate a player for each point
    if printNames:
        for goalieIndex, stats in filteredGoalies.iterrows():
            ax.annotate(goalieIndex,
                        xy=(stats[xAxis], stats[yAxis]),
                        xytext=(5,0), textcoords='offset points',
                        family='sans-serif', fontsize=4, color='darkslategrey')
                        
    # Draw a diagonal line to visualize which goalies same more goals than expected
    if diagonalLine:
        xMin = filteredGoalies[xAxis].min()
        xMax = filteredGoalies[xAxis].max()
        yMin = filteredGoalies[yAxis].min()
        yMax = filteredGoalies[yAxis].max()
        globalMin = min(xMin, yMin)
        globalMax = max(xMax, yMax)
        plt.plot([globalMin,globalMax], [globalMin,globalMax])
                    
    # Show the plot
    plt.show()
    
# Make a scatter plot with goalie data using plotly
#
#  Arguments:
#   goalieData = pandas DataFrame containing studied goalie data
#   xAxis = Label in the DataFrame to be used as x-axis
#   yAxis = Label in the DataFrame to be used as y-axis
#   diagonalLine = Draw a diagonal line to the plot. Default = False
#   minGamesPlayed = Minimum number of games played to be included in the plot. Default = 20
def scatterWithPlotly(goalieData, xAxis, yAxis, diagonalLine = False, minGamesPlayed = 20):

    import plotly.graph_objects as go

    # Use the filter for minimum number of games played
    filteredGoalies = goalieData[goalieData["gamesPlayed"] >= minGamesPlayed]
    
    # Reset index so goalie names are a column
    df = filteredGoalies.reset_index().rename(columns={'index': 'goalieName'})

    # Create a plotly graph objects figure
    fig = go.Figure()
    
    # Add the scatter plot to the figure
    fig.add_trace(go.Scatter(
        x=df[xAxis],
        y=df[yAxis],
        mode='markers',
        text=df['goalieName'],
        hovertemplate='<b>%{text}</b><br>' + xAxis + ': %{x:.2f}<br>' + yAxis + ': %{y:.2f}<extra></extra>',
        marker=dict(size=8, color='blue'),
        name='All Goalies'
    ))

    fig.update_traces(marker=dict(size=8))
    
    # Create dropdown buttons for each goalie
    buttons = [dict(label='All Goalies',
                    method='update',
                    args=[{'marker.color': [['blue']*len(df)]},
                          {'title': 'All Goalies'}])]
                          
    for idx, goalie in enumerate(df['goalieName']):
        colors = ['lightgray'] * len(df)
        colors[idx] = 'red'  # Highlight selected goalie
        buttons.append(
            dict(label=goalie,
                 method='update',
                 args=[{'marker.color': [colors]},
                       {'title': f'Highlighted: {goalie}'}])
        )
        
    # Add dropdown menu and axis labels
    fig.update_layout(
        # Note: Title added here has different positioning compared to annotations below
        #title={
        #    'text': 'NHL goalie performance for season 2025-2026',
        #    'x': 0.5,
        #    'xanchor': 'center',
        #    'font': {'size': 20}
        #},
        xaxis_title=xAxis,
        yaxis_title=yAxis,
        margin=dict(l=200),  # Add margin to the left
        updatemenus=[
            dict(
                type='dropdown',
                direction='down',
                x=-0.07,
                y=1.15,
                showactive=True,
                buttons=buttons
            )
        ]
    )
    
    # Add title as annotation in order to have same centering as the disclaimer
    fig.add_annotation(
        text='NHL goalie performance for season 2025-2026',
        xref='paper',
        yref='paper',
        x=0.5,
        y=1.12,
        showarrow=False,
        font=dict(size=20),
        xanchor='center'
    )
    
    # Add a disclaimer telling the data source
    fig.add_annotation(
        text='Data for the figure is dowloaded from moneypuck.com on March 15, 2026. All goalies with at least {} played games are included.'.format(minGamesPlayed),
        xref='paper',
        yref='paper',
        x=0.5,
        y=1.05,
        showarrow=False,
        font=dict(size=10, color='gray'),
        xanchor='center'
    )
    
    
    # Draw a diagonal line to visualize which goalies same more goals than expected
    if diagonalLine:
        xMin = filteredGoalies[xAxis].min()
        xMax = filteredGoalies[xAxis].max()
        yMin = filteredGoalies[yAxis].min()
        yMax = filteredGoalies[yAxis].max()
        globalMin = min(xMin, yMin)
        globalMax = max(xMax, yMax)
        fig.add_shape(type="line",
                      x0=globalMin, y0=globalMin, x1=globalMax, y1=globalMax,
                      line=dict(color="RoyalBlue",width=3)
        )
    
    fig.show()
    
    # Save the figure to a file
    fig.write_html("goaliePlot.html")
    

# Collect the data from MoneyPuck csv file and NHL API
def collectGoalieData():
    
    # Start with expected goals agains vs. goals agains
    goalie = []
    goalsAgains = []
    expectedGoalsAgainst = []
    gamesPlayed = []
    iceTime = []

    # The input is in csv format, use Python reader for csv
    import csv
    with open('moneyPuck/goalies_season2526_2026-03-15.csv', newline='') as csvfile:

        # Since the file as column labels in the first row and values in the following rows, DictReader work well
        # Each row return a dictionary with keys defined by the strings in the first row
        moneyPuckReader = csv.DictReader(csvfile)
        for row in moneyPuckReader:
    
            # In this example, we want to get all stituation goals and expected goals for each team
            if row["situation"] == "all":
            
                goalie.append(row["name"])
                goalsAgains.append(float(row["goals"])) # Note that csv reader returns each value as string
                expectedGoalsAgainst.append(float(row["xGoals"])) # Note that csv reader returns each value as string
                gamesPlayed.append(int(row["games_played"]))
                iceTime.append(float(row["icetime"]))
                
    # TODO: Add things like goals agains average and save percentage from NHL API
    
    # Add the collected data to pandas dataframe and return the dataframe
    goalieData = {"goalsAgainst": goalsAgains, "expectedGoalsAgainst": expectedGoalsAgainst, "gamesPlayed": gamesPlayed, "iceTime": iceTime}
    goalieDataFrame = pandas.DataFrame(goalieData, index = goalie)
    
    # Normalize the goals agains and expected goals agains per 60 minutes played
    # Note: MoneyPuck gives the icetime in seconds. To transform this into 60 minute chunks
    # it needs to me divided bo 60*60 = 3600
    goalieDataFrame["goalsAgainstPer60"] = goalieDataFrame["goalsAgainst"] / goalieDataFrame["iceTime"] * 3600.0
    goalieDataFrame["expectedGoalsAgainstPer60"] = goalieDataFrame["expectedGoalsAgainst"] / goalieDataFrame["iceTime"] * 3600.0
    
    # Sort the DataFrame to be in alphabatical order based on surname
    goalieDataFrame.sort_index(
        key=lambda x: pandas.Series(x).str.split(n=1).apply(lambda name: (name[1], name[0])),
        inplace=True
    )
    
    return goalieDataFrame

# Main function
# Select which visualizations to make
def main():
    goalieData = collectGoalieData()
    #scatterWithPyplot(goalieData, "goalsAgainstPer60", "expectedGoalsAgainstPer60", printNames = False, diagonalLine = True)
    scatterWithPlotly(goalieData, "goalsAgainstPer60", "expectedGoalsAgainstPer60", diagonalLine = True)

# Follow good coding practices
if __name__ == "__main__":
    main()
