"""
Define here the models for your scraped items
"""
import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Compose
from w3lib.html import remove_tags
import re


def clean_text(value):
    """Clean text content"""
    if not value:
        return value
    # Remove extra whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', value.strip())
    return cleaned


def clean_price(value):
    """Clean and extract price from text"""
    if not value:
        return None
    
    # Remove non-numeric characters except decimals
    price_text = re.sub(r'[^\d.,]', '', str(value))
    
    # Handle Persian/Arabic numerals
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    english_digits = '0123456789'
    
    # Convert Persian/Arabic to English digits
    for i, digit in enumerate(persian_digits):
        price_text = price_text.replace(digit, english_digits[i])
    for i, digit in enumerate(arabic_digits):
        price_text = price_text.replace(digit, english_digits[i])
    
    # Remove thousand separators and convert to float
    if ',' in price_text:
        price_text = price_text.replace(',', '')
    
    try:
        return float(price_text) if price_text else None
    except (ValueError, TypeError):
        return None


def clean_url(value):
    """Clean and normalize URL"""
    if not value:
        return value
    
    url = value.strip()
    if not url.startswith(('http://', 'https://')):
        return None
    return url


class AutomotiveProductItem(scrapy.Item):
    """Item for automotive product data"""
    
    # Product identification
    name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    sku = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    # Pricing information
    price = scrapy.Field(
        input_processor=MapCompose(clean_price),
        output_processor=TakeFirst()
    )
    original_price_text = scrapy.Field(
        input_processor=MapCompose(remove_tags, str.strip),
        output_processor=TakeFirst()
    )
    currency = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    # Product details
    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    category = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    brand = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    
    # Availability
    availability = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst()
    )
    in_stock = scrapy.Field(
        input_processor=MapCompose(bool),
        output_processor=TakeFirst()
    )
    
    # Media
    image_urls = scrapy.Field()
    images = scrapy.Field()
    main_image_url = scrapy.Field(
        input_processor=MapCompose(clean_url),
        output_processor=TakeFirst()
    )
    
    # Source information
    source_url = scrapy.Field(
        input_processor=MapCompose(clean_url),
        output_processor=TakeFirst()
    )
    site_name = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    # Scraping metadata
    scraped_at = scrapy.Field()
    spider_name = scrapy.Field()
    
    # Additional fields
    specifications = scrapy.Field()  # Dictionary of specs
    tags = scrapy.Field()  # List of tags/keywords
    rating = scrapy.Field(
        input_processor=MapCompose(float),
        output_processor=TakeFirst()
    )
    review_count = scrapy.Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )


class PriceHistoryItem(scrapy.Item):
    """Item for price history tracking"""
    
    product_name = scrapy.Field()
    product_sku = scrapy.Field()
    site_name = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    availability = scrapy.Field()
    source_url = scrapy.Field()
    scraped_at = scrapy.Field()
