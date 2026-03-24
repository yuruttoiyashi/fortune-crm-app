# Fortune CRM App

占い師・ココナラ販売者向けの顧客管理アプリです。  
Python / Streamlit / SQLite を使用して作成しました。

## 概要
このアプリでは以下を管理できます。

- 顧客情報
- 鑑定履歴
- メッセージテンプレート
- ダッシュボード表示

## 使用技術
- Python
- Streamlit
- SQLite
- Pandas

## 主な機能
### 1. 顧客登録
顧客名、相談ジャンル、流入元、ステータス、メモなどを登録できます。

### 2. 鑑定履歴登録
鑑定日、購入メニュー、相談テーマ、結果要約、アドバイス、次回提案、金額を記録できます。

### 3. メッセージテンプレ管理
お礼、納品、再購入導線などのテンプレートを保存できます。

### 4. ダッシュボード
顧客数、鑑定履歴件数、テンプレ件数、最近の登録情報を確認できます。

## 画面イメージ
### ダッシュボード
![ダッシュボード](assets/dashboard.png)

### 顧客一覧
![顧客一覧](assets/customers.png)

### 鑑定履歴一覧
![鑑定履歴一覧](assets/readings.png)

### テンプレ一覧
![テンプレ一覧](assets/templates.png)

## 起動方法
```bash
pip install -r requirements.txt
streamlit run app.py