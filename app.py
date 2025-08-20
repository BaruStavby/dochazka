from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, static_folder="static", template_folder="static")

# Login stránka
@app.route("/", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    username = request.form["username"]
    password = request.form["password"]
    # Zatím bez kontroly – rovnou přesměrujeme na docházku
    return redirect(url_for("index"))

# Hlavní stránka
@app.route("/index")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
