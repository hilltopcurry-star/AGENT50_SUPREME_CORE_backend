class PaymentSkill:
    def get_config(self):
        return """
import stripe
import os
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
"""

    def get_checkout_logic(self):
        return """
@main.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Delivery Order'},
                'unit_amount': 2000,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('main.success', _external=True),
        cancel_url=url_for('main.cancel', _external=True),
    )
    return redirect(session.url, code=303)
"""