import stripe
from fastapi import HTTPException

# Placeholder Key (Baad mein .env se aayega)
stripe.api_key = "sk_test_placeholder"

class StripeService:
    async def create_payment_intent(self, amount: int, currency: str = "usd"):
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=["card"]
            )
            return {"client_secret": intent.client_secret, "id": intent.id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

stripe_service = StripeService()