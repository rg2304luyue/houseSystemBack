from datetime import datetime

from models.contract_model import Contract


def _parse_date(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def create_contract(data, *, house, tenant):
    """Build, but do not commit, a contract owned by the supplied entities."""
    return Contract(
        rentValue=str(data["rentValue"]),
        purpose=data["purpose"],
        startDate=_parse_date(data["startDate"]),
        endDate=_parse_date(data["endDate"]),
        landlordName=house.landlord,
        landlordId=str(house.landlord),
        landlordPhone=house.phone_num or "",
        tenantName=tenant.name or tenant.phone,
        tenantId=str(tenant.id),
        tenantPhone=tenant.phone or "",
        formattedRent=data.get("formattedRent", str(data["rentValue"])),
        currentDate=datetime.utcnow(),
        houseId=house.id,
    )


def get_contract_by_landlord_id_and_tenant(landlord_name, tenant_name):
    return Contract.query.filter_by(landlordName=landlord_name, tenantName=tenant_name).first()
