# wsgi.py
from app import app, db
# Explicitly import ALL models
from models import User, Project, CostEstimation, EstimationEntry, MiscEquipmentEstimation, MiscEquipmentEntry, LaborCostEstimation, LaborCostEntry, ProjectSummary  # [all your models]

# This ensures models are loaded before CLI commands
@app.cli.command("init-db")
def init_db():
    """Initialize or migrate the database."""
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run()