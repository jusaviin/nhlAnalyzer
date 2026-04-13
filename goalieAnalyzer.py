# Macro to analyze and visualize goalie statistics
# The data is read from SQL database

import sys
import pandas as pd
import sqlite3
    
def scatterWithPlotly(goalieData, xAxis, yAxis, diagonalLine = False, minGamesPlayed = 20):
    """
     Make a scatter plot with goalie data using plotly

    Arguments:
        goalieData = pandas DataFrame containing studied goalie data
        xAxis = Label in the DataFrame to be used as x-axis
        yAxis = Label in the DataFrame to be used as y-axis
        diagonalLine = Draw a diagonal line to the plot. Default = False
        minGamesPlayed = Minimum number of games played to be included in the plot. Default = 20
    """

    import plotly.graph_objects as go

    # Use the filter for minimum number of games played
    filteredGoalies = goalieData[goalieData["games_played"] >= minGamesPlayed]

    # Create a plotly graph objects figure
    fig = go.Figure()
    
    # Add the scatter plot to the figure
    fig.add_trace(go.Scatter(
        x=filteredGoalies[xAxis],
        y=filteredGoalies[yAxis],
        mode='markers',
        text=filteredGoalies['first_name'] + " " + filteredGoalies['last_name'],
        hovertemplate='<b>%{text}</b><br>' + xAxis + ': %{x:.2f}<br>' + yAxis + ': %{y:.2f}<extra></extra>',
        marker=dict(size=8, color='blue'),
        name='All Goalies'
    ))

    fig.update_traces(marker=dict(size=8))
    
    # Create dropdown buttons for each goalie
    buttons = [dict(label='All Goalies',
                    method='update',
                    args=[{'marker.color': [['blue']*len(filteredGoalies)]},
                          {'title': 'All Goalies'}])]
                          
    for idx, goalie_info in enumerate(filteredGoalies.itertuples(index=False)):
        colors = ['lightgray'] * len(filteredGoalies)
        colors[idx] = 'red'  # Highlight selected goalie
        goalie = f"{goalie_info.first_name} {goalie_info.last_name}"
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
    # TODO: text should not be hardcoded
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
    # TODO: text should not be hardcoded
    fig.add_annotation(
        text='Data for the figure is dowloaded from moneypuck.com on April 9, 2026. All goalies with at least {} played games are included.'.format(minGamesPlayed),
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
    
    
def collectGoalieData(season, phase, situation):
    """
    Read the goalie data for the specified season
    
    Arguments:
        season = Season for which the goalia data is read
        phase = "regular" for regular season or "playoffs" for playoffs
        situation = Play type: all, 5on5, 5on4, 4on5 or other
        
    Return:
        pandas dataframe containing contents of simple goalie stats view form NHL database.
    """
    
    # Check that input is good
    if phase not in ["regular", "playoffs"]:
        sys.exit("Error in collectGoalieData!\nThe phase parameter must be either regular or playoffs")
        
    if situation not in ["all", "5on5", "5on4", "4on5", "other"]:
        sys.exit("Error in collectGoalieData!\nThe situation parameter must be all, 5on5, 5on4, 4on5 or other")
    
    # Connect to the database that contains player and city information
    connection = sqlite3.connect('nhlDatabase.db')
    
    # Read the goalie information from the database
    sql_query = "SELECT * FROM simple_goalie_stats \
                 WHERE season = ? AND phase = ? AND situation = ? \
                 ORDER BY last_name, first_name"
    goalieDataFrame = pd.read_sql_query(sql_query, connection, params=(season, phase, situation))
    
    # Close the connection to the database
    connection.close()
    
    # Return the dataframe
    return goalieDataFrame

def main():
    """
    Main function. Currently just for testing the plotter
    """
    goalieData = collectGoalieData(2025, "regular", "all")
    scatterWithPlotly(goalieData, "goals_against_average", "xGoals_against_average", diagonalLine = True)

# Follow good coding practices
if __name__ == "__main__":
    main()
