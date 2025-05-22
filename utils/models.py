from dataclasses import dataclass
from typing import Optional

@dataclass
class CustomerContact:
    name: str
    email: str
    mobile: str

@dataclass
class PaymentLink:
    link_id: str
    link_name: str
    short_url: str
    status: str
    created_date: str
    expiry_date: str

@dataclass
class Transaction:
    txn_id: str
    order_id: str
    amount: float
    status: str
    completed_time: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None

@dataclass
class PaytmResponse:
    status: str
    message: str
    data: Optional[dict] = None

    @classmethod
    def from_response(cls, response: dict) -> 'PaytmResponse':
        result_info = response.get("body", {}).get("resultInfo", {})
        return cls(
            status=result_info.get("resultStatus", ""),
            message=result_info.get("resultMessage", ""),
            data=response.get("body")
        ) 
