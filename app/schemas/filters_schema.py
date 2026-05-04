from typing import Optional
from pydantic import BaseModel


class StatisticsFilter(BaseModel):
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    channel: Optional[str] = None
    responsible: Optional[str] = None
    product: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    revenue_type: Optional[str] = None
    ticket_range: Optional[str] = None
    activity: Optional[str] = None
