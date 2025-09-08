from flask import Flask, request, jsonify, render_template
import pandas as pd


app = Flask(__name__)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "players.csv")


# File CSV để lưu dữ liệu cầu thủ
DATA_FILE = "./data/players.csv"

# Đảm bảo thư mục tồn tại
os.makedirs("data", exist_ok=True)

# Nếu file chưa tồn tại -> tạo với header
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["name", "age", "position", "goals", "assists", "stamina"])
    df.to_csv(DATA_FILE, index=False)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/players')
def page1():
    return render_template('players.html')

# API thêm cầu thủ
@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.json
    player = {
        "name": data.get("name"),
        "age": int(data.get("age", 0)),
        "position": data.get("position"),
        "goals": int(data.get("goals", 0)),
        "assists": int(data.get("assists", 0)),
        "stamina": int(data.get("stamina", 0))
    }
    df = pd.read_csv(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([player])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    return jsonify({"message": "Player added successfully"}), 201



# API lấy danh sách cầu thủ
@app.route('/api/players', methods=['GET'])
def get_players():
    df = pd.read_csv(DATA_FILE)
    df = df.fillna(0)  # thay NaN thành 0
    return jsonify(df.to_dict(orient="records"))



# API thống kê
@app.route('/api/stats', methods=['GET'])
def stats():
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return jsonify({"error": "No players available"}), 400

    summary = {
        "avg_goals": round(df["goals"].mean(), 2),
        "avg_assists": round(df["assists"].mean(), 2),
        "avg_stamina": round(df["stamina"].mean(), 2),
        "top_scorer": df.loc[df["goals"].idxmax()].to_dict(),
        "top_assist": df.loc[df["assists"].idxmax()].to_dict()
    }
    return jsonify(summary)

# API xoá cầu thủ theo index (dùng số thứ tự trong CSV)
@app.route('/api/players/<int:index>', methods=['DELETE'])
def delete_player(index):
    df = pd.read_csv(DATA_FILE)
    if index < 0 or index >= len(df):
        return jsonify({"error": "Invalid player index"}), 400
    
    df = df.drop(index)
    df.to_csv(DATA_FILE, index=False)
    return jsonify({"message": "Player deleted successfully"})

# API sửa thông tin cầu thủ
@app.route('/api/players/<int:index>', methods=['PUT'])
def update_player(index):
    df = pd.read_csv(DATA_FILE)
    if index < 0 or index >= len(df):
        return jsonify({"error": "Invalid player index"}), 400

    data = request.json
    for key, value in data.items():
        if key in df.columns:
            df.at[index, key] = value
    df.to_csv(DATA_FILE, index=False)
    return jsonify({"message": "Player updated successfully"})



if __name__ == '__main__':
    app.run(debug=True, port=8000)

