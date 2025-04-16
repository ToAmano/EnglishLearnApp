import pandas as pd
from backend.core.db_core import get_db_connection

# 単語検索機能
def search_word(word:str) -> pd.DataFrame:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word_id FROM words WHERE word=?", (word,))
    word_id_row = cursor.fetchone()
    if not word_id_row: # return empty df if not found
        conn.close()
        return pd.DataFrame()
    word_id = word_id_row[0]
    df = pd.read_sql_query("SELECT * FROM meanings WHERE word_id=?", conn, params=(word_id,))
    return df 

def get_examples(word_id:int) -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM examples WHERE word_id=?", conn, params=(word_id,))
    conn.close()
    return df

def is_favorited(word_id: int) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM favorites WHERE word_id = ?",
        (word_id,)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def toggle_favorite(word_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    if is_favorited(word_id):
        cur.execute(
            "DELETE FROM favorites WHERE word_id = ?",
            (word_id,)
        )
    else:
        cur.execute(
            "INSERT INTO favorites (word_id) VALUES (?)",
            (word_id,)
        )
    conn.commit()
    conn.close()

def get_derived_words(word_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # word_id から該当 word_id を取得
    cur.execute("SELECT word_id FROM words WHERE word_id = ?", (word_id,))
    word_ids = [row[0] for row in cur.fetchall()]
    if not word_ids:
        return []

    # 派生語の stem_id を取得
    cur.execute(
        "SELECT DISTINCT stem_id FROM derived_words WHERE word_id IN ({})".format(
            ",".join("?" * len(word_ids))
        ),
        word_ids
    )
    stem_ids = [row[0] for row in cur.fetchall()]
    if not stem_ids:
        return []

    # 同じ stem_id に属する他の単語（自分自身以外）を取得
    cur.execute(
        """
        SELECT DISTINCT w.word_id, w.word
        FROM words w
        JOIN derived_words d ON w.word_id = d.word_id
        WHERE d.stem_id IN ({})
        AND w.word_id != ?
        """.format(",".join("?" * len(stem_ids))),
        stem_ids + [word_id]
    )
    results = cur.fetchall()
    conn.close()
    return results

# お気に入りリスト取得
def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM words WHERE word_id IN (SELECT word_id FROM favorites)")
    favorites = cursor.fetchall()
    conn.close()
    return favorites

    
def get_synonyms(word_id:int):
    conn = get_db_connection()
    cursor = conn.cursor()

    visited = set()
    queue = [word_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        cursor.execute("""
            SELECT word_id_2 FROM synonyms WHERE word_id_1 = ?
            UNION
            SELECT word_id_1 FROM synonyms WHERE word_id_2 = ?
        """, (current, current))
        neighbors = [row[0] for row in cursor.fetchall()]
        for neighbor in neighbors:
            if neighbor not in visited:
                queue.append(neighbor)

    visited.discard(word_id)  # 元の単語は除外

    # 類義語の単語を取得
    if not visited:
        conn.close()
        return []

    cursor.execute(
        f"""
        SELECT DISTINCT w.word_id, w.word
        FROM words w
        JOIN meanings m ON w.word_id = m.word_id
        WHERE w.word_id IN ({','.join('?' * len(visited))})
        """,
        list(visited)
    )
    results = cursor.fetchall()
    conn.close()
    return results
