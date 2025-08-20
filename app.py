from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from datetime import datetime
import os, csv
import pandas as pd

# Flask hledá HTML v ./static (tam máš index.html i login.html)
app = Flask(__name__, static_folder="static", template_folder="static")

CSV_FILE = "dochazka.csv"

# ----------------- Stránky -----------------
@app.route("/", methods=["GET"])
def login_page():
    # jednoduché přihlášení – formulář jen přesměruje dál
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    # tady může být kontrola jména/hesla – teď přesměrujeme rovnou do appky
    return redirect(url_for("app_page"))

@app.route("/index")
@app.route("/app")
def app_page():
    return render_template("index.html")

# ----------------- API pro docházku -----------------
def zapis_csv(radek):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if not exists:
            w.writerow(["datum","cas","jmeno","akce","mistr"])
        w.writerow(radek)

@app.route("/zaznam", methods=["POST"])
def zaznam():
    """Uloží start/stop – voláno z index.html přes fetch()."""
    data = request.get_json(force=True)
    jmeno = (data or {}).get("jmeno")
    akce  = (data or {}).get("akce")
    if not jmeno or akce not in ("start","stop"):
        return jsonify({"status":"error","message":"Chybí jméno nebo špatná akce"}), 400

    now = datetime.now()
    radek = [now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), jmeno, akce, "mistr"]
    zapis_csv(radek)
    return jsonify({"status":"ok","zaznam":radek})

@app.route("/data", methods=["GET"])
def data():
    """Vrátí záznamy pro tabulku, volitelné filtry ?datum=YYYY-MM-DD&hledat=Text"""
    if not os.path.exists(CSV_FILE):
        return jsonify([])
    df = pd.read_csv(CSV_FILE, sep=";")
    datum = request.args.get("datum")
    hledat = request.args.get("hledat")
    if datum:
        df = df[df["datum"] == datum]
    if hledat:
        df = df[df["jmeno"].str.contains(hledat, case=False, na=False)]
    return jsonify(df.to_dict(orient="records"))

@app.route("/souhrn", methods=["GET"])
def souhrn():
    """Spočítá odpracované hodiny z dvojic start/stop pro každé jméno."""
    if not os.path.exists(CSV_FILE):
        return jsonify([])
    df = pd.read_csv(CSV_FILE, sep=";")
    if df.empty:
        return jsonify([])
    df["dt"] = pd.to_datetime(df["datum"] + " " + df["cas"])
    df = df.sort_values(["jmeno","dt"])
    vysl = []
    for jmeno, g in df.groupby("jmeno"):
        s = g[g["akce"]=="start"]["dt"].reset_index(drop=True)
        e = g[g["akce"]=="stop"]["dt"].reset_index(drop=True)
        hod = 0.0
        for i in range(min(len(s),len(e))):
            hod += (e[i]-s[i]).total_seconds()/3600
        vysl.append({"jmeno": jmeno, "hodin": round(hod,2)})
    return jsonify(vysl)

@app.route("/export", methods=["GET"])
def export():
    """Vytvoří Excel s docházkou a pošle ke stažení."""
    if not os.path.exists(CSV_FILE):
        return "Žádná data", 404
    df = pd.read_csv(CSV_FILE, sep=";")
    out = "dochazka_export.xlsx"
    df.to_excel(out, index=False)
    return send_file(out, as_attachment=True)

# Lokální běh; na Renderu startuje Gunicorn (Procfile)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
