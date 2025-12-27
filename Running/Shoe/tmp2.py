import datetime
import pandas as pd
from pandasql import sqldf

# sqldf(query, globals())
pysqldf = lambda query: sqldf(query, globals())

def a():
    meat = pd.read_csv('C:\\Users\\Shang\\.conda\\envs\\abc\\lib\\site-packages\\pandasql\\data\\meat.csv')
    print(pysqldf("SELECT * FROM meat LIMIT 100;"))


if __name__ == '__main__':
    now = datetime.datetime.now()
    a()
    print(datetime.datetime.now() - now)