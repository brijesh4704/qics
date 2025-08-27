from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use MySQL by setting env var DATABASE_URL, else default to SQLite file
# Examples:
#   mysql+pymysql://user:password@localhost:3306/qics
#   postgresql+psycopg://user:password@localhost:5432/qics
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qics.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
