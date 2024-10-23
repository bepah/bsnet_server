import hashlib
import struct

from flask import Flask, request

app = Flask(__name__)


def make_upinfo_response(message: bytes, count: int = 0, b: int = 0, c: int = 0):
    out = struct.pack("<IIII", 32 + len(message), count, b, c)
    out += hashlib.md5(message).digest()
    out += message
    return out


@app.route("/")
def index():
    return "OK"


@app.route("/buso/patch/launcher/launcher.upinfo")
def launcher_up_info_route():
    return make_upinfo_response(b"\x00" * 16)


@app.route("/buso/patch/dstudio/dstudio.upinfo")
def dstudio_up_info_route():
    return make_upinfo_response(b"\x00" * 16)


@app.route("/buso/patch/dstudio/figure_data.upinfo")
def dstudio_figure_data_up_info_route():
    return make_upinfo_response(b"\x00" * 16)


@app.route("/mds/client/shinki_updater/if_launcher.php")
def launcher_news_route():
    return "abcdef"


@app.route("/buso/game_api/bs_ds_auth.html", methods=["POST"])
def studio_api_auth_route():
    # 6 = Maintenance
    # 7 = Client version out of date
    # 8 = Auth fail
    # 11 = Previously logged in
    return "0\t\n0000000000000000\t\n"


@app.route("/buso/game_api/bs_ds_get_sotailist.html", methods=["POST"])
def studio_api_sotai_list_route():
    sotai = [
        # 100000,
        1,
        1000,
        2000,
        4000,
        5000,
        6000,
        8000,
        9000,
        10000,
        11000,
        12000,
        13000,
        1001,
        2001,
        14000,
        15000,
        16000,
        5001,
        6001,
        17000,
        18000,
        19000,
        20000,
        21000,
        22000,
        # 10001,
        23000,
        24000,
        25000,
        14001,
        15001,
        26000,
        27000,
        2,
        204000,
        205000,
        200000,
        201000,
        202000,
        203000,
        20001,
        21001,
        28000,
        29000,
        204001,
        205001,
        1002,
        2002,
        3,
        300000,
        300001,
        300002,
        23001,
        24001,
        13001,
        25001
    ]

    out = "0\t\n"

    for i in sotai:
        out += str(i) + "\t\n"

    return out


@app.route("/buso/game_api/bs_ds_get_upartslist.html", methods=["POST"])
def studio_api_uparts_list_route():
    out = "0\t\n"

    with open("docs/items.txt", "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()

            if line:
                out += line.partition(",")[0] + "\t1\t\n"

    return out


@app.route("/buso/game_api/bs_ds_get_spoint.html", methods=["POST"])
def studio_api_get_spoint_route():
    return "0\t\n100\t\n"


@app.route("/buso/game_api/bs_ds_get_goodslist.html", methods=["POST"])
def studio_api_get_goodslist_route():
    # ID[0]
    # Name[1]
    # Price[3]
    # Types[5]:
    # 0 - Default
    # 1 - New
    # 2 - Campaign
    # 3 - Popular
    # 4 - Recommended
    goods_div = request.form["goods_div"]

    out = "0\t\n"
    items = []

    if goods_div == "0":
        items.extend([
            "12003\tPremium Card\t0\t0\t0\t3\t",
            "4167\tetc_goggle_bu\t0\t0\t0\t0\t",
            "4166\tetc_goggle_rd\t0\t0\t0\t0\t",
            "3222\tbui_sotai\t0\t0\t0\t3\t",
        ])
    else:
        items.extend([
            "7001\tBunny Set\t0\t0\t0\t1\t",
        ])

    for item in items:
        out += item + "\n"

    return out


@app.route("/buso/game_api/bs_ds_auth_accesscode.html", methods=["POST"])
def studio_api_access_code_route():
    return "0\t\n"


@app.route("/buso/game_api/bs_ds_get_buy_history.html", methods=["POST"])
def studio_api_get_buy_history_route():
    return "0\t\n"


@app.route("/buso/game_api/bs_ds_get_goodsdetail.html", methods=["POST"])
def studio_api_get_goodsdetail_route():
    return "0\t\n0\t\n0\t\n0\t\nabc\t\n"


@app.route("/buso/game_api/bs_ds_buy_goods_confirm.html", methods=["POST"])
def studio_api_buy_goods_confirm_route():
    return "0\t\n"


@app.route("/buso/game_api/bs_ds_buy_goods.html", methods=["POST"])
def studio_api_buy_goods_route():
    return "0\t\n0\t\n0\t\n0\t\n"


@app.route("/buso/game_api/bs_br_auth.html", methods=["POST"])
def game_api_auth_route():
    return "0\t\n0000000000000000\t\n0\t\n"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
