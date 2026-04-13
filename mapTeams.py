# Macro for creating a html map containing of roster of a selected NHL teams

import sqlite3
import pandas as pd

def mapTeams(mappedTeamsAndSeasons):
    """
    Main function. Connects to SQLite database and calls methods to fill it.
    """

    # Connect to the database that contains player and city information
    connection = sqlite3.connect('nhlDatabase.db')

    # Create a map centered on somewhere in the Atlantic
    import folium
    map = folium.Map(location=[50, -30], zoom_start=3)
        
    # Loop over all the teams we want to map and map their rosters
    mapPoints = {}
    for team, season in mappedTeamsAndSeasons:
    
        # TODO: If we query multiple teams and same player is in both of them
        # TODO: (for example we want to plot same team from multiple seasons)
        # TODO: the same player will show multiple times! Need to build protection
        # TODO: against this!
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
            
            # TODO: If not state, currently a string "NULL" is inserted instead of NULL value!
            # Check if the state is NULL in the database
            if state == "NULL":
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
                # Adding to existing map point
                mapPoints[cityKey]["players"].append(playerName)
            else:
                # Creating a new map point
                cityPoint = {}
                cityPoint["coordinates"] = coordinates
                cityPoint["players"] = [playerName]
                mapPoints[cityKey] = cityPoint
    
    # Once we have collected all the players we want to map, draw them to the map
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
    map.save("testMap.html")
    
    # Close the connection to the database
    connection.close()


def main():
    """
    Main function. Provides a list of teams and seasons to the drawer macro.
    TODO: More user friendly interface
    """
    
    teamsAndSeasons = [("CHI", 2025), ("CHI", 2015)]
    mapTeams(teamsAndSeasons)
    

# Follow good coding practices
if __name__ == "__main__":
    main()
