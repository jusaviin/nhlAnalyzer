#!/Users/jviinika/code/nhl/nhlEnvironment/bin/python3

from nhlpy import NHLClient
from geopy.geocoders import Nominatim
from manualDataEntry import NHLTeamData, NHLPlayerData
import country_converter as coco
import time
import json

def formatCityName(player):
    """
    Format the birth city of a player from NHL API dictionary to a good format
    
    Argument:
        player: Player dictionary read from NHL API
        
    Return:
        Birth city, state, and country for the player
    """
            
    city = ""
    state = ""
    if "birthStateProvince" in player:
        state = ", {}".format(player["birthStateProvince"]["default"])
        
    # There are players who are missing birth city
    # These cases have been fixed by manually entering the missing data
    if "birthCity" in player:
        city = player["birthCity"]["default"] + state
        countryCode = player["birthCountry"]
    else:
        data_provider = NHLPlayerData()
        city = data_provider.get_birth_city(player["id"])
        state = data_provider.get_birth_state(player["id"])
        countryCode = data_provider.get_birth_country(player["id"])
        
        if state != "":
            state = ", {}".format(state)
            city = city + state
    
    # Transform the country code to full country name to be used in geolocation
    # Comma is there so separate country from the name for the geolocator
    country = ", " + coco.convert(names=countryCode, to="name_short")
    
    return city, state[2:], country
    

def addCityToDictionary(geolocator, cityLocations, city, state_code, country = ""):
    """
    Function for adding a new city to the city locations dictionary
    
    Arguments:
        geolocator = Nominatim object for geolocating the cities
        city = City name formatted according to NHL API rules
        cityLocation = Dictionary to which the city infomation is added
        state_code = Two letter abbreviation for state in USA and Canada
        country = Country in which the city is located
    """
    
    # There are some city names in North America that are copied from Europe.
    # In order for the geolocator to find these reliably, provide also USA or
    # Canada to the locator in case state_code is provided but country is not
    if country == "" and state_code != "":
        if state_code in ["AB", "BC", "MB", "NB", "NL", "NT", "NS", "NU", "ON", "PE", "QC", "SK", "YT"]:
            country = ", Canada"
        else:
            country = ", United States"
            
    # Some cities in NHL API are misspelled, which breaks the geolocator
    # Manually fix these misspellings here
    cityLocator = city
    if cityLocator == "St-Francois de Madaw, NB":
        # Saint-François-de-Madawaska is cut short
        cityLocator = "St-Francois de Madawaska, NB"
    elif cityLocator == "Maters" and country == ", Switzerland":
        # Naters is misspelled as Maters
        cityLocator = "Naters"
    elif cityLocator == "Ljunby" and country == ", Sweden":
        # Ljungby is misspelled as Ljunby
        cityLocator = "Ljungby"
    elif cityLocator == "Garden River, First Nations, ON":
        # First Nations throws the geolocator off here
        cityLocator = "Garden River, ON"
        
    
    # Geolocate the city and find its latitude and longitude
    location = geolocator.geocode(cityLocator + country)
    cityInfo = {}
    cityInfo["coordinates"] = [location.latitude, location.longitude]
                
    # This gives the city name in local language
    cityInfo["nameLocal"] = location.raw['name']
                    
    # We also want to use the city name in english. Read that too
    time.sleep(1)  # Can only make 1 Nominatim request per second
    location = geolocator.geocode(cityLocator + country, language="en")
    cityInfo["nameEnglish"] = location.raw['name']
                    
    # Also remember the country and state information in English
    display_name = location.raw["display_name"]
    country = display_name.split(",")[-1].strip()
    state_full = display_name.split(",")[-2].strip()
    
    # In some cases the second last item in display_name gives zip code
    # If this is the case, we need to read the third last split for the state information
    if any(char.isdigit() for char in state_full):
        state_full = display_name.split(",")[-3].strip()
                  
    # Only apply state information for Unites States and Canada
    cityInfo["country"] = country
    if country in ["United States", "Canada"]:
        cityInfo["state"] = state_full
        cityInfo["state_code"] = state_code
                    
                
    # Add the city info to the cityLocations dictionary
    cityLocations[city] = cityInfo
    time.sleep(1)  # Can only make 1 Nominatim request per second
    

def main():
    """
    Main program. Creates a json file with information about birth cities of NHL players.
    Also cities of all the teams are added to the json file
    """

    # Define the filename for the city file we want to modify/create
    cityFileName = "cityCoordinatesUpdatedAgain.json"

    # If the json file exists, append new cities to that
    # If it does not exist, create a new one
    cityLocations = {}
    try:
        with open(cityFileName, "r", encoding='utf-8') as f:
            cityLocations = json.load(f)
            print("Updating city dictionary in file {}".format(cityFileName))
    except FileNotFoundError:
        print("Creating a new city dictionary with file name {}".format(cityFileName))
        
    # Create the geolocator to find the city coordinates from city name
    geolocator = Nominatim(user_agent="nhlCityLocationCreator")
        
    # Start by adding all the cities from where the NHL teams are from
    # All teams that have played in the league since 2008 are included
    # For some reason cities are not included in NHL API, so adding them manually
    data_finder = NHLTeamData()
    nhlCities = data_finder.get_all_cities()
        
    print("Locating team home cities")
    for city in nhlCities:
        if city not in cityLocations:
            addCityToDictionary(geolocator, cityLocations, city, city[-2:])
    
    # Once the home cities of the teams are gone through, go through all the players

    # Prepare the NHL client
    client = NHLClient()

    # Define the seasons for which the rosters are scanned
    seasons = ["20252026"]

    # Loop over seasons
    for currentSeason in seasons:
        print("Finding cities for all players for {} season".format(currentSeason))
        
        # Find all the teams that were playing in the given season
        teams = client.teams.teams(date="{}-01-30".format(currentSeason[-4:]))

        # Loop over teams that played in the NHL the given season
        for team in teams:
        
            # Debug
            #if team["abbr"] != "STL":
            #    continue

            # Print a message that we are finding cities for a spacific team
            print("Finding city locations for {}".format(team['name']))

            # Loop over all players in the given team
            roster = client.teams.team_roster(team_abbr=team['abbr'], season = currentSeason)
            for position in roster:
                for player in roster[position]:
                
                    # Debug
                    #print(player)
            
                    # Get the city and state information in a nice format
                    city, state, country = formatCityName(player)
        
                    # If the city is not already in the cityLocations dictionary, find its coordinates
                    # and add it to the dictionary
                    if city not in cityLocations:
                        addCityToDictionary(geolocator, cityLocations, city, state, country)

    # After all the city locations have been gone through, save the output to json file
    with open(cityFileName, "w", encoding='utf-8') as f:
        json.dump(cityLocations, f, indent=4, ensure_ascii=False)

# Follow good coding practices
if __name__ == "__main__":
    main()
