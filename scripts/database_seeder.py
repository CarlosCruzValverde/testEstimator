import os
from datetime import date
from app import app, db  # Changed from create_app to app
from models import (
    MaterialSupplier, WirePrice, ConduitPrice, 
    ConstructionMaterial, ConstructionPrice,
    Union, UnionPosition, UnionWageRate, 
)

def populate_suppliers():
    """Populate material suppliers - only J & S and The Home Depot"""
    suppliers = [
        "J & S",
        "The Home Depot"
    ]

    for name in suppliers:
        existing = MaterialSupplier.query.filter_by(name=name).first()
        if not existing:
            supplier = MaterialSupplier(name=name)
            db.session.add(supplier)
    
    db.session.commit()
    print("✅ Added material suppliers (J & S and The Home Depot)")

def populate_wire_prices():
    """Populate initial wire prices for J & S and The Home Depot"""
    suppliers = MaterialSupplier.query.all()
    if not suppliers:
        print("⚠️ No suppliers found - run populate_suppliers() first")
        return

    # Wire prices (per foot) - J & S typically has better prices for electrical supplies
    wire_prices = {
        # J & S prices (wholesale electrical supplier)
        "J & S": {
            '10': 0.28,    # 10 AWG
            '8': 0.52,     # 8 AWG
            '6': 0.85,     # 6 AWG
            '4': 1.40,     # 4 AWG
            '3/0': 2.75,   # 3/0 AWG
            '4/0': 3.45,   # 4/0 AWG
            '250 MCM': 4.75,  # 250 MCM
            '350 MCM': 6.20,  # 350 MCM
            '600 MCM': 9.80   # 600 MCM
        },
        # The Home Depot prices (retail)
        "The Home Depot": {
            '10': 0.35,    # 10 AWG
            '8': 0.65,     # 8 AWG
            '6': 1.05,     # 6 AWG
            '4': 1.75,     # 4 AWG
            '3/0': 3.25,   # 3/0 AWG
            '4/0': 4.10,   # 4/0 AWG
            '250 MCM': 5.50,  # 250 MCM
            '350 MCM': 7.25,  # 350 MCM
            '600 MCM': 11.00  # 600 MCM
        }
    }

    for supplier in suppliers:
        supplier_prices = wire_prices.get(supplier.name, {})
        for awg, price in supplier_prices.items():
            existing = WirePrice.query.filter_by(
                supplier_id=supplier.id,
                awg=awg
            ).first()
            
            if not existing:
                wire_price = WirePrice(
                    supplier_id=supplier.id,
                    awg=awg,
                    price_per_foot=price
                )
                db.session.add(wire_price)
    
    db.session.commit()
    print("✅ Added wire prices for J & S and The Home Depot")

def populate_conduit_prices():
    """Populate initial conduit prices for J & S and The Home Depot"""
    suppliers = MaterialSupplier.query.all()
    if not suppliers:
        print("⚠️ No suppliers found - run populate_suppliers() first")
        return

    # Conduit prices (per foot) - J & S has better prices for electrical conduit
    conduit_prices = {
        # J & S prices (wholesale electrical supplier)
        "J & S": {
            '3/4"': 0.38,
            '1"': 0.55,
            '1 1/4"': 0.80,
            '1 1/2"': 0.98,
            '2"': 1.50,
            '3"': 2.40,
            '2" Rigid': 2.75,
            '2 1/2 EMT': 1.85,
            '3" Rigid': 3.95,
            '4" Rigid': 5.45
        },
        # The Home Depot prices (retail)
        "The Home Depot": {
            '3/4"': 0.45,
            '1"': 0.65,
            '1 1/4"': 0.95,
            '1 1/2"': 1.15,
            '2"': 1.75,
            '3"': 2.85,
            '2" Rigid': 3.25,
            '2 1/2 EMT': 2.10,
            '3" Rigid': 4.50,
            '4" Rigid': 6.25
        }
    }

    for supplier in suppliers:
        supplier_prices = conduit_prices.get(supplier.name, {})
        for size, price in supplier_prices.items():
            existing = ConduitPrice.query.filter_by(
                supplier_id=supplier.id,
                size=size
            ).first()
            
            if not existing:
                conduit_price = ConduitPrice(
                    supplier_id=supplier.id,
                    size=size,
                    price_per_foot=price
                )
                db.session.add(conduit_price)
    
    db.session.commit()
    print("✅ Added conduit prices for J & S and The Home Depot")


def populate_construction_materials():
    """Populate construction materials and prices"""
    materials = [
        ("Concrete Pad 5' 1/2'' x 30'' x 5''", 250.00),
        ("Concrete Pad 5' x 7' x 5''", 350.00),
        ("Concrete Footings 24'' x 24'' x 12''", 180.00),
        ("Direct Bury Bollards", 120.00),
        ("Core Drilling Fee", 300.00),
        ("Portable Restroom (30 Days)", 200.00),
        ("Signage", 75.00),
        ("X-Rays", 500.00),
        ("Crane Service (4 Hours)", 1200.00)
    ]

    for name, price in materials:
        existing = ConstructionMaterial.query.filter_by(name=name).first()
        if not existing:
            material = ConstructionMaterial(name=name)
            db.session.add(material)
            db.session.flush()
            
            price_entry = ConstructionPrice(
                material_id=material.id,
                price=price
            )
            db.session.add(price_entry)
    
    db.session.commit()
    print("✅ Added construction materials and prices")

def populate_unions_and_positions():
    """Populate unions, positions, and wage rates"""
    unions = [
        {
            "name": "Local 441",
            "positions": [
                {"name": "Project Manager", "is_apprentice": False},
                {"name": "Foreman", "is_apprentice": False},
                {"name": "Journeyman", "is_apprentice": False},
                {"name": "Apprentice 1st Year", "is_apprentice": True, "year": 1},
                {"name": "Apprentice 2nd Year", "is_apprentice": True, "year": 2},
                {"name": "Apprentice 3rd Year", "is_apprentice": True, "year": 3},
                {"name": "Apprentice 4th Year", "is_apprentice": True, "year": 4},
                {"name": "Apprentice 5th Year", "is_apprentice": True, "year": 5}
            ],
            "wage_rates": {
                "Project Manager": 75.00,
                "Foreman": 65.00,
                "Journeyman": 55.00,
                "Apprentice 1st Year": 25.00,
                "Apprentice 2nd Year": 30.00,
                "Apprentice 3rd Year": 35.00,
                "Apprentice 4th Year": 40.00,
                "Apprentice 5th Year": 45.00
            }
        },
        {
            "name": "Local 11",
            "positions": [
                {"name": "Project Manager", "is_apprentice": False},
                {"name": "Foreman", "is_apprentice": False},
                {"name": "Journeyman", "is_apprentice": False},
                {"name": "Apprentice 1st Year", "is_apprentice": True, "year": 1},
                {"name": "Apprentice 2nd Year", "is_apprentice": True, "year": 2},
                {"name": "Apprentice 3rd Year", "is_apprentice": True, "year": 3},
                {"name": "Apprentice 4th Year", "is_apprentice": True, "year": 4},
                {"name": "Apprentice 5th Year", "is_apprentice": True, "year": 5}
            ],
            "wage_rates": {
                "Project Manager": 80.00,
                "Foreman": 70.00,
                "Journeyman": 60.00,
                "Apprentice 1st Year": 28.00,
                "Apprentice 2nd Year": 33.00,
                "Apprentice 3rd Year": 38.00,
                "Apprentice 4th Year": 43.00,
                "Apprentice 5th Year": 48.00
            }
        }
    ]

    for union_data in unions:
        union = Union.query.filter_by(name=union_data["name"]).first()
        if not union:
            union = Union(name=union_data["name"])
            db.session.add(union)
            db.session.flush()
        
        for position_data in union_data["positions"]:
            position = UnionPosition.query.filter_by(
                name=position_data["name"],
                union_id=union.id
            ).first()
            
            if not position:
                position = UnionPosition(
                    name=position_data["name"],
                    is_apprentice=position_data["is_apprentice"],
                    apprentice_year=position_data.get("year"),
                    union_id=union.id
                )
                db.session.add(position)
                db.session.flush()
            
            rate = UnionWageRate.query.filter_by(
                union_id=union.id,
                position_id=position.id,
                effective_date=date.today()
            ).first()
            
            if not rate and position_data["name"] in union_data["wage_rates"]:
                rate = UnionWageRate(
                    union_id=union.id,
                    position_id=position.id,
                    base_rate=union_data["wage_rates"][position_data["name"]],
                    effective_date=date.today()
                )
                db.session.add(rate)
    
    db.session.commit()
    print("✅ Added unions, positions, and wage rates")


if __name__ == "__main__":
    # Initialize the app context directly using your existing app instance
    with app.app_context():
        print("🚀 Starting database population...")
        populate_suppliers()
        populate_wire_prices()
        populate_conduit_prices()
        populate_construction_materials()
        populate_unions_and_positions()
        print("🎉 Database population completed successfully!")