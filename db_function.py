import sqlite3


def add_user(user_id):
    conn = sqlite3.connect("db/user.db", timeout=10)
    c = conn.cursor()
    try:
        sql = "insert into users (user_id) values (?)"
        c.execute(sql, (user_id,))
    except sqlite3.DatabaseError as error:
        print("Error:", error)

    conn.commit()
    c.close()
    if conn:
        conn.close()


