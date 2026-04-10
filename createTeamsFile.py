#!/Users/jviinika/code/nhl/nhlEnvironment/bin/python3

from nhlpy import NHLClient
from manualDataEntry import NHLTeamData
import json

# Define the filename for the team file we want to create
teamFileName = "nhlTeams.json"

teamDictionary = {}

client = NHLClient()

# Manually collected data
data_provider = NHLTeamData()

# Get all current teams
teams = client.teams.teams()

for team in teams:
    if team["abbr"] not in teamDictionary:
        teamDictionary[team["abbr"]] = {}
        teamDictionary[team["abbr"]]["name"] = team["name"]
        teamDictionary[team["abbr"]]["logo"] = team["logo"]
        teamDictionary[team["abbr"]]["franchise_id"] = team["franchise_id"]
        teamDictionary[team["abbr"]]["city"] = data_provider.get_city()
        teamDictionary[team["abbr"]]["city"] = data_provider.get_city()
        teamDictionary[team["abbr"]]["city"] = data_provider.get_city()
        teamDictionary[team["abbr"]]["city"] = data_provider.get_city()
        teamDictionary[team["abbr"]]["city"] = data_provider.get_city()
        
        
print(teamDictionary)

# After all the city locations have been gone through, save the output to json file
#with open(cityFileName, "w", encoding='utf-8') as f:
#    json.dump(cityLocations, f, indent=4, ensure_ascii=False)
