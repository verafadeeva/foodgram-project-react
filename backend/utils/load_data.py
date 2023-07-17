import sqlite3
from sqlite3 import Error


def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection


if __name__ == '__main__':
    import csv # noqa E999
    from pathlib import Path

    data_file = Path(__file__).resolve().parent.parent.parent / 'data' / 'ingredients.csv' # noqa E501
    db_path = Path(__file__).resolve().parent.parent / 'db.sqlite3'

    connection = create_connection(db_path)
    cursor = connection.cursor()

    with data_file.open('r') as file:
        reader = csv.reader(file)
        for row in reader:
            query = ("""
                    INSERT INTO
                    api_ingredient (name, measurement_unit)
                    VALUES
                    """
                     f"('{row[0]}', '{row[1]}');"
                     )

            cursor.execute(query)
        connection.commit()
        print('Data loaded')
