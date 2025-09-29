"""
Configuration package for Automotive Price Monitor
"""
from .settings import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from .database import DatabaseManager
from .scrapy_settings import SCRAPY_SETTINGS

__all__ = [
    'Config',
    'DevelopmentConfig', 
    'ProductionConfig',
    'TestingConfig',
    'DatabaseManager',
    'SCRAPY_SETTINGS'
]
