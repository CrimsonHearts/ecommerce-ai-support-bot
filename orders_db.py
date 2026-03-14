"""
Simulated order database for demo purposes.
In production, this connects to Shopify, WooCommerce, or your OMS.
"""

ORDERS = {
    "ORD-2024-001": {
        "customer_email": "sarah@example.com",
        "items": ["Wireless Headphones Pro", "USB-C Cable"],
        "total": 89.99,
        "status": "delivered",
        "tracking": "1Z999AA1234567890",
        "carrier": "UPS",
        "order_date": "2024-03-01",
        "delivery_date": "2024-03-05"
    },
    "ORD-2024-002": {
        "customer_email": "mike@example.com", 
        "items": ["Mechanical Keyboard RGB"],
        "total": 149.50,
        "status": "shipped",
        "tracking": "9400111899223456789012",
        "carrier": "USPS",
        "order_date": "2024-03-10",
        "estimated_delivery": "2024-03-15"
    },
    "ORD-2024-003": {
        "customer_email": "jessica@example.com",
        "items": ["4K Webcam", "Ring Light", "Mic Stand"],
        "total": 245.00,
        "status": "processing",
        "tracking": None,
        "carrier": None,
        "order_date": "2024-03-12",
        "estimated_ship": "2024-03-14"
    },
    "ORD-2024-004": {
        "customer_email": "david@example.com",
        "items": ["Smart Watch Series 5"],
        "total": 299.99,
        "status": "out_for_delivery",
        "tracking": "1Z888BB9876543210",
        "carrier": "UPS",
        "order_date": "2024-03-08",
        "estimated_delivery": "2024-03-13"
    }
}

EMAIL_TO_ORDER = {order["customer_email"]: oid for oid, order in ORDERS.items()}


def lookup_order(query: str) -> dict:
    """
    Look up an order by ID or email.
    Returns order dict or None if not found.
    """
    query = query.strip().upper()
    
    # Direct order ID lookup
    if query in ORDERS:
        return {"found": True, "order_id": query, **ORDERS[query]}
    
    # Try with ORD- prefix if not provided
    if not query.startswith("ORD-"):
        order_id = f"ORD-{query}"
        if order_id in ORDERS:
            return {"found": True, "order_id": order_id, **ORDERS[order_id]}
    
    # Email lookup (case insensitive)
    query_lower = query.lower()
    if query_lower in EMAIL_TO_ORDER:
        oid = EMAIL_TO_ORDER[query_lower]
        return {"found": True, "order_id": oid, **ORDERS[oid]}
    
    return {"found": False}


def get_status_message(order: dict) -> str:
    """Generate a human-friendly status message."""
    status = order["status"]
    items = ", ".join(order["items"])
    
    if status == "delivered":
        return f"Delivered on {order['delivery_date']}. Your {items} arrived successfully!"
    elif status == "out_for_delivery":
        return f"Out for delivery today! Your {items} will arrive by 8 PM. Tracking: {order['carrier']} {order['tracking']}"
    elif status == "shipped":
        return f"Shipped! Your {items} is on its way, arriving {order['estimated_delivery']}. Tracking: {order['carrier']} {order['tracking']}"
    elif status == "processing":
        return f"Processing. Your {items} will ship by {order['estimated_ship']}. We'll email tracking once it ships."
    else:
        return f"Status: {status}. Items: {items}"
