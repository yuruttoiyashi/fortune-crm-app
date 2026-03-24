import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("coconala_customers.db")

st.set_page_config(page_title="ココナラ顧客管理アプリ", layout="wide")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            nickname TEXT,
            platform TEXT,
            birthdate TEXT,
            gender TEXT,
            concern_category TEXT,
            first_contact_date TEXT,
            last_contact_date TEXT,
            status TEXT,
            rating TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            reading_date TEXT NOT NULL,
            menu_name TEXT,
            theme TEXT,
            result_summary TEXT,
            advice TEXT,
            next_action TEXT,
            price INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS message_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL,
            category TEXT,
            subject TEXT,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid


st.title("🔮 ココナラ顧客管理アプリ")
st.caption("顧客情報・鑑定履歴・メッセージテンプレをまとめて管理")

menu = st.sidebar.radio(
    "メニュー",
    ["ダッシュボード", "顧客登録", "顧客一覧", "鑑定履歴登録", "鑑定履歴一覧", "テンプレ登録", "テンプレ一覧"],
)

# --------------------
# Dashboard
# --------------------
if menu == "ダッシュボード":
    customers_df = fetch_df("SELECT * FROM customers ORDER BY id DESC")
    readings_df = fetch_df("SELECT * FROM readings ORDER BY id DESC")
    templates_df = fetch_df("SELECT * FROM message_templates ORDER BY id DESC")

    col1, col2, col3 = st.columns(3)
    col1.metric("顧客数", len(customers_df))
    col2.metric("鑑定履歴件数", len(readings_df))
    col3.metric("テンプレ件数", len(templates_df))

    st.subheader("最近の顧客")
    if customers_df.empty:
        st.info("まだ顧客が登録されていません。")
    else:
        show_cols = [
            "id",
            "customer_name",
            "platform",
            "concern_category",
            "status",
            "last_contact_date",
        ]
        st.dataframe(customers_df[show_cols].head(10), use_container_width=True)

    st.subheader("最近の鑑定履歴")
    if readings_df.empty:
        st.info("まだ鑑定履歴がありません。")
    else:
        merged = fetch_df(
            """
            SELECT r.id, c.customer_name, r.reading_date, r.menu_name, r.theme, r.price
            FROM readings r
            INNER JOIN customers c ON r.customer_id = c.id
            ORDER BY r.reading_date DESC, r.id DESC
            LIMIT 10
            """
        )
        st.dataframe(merged, use_container_width=True)

# --------------------
# Customer Registration
# --------------------
elif menu == "顧客登録":
    st.subheader("顧客登録")
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("顧客名 *")
            nickname = st.text_input("ニックネーム")
            platform = st.selectbox("流入・プラットフォーム", ["ココナラ", "Instagram", "YouTube", "X", "その他"])
            birthdate = st.text_input("生年月日", placeholder="例: 1990-12-03")
            gender = st.selectbox("性別", ["未設定", "女性", "男性", "その他"])
        with col2:
            concern_category = st.selectbox(
                "相談ジャンル",
                ["恋愛", "復縁", "仕事", "お金", "人間関係", "家庭", "その他"],
            )
            first_contact_date = st.date_input("初回接点日")
            last_contact_date = st.date_input("最終接点日")
            status = st.selectbox("顧客ステータス", ["新規", "継続", "再購入見込み", "完了", "保留"])
            rating = st.selectbox("温度感", ["高", "中", "低"])

        note = st.text_area("メモ", height=120, placeholder="相談内容の傾向、好み、対応時の注意点など")
        submitted = st.form_submit_button("顧客を登録")

        if submitted:
            if not customer_name.strip():
                st.error("顧客名は必須です。")
            else:
                timestamp = now_str()
                execute_query(
                    """
                    INSERT INTO customers (
                        customer_name, nickname, platform, birthdate, gender,
                        concern_category, first_contact_date, last_contact_date,
                        status, rating, note, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        customer_name.strip(),
                        nickname.strip(),
                        platform,
                        birthdate.strip(),
                        gender,
                        concern_category,
                        str(first_contact_date),
                        str(last_contact_date),
                        status,
                        rating,
                        note.strip(),
                        timestamp,
                        timestamp,
                    ),
                )
                st.success("顧客を登録しました。")

# --------------------
# Customer List
# --------------------
elif menu == "顧客一覧":
    st.subheader("顧客一覧")

    keyword = st.text_input("キーワード検索", placeholder="顧客名、メモ、相談ジャンルなど")
    status_filter = st.selectbox("ステータス絞り込み", ["すべて", "新規", "継続", "再購入見込み", "完了", "保留"])

    query = "SELECT * FROM customers WHERE 1=1"
    params = []

    if keyword:
        query += " AND (customer_name LIKE ? OR nickname LIKE ? OR concern_category LIKE ? OR note LIKE ?)"
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword, like_keyword])

    if status_filter != "すべて":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY updated_at DESC, id DESC"
    customers_df = fetch_df(query, params)

    if customers_df.empty:
        st.info("条件に一致する顧客はいません。")
    else:
        st.dataframe(customers_df, use_container_width=True)

        st.markdown("### 顧客削除")
        delete_options = {
            f"{row['id']}：{row['customer_name']}": row["id"]
            for _, row in customers_df.iterrows()
        }
        selected_delete = st.selectbox("削除する顧客", ["選択してください"] + list(delete_options.keys()))
        if st.button("選択した顧客を削除"):
            if selected_delete == "選択してください":
                st.warning("削除する顧客を選んでください。")
            else:
                customer_id = delete_options[selected_delete]
                execute_query("DELETE FROM readings WHERE customer_id = ?", (customer_id,))
                execute_query("DELETE FROM customers WHERE id = ?", (customer_id,))
                st.success("顧客と関連する鑑定履歴を削除しました。")
                st.rerun()

# --------------------
# Reading Registration
# --------------------
elif menu == "鑑定履歴登録":
    st.subheader("鑑定履歴登録")
    customers_df = fetch_df("SELECT id, customer_name FROM customers ORDER BY customer_name")

    if customers_df.empty:
        st.warning("先に顧客登録をしてください。")
    else:
        customer_options = {
            f"{row['customer_name']} (ID:{row['id']})": row["id"]
            for _, row in customers_df.iterrows()
        }

        with st.form("reading_form"):
            selected_customer = st.selectbox("顧客を選択 *", list(customer_options.keys()))
            reading_date = st.date_input("鑑定日")
            menu_name = st.text_input("購入メニュー", placeholder="例: 恋愛総合鑑定")
            theme = st.text_input("相談テーマ", placeholder="例: 復縁できるか")
            result_summary = st.text_area("鑑定結果の要約", height=120)
            advice = st.text_area("伝えたアドバイス", height=120)
            next_action = st.text_input("次回提案・導線", placeholder="例: 1週間後の深掘り鑑定を提案")
            price = st.number_input("金額", min_value=0, step=500)
            submitted = st.form_submit_button("鑑定履歴を登録")

            if submitted:
                timestamp = now_str()
                customer_id = customer_options[selected_customer]
                execute_query(
                    """
                    INSERT INTO readings (
                        customer_id, reading_date, menu_name, theme,
                        result_summary, advice, next_action, price, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        customer_id,
                        str(reading_date),
                        menu_name.strip(),
                        theme.strip(),
                        result_summary.strip(),
                        advice.strip(),
                        next_action.strip(),
                        int(price),
                        timestamp,
                    ),
                )
                execute_query(
                    "UPDATE customers SET last_contact_date = ?, updated_at = ? WHERE id = ?",
                    (str(reading_date), timestamp, customer_id),
                )
                st.success("鑑定履歴を登録しました。")

# --------------------
# Reading List
# --------------------
elif menu == "鑑定履歴一覧":
    st.subheader("鑑定履歴一覧")

    readings_df = fetch_df(
        """
        SELECT r.id, c.customer_name, r.reading_date, r.menu_name, r.theme,
               r.result_summary, r.advice, r.next_action, r.price
        FROM readings r
        INNER JOIN customers c ON r.customer_id = c.id
        ORDER BY r.reading_date DESC, r.id DESC
        """
    )

    if readings_df.empty:
        st.info("まだ鑑定履歴がありません。")
    else:
        st.dataframe(readings_df, use_container_width=True)

# --------------------
# Template Registration
# --------------------
elif menu == "テンプレ登録":
    st.subheader("メッセージテンプレ登録")

    with st.form("template_form"):
        template_name = st.text_input("テンプレ名 *", placeholder="例: 初回購入お礼")
        category = st.selectbox("カテゴリ", ["お礼", "再購入導線", "フォロー", "納品", "その他"])
        subject = st.text_input("件名")
        body = st.text_area(
            "本文 *",
            height=220,
            placeholder="例: ご購入ありがとうございます。今回の鑑定では…",
        )
        submitted = st.form_submit_button("テンプレを登録")

        if submitted:
            if not template_name.strip() or not body.strip():
                st.error("テンプレ名と本文は必須です。")
            else:
                timestamp = now_str()
                execute_query(
                    """
                    INSERT INTO message_templates (
                        template_name, category, subject, body, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        template_name.strip(),
                        category,
                        subject.strip(),
                        body.strip(),
                        timestamp,
                        timestamp,
                    ),
                )
                st.success("テンプレを登録しました。")

# --------------------
# Template List
# --------------------
elif menu == "テンプレ一覧":
    st.subheader("メッセージテンプレ一覧")
    templates_df = fetch_df("SELECT * FROM message_templates ORDER BY updated_at DESC, id DESC")

    if templates_df.empty:
        st.info("まだテンプレがありません。")
    else:
        st.dataframe(templates_df, use_container_width=True)

        st.markdown("### テンプレ本文コピー用表示")
        selected_template_id = st.selectbox("テンプレを選択", templates_df["id"].tolist())
        selected_row = templates_df[templates_df["id"] == selected_template_id].iloc[0]

        st.text_input("テンプレ名", value=selected_row["template_name"], disabled=True)
        st.text_input("件名", value=selected_row["subject"], disabled=True)
        st.text_area("本文", value=selected_row["body"], height=260)

st.sidebar.markdown("---")
st.sidebar.write("使用技術: Python / Streamlit / SQLite")
st.sidebar.write("ポートフォリオ向けのシンプル構成です。")
