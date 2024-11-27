from sqlite3 import connect, Row, OperationalError
import sqlite3
import os
import time

database = "studentinfo.db"
def get_connection():
    return connect(database, check_same_thread=False)

def get_student_by_id(idno):
    sql = "SELECT * FROM `students` WHERE `idno` = ?"
    db = get_connection()
    cursor = db.cursor()
    cursor.row_factory = Row
    cursor.execute(sql, (idno,))
    student = cursor.fetchone() 
    cursor.close()
    db.close()
    return student  

def getprocess(sql: str, retries: int = 5) -> list:
    db = get_connection()
    db.row_factory = Row
    cursor = db.cursor()

    for attempt in range(retries):
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            db.close()
            return data
        except OperationalError as e:
            if "locked" in str(e).lower() and attempt < retries - 1:
                print(f"Database is locked, retrying... (Attempt {attempt + 1})")
                time.sleep(1) 
                continue
            raise e  
        
def postprocess(sql: str) -> bool:
    db = get_connection()
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit() 
        success = cursor.rowcount > 0
    except OperationalError as e:
        db.rollback()  
        print(f"Error occurred: {e}")
        return False
    finally:
        cursor.close()
        db.close()
    return success

def gettall_records(table: str) -> list:
    sql = f"SELECT * FROM `{table}`"
    return getprocess(sql)

def fund_record(table: str, **kwargs) -> list:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    sql = f"SELECT * FROM `{table}` WHERE `{keys[0]}` = '{values[0]}'"
    return getprocess(sql)

def check_if_exists(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    sql = f"SELECT 1 FROM `{table}` WHERE `{keys[0]}` = '{values[0]}' LIMIT 1"
    data = getprocess(sql)
    return len(data) > 0

def add_record(table: str, **kwargs) -> bool:
    try:
        if check_if_exists(table, idno=kwargs['idno']):
            print(f"Student with ID {kwargs['idno']} already exists.")
            return False

        keys = list(kwargs.keys())
        values = [str(value) if value is not None else '' for value in kwargs.values()]
        fld = "`,`".join(keys)
        val = "','".join(values)
        sql = f"INSERT OR IGNORE INTO `{table}`(`{fld}`) VALUES('{val}')"
        return postprocess(sql)
    except Exception as e:
        print(f"Error in add_record: {e}")
        return False

def get_all_students() -> list:
    sql: str = "SELECT * FROM `students`"
    return getprocess(sql)

def user_login(username: str, password: str) -> bool:
    sql: str = "SELECT * FROM `USERS` WHERE `username` = ? AND `password` = ?"
    db: object = get_connection()
    cursor: object = db.cursor()
    cursor.row_factory = Row
    cursor.execute(sql, (username, password))
    data: list = cursor.fetchall()
    cursor.close()
    db.close()
    return len(data) > 0

def delete_student_record(idno: str) -> bool:
    try:
        db = get_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM `students` WHERE `idno` = ?", (idno,))
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting student: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()
        db.close()


def update_record(table, idno, lastname, firstname, course, level, image):
    query = """
        UPDATE {table}
        SET lastname = ?, firstname = ?, course = ?, level = ?, image = ?
        WHERE idno = ?
    """.format(table=table)
    
    try:
        connection = sqlite3.connect('studentinfo.db')
        cursor = connection.cursor()
        cursor.execute(query, (lastname, firstname, course, level, image, idno))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print(f"Error updating record: {str(e)}")
        return False