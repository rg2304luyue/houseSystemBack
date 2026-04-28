from models.appointment_model import AppointmentModel
from exts.db import db
from datetime import datetime

def create_appointments(data):
    """添加新预约"""
    appointment = AppointmentModel(
        username=data['username'],
        property=data['property'],
        time=data['time'],
    )
    db.session.add(appointment)
    db.session.commit()
    return appointment