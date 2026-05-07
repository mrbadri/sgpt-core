"""Database base — re-exports SQLModel as the project's Base for backward compatibility."""

from sqlmodel import SQLModel

Base = SQLModel
