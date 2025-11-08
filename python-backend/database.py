import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Kenstar1",
  database="detectrecord"
)

mycursor = mydb.cursor()

#mycursor.execute("CREATE DATABASE detectrecord")

mycursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    timestamp TEXT,
    image_name varchar(255),
    image_path TEXT,
    image_analysis TEXT
)
''')

mycursor.execute('''
INSERT INTO events(id, timestamp, image_name, image_path, image_analysis)
VALUES(1,{dt},{filename},Frames/+{filename}, {content});
    
''')