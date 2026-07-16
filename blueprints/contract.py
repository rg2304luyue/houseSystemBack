from datetime import datetime

from flask import Blueprint, g, request

from decorators.decorators import token_required
from exts.db import db
from models.house_model import HouseInfo
from models.rental_model import Rental
from utils.response_utils import Code, error_response, success_response
from services.contract_service import create_contract, get_contract_by_landlord_id_and_tenant

contract_bp = Blueprint("contract", __name__)


@contract_bp.route("/contracts", methods=["POST"])
@token_required
def create_contract_route():
    """Create a contract and its rental record atomically.

    The client may provide display fields, but landlord and tenant identities are
    always derived from the authenticated user and the selected house.
    """
    data = request.get_json(silent=True) or {}
    if "house_id" not in data and "houseid" in data:
        data["house_id"] = data["houseid"]
    required = ("house_id", "rentValue", "purpose", "startDate", "endDate")
    missing = [field for field in required if not data.get(field)]
    if missing:
        return error_response(code=Code.BAD_REQUEST, message=f"Missing required fields: {', '.join(missing)}")

    try:
        house_id = int(data["house_id"])
        house = HouseInfo.query.filter_by(id=house_id).with_for_update().first()
        if not house:
            return error_response(code=Code.NOT_FOUND, message="House not found")
        if not house.landlord:
            return error_response(code=Code.BAD_REQUEST, message="House has no landlord")
        if house.landlord == (g.user.name or g.user.phone):
            return error_response(code=Code.FORBIDDEN, message="Landlord cannot rent their own house")
        if not house.available:
            return error_response(code=Code.BAD_REQUEST, message="House is not available")

        contract = create_contract(data, house=house, tenant=g.user)
        rental = Rental(
            tenant_username=g.user.name or g.user.phone,
            landlord_username=house.landlord,
            house_id=house.id,
            currentDate=datetime.utcnow(),
        )
        house.available = 0
        db.session.add_all([contract, rental])
        db.session.commit()
        result = contract.to_dict()
        result["rental_info"] = rental.to_dict()
        return success_response(data=result, message="Contract created", code=201)
    except (TypeError, ValueError):
        db.session.rollback()
        return error_response(code=Code.BAD_REQUEST, message="Invalid contract data")
    except Exception:
        db.session.rollback()
        return error_response(code=Code.INTERNAL_SERVER_ERROR, message="Unable to create contract")


@contract_bp.route("/contracts/<string:tenant_name>/<string:landlord_name>", methods=["GET"])
@token_required
def get_contract(tenant_name, landlord_name):
    if (g.user.name or g.user.phone) not in {tenant_name, landlord_name}:
        return error_response(code=Code.FORBIDDEN, message="Not allowed to view this contract")
    contract = get_contract_by_landlord_id_and_tenant(landlord_name, tenant_name)
    if not contract:
        return error_response(code=Code.NOT_FOUND, message="Contract not found")
    return success_response(data=contract.to_dict(), message="Success", code=Code.GET_OK)
