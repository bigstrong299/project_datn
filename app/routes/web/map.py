from flask import Blueprint, render_template

bp = Blueprint("admin_map", __name__, template_folder="../../templates")

@bp.route("/")
def map_view():
    # Map page will request GeoJSON from /api/households
    return render_template("map.html")
