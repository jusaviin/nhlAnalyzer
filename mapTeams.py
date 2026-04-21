# Macro for creating a html map containing of roster of a selected NHL teams

import sqlite3
import pandas as pd
import folium

def save_map(map, save_name):
    """
    Helper function to save the map into html file
    
    Arguments:
        map = Folium map that is saved to the file
        save_name = Name given to the created html file
    """
    
    if not save_name.endswith(".html"):
        save_name = save_name + ".html"
    map.save(save_name)
    

def mapTeamDictionary(map, team_dictionary):
    """
    Helper function to map all teams from a team dictionary
    
    Arguments:
        map = Folium map to which the teams are added
        team_dictionary = Dictionary containing the team information
    """
    for team in team_dictionary:
        folium.Marker(
            location=team_dictionary[team]["coordinates"],
            popup=team_dictionary[team]["city"],
            tooltip=team_dictionary[team]["name"],
            icon=folium.CustomIcon(icon_image=team_dictionary[team]["logo"], icon_size=[75,75])
        ).add_to(map)
    

def mapTeams(season, save_name = "teamTest.html"):
    """
    Maps all the teams from the selected season
    
    Arguments:
        season = Starting year of the requested season
        save_name = Name given to the created html file
    """
    
    # Connect to the database that contains team information
    connection = sqlite3.connect('nhlDatabase.db')
    
    # Find the teams that played in the specified season
    sql_query = "SELECT name, city, logo, arena_latitude AS latitude, arena_longitude AS longitude \
                 FROM teams \
                 WHERE code IN \
                 (SELECT team FROM team_season_stats \
                  WHERE season = ?)"
                  
    team_frame = pd.read_sql_query(sql_query, connection, params=(season,))
    
    # Extract the team information from the dataframe
    teamPoints = {}
    for team in team_frame.itertuples():
    
        team_info = {}
        team_info["name"] = team.name
        team_info["city"] = team.city
        team_info["logo"] = team.logo
        team_info["coordinates"] = [team.latitude, team.longitude]
        
        teamPoints[team] = team_info
        
        
    # Create a a new map centered at North America
    map = folium.Map(location=[40, -100], zoom_start=4)
    
    # Add all teams to the map
    mapTeamDictionary(map, teamPoints)
        
    # Save the map
    save_map(map, save_name)
    
    # Close the connection to the database
    connection.close()
    

def mapRosters(mappedTeamsAndSeasons, save_name = "rosterTest.html"):
    """
    Maps all the requested team rosters from the requested seasons and saves
    them into a html.file
    
    Arguments:
        mappedTeamsAndSeasons = List of (team, season) tuples telling what to draw
        save_name = Name given to the created html file
    """

    # Connect to the database that contains player and city information
    connection = sqlite3.connect('nhlDatabase.db')

    # Create a map centered on somewhere in the Atlantic
    map = folium.Map(location=[50, -30], zoom_start=3)
        
    # Loop over all the teams we want to map and map their rosters
    mapPoints = {}
    teamPoints = {}
    for team, season in mappedTeamsAndSeasons:
    
        # First, find the coordinates for the team stadium
        sql_query = "SELECT name, city, logo, arena_latitude AS latitude, arena_longitude AS longitude \
                     FROM teams WHERE code = ?"
                     
        team_frame = pd.read_sql_query(sql_query, connection, params=(team,))
        team_info = {}
        team_info["name"] = team_frame.loc[0,"name"]
        team_info["city"] = team_frame.loc[0,"city"]
        team_info["logo"] = team_frame.loc[0,"logo"]
        team_info["coordinates"] = [team_frame.loc[0,"latitude"], team_frame.loc[0,"longitude"]]
        
        if team not in teamPoints:
            teamPoints[team] = team_info
    
        # Then find the roster of the team for the given season
        sql_query = "SELECT player_first_name AS first_name, player_last_name AS last_name, \
                             city_name_english AS city_name, city_state_code AS state_code, \
                             city_latitude AS latitude, city_longitude AS longitude  \
                      FROM roster \
                      WHERE team_code = ? AND season = ?"
        roster = pd.read_sql_query(sql_query, connection, params=(team, season))
                
        # Loop over all the players in the roster
        for player in roster.itertuples(index=False):
                
            # Find the city where this player was born in
            city = player.city_name
            state = player.state_code
            
            # Check if the state is NULL in the database
            if pd.isna(state):
                # If there is no state information, use city directly as city key
                cityKey = city
            else:
                # If state information is included, add this to the city key
                cityKey = city + ", " + state
            
            coordinates = [player.latitude, player.longitude]
            playerName = player.first_name + " " + player.last_name
                
            # If the city with unique key is already on the map points, add to existing description
            # If it is not in the map points, create a new entry to map points
            if cityKey in mapPoints:
                # Adding to existing map point if the player is not already there
                if playerName not in mapPoints[cityKey]["players"]:
                    mapPoints[cityKey]["players"].append(playerName)
            else:
                # Creating a new map point
                cityPoint = {}
                cityPoint["coordinates"] = coordinates
                cityPoint["players"] = [playerName]
                mapPoints[cityKey] = cityPoint
    
    # Once we have collected all the players and teams  we want to map, draw them to the map
    
    # Start with the teams
    mapTeamDictionary(map, teamPoints)
    
    # Then add the players
    for city in mapPoints:
            
        # TODO: Change the marker color based on how many players are from that city
        # Note: folium uses HTML rendering, so new line is given with command <br>
        playerString = mapPoints[city]["players"][0]
        for iPlayer in range(1, len(mapPoints[city]["players"])):
            playerString = playerString + "<br>" + mapPoints[city]["players"][iPlayer]
        
        folium.Marker(
            location=mapPoints[city]["coordinates"],
            popup=city,
            tooltip=playerString,
            icon=folium.Icon(color="blue")
        ).add_to(map)
        
    # Save the map
    save_map(map, save_name)
    
    # Close the connection to the database
    connection.close()


def main():
    """
    Main function. Provides a list of teams and seasons to the drawer macro.
    TODO: More user friendly interface
    TODO: It would be cool to add historical logos for the teams
    TODO: Scrape historical arenas from Wikipedia for historical team mapping
    """
    
    teamsAndSeasons = [("CHI", 2025)]
    mapRosters(teamsAndSeasons, "chicago2025")
    mapTeams(2025, "nhl2025")

# Follow good coding practices
if __name__ == "__main__":
    main()
