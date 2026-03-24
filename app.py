import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="ココナラ顧客管理アプリ", layout="wide")

# -------------------------
# シンプルCSS
# -------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Hiragino Maru Gothic Pro', 'Yu Gothic UI', sans-serif;
    color: #333;
}
.card {
    background-color: rgba(255, 255, 255, 0.94);
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
h1, h2, h3 {
    color: #4B3F72;
}
section[data-testid="stSidebar"] {
    background-color: rgba(255,255,255,0.78);
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent

# -------------------------
# DB接続
# -------------------------
db_path = BASE_DIR / "customers.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

# -------------------------
# テーブル作成
# -------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    nickname TEXT,
    category TEXT,
    memo TEXT,
    next_proposal TEXT,
    repeat_status TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    menu_name TEXT,
    theme TEXT,
    result_summary TEXT,
    advice TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT,
    template_type TEXT,
    content TEXT,
    created_at TEXT
)
""")

conn.commit()

# -------------------------
# 既存DBの列追加対策
# -------------------------
def ensure_column_exists(table_name, column_name, column_type):
    cols = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
    if column_name not in cols["name"].tolist():
        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        conn.commit()

ensure_column_exists("customers", "next_proposal", "TEXT")
ensure_column_exists("customers", "repeat_status", "TEXT")

# -------------------------
# サンプルデータ
# -------------------------
sample_customers = [
    ("", "さくら🌸", "恋愛", "元彼との復縁を希望。連絡は来ているが不安定", "1週間後に状況変化を確認する深掘り鑑定を提案", "高", "2026-03-01"),
    ("", "みほ", "仕事", "転職を考えている。今の職場に不満あり", "求人応募開始の時期に再鑑定を提案", "中", "2026-03-02"),
    ("", "ゆりな✨", "お金", "副業で収入を増やしたい。投資にも興味あり", "SNS導線を整えた後の再鑑定を提案", "高", "2026-03-03"),
    ("", "あかね", "恋愛", "片思い中。相手の気持ちを知りたい", "相手と接点が増えたタイミングで再鑑定を提案", "中", "2026-03-04"),
    ("", "リナ💫", "人間関係", "職場の人間関係でストレスを感じている", "配置転換や環境変化後の再鑑定を提案", "低", "2026-03-05"),
]

sample_readings = [
    ("さくら🌸", "復縁鑑定", "元彼の気持ち", "相手に未練はあるが慎重", "今は追いすぎず、1週間あけて連絡", "2026-03-06"),
    ("みほ", "仕事運鑑定", "転職のタイミング", "春以降に流れが動く", "焦らず情報収集を優先", "2026-03-07"),
    ("ゆりな✨", "金運鑑定", "副業の伸ばし方", "発信を増やすと追い風あり", "SNS導線を整える", "2026-03-08"),
]

sample_templates = [
    ("初回お礼メッセージ", "お礼", "この度はご依頼ありがとうございました。今回の鑑定が少しでも心の整理につながれば嬉しいです。", "2026-03-10"),
    ("再購入導線", "再提案", "状況が動いたタイミングで再度鑑定すると、より具体的に流れを読みやすくなります。", "2026-03-10"),
    ("納品メッセージ", "納品", "鑑定結果をお届けします。不安な点があれば遠慮なくご確認ください。", "2026-03-10"),
]

# -------------------------
# 共通関数
# -------------------------
def get_display_name(name, nickname):
    name = name or ""
    nickname = nickname or ""
    return name.strip() if name.strip() else nickname.strip()

def load_customers():
    return pd.read_sql("SELECT * FROM customers ORDER BY id DESC", conn)

def load_readings():
    return pd.read_sql("SELECT * FROM readings ORDER BY id DESC", conn)

def load_templates():
    return pd.read_sql("SELECT * FROM templates ORDER BY id DESC", conn)

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

# -------------------------
# UI
# -------------------------
st.title("🔮 ココナラ顧客管理アプリ")

menu = st.sidebar.radio(
    "メニュー",
    [
        "ダッシュボード",
        "顧客登録",
        "顧客一覧",
        "顧客詳細",
        "鑑定履歴登録",
        "鑑定履歴一覧",
        "テンプレ登録",
        "テンプレ一覧",
    ],
)

# -------------------------
# ダッシュボード
# -------------------------
if menu == "ダッシュボード":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("顧客サンプル追加"):
            for customer in sample_customers:
                c.execute(
                    "INSERT INTO customers (name, nickname, category, memo, next_proposal, repeat_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    customer
                )
            conn.commit()
            st.success("顧客サンプルを追加しました✨")

    with col_btn2:
        if st.button("鑑定履歴サンプル追加"):
            for reading in sample_readings:
                c.execute(
                    "INSERT INTO readings (customer_name, menu_name, theme, result_summary, advice, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    reading
                )
            conn.commit()
            st.success("鑑定履歴サンプルを追加しました✨")

    with col_btn3:
        if st.button("テンプレサンプル追加"):
            for template in sample_templates:
                c.execute(
                    "INSERT INTO templates (template_name, template_type, content, created_at) VALUES (?, ?, ?, ?)",
                    template
                )
            conn.commit()
            st.success("テンプレサンプルを追加しました✨")

    customers_df = load_customers()
    readings_df = load_readings()
    templates_df = load_templates()

    col1, col2, col3 = st.columns(3)
    col1.metric("顧客数", len(customers_df))
    col2.metric("鑑定履歴件数", len(readings_df))
    col3.metric("テンプレ件数", len(templates_df))

    st.subheader("分析")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.markdown("**ジャンル別顧客数**")
        if customers_df.empty:
            st.info("データなし")
        else:
            tmp = customers_df.copy()
            tmp["category"] = tmp["category"].fillna("未設定")
            cat_counts = tmp["category"].value_counts().reset_index()
            cat_counts.columns = ["ジャンル", "件数"]
            st.dataframe(cat_counts, use_container_width=True)

    with col_b:
        st.markdown("**相談テーマ件数**")
        if readings_df.empty:
            st.info("データなし")
        else:
            tmp = readings_df.copy()
            tmp["theme"] = tmp["theme"].fillna("未設定")
            theme_counts = tmp["theme"].value_counts().reset_index()
            theme_counts.columns = ["テーマ", "件数"]
            st.dataframe(theme_counts, use_container_width=True)

    with col_c:
        st.markdown("**テンプレ種別件数**")
        if templates_df.empty:
            st.info("データなし")
        else:
            tmp = templates_df.copy()
            tmp["template_type"] = tmp["template_type"].fillna("未設定")
            type_counts = tmp["template_type"].value_counts().reset_index()
            type_counts.columns = ["種別", "件数"]
            st.dataframe(type_counts, use_container_width=True)

    with col_d:
        st.markdown("**リピート見込み件数**")
        if customers_df.empty:
            st.info("データなし")
        else:
            tmp = customers_df.copy()
            tmp["repeat_status"] = tmp["repeat_status"].fillna("未設定")
            repeat_counts = tmp["repeat_status"].value_counts().reset_index()
            repeat_counts.columns = ["見込み", "件数"]
            st.dataframe(repeat_counts, use_container_width=True)

    st.subheader("最近の顧客")
    if customers_df.empty:
        st.info("まだ顧客が登録されていません。")
    else:
        display_df = customers_df.copy()
        display_df["表示名"] = display_df.apply(
            lambda row: get_display_name(row["name"], row["nickname"]),
            axis=1
        )
        st.dataframe(
            display_df[["id", "表示名", "category", "repeat_status", "created_at"]].head(5),
            use_container_width=True
        )

    st.subheader("最近の鑑定履歴")
    if readings_df.empty:
        st.info("まだ鑑定履歴がありません。")
    else:
        st.dataframe(readings_df.head(5), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 顧客登録
# -------------------------
elif menu == "顧客登録":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("顧客名")
    nickname = st.text_input("ニックネーム")
    category = st.selectbox("ジャンル", ["恋愛", "仕事", "お金", "人間関係", "その他"])
    repeat_status = st.selectbox("リピート見込み", ["高", "中", "低", "未定"])
    memo = st.text_area("メモ")
    next_proposal = st.text_area("次回提案メモ")

    if st.button("顧客を登録"):
        if not name.strip() and not nickname.strip():
            st.error("顧客名またはニックネームを入力してください。")
        else:
            c.execute(
                "INSERT INTO customers (name, nickname, category, memo, next_proposal, repeat_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    name.strip(),
                    nickname.strip(),
                    category,
                    memo,
                    next_proposal,
                    repeat_status,
                    datetime.now().strftime("%Y-%m-%d")
                )
            )
            conn.commit()
            st.success("登録しました✨")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 顧客一覧
# -------------------------
elif menu == "顧客一覧":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    customers_df = load_customers()

    keyword = st.text_input("顧客検索", placeholder="名前・ニックネーム・メモ・次回提案で検索")
    category_filter = st.selectbox("ジャンル絞り込み", ["すべて", "恋愛", "仕事", "お金", "人間関係", "その他"])
    repeat_filter = st.selectbox("リピート見込み絞り込み", ["すべて", "高", "中", "低", "未定"])

    if customers_df.empty:
        st.info("まだ顧客データがありません。")
    else:
        customers_df["表示名"] = customers_df.apply(
            lambda row: get_display_name(row["name"], row["nickname"]),
            axis=1
        )

        filtered_df = customers_df.copy()

        if keyword.strip():
            kw = keyword.strip()
            filtered_df = filtered_df[
                filtered_df["表示名"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["memo"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["next_proposal"].astype(str).str.contains(kw, case=False, na=False)
            ]

        if category_filter != "すべて":
            filtered_df = filtered_df[filtered_df["category"] == category_filter]

        if repeat_filter != "すべて":
            filtered_df = filtered_df[filtered_df["repeat_status"] == repeat_filter]

        export_df = filtered_df[["id", "表示名", "category", "repeat_status", "memo", "next_proposal", "created_at"]].copy()

        st.download_button(
            label="顧客一覧をCSVダウンロード",
            data=to_csv_bytes(export_df),
            file_name="customers.csv",
            mime="text/csv"
        )

        st.dataframe(export_df, use_container_width=True)

        st.subheader("顧客編集・削除")
        customer_options = filtered_df["表示名"].tolist()
        if customer_options:
            selected_customer_name = st.selectbox("編集する顧客を選択", customer_options)
            selected_row = filtered_df[filtered_df["表示名"] == selected_customer_name].iloc[0]

            with st.form("edit_customer_form"):
                edit_name = st.text_input("顧客名", value=selected_row["name"] if pd.notna(selected_row["name"]) else "")
                edit_nickname = st.text_input("ニックネーム", value=selected_row["nickname"] if pd.notna(selected_row["nickname"]) else "")
                edit_category = st.selectbox(
                    "ジャンル",
                    ["恋愛", "仕事", "お金", "人間関係", "その他"],
                    index=["恋愛", "仕事", "お金", "人間関係", "その他"].index(selected_row["category"]) if selected_row["category"] in ["恋愛", "仕事", "お金", "人間関係", "その他"] else 0
                )
                repeat_options = ["高", "中", "低", "未定"]
                current_repeat = selected_row["repeat_status"] if pd.notna(selected_row["repeat_status"]) else "未定"
                edit_repeat = st.selectbox(
                    "リピート見込み",
                    repeat_options,
                    index=repeat_options.index(current_repeat) if current_repeat in repeat_options else 3
                )
                edit_memo = st.text_area("メモ", value=selected_row["memo"] if pd.notna(selected_row["memo"]) else "")
                edit_next = st.text_area("次回提案メモ", value=selected_row["next_proposal"] if pd.notna(selected_row["next_proposal"]) else "")

                submitted = st.form_submit_button("顧客情報を更新")
                if submitted:
                    if not edit_name.strip() and not edit_nickname.strip():
                        st.error("顧客名またはニックネームを入力してください。")
                    else:
                        c.execute(
                            """
                            UPDATE customers
                            SET name = ?, nickname = ?, category = ?, memo = ?, next_proposal = ?, repeat_status = ?
                            WHERE id = ?
                            """,
                            (
                                edit_name.strip(),
                                edit_nickname.strip(),
                                edit_category,
                                edit_memo,
                                edit_next,
                                edit_repeat,
                                int(selected_row["id"])
                            )
                        )
                        conn.commit()
                        st.success("顧客情報を更新しました✨")

            if st.button("選択した顧客を削除"):
                target_name = get_display_name(
                    selected_row["name"] if pd.notna(selected_row["name"]) else "",
                    selected_row["nickname"] if pd.notna(selected_row["nickname"]) else ""
                )
                c.execute("DELETE FROM customers WHERE id = ?", (int(selected_row["id"]),))
                c.execute("DELETE FROM readings WHERE customer_name = ?", (target_name,))
                conn.commit()
                st.success("顧客と関連する鑑定履歴を削除しました。")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 顧客詳細
# -------------------------
elif menu == "顧客詳細":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    customers_df = load_customers()

    if customers_df.empty:
        st.info("まだ顧客データがありません。")
    else:
        customers_df["表示名"] = customers_df.apply(
            lambda row: get_display_name(row["name"], row["nickname"]),
            axis=1
        )

        customer_options = customers_df["表示名"].tolist()
        selected_customer = st.selectbox("顧客を選択", customer_options)

        detail_df = customers_df[customers_df["表示名"] == selected_customer].head(1)

        if not detail_df.empty:
            row = detail_df.iloc[0]

            st.subheader("基本情報")
            col1, col2 = st.columns(2)
            col1.write(f"**表示名:** {row['表示名']}")
            col1.write(f"**ジャンル:** {row['category']}")
            col1.write(f"**リピート見込み:** {row['repeat_status'] if pd.notna(row['repeat_status']) else '未定'}")
            col2.write(f"**登録日:** {row['created_at']}")
            col2.write(f"**顧客ID:** {row['id']}")

            st.write("**メモ**")
            st.write(row["memo"] if pd.notna(row["memo"]) and str(row["memo"]).strip() else "メモなし")

            st.write("**次回提案メモ**")
            st.write(row["next_proposal"] if pd.notna(row["next_proposal"]) and str(row["next_proposal"]).strip() else "未設定")

            st.subheader("この顧客の鑑定履歴")
            readings_df = load_readings()
            related_readings = readings_df[readings_df["customer_name"] == selected_customer]

            if related_readings.empty:
                st.info("この顧客の鑑定履歴はまだありません。")
            else:
                st.download_button(
                    label="この顧客の鑑定履歴をCSVダウンロード",
                    data=to_csv_bytes(related_readings),
                    file_name=f"{selected_customer}_readings.csv",
                    mime="text/csv"
                )
                st.dataframe(related_readings, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 鑑定履歴登録
# -------------------------
elif menu == "鑑定履歴登録":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    customer_options_df = load_customers()
    customer_names = []

    if not customer_options_df.empty:
        customer_options_df["表示名"] = customer_options_df.apply(
            lambda row: get_display_name(row["name"], row["nickname"]),
            axis=1
        )
        customer_names = customer_options_df["表示名"].tolist()

    customer_name = st.selectbox("顧客", [""] + customer_names)
    menu_name = st.text_input("鑑定メニュー名")
    theme = st.text_input("相談テーマ")
    result_summary = st.text_area("鑑定結果の要約")
    advice = st.text_area("アドバイス")

    if st.button("鑑定履歴を登録"):
        if not customer_name:
            st.error("顧客を選択してください。")
        else:
            c.execute(
                "INSERT INTO readings (customer_name, menu_name, theme, result_summary, advice, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    customer_name,
                    menu_name,
                    theme,
                    result_summary,
                    advice,
                    datetime.now().strftime("%Y-%m-%d")
                )
            )
            conn.commit()
            st.success("鑑定履歴を登録しました✨")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 鑑定履歴一覧
# -------------------------
elif menu == "鑑定履歴一覧":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    readings_df = load_readings()

    keyword = st.text_input("鑑定履歴検索", placeholder="顧客名・メニュー名・テーマで検索")

    if readings_df.empty:
        st.info("まだ鑑定履歴がありません。")
    else:
        filtered_df = readings_df.copy()

        if keyword.strip():
            kw = keyword.strip()
            filtered_df = filtered_df[
                filtered_df["customer_name"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["menu_name"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["theme"].astype(str).str.contains(kw, case=False, na=False)
            ]

        st.download_button(
            label="鑑定履歴をCSVダウンロード",
            data=to_csv_bytes(filtered_df),
            file_name="readings.csv",
            mime="text/csv"
        )

        st.dataframe(filtered_df, use_container_width=True)

        st.subheader("鑑定履歴編集・削除")
        reading_options = [
            f"{row['id']} | {row['customer_name']} | {row['theme']}"
            for _, row in filtered_df.iterrows()
        ]

        if reading_options:
            selected_label = st.selectbox("編集する鑑定履歴を選択", reading_options)
            selected_id = int(selected_label.split("|")[0].strip())
            selected_row = filtered_df[filtered_df["id"] == selected_id].iloc[0]

            with st.form("edit_reading_form"):
                edit_customer_name = st.text_input("顧客名", value=selected_row["customer_name"])
                edit_menu_name = st.text_input("鑑定メニュー名", value=selected_row["menu_name"])
                edit_theme = st.text_input("相談テーマ", value=selected_row["theme"])
                edit_result = st.text_area("鑑定結果の要約", value=selected_row["result_summary"])
                edit_advice = st.text_area("アドバイス", value=selected_row["advice"])

                submitted = st.form_submit_button("鑑定履歴を更新")
                if submitted:
                    c.execute(
                        """
                        UPDATE readings
                        SET customer_name = ?, menu_name = ?, theme = ?, result_summary = ?, advice = ?
                        WHERE id = ?
                        """,
                        (
                            edit_customer_name,
                            edit_menu_name,
                            edit_theme,
                            edit_result,
                            edit_advice,
                            selected_id
                        )
                    )
                    conn.commit()
                    st.success("鑑定履歴を更新しました✨")

            if st.button("選択した鑑定履歴を削除"):
                c.execute("DELETE FROM readings WHERE id = ?", (selected_id,))
                conn.commit()
                st.success("鑑定履歴を削除しました。")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# テンプレ登録
# -------------------------
elif menu == "テンプレ登録":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    template_name = st.text_input("テンプレ名")
    template_type = st.selectbox("テンプレ種別", ["お礼", "納品", "再提案", "フォロー", "その他"])
    content = st.text_area("テンプレ内容", height=220)

    if st.button("テンプレを登録"):
        if not template_name.strip() or not content.strip():
            st.error("テンプレ名と内容を入力してください。")
        else:
            c.execute(
                "INSERT INTO templates (template_name, template_type, content, created_at) VALUES (?, ?, ?, ?)",
                (
                    template_name.strip(),
                    template_type,
                    content.strip(),
                    datetime.now().strftime("%Y-%m-%d")
                )
            )
            conn.commit()
            st.success("テンプレを登録しました✨")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# テンプレ一覧
# -------------------------
elif menu == "テンプレ一覧":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    templates_df = load_templates()

    keyword = st.text_input("テンプレ検索", placeholder="テンプレ名・内容で検索")

    if templates_df.empty:
        st.info("まだテンプレがありません。")
    else:
        filtered_df = templates_df.copy()

        if keyword.strip():
            kw = keyword.strip()
            filtered_df = filtered_df[
                filtered_df["template_name"].astype(str).str.contains(kw, case=False, na=False) |
                filtered_df["content"].astype(str).str.contains(kw, case=False, na=False)
            ]

        export_df = filtered_df[["id", "template_name", "template_type", "content", "created_at"]].copy()

        st.download_button(
            label="テンプレ一覧をCSVダウンロード",
            data=to_csv_bytes(export_df),
            file_name="templates.csv",
            mime="text/csv"
        )

        st.dataframe(
            filtered_df[["id", "template_name", "template_type", "created_at"]],
            use_container_width=True
        )

        st.subheader("テンプレ本文コピペ用")
        template_options = filtered_df["template_name"].tolist()
        selected_template = st.selectbox("表示するテンプレを選択", template_options)

        selected_row = filtered_df[filtered_df["template_name"] == selected_template].iloc[0]

        customer_name_for_replace = st.text_input("差し込み用の顧客名（任意）", placeholder="例：さくら様")

        preview_text = selected_row["content"]
        if customer_name_for_replace.strip():
            preview_text = f"{customer_name_for_replace.strip()}\n\n{preview_text}"

        st.text_area("このままコピーして使えます", value=preview_text, height=220)

        st.subheader("テンプレ編集・削除")
        template_edit_options = [
            f"{row['id']} | {row['template_name']}"
            for _, row in filtered_df.iterrows()
        ]

        if template_edit_options:
            selected_label = st.selectbox("編集するテンプレを選択", template_edit_options)
            selected_id = int(selected_label.split("|")[0].strip())
            selected_row = filtered_df[filtered_df["id"] == selected_id].iloc[0]

            with st.form("edit_template_form"):
                edit_template_name = st.text_input("テンプレ名", value=selected_row["template_name"])
                type_options = ["お礼", "納品", "再提案", "フォロー", "その他"]
                current_type = selected_row["template_type"] if pd.notna(selected_row["template_type"]) else "その他"
                edit_template_type = st.selectbox(
                    "テンプレ種別",
                    type_options,
                    index=type_options.index(current_type) if current_type in type_options else 4
                )
                edit_content = st.text_area("テンプレ内容", value=selected_row["content"], height=220)

                submitted = st.form_submit_button("テンプレを更新")
                if submitted:
                    if not edit_template_name.strip() or not edit_content.strip():
                        st.error("テンプレ名と内容を入力してください。")
                    else:
                        c.execute(
                            """
                            UPDATE templates
                            SET template_name = ?, template_type = ?, content = ?
                            WHERE id = ?
                            """,
                            (
                                edit_template_name.strip(),
                                edit_template_type,
                                edit_content.strip(),
                                selected_id
                            )
                        )
                        conn.commit()
                        st.success("テンプレを更新しました✨")

            if st.button("選択したテンプレを削除"):
                c.execute("DELETE FROM templates WHERE id = ?", (selected_id,))
                conn.commit()
                st.success("テンプレを削除しました。")

    st.markdown('</div>', unsafe_allow_html=True)