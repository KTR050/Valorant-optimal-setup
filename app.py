import streamlit as st
import pandas as pd
import itertools
import json
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# タイトル
st.title("VALORANT 最適構成計算アプリ")

# Google Sheets API 認証
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# スプレッドシートの設定
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1obAh28HKGfxdN5q7LjqTtSassDpYelBtG-oiEYp1YAY/edit#gid=1978610552"
spreadsheet = client.open_by_url(SPREADSHEET_URL)

# マップ選択
map_options = ["アイスボックス", "アセント", "サンセット", "スプリット", "パール", "ヘイブン", "ロータス"]
selected_map = st.selectbox("マップを選択してください", map_options)

# 「プログラム用」シートの A1 セルにマップ名を書き込む
try:
    agent_data_sheet = spreadsheet.worksheet("プログラム用")
    agent_data_sheet.update_acell("A1", selected_map)
except Exception as e:
    st.error(f"エージェントデータシートの更新中にエラーが発生しました: {e}")
    st.stop()

# 「プログラム用」シートからデータを読み込む
try:
    program_sheet = spreadsheet.worksheet("プログラム用")
    data = program_sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    df.set_index(df.columns[0], inplace=True)
except Exception as e:
    st.error(f"プログラム用シートの読み込み中にエラーが発生しました: {e}")
    st.stop()

player_options = df.columns.tolist()

# ロールごとのエージェント定義
role_agents = {
    'デュエリスト': ['ジェット', 'レイズ', 'フェニックス', 'レイナ', 'ヨル', 'ネオン', 'アイソ', 'ウェイレイ'],
    'イニシエーター': ['ソーヴァ', 'フェイド', 'ゲッコー', 'スカイ', 'テホ', 'KAY/O', 'ブリーチ'],
    'コントローラー': ['オーメン', 'ブリムストーン', 'ヴァイパー', 'アストラ', 'ハーバー', 'クローブ'],
    'センチネル': ['サイファー', 'キルジョイ', 'ヴァイス', 'チェンバー', 'デッドロック', 'セージ']
}
all_agents = sorted(set(itertools.chain.from_iterable(role_agents.values())))

# プレイヤーを選択（重複不可、5人）
selected_players = st.multiselect("メンバーを5人選択してください（重複不可）", player_options, max_selections=5)

if len(selected_players) != 5:
    st.warning("ちょうど5人のプレイヤーを選んでください。")
    st.stop()

# 各ロールのエージェント選択
role1_agents = st.multiselect("ロール1（デュエリスト）", role_agents['デュエリスト'], key="r1")
role2_agents = st.multiselect("ロール2（イニシエーター）", role_agents['イニシエーター'], key="r2")
role3_agents = st.multiselect("ロール3（コントローラー）", role_agents['コントローラー'], key="r3")
role4_agents = st.multiselect("ロール4（センチネル）", role_agents['センチネル'], key="r4")
role5_agents = st.multiselect("ロール5（自由枠）", all_agents, key="r5")

if st.button("最適構成を計算"):
    # 入力チェック
    if not all([role1_agents, role2_agents, role3_agents, role4_agents, role5_agents]):
        st.warning("すべてのロールに対して少なくとも1つ以上のエージェントを選択してください。")
        st.stop()

    results = []

    # ロールの組み合わせを全探索
    all_role_combinations = list(itertools.product(role1_agents, role2_agents, role3_agents, role4_agents, role5_agents))

    for roles in all_role_combinations:
        for perm in itertools.permutations(selected_players):
            used_agents = set()
            assignment = []
            total_score = 0
            valid = True

            for i in range(5):
                agent = roles[i]
                player = perm[i]

                if agent in used_agents:
                    valid = False
                    break

                used_agents.add(agent)

                try:
                    value = df.loc[agent, player]
                    if isinstance(value, pd.Series):
                        score = float(value.values[0])
                    else:
                        score = float(value)
                except Exception:
                    valid = False
                    break

                assignment.append((player, f"Role {i+1}", agent, score))
                total_score += score

            if valid:
                results.append((total_score, assignment))

    if results:
        best_result = max(results, key=lambda x: x[0])
        total_score, best_assignment = best_result

        st.success(f"最適構成（スコア合計: {total_score:.2f}）")
        df_result = pd.DataFrame(best_assignment, columns=["Player", "Role", "Agent", "Score"])
        st.dataframe(df_result)
        st.info("使用エージェント:")
        st.write(", ".join(agent for _, _, agent, _ in best_assignment))
    else:
        st.error("有効な構成が見つかりませんでした。")
