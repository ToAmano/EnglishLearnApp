import sqlite3

def init_user_db():
    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()

    # favorites テーブル（word 主キー）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            word TEXT PRIMARY KEY
        );
    """)

    # vocab_status テーブル（word 主キー）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_status (
            word TEXT PRIMARY KEY,
            status TEXT CHECK(status IN ('unknown', 'passive', 'active'))
        );
    """)

    conn.commit()
    conn.close()
    print("✅ favorites / vocab_status テーブル（wordベース）を作成しました。")
    
    
if __name__ == "__main__":
    init_user_db()
    print("データベースを初期化しました。")