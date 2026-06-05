from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://usuario:password@localhost/db"

engine = create_engine(DATABASE_URL)

def execute_query(query):
    with engine.connect() as conn:
        result = conn.execute(query)

        return [row for row in result]