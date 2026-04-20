# The player statistics and player basic information are read from two different sources
# This will result in some discrepancies in these tables
# 1) There will be players in the players table that do not have stats
#    Upon first incpection, these seem to be mostly prospects that have not
#    actually played in the NHL team yet, so I am going to ignore these cases.
# 2) There will be stats for players who are not in the players table.
#    I am not 100% sure how NHL API decides which players are in the team
#    season roster. It seems like if there is a mostly AHL player who only
#    plays a few games during the season, they do not make it to the roster in API.
#    However, they will have stats recorded. In these cases, we can use different
#    NHL API call to fill basic player information to the SQL database.
# The purpose of this script is to find all case 2) discrepancies and fill
# the players and cities tables with the information for the these players
#
# Notice that filling the database for all information happens last
# This is to avoid partially filled information in the database in case
# anything fails in data collection.

# Required imports
import sqlite3
import json
import time
import pandas
import sys
import subprocess

from nhlpy import NHLClient
from helperFunctions import cityFormatter, getAccentedName, add_quotes
from createCityLocationFile import addCityToDictionary
from createDatabase import fillCities
from geopy.geocoders import Nominatim

    
def fillPlayers(connection, cursor, players):
    """ 
    Function for adding missing players to the players table in the database
    Filling is done from a provided dictionary

    Arguments:
        connection = Connection object to SQLite database
        cursor = cursor object to SQLite database
        players = Dictionary containing missing player information
    """
    
    # Loop over all the missing players we are adding to the database
    for player in players:
    
        # Gather the player information
        id = player["id"]
        first_name = add_quotes(player["first_name"])
        last_name = add_quotes(player["last_name"])
        birth_city = add_quotes(player["birth_city"])
        birth_date = add_quotes(player["birth_date"])
        position = add_quotes(player["position"])
        handedness = add_quotes(player["handedness"])
        headshot = add_quotes(player["headshot"])
        height = player["height"]
        weight = player["weight"]
                
        # Compile the SQL command
        sql_command = f"""INSERT INTO players (id, first_name, last_name, birth_city, birth_date, position, handedness, headshot, height, weight) VALUES ({id}, {first_name}, {last_name}, {birth_city}, {birth_date}, {position}, {handedness}, {headshot}, {height}, {weight});"""
                
        # Once the command has been compiled, we can execute it
        cursor.execute(sql_command)
                
    # Commit all the changes at the same time
    connection.commit()
 
    
def find_players_cities(nhl_client, id_list):
    """
    Find players and cities they are from based on player ID list
    
    Arguments: 
        nhl_client = Client connected to NHL API to read team information
        id_list = List of player ID numbers that we need to find information for
        
    Return:
        player information list
        city information list
    """
    
    # Initialize the returned lists
    added_players = []
    added_cities = []
    
    # Create a class that helps to properly format city names
    cityHelper = cityFormatter()
    
    # Loop over all the player IDs
    for player_id in id_list:
    
        # Find the career stat entry for the player in question
        player = nhl_client.stats.player_career_stats(player_id=player_id)
        time.sleep(1) # Do not overwhelm the NHL API
        
        # Get the city and state information in a nice format
        city, state, country = cityHelper.formatCityName(player)
        
        city_entry = {}
        city_entry["name"] = city
        city_entry["state"] = state
        city_entry["country"] = country
        
        added_cities.append(city_entry)
        
        # Gather the player information from API entry
        name_entry = {}
        name_entry["id"] = player_id
        name_entry["first_name"] = getAccentedName(player, "firstName")
        name_entry["last_name"] = getAccentedName(player, "lastName")
        name_entry["birth_city"] = city
        name_entry["birth_date"] = player.get("birthDate", "NULL")
        name_entry["position"] = player.get("position", "NULL")
        name_entry["handedness"] = player.get("shootsCatches", "NULL")
        name_entry["headshot"] = player.get("headshot", "NULL")
        name_entry["height"] = player.get("heightInCentimeters", "NULL")
        name_entry["weight"] = player.get("weightInKilograms", "NULL")
        
        added_players.append(name_entry)
    
    # After collecting all data, return the lists
    return added_players, added_cities
    
     
def main():
    """
    Main function. Connects to SQLite database and calls methods to fill it.
    """
    
    # Create a client for information to be read from NHL API
    nhl_client = NHLClient()

    # Connect to the SQLite3 database
    databaseName = "nhlDatabase.db"
    connection = sqlite3.connect(databaseName)
    cursor = connection.cursor()
    print("Connected to database {}".format(databaseName))
    
    ##############################################################
    # Find stats entries that do not have a corresponding player #
    ##############################################################
    
    # Define the query to find missing player ids
    sql_query = """
      SELECT DISTINCT playerId FROM skater_season_stats
      WHERE playerId NOT IN (SELECT id FROM players)
    
      UNION ALL

      SELECT DISTINCT playerId FROM goalie_season_stats
      WHERE playerId NOT IN (SELECT id FROM players)
      """
      
    # Execute the query and store the values in a list
    missing_id_dataframe = pandas.read_sql_query(sql_query, connection)
    missing_player_ids = missing_id_dataframe["playerId"].values.tolist()

    # Once we have the list ready, we need to find who these players are and extract their information
    missing_players, missing_cities = find_players_cities(nhl_client, missing_player_ids)
    
    #############################################################
    # Geolocate the cities that are not already in our database #
    #############################################################
    
    # Start by finding the existing city location json file
    cityLocations = {}
    cityFileName = "cityCoordinatesUpdatedAgain.json"
    try:
        with open(cityFileName, "r", encoding='utf-8') as f:
            cityLocations = json.load(f)
            print("Updating city dictionary in file {}".format(cityFileName))
    except FileNotFoundError:
        sys.exit("Could not find city location file {}. Please provide an existing city location file!".format(cityFileName))
        
    # Add any cities not already in the city location file to the file
    geolocator = Nominatim(user_agent="nhlCityLocationCreator")
    for city in missing_cities:
        if city["name"] not in cityLocations:
            addCityToDictionary(geolocator, cityLocations, city["name"], city["state"], city["country"])
        
    # Update the city location file
    with open(cityFileName, "w", encoding='utf-8') as f:
        json.dump(cityLocations, f, indent=4, ensure_ascii=False)
    
    ########################################
    # Trim the newly geolocated city names #
    ########################################
    
    trimmedFileName = "nhlPlayerHomeTownsFrom2008To2026.json"
    subprocess.run(['bash', 'trimCityNames.sh', cityFileName, trimmedFileName])
    time.sleep(1) # Wait a bit after executing the bash command
    
    #############################################
    # Add the missing players into the database #
    #############################################
    
    fillPlayers(connection, cursor, missing_players)
    
    ############################################
    # Add the missing cities into the database #
    ############################################
    
    fillCities(connection, cursor, trimmedFileName)

    # Close the connection
    connection.close()

# Follow good coding practices
if __name__ == "__main__":
    main()
