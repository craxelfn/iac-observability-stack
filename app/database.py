"""
Database configuration and connection management.
Uses SQLAlchemy with connection pooling for PostgreSQL.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Text, DateTime, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger("masterproject.database")

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "masterprojectdb")
DB_USER = os.getenv("DB_USER", "dbadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Max additional connections when pool is full
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ============================================================================
# Product Model
# ============================================================================
class Product(Base):
    """Product model for the masterproject database."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_name_category', 'name', 'category'),
        Index('idx_price', 'price'),
    )
    
    def to_dict(self):
        """Convert product to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": float(self.price) if self.price else 0.0,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# Database Utilities
# ============================================================================

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def check_db_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


@contextmanager
def get_db() -> Session:
    """
    Database session context manager.
    
    Usage:
        with get_db() as db:
            products = db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get database session (for FastAPI dependency injection).
    
    Usage:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db_session)):
            return db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Query Helpers
# ============================================================================

def get_products_by_category(category: str = None, limit: int = 100, offset: int = 0):
    """Get products by category with pagination. If category is None, get all products."""
    with get_db() as db:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        products = query.limit(limit).offset(offset).all()
        return [p.to_dict() for p in products]


def get_product_by_id(product_id: int):
    """Get single product by ID."""
    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        return product.to_dict() if product else None


def count_products_by_category(category: str = None):
    """Count total products, optionally filtered by category."""
    with get_db() as db:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        return query.count()
