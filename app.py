import streamlit as st
import pandas as pd
import itertools
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# ------------------------
# Google Sheets 認証
# ------------------------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# スプレッドシートID（固定）
spreadsheet_id = "1obAh28HKGfxdN5q7LjqTtSassDpYelBtG-oiEYp1YAY"

# ------------------------
# UI - タイトルとマップ選択
# ------------------------
st.title("VALORANT 最適構成計算アプリ")

map_list = ["アイスボックス", "アセント", "サンセット", "スプリット", "パール", "ヘイブン", "ロータス"]
selected_map = st.selectbox("マップを選択してください", map_list)

# ------------------------
# A1セルにマップ名を入力
# ------------------------
try:
    sheet_agent_data = client.open_by_key(spreadsheet_id).worksheet("program")
    sheet_agent_data.update_acell("A1", selected_map)
except Exception as e:
    st.error(f"programのA1更新に失敗しました: {e}")
    st.stop()

# ------------------------
# 「プログラム用」シートからデータ取得
# ------------------------
try:
    sheet_program = client.open_by_key(spreadsheet_id).worksheet("program")
    df = get_as_dataframe(sheet_program, index_col=0).dropna(how="all")
except Exception as e:
    st.error(f"programシートの読み込みに失敗しました: {e}")
    st.stop()

# ------------------------
# プレイヤー選択
# ------------------------
player_options = df.columns.tolist()
selected_players = st.multiselect("メンバーを5人選択してください（重複不可）", player_options, max_selections=5)

if len(selected_players) != 5:
    st.warning("ちょうど5人のプレイヤーを選んでください。")
    st.stop()

# ------------------------
# ロール別エージェント定義と選択
# ------------------------
role_agents = {
    'デュエリスト': ['ジェット', 'レイズ', 'フェニックス', 'レイナ', 'ヨル', 'ネオン', 'アイソ', 'ウェイレイ'],
    'イニシエーター': ['ソーヴァ', 'フェイド', 'ゲッコー', 'スカイ', 'テホ', 'KAY/O', 'ブリーチ'],
    'コントローラー': ['オーメン', 'ブリムストーン', 'ヴァイパー', 'アストラ', 'ハーバー', 'クローブ'],
    'センチネル': ['サイファー', 'キルジョイ', 'ヴァイス', 'チェンバー', 'デッドロック', 'セージ']
}
all_agents = sorted(set(itertools.chain.from_iterable(role_agents.values())))

role1_agents = st.multiselect("ロール1（デュエリスト）", role_agents['デュエリスト'], key="r1")
role2_agents = st.multiselect("ロール2（イニシエーター）", role_agents['イニシエーター'], key="r2")
role3_agents = st.multiselect("ロール3（コントローラー）", role_agents['コントローラー'], key="r3")
role4_agents = st.multiselect("ロール4（センチネル）", role_agents['センチネル'], key="r4")
role5_agents = st.multiselect("ロール5（自由枠）", all_agents, key="r5")

# ------------------------
# 最適構成の計算
# ------------------------
if st.button("最適構成を計算"):
    if not all([role1_agents, role2_agents, role3_agents, role4_agents, role5_agents]):
        st.warning("すべてのロールに対して少なくとも1つ以上のエージェントを選択してください。")
        st.stop()

    results = []
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
