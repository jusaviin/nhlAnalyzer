# Create a SQLite database for the NHL and fill in some information
# Notice that all previous tables from the database are wiped using this script
# TODO: There should be some options on which information to fill

# Required imports
import sqlite3
     
def main():
    """
    Main function. Creates the defined views for the database.
    """

    # Connect to the SQLite3 database
    databaseName = "nhlDatabase.db"
    connection = sqlite3.connect(databaseName)
    cursor = connection.cursor()
    print("Connected to database {}".format(databaseName))
    
    # Initialize the views
    initializationFile = "viewSchema.sql"
    with open(initializationFile, 'r') as sql_file:
        sql_script = sql_file.read()

    # Use a cursor for updating information and run the initialization script
    cursor.executescript(sql_script)
    print("Initialized the views from file {}".format(initializationFile))
    
    # Close the connection
    connection.close()

# Follow good coding practices
if __name__ == "__main__":
    main()
