class DeliverySkill:
    def get_models(self):
        return """
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, cooking, delivering, delivered
    driver_id = db.Column(db.Integer, nullable=True)
"""

    def get_routes(self):
        return """
@main.route('/menu')
def menu():
    products = Product.query.all()
    return render_template('menu.html', products=products)

@main.route('/order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    # Order logic
    return "Order Placed!"
"""