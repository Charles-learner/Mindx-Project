from flask import Flask, request, jsonify, render_template
import csv, os

app = Flask(__name__)

DATA_FILE = "data/players.csv"
FIELDNAMES = [
    "id","name","age","position","goals","assists","stamina","games",
    "clean_sheets","saves","high_claims","catches",
    "tackles","clearances","blocks","interceptions",
    "passes_completed","key_passes","ball_recoveries",
    "dribbles","shots","shots_on_target","chances_created"
]

# ========== Helpers ==========
def load_data():
    players = []
    if not os.path.exists(DATA_FILE):
        return players
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            p = {}
            for k in FIELDNAMES:
                if k == "id":
                    try:
                        p["id"] = int(row.get("id", i))
                    except:
                        p["id"] = i
                else:
                    try:
                        p[k] = int(row.get(k, 0))
                    except:
                        p[k] = row.get(k, "")
            players.append(p)
    return players

def save_data(players):
    # đảm bảo tất cả field đều có
    for p in players:
        for k in FIELDNAMES:
            if k not in p:
                p[k] = 0 if k != "name" and k != "position" else ""
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for p in players:
            writer.writerow(p)


def try_int(val):
    try: return int(val)
    except: return val

# ========== Routes ==========
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/players")
def players_page():
    return render_template("players.html")

@app.route("/chart")
def chart_page():
    return render_template("chart.html")

@app.route("/comp")
def comp_page():
    return render_template("comp.html")

@app.route("/player")
def player_page():
    return render_template("player.html")

# ========== API ==========
@app.route("/api/players", methods=["GET"])
def api_get_players():
    return jsonify(load_data())

@app.route("/api/players", methods=["POST"])
def api_add_player():
    players = load_data()
    data = request.json
    new_id = max([p["id"] for p in players], default=0) + 1
    data["id"] = new_id
    players.append(data)
    save_data(players)
    return jsonify({"message": "Player added", "id": new_id})

@app.route("/api/players/<int:pid>", methods=["PUT"])
def api_update_player(pid):
    players = load_data()
    data = request.json
    for i, p in enumerate(players):
        if p["id"] == pid:
            data["id"] = pid
            players[i] = data
            break
    save_data(players)
    return jsonify({"message": "Player updated"})

@app.route("/api/players/<int:pid>", methods=["DELETE"])
def api_delete_player(pid):
    players = load_data()
    players = [p for p in players if p["id"] != pid]
    save_data(players)
    return jsonify({"message": "Player deleted"})

@app.route("/api/stats", methods=["GET"])
def api_stats():
    players = load_data()
    if not players:
        return jsonify({"total":0})

    total = len(players)
    sum_goals = sum(p["goals"] for p in players)
    sum_assists = sum(p["assists"] for p in players)
    avg_stamina = round(sum(p["stamina"] for p in players)/total, 1)

    top_scorer = max(players, key=lambda p:p["goals"], default=None)
    gks = [p for p in players if p["position"]=="Goalkeeper"]
    top_gk = max(gks, key=lambda p:p["clean_sheets"], default=None) if gks else None

    return jsonify({
        "total": total,
        "sum_goals": sum_goals,
        "sum_assists": sum_assists,
        "avg_stamina": avg_stamina,
        "top_scorer": top_scorer,
        "top_gk": top_gk
    })

import unicodedata

def normalize_name(s: str):
    """Chuẩn hoá tên: lower, bỏ dấu, trim"""
    if not s: return ""
    s = s.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

@app.route("/api/comp")
def api_comp():
    p1 = request.args.get("player1")
    p2 = request.args.get("player2")
    players = load_data()

    # Chuẩn hoá tên
    np1, np2 = normalize_name(p1), normalize_name(p2)
    pl1 = next((x for x in players if normalize_name(x["name"]) == np1), None)
    pl2 = next((x for x in players if normalize_name(x["name"]) == np2), None)
    if not pl1 or not pl2:
        return jsonify({"error": "Not found"}), 404

    # Lấy tất cả chỉ số từ goals → chances_created
    categories = [
        "goals","assists","stamina","games",
        "clean_sheets","saves","high_claims","catches",
        "tackles","clearances","blocks","interceptions",
        "passes_completed","key_passes","ball_recoveries",
        "dribbles","shots","shots_on_target","chances_created"
    ]

    # Tìm max toàn đội cho từng chỉ số
    max_vals = {c: max(int(p.get(c,0) or 0) for p in players) or 1 for c in categories}

    def scaled(player):
        return [ round(int(player.get(c,0) or 0) / max_vals[c] * 100, 1) for c in categories ]

    series = [
        {"name": pl1["name"], "data": scaled(pl1)},
        {"name": pl2["name"], "data": scaled(pl2)}
    ]

    return jsonify({"categories": categories, "series": series})

@app.route("/api/player")
def api_player():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "No name"}), 400

    players = load_data()

    # Chuẩn hoá để so khớp (dùng lại normalize_name nếu có)
    n = normalize_name(name)
    pl = next((x for x in players if normalize_name(x["name"]) == n), None)

    if not pl:
        return jsonify({"error": "Not found"}), 404

    # Lấy danh sách chỉ số (trừ id, name, age, position)
    categories = [
        "goals","assists","stamina","games",
        "clean_sheets","saves","high_claims","catches",
        "tackles","clearances","blocks","interceptions",
        "passes_completed","key_passes","ball_recoveries",
        "dribbles","shots","shots_on_target","chances_created"
    ]

    # Tính max để scale 0–100
    max_vals = {c: max(int(p.get(c,0) or 0) for p in players) or 1 for c in categories}

    raw = {c:int(pl.get(c,0) or 0) for c in categories}
    scaled = {c: round(raw[c]/max_vals[c]*100,1) for c in categories}

    return jsonify({
        "id": pl["id"],
        "name": pl["name"],
        "age": pl["age"],
        "position": pl["position"],
        "raw": raw,
        "scaled": scaled
    })

# ========== Run ==========
if __name__ == "__main__":
    app.run(debug=True)


