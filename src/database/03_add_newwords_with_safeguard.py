
import pandas as pd
import sqlite3

# ==== 設定 ====
DB_PATH = "words.db"  # SQLite のファイルパス
NEW_WORDS_CSV = "../data/word_data/eiken.csv"  # 追加したい単語が入ったCSV（列名: word, meaning, example）
NEW_WORDS_CSV = "../data/word_data/eiken_derujun.csv"  # 追加したい単語が入ったCSV（列名: word, meaning, example）

# ==== ステップ1: 新しい単語をCSVから読み込み ====
new_words_df = pd.read_csv(NEW_WORDS_CSV)

# 必要なカラムだけ抽出（他のカラムがあっても無視されるように）
new_words_df = new_words_df[["word","source"]]
new_words_df["word"] = new_words_df["word"].str.strip().str.lower()
print(new_words_df[new_words_df.duplicated(subset="word", keep=False)])


# ==== ステップ2: DB から既存の単語を取得 ====
conn = sqlite3.connect(DB_PATH)
existing_words_df = pd.read_sql_query("SELECT word FROM words", conn)
existing_words_df["word"] = existing_words_df["word"].str.strip().str.lower()

existing_words = existing_words_df["word"] # set(existing_words_df["word"])
print(f"DB に既に {len(existing_words)} 単語が登録されています。")


# ==== ステップ3: 重複しない単語だけフィルタ ====
unique_new_words = new_words_df[~new_words_df["word"].isin(existing_words)]

print(unique_new_words)
unique_new_words.to_csv("unique_new_words.csv", index=False)

# ==== ステップ4: データベースに挿入 ====
if not unique_new_words.empty:
    unique_new_words.to_sql("words", conn, if_exists="append", index=False)
    print(f"✅ {len(unique_new_words)} 単語を追加しました。")
else:
    print("⚠️ 追加すべき新しい単語はありませんでした。")

# 5. 新たに挿入された単語と割り当てられた word_id を取得
#    - word がユニークであることを前提
placeholders = ",".join(["?"] * len(unique_new_words))
query = f"SELECT word_id, word FROM words WHERE word IN ({placeholders})"
added_rows = pd.read_sql_query(query, conn, params=unique_new_words["word"].tolist())

# 6. CSV に保存
added_rows.sort_values("word_id").to_csv("added_words_with_ids.csv", index=False, encoding="utf-8")
print("追加された単語とword_idをCSVに書き出しました。")

# ==== クローズ ====
conn.close()

