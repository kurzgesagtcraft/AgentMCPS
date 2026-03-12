from typing import Any, Callable, Dict, Optional
from functools import wraps
from fastmcp import Context
import json

class X402PaymentRequired(Exception):
    """Exception raised when payment is required according to x402 protocol."""
    def __init__(self, message: str, requirements: Dict[str, Any]):
        super().__init__(message)
        self.requirements = requirements
        self.code = 402

def with_x402(
    price_amount: str,
    price_currency: str,
    pay_to_address: str,
    chain_id: int = 8453, # Default to Base Mainnet
    description: Optional[str] = None
):
    """
    Decorator to enforce x402 payment for a FastMCP tool.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context if present
            ctx: Optional[Context] = kwargs.get("ctx")
            
            # In a real implementation, we would extract _meta from the JSON-RPC request.
            # FastMCP currently abstracts the raw request, so we might need to 
            # check if the client passed payment info in the context or arguments.
            
            # For the prototype, we check for a 'payment_proof' in kwargs or ctx.info
            payment_proof = kwargs.get("_payment_proof")
            
            if not payment_proof:
                # Construct x402 Payment Requirements
                requirements = {
                    "x402/payment": {
                        "amount": price_amount,
                        "currency": price_currency,
                        "to": pay_to_address,
                        "chainId": chain_id,
                        "description": description or f"Payment for {func.__name__}"
                    }
                }
                # Note: FastMCP might need a custom error handler to return 402 code correctly.
                # For now, we raise a structured exception.
                raise X402PaymentRequired("Payment Required", requirements)
            
            # If payment proof exists, proceed with the tool execution
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def format_x402_error(e: X402PaymentRequired) -> Dict[str, Any]:
    """Formats the exception into a JSON-RPC error response compatible with x402."""
    return {
        "code": e.code,
        "message": str(e),
        "data": {
            "_meta": e.requirements
        }
    }