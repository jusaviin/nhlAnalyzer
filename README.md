# NHL visualizations

The project is in active state of development, and things change fast. Nothing is guaranteed to work at this stage. I have started working on this readme file, but it is out of date. I will update the readme file with proper instructions once the first working version of the project is ready.

## Setting up the repository

I recommend to run in a virtual python environment. It help to prevent messing up your global configuration or any package version discrepansies with your other project. Start with creating the virtual environment:

```
python3 -m venv nhlEnvironment
```

This needs to be activated before you start working, can can be deactivated once you are done:

```
source nhlEnvironment/bin/activate
deactivate
```

Once you are in a virtual environment, you need to install some packages used by the code. Use pip to install the following packages:

```
pip install nhl-api-py
pip install geopy
pip install jupyter
pip install jupysql
pip install country_converter --upgrade
pip install matplotlib
pip install plotly
```

## Create a database for city locations

One of the features of this repository is to map players from different NHL teams to a map. To know where to place a marker, we need to determine the longitude and latitude of each city from the player names. This is done with Nominatim package in geopy. It takes a while to build this database, but it only needs to be done once. Do it with the command:

```
python3 createCityLocationFile.py
```

The reason why this takes so long is that Nominatim uses OpenStreetMap API, which only allows one request per second. Thus the code sleeps between each city coordinate request. This is also polite thing to do in order not to overwhelm the servers with your requests. This script creates a json file with city coordinates, local names, and English names. I also read the names the cities from Nominatim since cities read from NHL API do not have accents and umlauts properly or consistently inserted. There are a few city names that I read from Nominatim where I do not like the formatting. To fix this, run the script

```
./trimCityNames.sh cityCoordinates.json trimmedCityCoordinates.json
```

This macro changes some of the city names in the json file to my preferred formatting.
