"""
Seed database with sample product data.
Run this script after database is created to populate with 50,000 products.
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Product, Base, SessionLocal

# Product categories
CATEGORIES = [
    "electronics", "clothing", "books", "food", "toys",
    "furniture", "sports", "beauty", "automotive", "garden"
]

# Product name prefixes by category
PRODUCT_NAMES = {
    "electronics": ["Smartphone", "Laptop", "Tablet", "Headphones", "Monitor", "Keyboard", "Mouse", "Camera"],
    "clothing": ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes", "Hat", "Sweater", "Shorts"],
    "books": ["Novel", "Textbook", "Comic", "Magazine", "Guide", "Dictionary", "Biography", "Cookbook"],
    "food": ["Snack", "Beverage", "Frozen Meal", "Cereal", "Pasta", "Sauce", "Spices", "Candy"],
    "toys": ["Action Figure", "Board Game", "Puzzle", "Doll", "Ball", "Car", "Lego Set", "Plushie"],
    "furniture": ["Chair", "Table", "Desk", "Bed", "Sofa", "Cabinet", "Shelf", "Lamp"],
    "sports": ["Ball", "Racket", "Gloves", "Shoes", "Weights", "Yoga Mat", "Helmet", "Bike"],
    "beauty": ["Shampoo", "Lotion", "Makeup", "Perfume", "Cream", "Soap", "Brush", "Nail Polish"],
    "automotive": ["Oil", "Filter", "Tire", "Battery", "Cleaner", "Wax", "Tools", "Mat"],
    "garden": ["Shovel", "Seeds", "Pot", "Fertilizer", "Hose", "Gloves", "Rake", "Trimmer"]
}

def generate_products(count=50000, batch_size=1000):
    """Generate and insert product data in batches."""
    
    print(f"Generating {count} products...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    start_date = datetime.now() - timedelta(days=365)  # Products from last year
    total_inserted = 0
    
    try:
        for batch_num in range(0, count, batch_size):
            products = []
            
            for i in range(batch_size):
                if total_inserted >= count:
                    break
                    
                category = random.choice(CATEGORIES)
                name_base = random.choice(PRODUCT_NAMES[category])
                
                # Create unique product name
                product = Product(
                    name=f"{name_base} {random.choice(['Pro', 'Plus', 'Max', 'Elite', 'Premium', 'Ultra'])} {random.randint(1, 999)}",
                    category=category,
                    price=round(random.uniform(9.99, 999.99), 2),
                    description=f"High-quality {name_base.lower()} perfect for {category} enthusiasts. "
                               f"Features advanced technology and premium materials.",
                    created_at=start_date + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
                )
                
                products.append(product)
                total_inserted += 1
            
            # Batch insert
            if products:
                session.bulk_save_objects(products)
                session.commit()
                print(f"Inserted {total_inserted}/{count} products...")
        
        print(f"\n✅ Successfully seeded {total_inserted} products!")
        
        # Print statistics
        print("\nDatabase Statistics:")
        for category in CATEGORIES:
            count = session.query(Product).filter(Product.category == category).count()
            print(f"  {category}: {count:,} products")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed database with product data")
    parser.add_argument("--count", type=int, default=50000, help="Number of products to generate (default: 50000)")
    parser.add_argument("--batch", type=int, default=1000, help="Batch size for inserts (default: 1000)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MasterProject Database Seeder")
    print("=" * 60)
    print(f"\nTarget: {args.count:,} products")
    print(f"Batch size: {args.batch:,}")
    print(f"Categories: {', '.join(CATEGORIES)}\n")
    
    confirm = input("Proceed with seeding? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        generate_products(count=args.count, batch_size=args.batch)
    else:
        print("Seeding cancelled.")
