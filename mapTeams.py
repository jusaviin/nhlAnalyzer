# Macro for creating a html map containing of roster of a selected NHL teams

import sqlite3
import pandas as pd

# Find the name with proper accents from NHL API
def getAccentedName(player, nameString):
    
    # If there are no alternative formats for the name, return default format
    if len(player[nameString]) == 1:
        return player[nameString]["default"]
        
    # If there are other formats, try to find the local language
    if player["birthCountry"] == "FIN":
        if "fi" in player[nameString]:
            return player[nameString]["fi"]
            
    if player["birthCountry"] == "SWE" or player["birthCountry"] == "DKN" or player["birthCountry"] == "NOR":
        if "sv" in player[nameString]:
            return player[nameString]["sv"]
            
    if player["birthCountry"] == "CZE" or player["birthCountry"] == "SVK":
        if "cs" in player[nameString]:
            return player[nameString]["cs"]
            
    if player["birthCountry"] == "DEU" or player["birthCountry"] == "CHE":
        if "de" in player[nameString]:
            return player[nameString]["de"]
            
    if player["birthCountry"] == "AUT":
        if "de" in player[nameString]:
            return player[nameString]["de"]
        if "cs" in player[nameString]:
            return player[nameString]["cs"]
            
    # There are a lot of Canadian players that might have French pronunciation for their name
    # This might be valid also for French and Swiss players, so do not have country specific argument
    if "fr" in player[nameString]:
        return player[nameString]["fr"]
            
        
    # If we cannot find properly accented name, just use the default name
    return player[nameString]["default"]

# To get accents properly in player names, we need find if there is local name available in NHL API
def determinePlayerName(player):
    
    # Get properly accented first and last names and put them together
    firstName = getAccentedName(player, "firstName")
    lastName = getAccentedName(player, "lastName")
    return firstName + " " + lastName

# Actual team mapping functions. Maps players from all the teams in the list
def mapTeams(mappedTeams):

    # Connect to the database that contains player and city information
    connection = sqlite3.connect('nhlDatabase.db')

    # Create a map centered on somewhere in the Atlantic
    import folium
    map = folium.Map(location=[50, -30], zoom_start=3)
        
    # Loop over all the teams we want to map and map their rosters
    mapPoints = {}
    for team in mappedTeams:
    
        # TODO: We should also be able to define which season we want to look at
        sql_query = f"SELECT p.first_name, p.last_name, p.birth_city, c.name_english, c.latitude, c.longitude  \
                      FROM players p JOIN cities c \
                      ON p.birth_city = c.name_NHL_API \
                      WHERE p.team_code = \'{team}\'"
        roster = pd.read_sql_query(sql_query, connection)
                
        # Loop over all the players in the roster
        for player in roster.itertuples(index=False):
                
            # Find the city where this player was born in
            city = player.name_english
            cityKey = player.birth_city
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


# Main function
# Read the list of teams to plot
# Provide the list to plotter functions
def main():
    teams = ["CBJ"]
    mapTeams(teams)
    

# Follow good coding practices
if __name__ == "__main__":
    main()
