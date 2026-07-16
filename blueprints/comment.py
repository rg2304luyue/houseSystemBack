from flask import Blueprint, g, request

from decorators.decorators import token_required
from exts.db import db
from models.comment_model import Comment
from utils.response_utils import Code, error_response, success_response

comment_bp = Blueprint("comment", __name__)


def _serialize(comment):
    return {"comment_id": comment.comment_id, "house_id": comment.house_id,
            "username": comment.username, "type": comment.type, "desc": comment.desc,
            "time": comment.time.strftime("%Y-%m-%d %H:%M:%S") if comment.time else None,
            "at": comment.at}


@comment_bp.route("/comments/<int:house_id>", methods=["GET"])
def get_comments(house_id):
    return success_response(data=[_serialize(item) for item in Comment.query.filter_by(house_id=house_id).all()], message="Success")


@comment_bp.route("/comments/detail/<int:comment_id>", methods=["GET"])
def get_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return error_response(code=Code.NOT_FOUND, message="Comment not found")
    return success_response(data=_serialize(comment), message="Success")


@comment_bp.route("/comments", methods=["POST"])
@token_required
def add():
    data = request.get_json(silent=True) or {}
    if not data.get("house_id") or not data.get("desc"):
        return error_response(code=Code.BAD_REQUEST, message="house_id and desc are required")
    try:
        reply_to = data.get("at")
        if reply_to is not None and not db.session.get(Comment, int(reply_to)):
            return error_response(code=Code.NOT_FOUND, message="Reply target not found")
        comment = Comment(house_id=int(data["house_id"]), username=g.user.name or g.user.phone,
                          type=g.user.userType, desc=data["desc"].strip(),
                          at=int(reply_to) if reply_to is not None else None)
        db.session.add(comment)
        db.session.commit()
        return success_response(data=_serialize(comment), message="Comment created", code=201)
    except (TypeError, ValueError):
        db.session.rollback()
        return error_response(code=Code.BAD_REQUEST, message="Invalid comment data")
