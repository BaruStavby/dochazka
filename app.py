from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect
from datetime import datetime
import csv
import os
import pandas as pd

app = Flask(__name__, static_folder="static")
app.secret_key = "tajny_klic"
CSV_FILE = "dochazka.csv"

users = {
    "Petr": "1234",
    "Martin": "5678"
}

@app.route("/")
def index():
    if "user" in session:
        return send_from_directory("static", "index.html")
    return send_from_directory("static", "login.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username in users and users[username] == password:
        session["user"] = username
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Neplatné přihlášení"}), 401

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/zaznam", methods=["POST"])
def zaznam():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Nepřihlášený uživatel"}), 403

    data = request.json
    now = datetime.now()
    datum = now.strftime("%Y-%m-%d")
    cas = now.strftime("%H:%M:%S")
    jmeno = data.get("jmeno")
    akce = data.get("akce")
    mistr = session["user"]

    if not jmeno or not akce:
        return jsonify({"status": "error", "message": "Neúplná data"}), 400

    zapis = [datum, cas, jmeno, akce, mistr]
    zapis_csv(zapis)

    return jsonify({"status": "ok", "zaznam": zapis})

def zapis_csv(zaznam):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        if not exists:
            writer.writerow(["datum", "cas", "jmeno", "akce", "mistr"])
        writer.writerow(zaznam)

@app.route("/data")
def data():
    if not os.path.exists(CSV_FILE):
        return jsonify([])
    df = pd.read_csv(CSV_FILE, sep=";")
    datum = request.args.get("datum")
    hledat = request.args.get("hledat")
    if datum:
        df = df[df["datum"] == datum]
    if hledat:
        df = df[df["jmeno"].str.contains(hledat, case=False, na=False)]
    return df.to_dict(orient="records")

@app.route("/souhrn")
def souhrn():
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    df = pd.read_csv(CSV_FILE, sep=";")
    df["datetime"] = pd.to_datetime(df["datum"] + " " + df["cas"])
    df.sort_values(by=["jmeno", "datetime"], inplace=True)

    vysledky = []
    for jmeno, skupina in df.groupby("jmeno"):
        starty = skupina[skupina["akce"] == "start"]["datetime"].reset_index(drop=True)
        stopy = skupina[skupina["akce"] == "stop"]["datetime"].reset_index(drop=True)
        doby = []
        for i in range(min(len(starty), len(stopy))):
            doba = (stopy[i] - starty[i]).total_seconds() / 3600  # hodiny
            doby.append(doba)
        vysledky.append({"jmeno": jmeno, "hodin": round(sum(doby), 2)})
    return jsonify(vysledky)

@app.route("/export")
def export():
    if not os.path.exists(CSV_FILE):
        return "Žádná data", 404
    df = pd.read_csv(CSV_FILE, sep=";")
    excel_file = "dochazka_export.xlsx"
    df.to_excel(excel_file, index=False)
    return send_file(excel_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
