# NHL visualizations

The project is in active state of development, and things change fast. Nothing is guaranteed to work at this stage. At the point the last update of this README file, the initial creation of the SQLite database and a couple of example scripts for visualizing the data are working.

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
pip install folium
```

## Create a city location json file

One of the features of this repository is to map players from different NHL teams to a map. To know where to place a marker, we need to determine the longitude and latitude of each city from the player names. This is done with Nominatim package in geopy. It takes a while to create this json file, so I have included a version with readily available in the database containing all players from NHL API from 2008 to 2026 season summaries. The file is available at 

```
nhlPlayerHomeTownsFrom2008To2026.json
```

If you ever need to update this, or you want to create the file on your own from scratch, you can do it with the command:

```
python3 createCityLocationFile.py
```

This script either updates the defined json file with cities not already present in the file, or creates a new json file if the output file does not already exist. The reason why this takes so long is that Nominatim uses OpenStreetMap API, which only allows one request per second. Thus the code sleeps between each city coordinate request. This is also polite thing to do in order not to overwhelm the servers with your requests. This script creates a json file with city coordinates, local names, English names, state information, and country information. These names are used rather than the names directly from NHL API since the names from NHL API do not have accents and umlauts properly or consistently inserted. There are a few city names that I read from Nominatim where I do not like the formatting. To fix this, run the script

```
./trimCityNames.sh cityCoordinates.json trimmedCityCoordinates.json
```

This macro changes some of the city names in the json file to my preferred formatting.

## Download MoneyPuck csv files

MoneyPuck has some advanced statistics that cannot be obtained from NHL API. Thus, I have decided to use MoneyPuck for player statistics. You can download the all files with

```
cd moneyPuck
./moneyPuckDownloader
```

Running the command without arguments gives you the instructions how to use it. At this point you can use the `-a` flag to download all files.

## Build the database and views

The structure of the database and the views to obtain simplified access to the tables are defined in files

```
databaseSchema.sql
viewSchema.sql
```

To build the database using these specifications, run the commands

```
python3 createDatabase.py
python3 createViews.py
```

Notice that building the players table from NHL API takes about 10 minutes, since the code sleeps 1 second after every API call in order to be polite and not to overwhelm the servers. After running these commands, you have the database with summary level statistics available!

## Play with the database or try basin visualizations

If you want to just play with the database, easiest thing to do is to open the sample Jupyter notebook

```
jupyter notebook databaseTesting.ipynb
```

The first few lines here setup SQL magic for you. Then you can give any SELECT statements you like and enjoy the results.

This version also includes two sample macros for visualizations. You can map all the players in a selection of teams with

```
python3 mapTeams.py
```

Also, you can make a sample goalie performance plot with

```
python3 goalieAnalyzer.py
```

More visualizations and hopefully also machine learning model for predictions will be included in the future updates.
