import sqlite3

def get_items():
    conn = sqlite3.connect("./data/master.db")
    cursor = conn.cursor()
    try:
        query = '''SELECT * FROM char_inventory'''
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            new_results = []
            for result in results:
                item = {
                    "charName": result[1],
                    "charGuild": result[2],
                    "itemName": result[3],
                    "itemCount": result[4],
                    "itemLocation": result[5]
                }
                new_results.append(item)
            return new_results
        return []
    except Exception as e:
        print(e)
        return []
    finally:
        conn.close()
