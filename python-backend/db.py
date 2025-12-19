import mysql.connector
import datetime
import os

def storeevent(filename, content):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Kenstar1",
            database="detectrecord"
        )

        cursor = mydb.cursor()

        sql = """
        INSERT INTO events (timestamp, image_name, image_path, image_analysis)
        VALUES (%s, %s, %s, %s)
        """

        values = (
            datetime.datetime.now(),
            filename,
            os.path.join("Frames", filename),
            content
        )

        print("Saving to DB:", values)

        cursor.execute(sql, values)
        mydb.commit()

        print("Insert successful.")

    except Exception as e:
        print("DB Error:", type(e).__name__, e)

    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            mydb.close()
        except:
            pass
