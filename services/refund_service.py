import requests
import json
from paytmchecksum import PaytmChecksum
from typing import Optional
from config.settings import settings
import datetime

class RefundService:
    def __init__(self, merchant_key: str, mid: str):
        self.merchant_key = merchant_key
        self.mid = mid
        self.base_url = settings.PAYTM_BASE_URL

    def initiate_refund(self, order_id: str, refund_reference_id: str, txn_id: str, refund_amount: float) -> str:
        """
        Initiate a refund for a transaction
        
        Args:
            order_id (str): Original order ID of the transaction
            refund_reference_id (str): Unique refund reference ID (max 50 chars)
            txn_id (str): Original Paytm transaction ID
            refund_amount (float): Amount to be refunded (must be <= original transaction amount)
            
        Returns:
            str: Response message indicating success or failure of refund initiation along with the Refund Status, Message and Code of the refund
        """
        # Prepare the request parameters
        paytm_params = {
            "body": {
                "mid": self.mid,
                "txnType": "REFUND",
                "orderId": order_id,
                "txnId": txn_id,
                "refId": refund_reference_id,
                "refundAmount": str(format(refund_amount, '.2f'))  # Ensure 2 decimal places
            }
        }

        # Generate checksum
        checksum = PaytmChecksum.generateSignature(
            json.dumps(paytm_params["body"]), 
            self.merchant_key
        )

        # Add checksum to header
        paytm_params["head"] = {
            "signature": checksum
        }

        try:
            # Make API call
            resp = requests.post(
                f"{self.base_url}/refund/apply",
                json=paytm_params,
                headers={"Content-type": "application/json"}
            )

        

            response = resp.json()

            # Process response
            result_info = response.get("body", {}).get("resultInfo", {})
            result_status = result_info.get("resultStatus")
            result_msg = result_info.get("resultMsg")
            result_code = result_info.get("resultCode")
            refund_id = response.get("body", {}).get("refundId", "")
            paytm_txn_id = response.get("body", {}).get("txnId", "")
            refund_amt = response.get("body", {}).get("refundAmount", "")

            # Format response message
            status_message = (
                f"Refund Status: {result_status}\n"
                f"Message: {result_msg}\n"
                f"Code: {result_code}\n"
                f"Refund ID: {refund_id}\n"
                f"Paytm Txn ID: {paytm_txn_id}\n"
                f"Refund Amount: {refund_amt}\n"
            )

            if result_status == "PENDING":
                return f"Refund initiated successfully and is pending:\n{status_message}"
            elif result_status == "TXN_FAILURE":
                return f"Refund initiation failed:\n{status_message}"
            else:
                return f"Unexpected response:\n{status_message}"

        except Exception as e:
            return f"Error initiating refund: {str(e)}"

    def check_refund_status(self, order_id: str, refund_reference_id: str) -> str:
        """
        Check the status of a refund request
        
        Args:
            order_id (str): Original order ID of the transaction
            refund_reference_id (str): Refund reference ID used during refund initiation
            
        Returns:
            str: Current status of the refund request
        """
        paytm_params = {
            "body": {
                "mid": self.mid,
                "orderId": order_id,
                "refId": refund_reference_id
            }
        }

        # Generate checksum
        checksum = PaytmChecksum.generateSignature(
            json.dumps(paytm_params["body"]), 
            self.merchant_key
        )

        # Add checksum to header
        paytm_params["head"] = {
            "signature": checksum
        }

        try:
            # Make API call
            response = requests.post(
                f"{self.base_url}/v2/refund/status",
                json=paytm_params,
                headers={"Content-type": "application/json"}
            ).json()

            # Process response
            result_info = response.get("body", {}).get("resultInfo", {})
            refund_status = response.get("body", {}).get("refundStatus", "")
            result_msg = result_info.get("resultMsg", "")
            refund_id = response.get("body", {}).get("refundId", "")
            txn_id = response.get("body", {}).get("txnId", "")
            total_refund_amount = response.get("body", {}).get("totalRefundAmount", "")
            refund_amount = response.get("body", {}).get("refundAmount", "")
            txn_amount = response.get("body", {}).get("txnAmount", "")
            return (
                f"Refund Status: {refund_status}\n"
                f"Details: {result_msg}\n"
                f"Refund ID: {refund_id}\n"
                f"Txn ID: {txn_id}\n"
                f"Total Refund Amount: {total_refund_amount}\n"
                f"Refund Amount: {refund_amount}\n"
                f"Txn Amount: {txn_amount}\n"
            )

        except Exception as e:
            return f"Error checking refund status: {str(e)}"

    def fetch_refund_list(
        self,
        start_date: str,
        end_date: str,
        is_sort: bool = True,
        page_num: int = 1,
        page_size: int = 50
    ) -> str:
        """
        Fetches the list of refunds for the merchant within a date range.
        Current Date is {datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')}
        Args:
            start_date (str): Start date in 'yyyy-MM-ddTHH:mm:ss+zzzz' format.
            end_date (str): End date in 'yyyy-MM-ddTHH:mm:ss+zzzz' format.
            is_sort (bool): Whether to sort results by refund date.
            page_num (int): Page number for pagination.
            page_size (int): Number of records per page (max 50).

        Returns:
            str: Formatted refund list or error message.
        """
        try:
            # Validate required parameters
            if not all([start_date, end_date]):
                return "Error: start_date and end_date are required parameters"
            
            if not self.mid:
                return "Error: Merchant ID (mid) is not configured"

            url = f"{self.base_url}/merchant-passbook/api/v1/refundList"
            body = {
                "mid": self.mid,
                "isSort": str(is_sort).lower(),
                "startDate": start_date,
                "endDate": end_date,
                "pageNum": str(page_num),
                "pageSize": str(page_size)
            }
            
            try:
                
                signature = PaytmChecksum.generateSignature(json.dumps(body), self.merchant_key)
                head = {
                    "tokenType": "CHECKSUM",
                    "signature": signature
                }
                payload = {
                    "head": head,
                    "body": body
                }

                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers={"Content-type": "application/json"}
                )
                
               
                if not response.ok:
                    return f"API request failed with status code: {response.status_code}"
                    
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    return "Error: Invalid JSON response from server"
                if response_data["status"] == "SUCCESS":
                    orders = response_data["orders"]
                    if not orders:
                        return "No refunds found for the given date range."
                    
                        
                    result = f"Refunds List (Count: {response_data['count']})"
                    for order in orders:
                        try:
                            # Convert each field to string and handle None values
                            order_id = str(order['orderId'])
                            refund_id = str(order['refundId'])
                            ref_id = str(order['refId'])
                            txn_amount = str(order['txnAmount'])
                            refund_amount = str(order['refundAmount'])
                            status = str(order['acceptRefundStatus'])
                            refund_time = str(order['acceptRefundTimeStamp'])
                            
                            result += (
                                f"Order ID: {order_id}, "
                                f"Refund ID: {refund_id}, "
                                f"Ref ID: {ref_id}, "
                                f"Txn Amount: {txn_amount}, "
                                f"Refund Amount: {refund_amount}, "
                                f"Status: {status}, "
                                f"Refund Time: {refund_time}\n"
                            )
                        except Exception as e:
                            continue
                    return result
                else:
                    error_msg = str(orders.get("errorMessage", "Unknown error"))
                    return f"Failed to fetch refund list from refund service: {error_msg}"
                    
            except requests.RequestException as e:
                return f"Network error while fetching refund list: {str(e)}"
                
        except Exception as e:
            return f"Error fetching refund list: {str(e)}"
