import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        con = psycopg2.connect(dbname='postgres', user='postgres', host='localhost', password='postgres123')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("CREATE DATABASE halleyx_db")
        cur.close()
        con.close()
        print("Database 'halleyx_db' created successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_database()
