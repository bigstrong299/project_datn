from flask import Blueprint, request, jsonify
from ...models.household import Household
from ...models.database import db

bp = Blueprint("households", __name__)

@bp.route("/", methods=["GET"])
def list_households():
    # Demo: return static list. Replace with real DB queries (filter by bbox, pagination).
    demo = [
        {"id": 1, "ma_hodan": "HD001", "ten_chu_ho": "Nguyen Van A", "diachi": "Address 1", "trang_thai_payment": False},
        {"id": 2, "ma_hodan": "HD002", "ten_chu_ho": "Tran Thi B", "diachi": "Address 2", "trang_thai_payment": True},
    ]
    return jsonify({"data": demo})

@bp.route("/<int:hid>", methods=["GET"])
def get_household(hid):
    return jsonify({"id": hid, "ma_hodan": f"HD{hid:03d}"})
