from typing import Optional, List, Dict, Any
import requests
from datetime import datetime
from paytmchecksum import PaytmChecksum
from config.settings import settings
import json
import datetime


class OrderListService:
    def __init__(self, key_secret: str, mid: str):
        """
        Initialize the OrderListService with Paytm credentials.
        
        Args:
            key_secret (str): Paytm merchant key secret
            mid (str): Paytm merchant ID
        """
        self.key_secret = key_secret
        self.mid = mid
        self.base_url = settings.PAYTM_BASE_URL

    def fetch_order_list(
        self,
        from_date: str,
        to_date: str,
        order_search_type: str = "TRANSACTION",
        order_search_status: str = "SUCCESS",
        page_number: int = 1,
        page_size: int = 50,
        is_sort: bool = True
    ) -> str:
        """
        Fetch the list of orders from Paytm.
        
        Args:
            from_date (str): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm)
            to_date (str): End date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm)
            order_search_type (str): Type of order search (default: TRANSACTION)
            order_search_status (str): Status of orders to search for (default: SUCCESS)
            page_number (int): Page number for pagination (default: 1)
            page_size (int): Number of records per page (default: 50)
            is_sort (bool): Whether to sort results by order date (default: True)
            
        Returns:
            str: Formatted string containing order list details
        """
        try:
            # Prepare request body
            body = {
                "mid": self.mid,
                "fromDate": from_date,
                "toDate": to_date,
                "orderSearchType": order_search_type,
                "pageNumber": str(page_number),
                "pageSize": str(page_size),
                "isSort": is_sort
            }

            # Add optional parameters if provided
            if order_search_status:
                body["orderSearchStatus"] = order_search_status

            signature = PaytmChecksum.generateSignature(json.dumps(body), self.key_secret)

            # Prepare request head
            head = {
                "tokenType": "CHECKSUM",
                "signature": signature
            }

            # Make API request
            response = requests.post(
                f"{self.base_url}/merchant-passbook/search/list/order/v2",
                json={"head": head, "body": body},
                headers={"Content-Type": "application/json"}
            )
            
            
            
            # Check if response is successful
            response.raise_for_status()
            
            # Try to get response text first
            response_text = response.text
            
            
            if not response_text:
                return "Empty response received from Paytm API"
            
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                return f"Invalid JSON response from Paytm API: {str(e)}"
            
            # Check if the response is successful - resultInfo is in body
            result_info = response_data.get("body", {}).get("resultInfo", {})
            if result_info.get("resultStatus") != "SUCCESS":
                error_msg = result_info.get("resultMsg", "Unknown error")
                return f"Error fetching order list: {error_msg}"
            
            # Get orders from response
            orders = response_data.get("body", {}).get("orders", [])
            if not orders:
                return "No orders found for the given criteria."
            
            # Format the response
            result = "Order List:\n"
            for order in orders:
                result += f"\nOrder ID: {order.get('merchantOrderId', 'N/A')}"
                result += f"\nTransaction ID: {order.get('txnId', 'N/A')}"
                result += f"\nAmount: ₹{order.get('amount', 'N/A')}"
                result += f"\nPayment Mode: {order.get('payMode', 'N/A')}"
                result += f"\nCreated Time: {order.get('orderCreatedTime', 'N/A')}"
                result += f"\nCompleted Time: {order.get('orderCompletedTime', 'N/A')}"
                result += f"\nStatus: {order.get('orderSearchStatus', 'N/A')}"
                result += f"\nMerchant Name: {order.get('merchantName', 'N/A')}"
                if order.get('vanId'):
                    result += f"\nVAN ID: {order.get('vanId')}"
                if order.get('rrn'):
                    result += f"\nRRN: {order.get('rrn')}"
                if order.get('vanIfscCode'):
                    result += f"\nVAN IFSC Code: {order.get('vanIfscCode')}"
                result += "\n" + "-"*50
            
            # Add pagination info
            result += f"\n\nPage {page_number}"
            result += f"\nTotal Records: {len(orders)}"
            
            return result

        except requests.exceptions.RequestException as e:
            return f"Failed to fetch order list: {str(e)}"
        except Exception as e:
            return f"Unexpected error while fetching order list: {str(e)}"
