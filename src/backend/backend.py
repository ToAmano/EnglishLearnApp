from typing import Any, List, Set, Tuple

import pandas as pd

from backend.core.db_core import get_db_connection
from backend.search_count import increment_search_count


def search_meanings(word_id: int) -> pd.DataFrame:
    """単語検索"""
    increment_search_count(word_id)
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM meanings WHERE word_id=?", conn, params=(word_id,)
    )
    print(f"df = {df}")
    return df


def get_examples(word_id: int) -> pd.DataFrame:
    """Get examples from word_id"""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM examples WHERE word_id=?", conn, params=(word_id,)
    )
    conn.close()
    return df


def get_derived_words(word_id: int) -> Any:
    """Get derived words from word_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    # word_id から該当 word_id を取得
    cur.execute("SELECT word_id FROM words WHERE word_id = ?", (word_id,))
    word_ids = [row[0] for row in cur.fetchall()]
    if not word_ids:
        return []

    # 派生語の stem_id を取得
    placeholders = ",".join("?" for _ in word_ids)
    query = (
        f"SELECT DISTINCT stem_id FROM derived_words WHERE word_id IN ({placeholders})"
    )
    cur.execute(query, word_ids)
    stem_ids = [row[0] for row in cur.fetchall()]
    if not stem_ids:
        return []

    # 同じ stem_id に属する他の単語（自分自身以外）を取得
    # プレースホルダ生成
    placeholders = ",".join("?" for _ in stem_ids)

    # SQL クエリを安全に組み立て
    query = f"""
        SELECT DISTINCT w.word_id, w.word
        FROM words w
        JOIN derived_words d ON w.word_id = d.word_id
        WHERE d.stem_id IN ({placeholders})
        AND w.word_id != ?
    """

    # stem_ids + [word_id] をバインドパラメータとして渡す
    cur.execute(query, stem_ids + [word_id])
    results = cur.fetchall()
    conn.close()
    return results


def find_synonym_ids(start_id: int) -> set[int]:
    """Breadth-first search over synonym graph starting from start_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    synonym_query = """
        SELECT word_id_2 FROM synonyms WHERE word_id_1 = ?
        UNION
        SELECT word_id_1 FROM synonyms WHERE word_id_2 = ?
    """
    visited_ids: set[int] = set()
    to_visit = [start_id]

    while to_visit:
        current = to_visit.pop(0)
        if current in visited_ids:
            continue
        visited_ids.add(current)

        cursor.execute(synonym_query, (current, current))
        neighbors = [row[0] for row in cursor.fetchall()]
        to_visit.extend(n for n in neighbors if n not in visited_ids)

    visited_ids.discard(start_id)
    conn.close()
    return visited_ids


def fetch_word_info(word_ids: Set[int]) -> List[Tuple[int, str]]:
    """Retrieve word_id and word text for given word_ids."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if not word_ids:
        return []

    placeholders = ",".join("?" for _ in word_ids)
    query = f"""
        SELECT DISTINCT w.word_id, w.word
        FROM words w
        JOIN meanings m ON w.word_id = m.word_id
        WHERE w.word_id IN ({placeholders})
    """
    cursor.execute(query, list(word_ids))
    results: List[Tuple[int, str]] = cursor.fetchall()
    conn.close()
    return results


def get_synonyms(word_id: int) -> Any:
    """get synonyms of given word_id"""
    visited_ids = find_synonym_ids(word_id)
    results = fetch_word_info(visited_ids)
    return results
