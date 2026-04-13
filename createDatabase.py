# Create a SQLite database for the NHL and fill in some information
# Notice that all previous tables from the database are wiped using this script
# TODO: There should be some options on which information to fill

# Required imports
import sqlite3
import json
import time
import pandas
import warnings

# The code gives performance warnings for the pandas dataframes.
# The dataframe here is only used to transfer data from csv files to SQLite database.
# Thus we do not care about these warnings, and can safely suppress them.
warnings.simplefilter(action='ignore', category=pandas.errors.PerformanceWarning)

from nhlpy import NHLClient
from manualDataEntry import NHLTeamData, NHLPlayerData

# MoneyPuck has inconsistent team names. Transform all to follow NHL API convention.
moneyPuckDecoder = {"L.A": "LAK",
                    "N.J": "NJD",
                    "T.B": "TBL",
                    "S.J": "SJS"}

def formatCityName(player):
    """
    Format the birth city of a player from NHL API dictionary to a good format
    TODO: synchronize this function with the one in createCityLocationFile
    
    Argument:
        player = Player dictionary read from NHL API
        
    Return:
        Formatted birth city
    """
            
    city = ""
    state = ""
    if "birthStateProvince" in player:
        state = ", {}".format(player["birthStateProvince"]["default"])
        
    # There are players who are missing birth city
    # These cases have been fixed by manually entering the missing data
    if "birthCity" in player:
        city = player["birthCity"]["default"] + state
    else:
        data_provider = NHLPlayerData()
        city = data_provider.get_birth_city(player["id"])
        state = data_provider.get_birth_state(player["id"])
        
        if state != "":
            state = ", {}".format(state)
            city = city + state
    
    return city

def getAccentedName(player, nameString):
    """ 
    Function for getting player name using local spelling if possible

    Arguments:
        player = Dictionary containing player data from NHL API
        nameString = Can be either firstname or lastname
        
    Return:
        Properly accented player name
    """
    
    # If there are no alternative formats for the name, return default format
    if len(player[nameString]) == 1:
        return player[nameString]["default"]
        
    # If there are other formats, try to find the local language
    if player["birthCountry"] == "FIN":
        if "fi" in player[nameString]:
            return player[nameString]["fi"]
            
    if player["birthCountry"] == "SWE" or player["birthCountry"] == "DNK" or player["birthCountry"] == "NOR":
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
    
def fillPlayers(connection, cursor, nhl_client):
    """ 
    Function for filling the players table in the database
    All the players from NHL API that are included in season rosters for teams are included
    There might be inconsistensies between MoneyPuck and NHL API, these will be solved later
    Notice that player stats will be in another table

    Arguments:
        connection = Connection object to SQLite database
        cursor = cursor object to SQLite database
        nhl_client = Client connected to NHL API to read team information
    """
    
    # We need to avoid adding same players multiple times
    # Remember the player ID of all the added players, and only add new players if ID not already in database
    added_players = []
    
    # Loop over all the seasons we want to include in the database
    for season in range(2025, 2007, -1):
    
        # Create a season string from the season number
        seasonString = "{}{}".format(season, season+1)
        print("Filling players table for season " + seasonString)
        
        teams = nhl_client.teams.teams(date="{}-01-30".format(season+1))
        time.sleep(1) # Do not overwhelm NHL API with excessive requests
        
        for team in teams:
    
            # Get the end-of-season roster for the studied team
            roster = nhl_client.teams.team_roster(team_abbr=team["abbr"], season=seasonString)
            time.sleep(1) # Do not overwhelm NHL API with excessive requests
        
            # Loop over all the players in the roster
            for position in roster:
                for player in roster[position]:
                
                    # Avoid adding same player from multiple seasons
                    if player["id"] in added_players:
                        continue
            
                    # Gather the player information
                    first_name = getAccentedName(player, "firstName")
                    last_name = getAccentedName(player, "lastName")
                    birth_city = formatCityName(player)
                    birth_date = player.get("birthDate", "NULL")
                    position = player.get("positionCode", "NULL")
                    handedness = player.get("shootsCatches", "NULL")
                    headshot = player.get("headshot", "NULL")
                    height = player.get("heightInCentimeters", "NULL")
                    weight = player.get("weightInKilograms", "NULL")
                
                    # Compile the SQL command
                    sql_command = f"""INSERT INTO players (id, first_name, last_name, birth_city, birth_date, position, handedness, headshot, height, weight) VALUES ({player["id"]}, \"{first_name}\", \"{last_name}\", \"{birth_city}\", \"{birth_date}\", \"{position}\", \"{handedness}\", \"{headshot}\", {height}, {weight});"""
                
                    # Once the command has been compiled, we can execute it
                    cursor.execute(sql_command)
                    
                    # Mark that this player is already in the database
                    added_players.append(player["id"])
                
            # Commit the changes one team at a time
            connection.commit()
   
def fillTeams(connection, cursor, nhl_client):
    """ 
    Function for filling the teams table in the database

    Arguments:
        connection = Connection object to SQLite database
        cursor = cursor object to SQLite database
        nhl_client = Client connected to NHL API to read team information
    """
    
    # Start by creating on object that finds manually collected data
    data_provider = NHLTeamData()
    
    # Find all the teams that have played in NHL between 2008 and current date
    # Fill their information from the database for the latest season they have participated
    added_teams = []
    
    # To optimize the performance, we can only check the seasons that actually add more teams to the list
    for season in [2026, 2024, 2014, 2011]:
        teams = nhl_client.teams.teams(date="{}-01-30".format(season))
        time.sleep(1) # Do not overwhelm NHL API with excessive requests
        
        for team in teams:
            if team["abbr"] not in added_teams:
                sql_command = f"""INSERT INTO teams (code, name, city, logo, arena, arena_capacity, arena_latitude, arena_longitude) VALUES (\"{team["abbr"]}\", \"{team["name"]}\", \"{data_provider.get_city(team["abbr"])}\", \"{team["logo"]}\", \"{data_provider.get_arena(team["abbr"])}\", {data_provider.get_arena_capacity(team["abbr"])}, {data_provider.get_arena_latitude(team["abbr"])}, {data_provider.get_arena_longitude(team["abbr"])});"""
                
                # Once the command has been compiled, we can execute it
                cursor.execute(sql_command)
                
                # Do not add the same team again
                added_teams.append(team["abbr"])
                
    # Once all commands have been execute to the cursor, save them to database by committing them
    connection.commit()
        
   
def fillCities(connection, cursor, cityFileName):
    """ 
    Function for filling the cities table in the database

    Arguments:
        connection = Connection object to SQLite database
        cursor = cursor object to SQLite database
        cityFileName = json file from which the city information is read
    """

    # Insert city information from json file
    try:
        with open(cityFileName, "r", encoding='utf-8') as f:
            cityLocations = json.load(f)
            print("Filled the cities table from file {}.".format(cityFileName))
        
            # Add all the VALUES for the INSERT command for all cities
            for cityCode in cityLocations:
            
                name_local = cityLocations[cityCode]["nameLocal"]
                name_english = cityLocations[cityCode]["nameEnglish"]
                country = cityLocations[cityCode].get("country","NULL")
                state = cityLocations[cityCode].get("state","NULL")
                state_code = cityLocations[cityCode].get("state_code","NULL")
                latitude = cityLocations[cityCode]["coordinates"][0]
                longitude = cityLocations[cityCode]["coordinates"][1]
        
                # Write the INSERT command for SQL
                sql_command = """INSERT INTO cities (name_NHL_API, name_local, name_english, country, state, state_code, latitude, longitude) VALUES (\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", {}, {});""".format(cityCode, name_local, name_english, country, state, state_code, latitude, longitude)
            
                # Once the command has been compiled, we can execute it
                cursor.execute(sql_command)
            
            # Commit the changes to save them to the database
            connection.commit()
        
        
    except FileNotFoundError:
        print("Could not open the file {}. Will not initialize the cities table.".format(cityFileName))
 
 
def fillTeamStats(connection):
    """ 
    Function for filling the team statistics for all seasons since 2008

    Arguments:
        connection = Connection object to SQLite database
    """
    
    # First collect all data to memory:
    all_team_data = []
    
    # Loop over all the seasons we want to include in the database
    for season in range(2025, 2007, -1):
    
        for phase in ["regular", "playoffs"]:
        
            # There is no playoff data yet for 2025 season
            if season == 2025 and phase == "playoffs":
                continue
        
            # Regular season or playoffs stats for the teams
            teamStats = pandas.read_csv("moneyPuck/teams_{}_{}.csv".format(season, phase))
        
            # Assign a new column for phase of season
            teamStats = teamStats.assign(phase=phase)
            
            # Rename some columns to make them consistent between tables
            # We need to do this at this point as some columns are inconsistent between years
            teamStats.rename(columns={"iceTime": "icetime", "penalityMinutesFor": "penaltyMinutesFor", "penalityMinutesAgainst": "penaltyMinutesAgainst", "penalitiesFor": "penaltiesFor", "penalitiesAgainst": "penaltiesAgainst"}, inplace=True)
            
            # Collect the stats to all_team_data list
            all_team_data.append(teamStats)
            
    # Combine all data into a single dataframe
    team_data_for_sql = pandas.concat(all_team_data, ignore_index=True)
    
    # Decode team names
    team_data_for_sql["team"] = team_data_for_sql["team"].replace(moneyPuckDecoder)
    
    # Drop unwanted columns from the combined dataframe to get better performance
    team_data_for_sql.drop(columns=["name", "team.1", "position"], inplace=True)
        
    # Write the combined dataframe to the database
    team_data_for_sql.to_sql(name="team_season_stats", con=connection, index=False, if_exists="append")
 
def fillGoalieStats(connection):
    """ 
    Function for filling the team statistics for all seasons since 2008

    Arguments:
        connection = Connection object to SQLite database
    """
    
    # First collect all data to memory:
    all_goalie_data = []
    
    # Loop over all the seasons we want to include in the database
    for season in range(2025, 2007, -1):
    
        for phase in ["regular", "playoffs"]:
        
            # There is no playoff data yet for 2025 season
            if season == 2025 and phase == "playoffs":
                continue
        
            # Regular season or playoffs stats for the teams
            goalieStats = pandas.read_csv("moneyPuck/goalies_{}_{}.csv".format(season, phase))
            
            # Add column to distinguish regular season and playoffs
            goalieStats = goalieStats.assign(phase=phase)
            
            # Collect the season stats into a list
            all_goalie_data.append(goalieStats)
            
    # Combine all data into a single dataframe
    goalie_data_for_sql = pandas.concat(all_goalie_data, ignore_index=True)
    
    # Decode team names
    goalie_data_for_sql["team"] = goalie_data_for_sql["team"].replace(moneyPuckDecoder)
    
    # Rename some columns to make them consistent between tables
    goalie_data_for_sql.rename(columns={"penalityMinutes": "penaltyMinutes"}, inplace=True)
    
    # Drop unwanted columns from the combined dataframe to get better performance
    goalie_data_for_sql.drop(columns=["name", "position"], inplace=True)
        
    # Write the combined dataframe to the database
    goalie_data_for_sql.to_sql(name="goalie_season_stats", con=connection, index=False, if_exists="append")
            
def fillSkaterStats(connection):
    """ 
    Function for filling the team statistics for all seasons since 2008

    Arguments:
        connection = Connection object to SQLite database
    """
    
    # First collect all data to memory:
    all_skater_data = []
    
    # Loop over all the seasons we want to include in the database
    for season in range(2025, 2007, -1):
    
        for phase in ["regular", "playoffs"]:
        
            # There is no playoff data yet for 2025 season
            if season == 2025 and phase == "playoffs":
                continue
        
            # Regular season or playoffs stats for the teams
            skaterStats = pandas.read_csv("moneyPuck/skaters_{}_{}.csv".format(season, phase))
            
            # Add column to distinguish regular season and playoffs
            skaterStats = skaterStats.assign(phase=phase)
            
            # Collect the season stats into a list
            all_skater_data.append(skaterStats)
       
    # Combine all data into a single dataframe
    skater_data_for_sql = pandas.concat(all_skater_data, ignore_index=True)
    
    # Decode team names
    skater_data_for_sql["team"] = skater_data_for_sql["team"].replace(moneyPuckDecoder)  
       
    # Remove the columns from the dataframe that we do not want to store
    skater_data_for_sql.drop(columns=["name", "position", "I_F_shifts", "I_F_penalityMinutes", "I_F_faceOffsWon"], inplace=True)
            
    # Rename some columns to make them consistent between tables
    skater_data_for_sql.rename(columns={"penalityMinutes": "penaltyMinutes", "penalityMinutesDrawn": "penaltyMinutesDrawn"}, inplace=True)
        
    # Write the dataframe to the database
    skater_data_for_sql.to_sql(name="skater_season_stats", con=connection, index=False, if_exists="append")
     
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
    
    # Initialize the tables
    initializeTables = True
    if initializeTables:
        initializationFile = "dataBaseSchema.sql"
        with open(initializationFile, 'r') as sql_file:
            sql_script = sql_file.read()

        # Use a cursor for updating information and run the initialization script
        cursor.executescript(sql_script)
        print("Initialized the tables from file {}".format(initializationFile))
    
    # Fill information from NHL API
    fillNHLAPI = True
    if fillNHLAPI:

        # Fill the cities table
        cityFileName = "nhlPlayerHomeTownsFrom2008To2026.json"
        fillCities(connection, cursor, cityFileName)
        print("Cities table ready")
    
        # Fill the teams table
        print("Filling teams table")
        fillTeams(connection, cursor, nhl_client)
        print("Teams table ready")
    
        # Fill the players table
        print("Filling players table")
        fillPlayers(connection, cursor, nhl_client)
        print("Players table ready")
        
    # Fill information from MoneyPuck csv files
    fillMoneyPuck = True
    if fillMoneyPuck:
        print("Filling stats from MoneyPuck")
    
        # Fill the teams information from MoneyPuck
        fillTeamStats(connection)
        fillGoalieStats(connection)
        fillSkaterStats(connection)

    # Close the connection
    connection.close()

# Follow good coding practices
if __name__ == "__main__":
    main()
