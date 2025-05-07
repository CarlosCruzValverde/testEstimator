import os
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from database import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configure database - use DATABASE_URL if available (Railway provides this)
if os.getenv("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
else:
    # Fallback to individual variables for development
    DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOSTNAME')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and migration
db.init_app(app)
migrate = Migrate(app, db)

# Import models after db initialization
from models import *  # This ensures models are registered with SQLAlchemy

# Register blueprints
from auth import bp as auth_bp
from portfolio import bp as portfolio_bp

app.register_blueprint(auth_bp)
app.register_blueprint(portfolio_bp)
app.add_url_rule("/", endpoint="index")

# Custom Jinja2 filter for currency formatting
@app.template_filter('currency')
def currency_format(value):
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

# Register the filter
app.jinja_env.filters['currency'] = currency_format

# Add template helpers
@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime for display"""
    if value is None:
        return "Never"
    return value.strftime('%Y-%m-%d %H:%M:%S')

# Template helpers
from portfolio import (
    get_wire_price,
    get_conduit_price,
    get_supplier_wire_update,
    get_supplier_conduit_update
)

@app.context_processor
def utility_processor():
    """Make these functions available to all templates"""
    return {
        'get_wire_price': get_wire_price,
        'get_conduit_price': get_conduit_price,
        'get_supplier_wire_update': get_supplier_wire_update,
        'get_supplier_conduit_update': get_supplier_conduit_update
    }

@app.teardown_appcontext
def teardown_db(exception):
    db.session.remove()

if __name__ == "__main__":
    with app.app_context():
        app.run(host="0.0.0.0", port=8000)