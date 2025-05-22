import sys
import os
import logging
from typing import Optional, List

from mcp.server.fastmcp import FastMCP
from services.payment_service import PaymentService
from services.refund_service import RefundService
from services.order_list_service import OrderListService
from config.settings import settings
from utils.models import PaymentLink, Transaction
from utils.system_utils import DateService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("paytm-mcp-server")

# Initialize services
try:
    payment_service = PaymentService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
    refund_service = RefundService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
    order_list_service = OrderListService(settings.PAYTM_KEY_SECRET,settings.PAYTM_MID)
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    sys.exit(1)

def main():
    mcp.run()

# Tool: Create Payment Link
@mcp.tool()
def create_payment_link(
    recipient_name: str,
    purpose: str,
    customer_email: str = None,
    customer_mobile: str = None,
    amount: str = None,
) -> str:
    """
    Create a new payment link for receiving payments.

    This operation generates a unique payment link that can be shared with customers
    for accepting payments. The link can be customized with recipient details,
    purpose, customer details and amount.

    Required Parameters:
        recipient_name (str): Name of the person or entity receiving the payment
        purpose (str): Description or reason for the payment
        customer_email (str): Email address of the customer
        customer_mobile (str): Mobile number of the customer
        Either customer_email or customer_mobile must be provided if else please ask from the user

    Optional Parameters:
        amount (float): Fixed amount for the payment

    Note:
        - Amount can be left optional for customer to decide
        - Generated link will be valid according to system's expiry settings
        - Please ask all the required fields from the user don't assume any fields
    
    IMPORTANT NOTE:
        - if user is not providing customer_email or customer_mobile, please ask for the same don't call any tool before asking for the same
        """
    
    try:
        return payment_service.create_payment_link(
            recipient_name=recipient_name,
            purpose=purpose,
            customer_email=customer_email,
            customer_mobile=customer_mobile,
            amount=amount
        )
    except Exception as e:
        logger.error(f"Failed to create payment link: {str(e)}")
        return str(e)

# Tool: Fetch All Payment Links
@mcp.tool()
def fetch_payment_links() -> str:
    """
    Retrieve all payment links created by the merchant.

    This operation returns a comprehensive list of all payment links created,
    including both active and expired links. Each link entry contains details
    such as:
        - Link ID
        - Link Name
        - Short URL
        - Status
        - Creation Date
        - Expiry Date

    Returns:
        List[PaymentLink]: A list of PaymentLink objects containing link details
        str: Error message in case of failure
    """
    try:
        links: List[PaymentLink] = payment_service.fetch_payment_links()
        if not links:
            return "No payment links found."
        return links
    except Exception as e:
        logger.error(f"Failed to fetch payment links: {str(e)}")
        return str(e)

# Tool: Fetch Transactions for a Specific Link
@mcp.tool()
def fetch_transactions_for_link(link_id: str) -> str:
    """
    Retrieve all transactions associated with a specific payment link.

    This operation provides detailed transaction history for a given payment link,
    including successful and failed transactions.

    Parameters:
        link_id (str): Unique identifier of the payment link

    Returns:
        List[Transaction]: List of transactions containing details such as:
            - Transaction ID
            - Order ID
            - Amount
            - Status
            - Completion Time
            - Customer Contact Information
        str: Error message in case of failure
    """
    try:
        transactions: List[Transaction] = payment_service.fetch_transactions_for_link(link_id)
        if not transactions:
            return f"No transactions found for link ID {link_id}."
    
        return transactions
    except Exception as e:
        logger.error(f"Failed to fetch transactions: {str(e)}")
        return str(e)

# Tool: Initiate Refund
@mcp.tool()
def initiate_refund(order_id: str, refund_reference_id: str, txn_id: str, refund_amount: float) -> str:
    """
    Initiate a refund for a specific transaction.

    This operation allows the merchant to initiate a refund for a previously
    completed transaction. The refund can be initiated for a specific amount,
    and the refund reference ID will be used to track the refund request.

    IMPORTANT NOTE:
        - if user is not providing order_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing txn_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing refund_reference_id, please ask for the same don't call any tool before asking for the same
        - if user is not providing refund_amount, please ask for the same don't call any tool before asking for the same
        

    Parameters:
        order_id (str): Original order ID of the transaction
        refund_reference_id (str): Unique refund reference ID (max 50 chars)
        txn_id (str): Original Paytm transaction ID
        refund_amount (float): Amount to be refunded (must be <= original transaction amount)

    Returns:
        str: Response message indicating success or failure of refund initiation along with the Refund Status, Message and Code of the refund
    """
    try:
        response =  refund_service.initiate_refund(order_id, refund_reference_id, txn_id, refund_amount)
        return response

    except Exception as e:
        logger.error(f"Failed to initiate refund: {str(e)}")
        return str(e)


# Tool: Check Refund Status
@mcp.tool()
def check_refund_status(order_id: str, refund_reference_id: str) -> str:
    """
    Check the status of a previously initiated refund.

    This operation allows the merchant to check the status of a previously
    initiated refund. The refund status can be checked for a specific order
    and refund reference ID.

    Parameters:
    order_id (str): Original order ID of the transaction
    refund_reference_id (str): Refund reference ID used during refund initiation

    Returns:
    str: Current status of the refund request
    str: Error message in case of failure
    """
    try:
        return refund_service.check_refund_status(order_id, refund_reference_id)
    except Exception as e:
        logger.error(f"Failed to check refund status: {str(e)}")
        return str(e)
    


    
# Tool: Fetch Refund List
@mcp.tool()
def fetch_refund_list(
    is_sort: bool = True, 
    page_num: int = 1, 
    page_size: int = 50, 
    time_range: str = "7",
    start_date: str = None,
    end_date: str = None
    ) -> str:
    """
    Fetch the list of refunds for the merchant within a date range of 30 days and never assume start_date and end_date.
    
    This operation allows the merchant to retrieve a list of refunds that have been
    initiated within a specified date range. The list can be sorted by date and
    paginated to handle large datasets.

    Parameters:
    start_date (str): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
    end_date (str): End date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
    is_sort (bool): Whether to sort the list by date
    page_num (int): The page number to retrieve
    page_size (int): The number of refunds per page
    time_range (str): Time range in days (default: 7)

    Returns:
    str: The list of refunds along with the Order ID, Refund ID, Ref ID, Txn Amount, Refund Amount, Refund Time of the refund
    str: Error message in case of failure
    """
    try:
        if not (start_date and end_date):
            start_date = DateService.get_date_by_time_range(time_range)
            end_date = DateService.get_current_date()
        return refund_service.fetch_refund_list(start_date, end_date, is_sort, page_num, page_size)
    except Exception as e:
        logger.error(f"Failed to fetch refund list from paytm mcp: {str(e)}")
        return str(e)
    

# Tool: Fetch Order List
@mcp.tool()
def fetch_order_list(
    order_search_type: str = "TRANSACTION",
    order_search_status: str = "SUCCESS",
    page_number: int = 1,
    page_size: int = 50,
    from_date: str = None,
    to_date: str = None,
    time_range: str = "7",
) -> str:
    """
    Fetch the list of orders from Paytm within a date range of 30 days and never assume from_date and to_date.

    This operation allows the merchant to retrieve a list of orders that have been
    created within a specified date range. The list can be filtered by order_search_status, order_search_type and
    paginated to handle large datasets.

    Parameters:
        from_date (str): Start date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
        to_date (str): End date in ISO format (YYYY-MM-DDTHH:mm:ss+HH:mm) don't generate any random date
        order_search_type (str): Type of order search (default: TRANSACTION)
        order_search_status (str, optional): Status of orders to search for
        page_number (int): Page number for pagination (default: 1)
        page_size (int): Number of records per page (default: 50)
        time_range (str): Time range in days (default: 7)
        
        - from_date and to_date or time_range SHOULD NOT be more than 30 days apart.Don't accept more than 30 days request from the user   

    Returns:
        str: The list of orders with their details
        str: Error message in case of failure
    """
    if not (from_date and to_date):
        from_date = DateService.get_date_by_time_range(time_range)
        to_date = DateService.get_current_date()
    try:
        return order_list_service.fetch_order_list(
            from_date=from_date,
            to_date=to_date,
            order_search_type=order_search_type,
            order_search_status=order_search_status,
            page_number=page_number,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to fetch order list: {str(e)}")
        return str(e)
    


if __name__ == "__main__":
    main()
