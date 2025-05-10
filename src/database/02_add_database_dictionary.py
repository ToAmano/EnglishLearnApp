import sqlite3
import pandas as pd

def insert_words_from_csv(csv_path: str, db_path: str = "words.db"):
    conflicts = []
    # CSV読み込み
    df = pd.read_csv(csv_path,dtype={'word_id': int, 'word': str, 'source': str},na_filter=False)

    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # データ挿入
    for _, row in df.iterrows():
        # print(f"word_id: {row['word_id']}, word: {row['word']}")
        try:
            cursor.execute(
                "INSERT INTO words (word_id, word, source) VALUES (?, ?, ?);",
                (int(row["word_id"]), row["word"], row["source"])
            )
        except sqlite3.IntegrityError as e:
            print(f"❌ 挿入失敗: word={row['word']}, 理由: {str(e)}")
            conflicts.append(row)
    print(f"⚠️ {len(conflicts)} 件の重複がありました。:: {conflicts}")
        
    # コミット・クローズ
    conn.commit()
    conn.close()
    print(f"✅ {csv_path}の単語データを登録しました！")

def insert_meanings_from_csv(csv_path: str, db_path: str = "words.db"):
    df = pd.read_csv(csv_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO meanings (word_id, meaning, part_of_speech, category)
            VALUES (?, ?, ?, ?)
        ''', (
            int(row['word_id']),
            row['meaning'],
            row.get('part_of_speech', None),
            row.get('category', None)
        ))
        
def insert_explanations_from_csv(csv_path: str, db_path: str = "words.db"):
    # CSV読み込み
    df = pd.read_csv(csv_path)

    # データベース接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # データ挿入
    for _, row in df.iterrows():
        # print(f"word_id: {row['word_id']}, word: {row['explanation']}")
        cursor.execute(
            "INSERT OR IGNORE INTO word_explanations (word_id, explanation) VALUES (?, ?);",
            (int(row["word_id"]), row["explanation"])
        )
    # コミット・クローズ
    conn.commit()
    conn.close()
    print(f"✅ {csv_path}の説明データを登録しました！")


# 使用例
if __name__ == "__main__":
    # CSVファイルのパスを指定
    WORD_PATH = "../data/word_data/"
    EXPLANATION_PATH = "../data/explanation_data/"
    # add svl 1-12
    for i in range(1,13):
        insert_words_from_csv(WORD_PATH+f"lv{i}.csv")
    for i in range(1,13):    
        insert_explanations_from_csv(EXPLANATION_PATH+f"lv{i}_explanation.csv")

    # add eiken 
    insert_words_from_csv(WORD_PATH+f"eiken_added.csv")
    insert_explanations_from_csv(EXPLANATION_PATH+f"eiken_explanation.csv")
