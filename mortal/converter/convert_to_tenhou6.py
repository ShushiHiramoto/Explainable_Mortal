#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import argparse

# ==========================================================
# 牌変換テーブル
# ==========================================================

TITLE_TO_ID = {
    # man
    "1m":11,"2m":12,"3m":13,"4m":14,"5m":15,
    "6m":16,"7m":17,"8m":18,"9m":19,

    # pin
    "1p":21,"2p":22,"3p":23,"4p":24,"5p":25,
    "6p":26,"7p":27,"8p":28,"9p":29,

    # sou
    "1s":31,"2s":32,"3s":33,"4s":34,"5s":35,
    "6s":36,"7s":37,"8s":38,"9s":39,

    # 字牌
    "E":41,
    "S":42,
    "W":43,
    "N":44,
    "P":45,
    "F":46,
    "C":47,

    # 赤
    "5mr":51,
    "5pr":52,
    "5sr":53,
}


PLAYER_OFFSET = {
    0:4,
    1:7,
    2:10,
    3:13,
}

# ==========================================================
# 牌名→天鳳ID
# ==========================================================

def title_to_id(tile):

    if tile is None:
        return 0

    if tile not in TITLE_TO_ID:
        raise ValueError(f"Unknown tile : {tile}")

    return TITLE_TO_ID[tile]

# ==========================================================
# Mortalログ読込
# ==========================================================

def load_mortal_log(path):
    events = []

    with open(path, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            events.append(json.loads(line))

    return events

def create_round(event):

    if event["bakaze"] == "E":
        kyoku = event["kyoku"] - 1
    elif event["bakaze"] == "S":
        kyoku = event["kyoku"] + 3
    elif event["bakaze"] == "W":
        kyoku = event["kyoku"] + 7
    elif event["bakaze"] == "N":
        kyoku = event["kyoku"] + 11
    else:
        raise ValueError(
            f"unsupported bakaze: {event['bakaze']}"
        )
    

    
    kyoku_info = [
        kyoku,
        event["honba"],
        event.get("kyotaku",0),
    ]

    scores = event.get(
        "scores",
        [25000,25000,25000,25000]
    )

    dora = [
        title_to_id(event["dora_marker"])
    ]

    ura = []

    round_data = [
        kyoku_info,
        scores,
        dora,
        ura,
    ]

    # プレイヤー0
    round_data.append([
        title_to_id(x)
        for x in event["tehais"][0]
    ])
    round_data.append([])
    round_data.append([])

    # プレイヤー1
    round_data.append([
        title_to_id(x)
        for x in event["tehais"][1]
    ])
    round_data.append([])
    round_data.append([])

    # プレイヤー2
    round_data.append([
        title_to_id(x)
        for x in event["tehais"][2]
    ])
    round_data.append([])
    round_data.append([])

    # プレイヤー3
    round_data.append([
        title_to_id(x)
        for x in event["tehais"][3]
    ])
    round_data.append([])
    round_data.append([])

    return round_data

# ==========================================================
# ツモ追加
# ==========================================================

def add_tsumo(round_data, actor, tile):

    idx = PLAYER_OFFSET[actor]

    round_data[idx+1].append(
        title_to_id(tile)
    )

# ==========================================================
# 打牌追加
# ==========================================================

def add_dahai(round_data, actor, tile, tsumogiri,reach):

    idx = PLAYER_OFFSET[actor]


    if reach:

        round_data[idx+2].append(
            f"r{title_to_id(tile)}"
        )

    elif tsumogiri:

        round_data[idx+2].append(60)

    else:

        round_data[idx+2].append(
            title_to_id(tile)
        )

def handle_chi(round_data, event):

    idx = PLAYER_OFFSET[event["actor"]]

    called = title_to_id(event["pai"])

    consumed = [
        title_to_id(x)
        for x in event["consumed"]
    ]

    # 仮実装
    code = f"c{called}{consumed[0]}{consumed[1]}"

    round_data[idx + 1].append(code)

# ==========================================================
# ポン
# ==========================================================

def handle_pon(round_data, event, last_discard, pon_history):

    idx = PLAYER_OFFSET[event["actor"]]

    called = title_to_id(event["pai"])

    consumed = [
        title_to_id(x)
        for x in event["consumed"]
    ]

    discard = title_to_id(
        last_discard[event["target"]]
    )

    rel_target = (event["actor"] - event["target"]) % 4
    #print(rel_target)
    if rel_target == 1:#下家
        code = (
            f"p"
            f"{discard}"
            f"{consumed[0]}"
            f"{consumed[1]}"
        )
    
    elif rel_target == 2:#対面
        code = (
            f"{consumed[0]}"
            f"p"
            f"{discard}"
            f"{consumed[1]}"
        )
    elif rel_target == 3:#上家
        code = (
            f"{consumed[0]}"
            f"{consumed[1]}"
            f"p"
            f"{discard}"
        )

    else:  
        raise ValueError(
            f"invalid pon direction actor={event['actor']} target={event['target']}"
        )


    insert_index = len(round_data[idx + 1])
    round_data[idx + 1].append(code)

    pon_history[(event["actor"], normalize(event["pai"]))] = {
        "index": insert_index,
        "code": code,
        "rel_target": rel_target,
        "discard": discard,
        "consumed": consumed,
    }

#===========================================================
#ポン時の情報保存(カン)
#===========================================================
def normalize(tile):
    if tile == "5mr":
        return "5m"
    if tile == "5pr":
        return "5p"
    if tile == "5sr":
        return "5s"
    return tile

# ==========================================================
# 暗槓
# ==========================================================

def handle_ankan(round_data, event):

    idx = PLAYER_OFFSET[event["actor"]]

    consumed = [
        title_to_id(x)
        for x in event["consumed"]
    ]

    code = (
        f"{consumed[0]}"
        f"{consumed[1]}"
        f"{consumed[2]}"
        f"a"
        f"{consumed[3]}"
    )

    round_data[idx + 2].append(code)

# ==========================================================
# 加槓
# ==========================================================

def handle_kakan(round_data, event, pon_history):

    idx = PLAYER_OFFSET[event["actor"]]
    #called = title_to_id(event["pai"])

    info = pon_history[
        (event["actor"], event["pai"])
    ]

    rel_target = info["rel_target"]
    #discard = info["discard"]

    consumed = [
        title_to_id(x)
        for x in event["consumed"]
    ]

    added = title_to_id(event["pai"])

    if rel_target == 1:
        # 上家から鳴いた
        new_code = (
            f"k"
            f"{added}"
            f"{consumed[0]}"
            f"{consumed[1]}"
            f"{consumed[2]}"
        )

    elif rel_target == 2:
        # 対面から鳴いた
        new_code = (
            f"{consumed[2]}"
            f"k"
            f"{added}"
            f"{consumed[0]}"
            f"{consumed[1]}"
        )

    elif rel_target == 3:
        # 下家から鳴いた
        new_code = (
            f"{consumed[1]}"
            f"{consumed[2]}"
            f"k"
            f"{added}"
            f"{consumed[0]}"
        )

    else:
        raise ValueError(
            f"invalid kakan direction actor={event['actor']}"
        )

    round_data[idx+2].append(new_code)
    ##
    #pon_history[(event["actor"], event["pai"])]["code"] = new_code

# ==========================================================
# 大明槓
# ==========================================================

def handle_daiminkan(round_data, event, last_discard):

    idx = PLAYER_OFFSET[event["actor"]]

    #called = title_to_id(event["pai"])

    consumed = [
        title_to_id(x)
        for x in event["consumed"]
    ]

    discard = title_to_id(
        last_discard[event["target"]]
    )

    rel_target = (event["actor"] - event["target"]) % 4
    if rel_target == 1:#下家
        code = (
            f"m"
            f"{discard}"
            f"{consumed[0]}"
            f"{consumed[1]}"
            f"{consumed[2]}"
        )
        
    elif rel_target == 2:#対面
        code = (
            f"{consumed[0]}"
            f"m"   
            f"{discard}"
            f"{consumed[1]}"
            f"{consumed[2]}"
        )
    elif rel_target == 3:#上家
        code = (
            f"{consumed[0]}"
            f"{consumed[1]}"
            f"{consumed[2]}"
            f"m"
            f"{discard}"
        )
    
    else:  
        raise ValueError(
            f"invalid minkan direction actor={event['actor']} target={event['target']}"
        )
    round_data[idx + 1].append(code)

    round_data[idx + 2].append(0)
#
#
#
#
#


# ==========================================================
# ドラ追加
# ==========================================================

def handle_dora(round_data, event):

    round_data[2].append(
        title_to_id(event["dora_marker"])
    )

# ==========================================================
# リーチ
# ==========================================================

#def handle_reach(round_data, event):
#
#    idx = PLAYER_OFFSET[event["actor"]]
#
    # 仮実装
#    round_data[idx + 1].append("r")


# ==========================================================
# 和了
# ==========================================================

def handle_hora(round_data, event):

    result = [
        "和了",
        event["deltas"],
        [
            event["actor"],
            event.get("target", event["actor"]),
            0,
            ""
        ]
    ]

    if "uradora_markers" in event:

        for ura in event["uradora_markers",[]]:
            result[2].append("裏ドラ")
            result[2].append(
                title_to_id(ura)
            )

    round_data.append(result)

# ==========================================================
# 流局
# ==========================================================

def handle_ryukyoku(round_data, event):

    result = [
        "流局",
        event["deltas"]
    ]

    round_data.append(result)

# ==========================================================
# Mortal → 天鳳JSON変換
# ==========================================================

def convert(events):

    tenhou = {
        "title": ["AI Battle", ""],
        "name": ["Best", "AI1", "AI2", "AI3"],
        "rule": {
            "disp": "般南喰赤",
            "aka": 1,
        },
        "log": [],
    }
    reach_pending = [False]*4
    last_discard = [None]*4
    current_round = None
    pon_history = {}
    skip_next_dahai = [False] * 4
    for event in events:

        event_type = event["type"]

        # ----------------------------
        # 半荘開始
        # ----------------------------
        if event_type == "start_game":
            continue

        # ----------------------------
        # 局開始
        # ----------------------------
        elif event_type == "start_kyoku":

            current_round = create_round(event)

        # ----------------------------
        # ツモ
        # ----------------------------
        elif event_type == "tsumo":

            add_tsumo(
                current_round,
                event["actor"],
                event["pai"],
            )

        # ----------------------------
        # 打牌
        # ----------------------------
        elif event_type == "dahai":

            add_dahai(
                current_round,
                event["actor"],
                event["pai"],
                event["tsumogiri"],
                reach_pending[event["actor"]],
            )
            reach_pending[event["actor"]] = False
            last_discard[event["actor"]] = event["pai"]

        # ----------------------------
        # チー
        # ----------------------------
        
        elif event_type == "chi":

            handle_chi(
                current_round,
                event,
            )

        # ----------------------------
        # ポン
        # ----------------------------
        elif event_type == "pon":

            handle_pon(
                current_round,
                event,
                last_discard,
                pon_history,
            )

        # ----------------------------
        # 暗槓
        # ----------------------------
        elif event_type == "ankan":

            handle_ankan(
                current_round,
                event,
            )

        # ----------------------------
        # 加槓
        # ----------------------------
        elif event_type == "kakan":

            handle_kakan(
                current_round,
                event,
                pon_history,
            )

            #current_round[idx + 2].append(
            #    f"kk{title_to_id(event["pai"])}"
            #)

            #skip_next_dahai[event["actor"]] = True

        # ----------------------------
        # 大明槓
        # ----------------------------
        elif event_type == "daiminkan":

            handle_daiminkan(
                current_round,
                event,
                last_discard,
            )

            #skip_next_dahai[event["actor"]] = True

        # ----------------------------
        # ドラ表示
        # ----------------------------
        elif event_type == "dora":

            current_round[2].append(
                title_to_id(
                    event["dora_marker"]
                )
            )

        # ----------------------------
        # リーチ
        # ----------------------------
        elif event_type == "reach":
            reach_pending[event["actor"]] = True

        # ----------------------------
        # 和了
        # ----------------------------
        elif event_type == "hora":
            # 裏ドラ
            current_round[3] = [
                title_to_id(x)
                for x in event.get("ura_markers", [])
            ]

            current_round.append([
                "和了",
                event["deltas"],
                [],
            ])

        # ----------------------------
        # 流局
        # ----------------------------
        elif event_type == "ryukyoku":

            current_round.append([
                "流局",
                event["deltas"],
            ])

        # ----------------------------
        # 局終了
        # ----------------------------
        elif event_type == "end_kyoku":

            tenhou["log"].append(
                current_round
            )

            current_round = None

        # ----------------------------
        # 半荘終了
        # ----------------------------
        elif event_type == "end_game":

            pass

    return tenhou

# ==========================================================
# JSON保存
# ==========================================================

def export_json(data, output_path):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            separators=(",", ":"),
        )

# ==========================================================
# main
# ==========================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        help="Mortal json log"
    )

    parser.add_argument(
        "output",
        help="Tenhou json"
    )

    args = parser.parse_args()

    events = load_mortal_log(
        args.input
    )

    tenhou = convert(events)

    export_json(
        tenhou,
        args.output,
    )

    print("Done.")
    print("Input :", args.input)
    print("Output:", args.output)

# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":
    main()

