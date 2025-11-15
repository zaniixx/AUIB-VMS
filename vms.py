"""
Compatibility module for Gunicorn/Docker deployment.
Imports create_app from Backend module.
"""
from Backend import create_app

__all__ = ['create_app']
