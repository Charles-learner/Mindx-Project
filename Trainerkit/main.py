from flask import Flask, request, jsonify, render_template
from markupsafe import Markup
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os

# Tạo Flask server
server = Flask(__name__)

# Đường dẫn file CSV
os.makedirs("data", exist_ok=True)
DATA_FILE = "./data/players.csv"

# Nếu file chưa tồn tại, tạo file mẫu với các cột chuẩn
if not os.path.exists(DATA_FILE):
    df0 = pd.DataFrame(columns=[
        "name", "age", "position", "goals", "assists", "stamina",
        "Clean sheets", "Saves", "High Claims", "Catches", "Games"
    ])
    df0.to_csv(DATA_FILE, index=False)

# --- Helper functions ----------------------------------------------------
def load_df_normalized():
    """
    Đọc CSV và chuẩn hóa tên cột về dạng dễ dùng.
    Trả về dataframe với các cột 'canonical' tồn tại.
    """
    df = pd.read_csv(DATA_FILE).fillna(0)

    # Create mapping from lower-stripped column name -> actual column name
    col_map = {c.strip().lower(): c for c in df.columns}

    # canonical names we want to support (original casing may vary in CSV)
    canonical = {
        "name": None,
        "age": None,
        "position": None,
        "goals": None,
        "assists": None,
        "stamina": None,
        "clean sheets": None,
        "saves": None,
        "high claims": None,
        "catches": None,
        "games": None
    }

    # map existing columns to canonical keys
    for key in canonical.keys():
        if key in col_map:
            canonical[key] = col_map[key]  # actual column name in df

    # If some canonical columns missing, create them with zeros or sensible defaults
    for key, actual in canonical.items():
        if actual is None:
            # choose a default name to add
            add_name = key if key not in df.columns else key + "_"
            # use 0 for numeric fields, "" for name/position
            if key == "name" or key == "position":
                df[add_name] = ""
            else:
                df[add_name] = 0
            canonical[key] = add_name

    # Rename dataframe columns to standardized lowercase keys for internal use
    rename_dict = {canonical[k]: k for k in canonical}
    df = df.rename(columns=rename_dict)

    # Ensure proper dtypes for numeric columns
    numeric_cols = ["age", "goals", "assists", "stamina", "clean sheets", "saves", "high claims", "catches", "games"]
    for c in numeric_cols:
        # coerce errors to 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Trim whitespace for string columns
    df["name"] = df["name"].astype(str).str.strip()
    df["position"] = df["position"].astype(str).str.strip()

    return df

def safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

# -------------------------------------------------------------------------

# ====== ROUTES FLASK ======
@server.route('/')
def home():
    return render_template('index.html')

@server.route('/players')
def page1():
    return render_template('players.html')

@server.route('/api/players', methods=['POST'])
def add_player():
    try:
        data = request.json
        # read, normalize existing df
        df = load_df_normalized()

        player = {
            "name": data.get("name", ""),
            "age": safe_int(data.get("age", 0)),
            "position": data.get("position", ""),
            "goals": safe_int(data.get("goals", 0)),
            "assists": safe_int(data.get("assists", 0)),
            "stamina": safe_int(data.get("stamina", 0)),
            # keeper fields default to 0 if not provided
            "clean sheets": safe_int(data.get("Clean sheets", data.get("clean_sheets", 0))),
            "saves": safe_int(data.get("Saves", 0)),
            "high claims": safe_int(data.get("High Claims", 0)),
            "catches": safe_int(data.get("Catches", 0)),
            "games": safe_int(data.get("Games", 0))
        }

        # append using the same column names as CSV
        df = pd.concat([df, pd.DataFrame([player])], ignore_index=True)
        # write back, preserving original CSV column names as-is (we'll write keys)
        df.to_csv(DATA_FILE, index=False)
        return jsonify({"message": "Player added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@server.route('/api/players', methods=['GET'])
def get_players():
    try:
        df = load_df_normalized()
        # return records with canonical keys (lowercase). Frontend can use those.
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@server.route('/api/player/<name>', methods=['GET'])
def get_player(name):
    """
    Trả JSON chi tiết cho 1 cầu thủ, với payload thay đổi tùy position.
    """
    try:
        df = load_df_normalized()
        # case-insensitive match
        recs = df[df["name"].str.lower() == name.lower()].to_dict(orient="records")
        if not recs:
            return jsonify({"error": "Player not found"}), 404
        p = recs[0]
        if p["position"].strip().lower() in ["gk", "goalkeeper", "goal keeper", "goal-keeper", "thủ môn"]:
            data = {
                "name": p["name"],
                "age": int(p["age"]),
                "position": p["position"],
                "clean_sheets": int(p["clean sheets"]),
                "saves": int(p["saves"]),
                "high_claims": int(p["high claims"]),
                "catches": int(p["catches"]),
                "games": int(p["games"])
            }
        else:
            data = {
                "name": p["name"],
                "age": int(p["age"]),
                "position": p["position"],
                "goals": int(p["goals"]),
                "assists": int(p["assists"]),
                "stamina": int(p["stamina"]),
                "games": int(p["games"])
            }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@server.route('/api/stats', methods=['GET'])
def stats():
    try:
        df = load_df_normalized()
        if df.empty:
            return jsonify({
                "avg_goals": 0,
                "avg_assists": 0,
                "avg_stamina": 0,
                "top_scorer": {"name": "N/A", "goals": 0},
                "top_assist": {"name": "N/A", "assists": 0}
            })

        summary = {
            "avg_goals": round(df["goals"].mean(), 2),
            "avg_assists": round(df["assists"].mean(), 2),
            "avg_stamina": round(df["stamina"].mean(), 2),
            "top_scorer": df.loc[df["goals"].idxmax()].to_dict() if df["goals"].sum() > 0 else {"name": "N/A", "goals": 0},
            "top_assist": df.loc[df["assists"].idxmax()].to_dict() if df["assists"].sum() > 0 else {"name": "N/A", "assists": 0}
        }
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@server.route('/api/players/<int:index>', methods=['DELETE'])
def delete_player(index):
    try:
        df = load_df_normalized()
        if index < 0 or index >= len(df):
            return jsonify({"error": "Invalid player index"}), 400
        df = df.drop(df.index[index]).reset_index(drop=True)
        df.to_csv(DATA_FILE, index=False)
        return jsonify({"message": "Player deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@server.route('/api/players/<int:index>', methods=['PUT'])
def update_player(index):
    try:
        df = load_df_normalized()
        if index < 0 or index >= len(df):
            return jsonify({"error": "Invalid player index"}), 400
        data = request.json
        # update using canonical column names
        for key, value in data.items():
            key_l = key.strip().lower()
            if key_l in df.columns:
                if key_l in ["age", "goals", "assists", "stamina", "clean sheets", "saves", "high claims", "catches", "games"]:
                    df.at[index, key_l] = safe_int(value)
                else:
                    df.at[index, key_l] = value
        df.to_csv(DATA_FILE, index=False)
        return jsonify({"message": "Player updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Dash app (kept as before)
dash_app = Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/'
)

# Layout Dash
dash_app.layout = html.Div([
    html.H4('Analysis of players', style={'textAlign': 'center', 'marginBottom': 30}),
    dcc.Graph(id="graph"),
    html.P("Choose metric:", style={'marginTop': 20, 'fontWeight': 'bold'}),
    dcc.Dropdown(
        id='names',
        options=[
            {"label": "Goals", "value": "goals"},
            {"label": "Assists", "value": "assists"},
            {"label": "Stamina", "value": "stamina"}
        ],
        value="goals",
        clearable=False,
        style={'marginBottom': 20}
    ),
], style={'padding': 20})

@dash_app.callback(
    Output("graph", "figure"),
    Input("names", "value")
)
def generate_chart(metric):
    try:
        df = load_df_normalized()
        if df.empty:
            fig = px.pie(values=[1], names=["No data"], title="No players available")
            return fig

        if metric not in df.columns:
            fig = px.pie(values=[1], names=["No data"], title=f"No {metric} data")
            return fig

        df_filtered = df[df[metric] > 0]

        if df_filtered.empty:
            fig = px.pie(values=[1], names=[f"No {metric} data"], title=f"No {metric} data available")
        else:
            fig = px.pie(
                df_filtered,
                names="name",
                values=metric,
                hole=.3,
                title=f"Player {metric.capitalize()} Distribution"
            )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    except Exception as e:
        fig = px.pie(values=[1], names=["Error"], title=f"Error: {str(e)}")
        return fig

@server.route('/chart')
def chart():
    try:
        metric = request.args.get("metric", "goals")
        df = load_df_normalized()

        if metric not in df.columns:
            fig = px.pie(values=[1], names=[f"No {metric} data"], title=f"No {metric} data available")
        else:
            df_filtered = df[df[metric] > 0]
            if df_filtered.empty:
                fig = px.pie(values=[1], names=[f"No {metric} data"], title=f"No {metric} data available")
            else:
                fig = px.pie(
                    df_filtered,
                    names="name",
                    values=metric,
                    hole=.3,
                    title=f"Player {metric.capitalize()} Distribution"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')

        fig.update_layout(
            font_size=12,
            title_font_size=18,
            showlegend=True
        )

        graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        return render_template("chart.html", graph=Markup(graph_html), metric=metric)
    except Exception as e:
        return f"Error: {str(e)}", 500

@server.route("/api/chart")
def chart_data():
    df = load_df_normalized()

    data = {
        "categories": df["name"].tolist(),
        "goals": df["goals"].astype(int).tolist(),
        "assists": df["assists"].astype(int).tolist()
    }
    return jsonify(data)

# ======= combined page with violin + GK stats =========
@server.route('/comp')
def comp():
    df = load_df_normalized()

    if df.empty:
        return render_template("comp.html", graph=None, gk_graph=None)

    # Tính tuổi trung bình
    age_avg = df['age'].mean()
    
    dark_mode = request.args.get("dark", "false") == "true"

    # ========== Violin plot (age by position) ==========
    fig = px.violin(df, y="age", x="position", color="position", box=True, points="all")

    fig.update_traces(
        width=0.9,          # tăng chiều rộng
        scalemode='count',  # hoặc 'width' để điều chỉnh theo số lượng
        line=dict(width=2)  # đường viền
    )

    fig.update_layout(template='plotly_dark' if dark_mode else 'simple_white')

    # Thêm đường trung bình
    fig.add_shape(
        type="line",
        line_color="blue",
        line_width=3,
        opacity=1,
        line_dash="dot",
        x0=0, x1=1, xref="paper",
        y0=age_avg, y1=age_avg, yref="y"
    )

    graph_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ========== goalkeeper stats ==========
    goalies = df[df["position"].str.lower().isin(["gk", "goalkeeper", "goal keeper", "goal-keeper", "thủ môn"])]

    # Đảm bảo các cột tồn tại
    for col in ["clean sheets", "saves", "high claims", "catches"]:
        if col not in goalies.columns:
            goalies[col] = 0

    if not goalies.empty and goalies[["clean sheets", "saves", "high claims", "catches"]].sum().sum() > 0:
        head = 5
        df1 = goalies.sort_values(by='clean sheets', ascending=False).head(head)
        df2 = goalies.sort_values(by='saves', ascending=False).head(head)
        df3 = goalies.sort_values(by='high claims', ascending=False).head(head)
        df4 = goalies.sort_values(by='catches', ascending=False).head(head)

        fig2 = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Clean sheets', 'Saves', 'High Claims', 'Catches'),
            horizontal_spacing=0.15,
            vertical_spacing=0.18
        )

        fig2.add_trace(go.Bar(y=df1["name"], x=df1["clean sheets"], orientation='h'), row=1, col=1)
        fig2.add_trace(go.Bar(y=df2["name"], x=df2["saves"], orientation='h'), row=1, col=2)
        fig2.add_trace(go.Bar(y=df3["name"], x=df3["high claims"], orientation='h'), row=2, col=1)
        fig2.add_trace(go.Bar(y=df4["name"], x=df4["catches"], orientation='h'), row=2, col=2)

        fig2.update_traces(marker_color='rgb(110,102,250)', marker_line_color='rgb(8,48,107)',
                           marker_line_width=1.5, opacity=0.8)
        fig2.update_layout(
            title=dict(
            text='<b>Top Goalkeepers Stats</b>',
            font=dict(size=22)
        ),
            template='ggplot2',
            showlegend=False,
            height=700,
            width=1000
        )
        gk_graph_html = fig2.to_html(full_html=False, include_plotlyjs=False)
    else:
        gk_graph_html = None

    return render_template(
        "comp.html",
        graph=Markup(graph_html),
        gk_graph=Markup(gk_graph_html) if gk_graph_html else None
    )


if __name__ == '__main__':
    server.run(debug=True, port=8000)




