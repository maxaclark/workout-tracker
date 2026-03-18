import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
p_word = os.getenv("DB_PWORD")

try:
    connection = psycopg2.connect(
        host="localhost",          
        port="5432",             
        database="dsci_551_project",
        user="postgres",
        password=p_word
    )
    print("Connection established successfully!")

except psycopg2.OperationalError as e:
    print(f"Unable to connect to the database: {e}")


def new_exercise():
    exercise = input('What would you like to name the new exercise? ')
    stop = False
    while stop == False:
        desc_toggle = input('Would you like to create a description? (Y/N) ')
        if desc_toggle.upper() == 'N':
            desc = None
            stop = True
        elif desc_toggle.upper() == 'Y':
            desc = input('Type a short description: ')
            stop = True
        else:
            print(f'Invalid input: {desc_toggle}')
    return [exercise, desc]


print(new_exercise())