#!/opt/homebrew/bin/bash

# Download all the MoneyPuck data used in this project

# Usage instructions for the script
if [ "$#" -lt 1 ]; then
  echo "Usage of the script:"
  echo "$0 [-a] [-s] [-p] [-o] [-f]"
  echo "-a = Download all MoneyPuck data"
  echo "-s = Download MoneyPuck data for current regular season"
  echo "-p = Download MoneyPuck data for current playoff"
  echo "-o = Download MoneyPuck data for previous regular seasons"
  echo "-f = Download MoneyPuck data for previous playoffs"
  echo "Please activate at least one flag. Otherwise nothing will be downloaded."
  exit
fi

# Read the optional arguments
while getopts ":aspof" opt; do
case $opt in
a) CURRENTSEASON=true
   CURRENTPLAYOFF=true
   OLDSEASONS=true
   OLDPLAYOFFS=true
;;
s) CURRENTSEASON=true
;;
p) CURRENTPLAYOFF=true
;;
o) OLDSEASONS=true
;;
f) OLDPLAYOFFS=true
;;
\?) echo "Invalid option -$OPTARG" >&2
exit 1
;;
esac
done

# Nothing will be downloaded unless activated by a flag
CURRENTSEASON=${CURRENTSEASON:-false}
CURRENTPLAYOFF=${CURRENTPLAYOFF:-false}
OLDSEASONS=${OLDSEASONS:-false}
OLDPLAYOFFS=${OLDPLAYOFFS:-false}

# Define the current season
# TODAY=$(date +"%Y-%m-%d") # Adding today makes updating data more annoying
CURRENTYEAR=2025

# Download all files for the current season
# Sleep 1 second after each request to be polite and not overwhelm the servers
if $CURRENTSEASON; then
  curl -L -H "User-Agent: Mozilla/5.0" -o "skaters_${CURRENTYEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/regular/skaters.csv"
  sleep 1
  curl -L -H "User-Agent: Mozilla/5.0" -o "goalies_${CURRENTYEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/regular/goalies.csv"
  sleep 1
  curl -L -H "User-Agent: Mozilla/5.0" -o "teams_${CURRENTYEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/regular/teams.csv"
  sleep 1
fi

# Download all files for the current playoffs
# Sleep 1 second after each request to be polite and not overwhelm the servers
if $CURRENTPLAYOFF; then
  curl -L -H "User-Agent: Mozilla/5.0" -o "skaters_${CURRENTYEAR}_playoffs_${TODAY}.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/playoffs/skaters.csv"
  sleep 1
  curl -L -H "User-Agent: Mozilla/5.0" -o "goalies_${CURRENTYEAR}_playoffs_${TODAY}.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/playoffs/goalies.csv"
  sleep 1
  curl -L -H "User-Agent: Mozilla/5.0" -o "teams_${CURRENTYEAR}_playoffs_${TODAY}.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${CURRENTYEAR}/playoffs/teams.csv"
  sleep 1
fi

# Download historical regular season data until 2008
# Sleep 1 second after each request to be polite and not overwhelm the servers
if $OLDSEASONS; then
  for ((YEAR = 2008 ; YEAR < ${CURRENTYEAR} ; YEAR++)); do
    curl -L -H "User-Agent: Mozilla/5.0" -o "skaters_${YEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/regular/skaters.csv"
    sleep 1
    curl -L -H "User-Agent: Mozilla/5.0" -o "goalies_${YEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/regular/goalies.csv"
    sleep 1
    curl -L -H "User-Agent: Mozilla/5.0" -o "teams_${YEAR}_regular.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/regular/teams.csv"
    sleep 1
  done
fi

# Download historical playoff data until 2008
# Sleep 1 second after each request to be polite and not overwhelm the servers
if $OLDPLAYOFFS; then
  for ((YEAR = 2008 ; YEAR < ${CURRENTYEAR} ; YEAR++)); do
    curl -L -H "User-Agent: Mozilla/5.0" -o "skaters_${YEAR}_playoffs.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/playoffs/skaters.csv"
    sleep 1
    curl -L -H "User-Agent: Mozilla/5.0" -o "goalies_${YEAR}_playoffs.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/playoffs/goalies.csv"
    sleep 1
    curl -L -H "User-Agent: Mozilla/5.0" -o "teams_${YEAR}_playoffs.csv" "https://moneypuck.com/moneypuck/playerData/seasonSummary/${YEAR}/playoffs/teams.csv"
    sleep 1
  done
fi
