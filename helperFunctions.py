#!/Users/jviinika/code/nhl/nhlEnvironment/bin/python3

import country_converter as coco
from manualDataEntry import NHLPlayerData

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
