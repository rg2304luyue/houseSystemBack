"""HouseInfo — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
import datetime
from sqlalchemy import Integer, String, Float, Date, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class HouseInfo(Base):
    __tablename__ = "house_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), comment='标题，如：整租·锦源小区 2室1厅 南')
    region: Mapped[Optional[str]] = mapped_column(String(50), comment='区，如：雨花')
    block: Mapped[Optional[str]] = mapped_column(String(50), comment='街道，如：树木岭')
    community: Mapped[Optional[str]] = mapped_column(String(100), comment='小区，如：锦源小区')
    area: Mapped[Optional[float]] = mapped_column(Float, comment='面积，单位㎡')
    direction: Mapped[Optional[str]] = mapped_column(String(20), comment='朝向，如：南')
    rooms: Mapped[Optional[str]] = mapped_column(String(20), comment='几室几厅，如：2室1厅1卫')
    price: Mapped[Optional[int]] = mapped_column(Integer, comment='价格，单位：元/月')
    rent_type: Mapped[Optional[str]] = mapped_column(String(20), comment='租赁方式，如：整租、合租')
    decoration: Mapped[Optional[str]] = mapped_column(String(20), comment='装修情况，如：精装')
    subway: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'0'"), comment='是否近地铁')
    available: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'1'"), comment='是否随时看房')
    tag_new: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'0'"), comment='是否新上')
    image_url: Mapped[Optional[str]] = mapped_column(String(255), comment='房源图片URL')
    publish_time: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='发布时间')
    page_views: Mapped[int] = mapped_column(Integer, default=0, comment='浏览量')
    landlord: Mapped[Optional[str]] = mapped_column(String(255), comment='房东')
    phone_num: Mapped[Optional[str]] = mapped_column(String(100), comment='房东电话')
    landlord_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    house_num: Mapped[Optional[int]] = mapped_column(Integer, comment='房源编号')

    # One-to-one relationship with HouseDetail
    detail_obj: Mapped[Optional["HouseDetail"]] = relationship(
        back_populates="house_info_obj",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime.date):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data
