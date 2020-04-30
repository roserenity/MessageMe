import os, csv, psycopg2, string

DATABASE_URL = os.environ['DATABASE_URL']

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

with open('books.csv') as csv_file:
    contents = csv_file.readline()
    line_count = 0
    connect = None
    while contents:
        try:
            #replacing commas and double quotations
            contents=contents.replace('"', '//').replace(", ", "/ ").replace("'", '/')
            row = contents.split(',')
            print(row[0]+'-'+row[1]+'-'+row[2]+'-'+row[3])
            sql="INSERT INTO booktbl VALUES ('"+str(line_count)+"','"+row[0]+"','"+row[1]+"', '"+row[2]+"', "+row[3]+" )"
            contents = csv_file.readline()

            connect = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connect.cursor()
            cursor.execute(sql)
            connect.commit()
            cursor.close()
            connect.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if connect is not None:
                connect.close()
        line_count +=1
