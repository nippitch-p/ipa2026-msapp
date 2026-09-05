from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
import os


app = Flask(__name__)


MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://admin:mongo@mongo:27017/?authSource=admin"
)

DB_NAME = os.environ.get(
    "DB_NAME",
    "ipa2026"
)

client = MongoClient(MONGO_URI)

db = client[DB_NAME]

routers = db["routers"]
router_results = db["router_results"]


@app.route("/")
def index():

    data = routers.find()

    return render_template(
        "index.html",
        data=data
    )


@app.route("/add", methods=["POST"])
def add_router():

    ip = request.form.get("ip")
    username = request.form.get("username")
    password = request.form.get("password")

    if ip and username and password:

        routers.insert_one({
            "ip": ip,
            "username": username,
            "password": password
        })

    return redirect(url_for("index"))


@app.route("/delete", methods=["POST"])
def delete_router():

    router_id = request.form.get("id")

    if router_id:

        routers.delete_one({
            "_id": ObjectId(router_id)
        })

    return redirect(url_for("index"))



@app.route("/router/<router_id>")
def router_detail(router_id):

    router = routers.find_one({
        "_id": ObjectId(router_id)
    })

    if not router:
        return "Router not found", 404


    results = list(
        router_results.find({
            "router_ip": router["ip"]
        })
        .sort("timestamp", -1)
        .limit(3)
    )


    return render_template(
        "router_detail.html",
        router=router,
        results=results
    )

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
