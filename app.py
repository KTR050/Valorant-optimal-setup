import streamlit as st
import pandas as pd
import itertools
import os

st.title("VALORANT 最適構成計算アプリ")

# マップ選択
map_file_dict = {
    "アイスボックス": "アイスボックス - シート1.csv",
    "アセント": "アセント - シート1.csv",
    "サンセット": "サンセット - シート1.csv",
    "スプリット": "スプリット - シート1.csv",
    "パール": "パール - シート1.csv",
    "ヘイブン": "ヘイブン - シート1.csv",
    "ロータス": "ロータス - シート1.csv"
}

selected_map = st.selectbox("マップを選択してください", list(map_file_dict.keys()))

# CSVファイルパスの構築
csv_file = os.path.join("マップ別データ", map_file_dict[selected_map])

# CSV読み込み
try:
    df = pd.read_csv(csv_file, index_col=0)
except FileNotFoundError:
    st.error(f"{csv_file} が見つかりません。'マップ別データ' フォルダが存在し、CSVがその中にあることを確認してください。")
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
        for perm in itertools.permutations(selected_players):  # 修正：selected_playersを使用
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
