#!/usr/bin/env python3

import os
from datetime import date
from app import app, db  # This imports from app.py
from models import (
    MaterialSupplier, WirePrice, ConduitPrice, 
    ConstructionMaterial, ConstructionPrice,
    Union, UnionPosition, UnionWageRate, 
)

# Add this right after your imports
print("🐍 Python path:")
import sys
print("\n".join(sys.path))

print(f"Current working directory: {os.getcwd()}")
print(f"Script directory contents: {os.listdir('scripts')}")

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
            '10': 130,    # 10 AWG
            '8': 300,     # 8 AWG
            '6': 400,     # 6 AWG
            '4': 750,     # 4 AWG
            '3/0': 4.80,   # 3/0 AWG
            '4/0': 5.50,   # 4/0 AWG
            '250 MCM': 7.50,  # 250 MCM
            '350 MCM': 11,  # 350 MCM
            '600 MCM': 21   # 600 MCM
        },
        # The Home Depot prices (retail)
        "The Home Depot": {
            '10': 186,    # 10 AWG
            '8': 369,     # 8 AWG
            '6': 565,     # 6 AWG
            '4': 0,     # 4 AWG
            '3/0': 6.58,   # 3/0 AWG
            '4/0': 4.10,   # 4/0 AWG
            '250 MCM': 0,  # 250 MCM
            '350 MCM': 9.84,  # 350 MCM
            '600 MCM': 0  # 600 MCM
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
            '3/4"': 10,
            '1"': 17,
            '1 1/4"': 28,
            '1 1/2"': 38,
            '2"': 42,
            '3"': 95,
            '2" Rigid': 75,
            '2 1/2 EMT': 48,
            '3" Rigid': 160,
            '4" Rigid': 210
        },
        # The Home Depot prices (retail)
        "The Home Depot": {
            '3/4"': 11.26,
            '1"': 19.48,
            '1 1/4"': 32,
            '1 1/2"': 37.80,
            '2"': 44.88,
            '3"': 98,
            '2" Rigid': 78,
            '2 1/2 EMT': 50,
            '3" Rigid': 164,
            '4" Rigid': 220
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
        ("Concrete Pad 5' 1/2'' x 30'' x 5''", 1200.00),
        ("Concrete Pad 5' x 7' x 5''", 1500.00),
        ("Concrete Footings 24'' x 24'' x 12''", 700.00),
        ("Direct Bury Bollards", 700.00),
        ("Core Drilling Fee", 650.00),
        ("Portable Restroom (30 Days)", 500.00),
        ("Signage", 500.00),
        ("X-Rays", 2500.00),
        ("Crane Service (4 Hours)", 1500.00)
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
                "Project Manager": 50.00,
                "Foreman": 93.00,
                "Journeyman": 86.00,
                "Apprentice 1st Year": 35.00,
                "Apprentice 2nd Year": 42.00,
                "Apprentice 3rd Year": 48.00,
                "Apprentice 4th Year": 55.00,
                "Apprentice 5th Year": 65.00
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
                "Project Manager": 50.00,
                "Foreman": 110.00,
                "Journeyman": 105.00,
                "Apprentice 1st Year": 48.00,
                "Apprentice 2nd Year": 55.00,
                "Apprentice 3rd Year": 61.00,
                "Apprentice 4th Year": 68.00,
                "Apprentice 5th Year": 78.00
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