from flask import Blueprint, g

from decorators.decorators import token_required
from models.contract_model import Contract
from models.house_model import HouseInfo
from models.rental_model import Rental
from utils.response_utils import Code, error_response, success_response

rental_bp = Blueprint("rental", __name__)


@rental_bp.route("/rental/tenants/<string:tenant_username>", methods=["GET"])
@token_required
def get_rental_by_tenant(tenant_username):
    """Return only the authenticated tenant's records; path value is ignored."""
    username = g.user.name or g.user.phone
    rentals = Rental.query.filter_by(tenant_username=username).all()
    data = []
    for rental in rentals:
        house = HouseInfo.query.get(rental.house_id)
        contract = Contract.query.filter_by(tenantName=username, houseId=rental.house_id).order_by(Contract.id.desc()).first()
        if not house or not contract:
            continue
        item = rental.to_dict()
        item.update({"purpose": contract.purpose, "startDate": contract.to_dict()["startDate"],
                     "endDate": contract.to_dict()["endDate"], "title": house.title,
                     "region": house.region, "landlordPhone": contract.landlordPhone,
                     "rentValue": contract.rentValue})
        data.append(item)
    if not data:
        return error_response(code=Code.NOT_FOUND, message="No rental records found")
    return success_response(data=data, message="Success")
