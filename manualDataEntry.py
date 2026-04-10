#!/Users/jviinika/code/nhl/nhlEnvironment/bin/python3

class NHLTeamData:
    """
    We cannot get city or arena information for teams from NHL API
    I have manually collected this information from Wikipedia
    Source: https://en.wikipedia.org/wiki/List_of_National_Hockey_League_arenas
    Instead of scraping, I just manually checked the numbers and wrote them down
    This is not scalable and is prone to errors, but feasible with a limited number of teams
    This also saves me the hassle of properly formatting everything after scraping the data
    Latitude and longitude: geolocate the arena with Nominatim
    """
    
    def __init__(self):
        self.data = {}
        self.data["SJS"] = {"city": "San Jose, CA", "arena": "SAP Center", "capacity": 17435, "arena_latitude": 37.3328604, "arena_longitude": -121.9012247}
        self.data["NYR"] = {"city": "New York, NY", "arena": "Madison Square Garden", "capacity": 18006, "arena_latitude": 40.7505129, "arena_longitude": -73.9935159}
        self.data["DET"] = {"city": "Detroit, MI", "arena": "Little Caesars Arena", "capacity": 19515, "arena_latitude": 42.3409774, "arena_longitude": -83.0549545}
        self.data["MTL"] = {"city": "Montréal, QC", "arena": "Bell Centre", "capacity": 20962, "arena_latitude": 45.4960358, "arena_longitude": -73.5692029}
        self.data["PIT"] = {"city": "Pittsburgh, PA", "arena": "PPG Paints Arena", "capacity": 18387, "arena_latitude": 40.4395912, "arena_longitude": -79.9895408}
        self.data["BOS"] = {"city": "Boston, MA", "arena": "TD Garden", "capacity": 17565, "arena_latitude": 42.3662986, "arena_longitude": -71.0621622}
        self.data["BUF"] = {"city": "Buffalo, NY", "arena": "KeyBank Center", "capacity": 19070, "arena_latitude": 42.8751467, "arena_longitude": -78.8766359}
        self.data["ANA"] = {"city": "Anaheim, CA", "arena": "Honda Center", "capacity": 17174, "arena_latitude": 33.8078316, "arena_longitude": -117.876534}
        self.data["CGY"] = {"city": "Calgary, AB", "arena": "Scotiabank Saddledome", "capacity": 19289, "arena_latitude": 51.0374124, "arena_longitude": -114.0519642}
        self.data["WSH"] = {"city": "Washington, DC", "arena": "Capital One Arena", "capacity": 18573, "arena_latitude": 38.8981883, "arena_longitude": -77.0209378}
        self.data["CAR"] = {"city": "Raleigh, NC", "arena": "Lenovo Center", "capacity": 18547, "arena_latitude": 35.803398, "arena_longitude": -78.7219166}
        self.data["MIN"] = {"city": "Saint Paul, MN", "arena": "Grand Casino Arena", "capacity": 17954, "arena_latitude": 44.9447659, "arena_longitude": -93.1010851}
        self.data["VAN"] = {"city": "Vancouver, BC", "arena": "Rogers Arena", "capacity": 18910, "arena_latitude": 49.2779085, "arena_longitude": -123.1089417}
        self.data["CHI"] = {"city": "Chicago, IL", "arena": "United Center", "capacity": 19717, "arena_latitude": 41.8806831, "arena_longitude": -87.6741851}
        self.data["EDM"] = {"city": "Edmonton, AB", "arena": "Rogers Place", "capacity": 18347, "arena_latitude": 53.5467936, "arena_longitude": -113.4977946}
        self.data["NJD"] = {"city": "Newark, NJ", "arena": "Prudential Center", "capacity": 16514, "arena_latitude": 40.7334302, "arena_longitude": -74.1711482}
        self.data["CBJ"] = {"city": "Columbus, OH", "arena": "Nationwide Arena", "capacity": 18144, "arena_latitude": 39.9691873, "arena_longitude": -83.00608}
        self.data["TOR"] = {"city": "Toronto, ON", "arena": "Scotiabank Arena", "capacity": 18800, "arena_latitude": 43.6434338, "arena_longitude": -79.3790777}
        self.data["NSH"] = {"city": "Nashville, TN", "arena": "Bridgestone Arena", "capacity": 17159, "arena_latitude": 36.1589806, "arena_longitude": -86.7783819}
        self.data["ARI"] = {"city": "Phoenix, AZ", "arena": "Mullett Arena", "capacity": 4600, "arena_latitude": 33.426643, "arena_longitude": -111.9284887}
        self.data["PHX"] = {"city": "Phoenix, AZ", "arena": "Desert Diamond Arena", "capacity": 17125, "arena_latitude": 33.5319666, "arena_longitude": -112.2613181}
        self.data["LAK"] = {"city": "Los Angeles, CA", "arena": "Crypto.com Arena", "capacity": 18230, "arena_latitude": 34.0429979, "arena_longitude": -118.2671352}
        self.data["TBL"] = {"city": "Tampa, FL", "arena": "Benchmark International Arena", "capacity": 19092, "arena_latitude": 27.942704, "arena_longitude": -82.4518903}
        self.data["OTT"] = {"city": "Ottawa, ON", "arena": "Canadian Tire Centre", "capacity": 19347, "arena_latitude": 45.2969069, "arena_longitude": -75.9268973}
        self.data["ATL"] = {"city": "Atlanta, GA", "arena": "Philips Arena", "capacity": 18545, "arena_latitude": 33.7573698, "arena_longitude": -84.3963848}
        self.data["PHI"] = {"city": "Philadelphia, PA", "arena": "Xfinity Mobile Arena", "capacity": 19538, "arena_latitude": 39.9011004, "arena_longitude": -75.1720165}
        self.data["DAL"] = {"city": "Dallas, TX", "arena": "American Airlines Center", "capacity": 18532, "arena_latitude": 32.7904894, "arena_longitude": -96.810283}
        self.data["COL"] = {"city": "Denver, CO", "arena": "Ball Arena", "capacity": 17809, "arena_latitude": 39.7486838, "arena_longitude": -105.007544}
        self.data["STL"] = {"city": "St. Louis, MO", "arena": "Enterprise Center", "capacity": 18096, "arena_latitude": 38.6268005, "arena_longitude": -90.20262}
        self.data["FLA"] = {"city": "Sunrise, FL", "arena": "Amerant Bank Arena", "capacity": 19250, "arena_latitude": 26.1583702, "arena_longitude": -80.3254289}
        self.data["NYI"] = {"city": "Elmont, NY", "arena": "UBS Arena", "capacity": 17255, "arena_latitude": 40.7116942, "arena_longitude": -73.7259229}
        self.data["UTA"] = {"city": "Salt Lake City, UT", "arena": "Delta Center", "capacity": 16020, "arena_latitude": 40.7683274, "arena_longitude": -111.9010551}
        self.data["SEA"] = {"city": "Seattle, WA", "arena": "Climate Pledge Arena", "capacity": 17151, "arena_latitude": 47.6219014, "arena_longitude": -122.3539905}
        self.data["VGK"] = {"city": "Las Vegas, NV", "arena": "T-Mobile Arena", "capacity": 17367, "arena_latitude": 36.102678, "arena_longitude": -115.1782239}
        self.data["WPG"] = {"city": "Winnipeg, MB", "arena": "Canada Life Centre", "capacity": 15321, "arena_latitude": 49.8925939, "arena_longitude": -97.1437389}

    def get_all_cities(self):
        """
        Getter for cities that have hosted NHL teams from 2008 to current date
        """
        return [self.data[team]["city"] for team in self.data]
        
    def get_value(self, team, field):
        """
        Getter for spacific information about a team
        """
        return self.data[team][field]
        
    def get_city(self, team):
        """
        Getter for a city for a team
        """
        return self.data[team]["city"]
        
    def get_arena(self, team):
        """
        Getter for a city for a team
        """
        return self.data[team]["arena"]
        
    def get_arena_capacity(self, team):
        """
        Getter for a arena capacity for a team
        """
        return self.data[team]["capacity"]
        
    def get_arena_latitude(self, team):
        """
        Getter for a arena latitude for a team
        """
        return self.data[team]["arena_latitude"]
        
    def get_arena_longitude(self, team):
        """
        Getter for a arena longitude for a team
        """
        return self.data[team]["arena_longitude"]

class NHLPlayerData:
    """
    Some players do not have all their information in NHL API
    I have manually searched those players from Wikipedia and feed their information here
    """
    
    def __init__(self):
        self.data = {}
        self.data[8478905] = {"birthCity": "Lappeenranta", "birthCountry": "FIN"}
        
    def get_birth_city(self, player_id):
        """
        Getter for birth city based on player_id
        """
        return self.data[player_id]["birthCity"]
        
    def get_birth_country(self, player_id):
        """
        Getter for birth country based on player_id
        """
        return self.data[player_id]["birthCountry"]
