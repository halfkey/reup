from typing import Dict, List, Any
from .validators import Validator
from .exceptions import ValidationError

class ProfileValidator:
    """Validates profile data structure and content."""
    
    @staticmethod
    def validate_profile(data: Dict[str, Any]) -> None:
        """Validate complete profile data."""
        if not isinstance(data, dict):
            raise ValidationError("Profile data must be a dictionary")
            
        # Validate required fields
        required = ['products', 'metadata']
        missing = [f for f in required if f not in data]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
            
        # Validate metadata
        ProfileValidator.validate_metadata(data['metadata'])
        
        # Validate products
        ProfileValidator.validate_products(data['products'])
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> None:
        """Validate profile metadata."""
        required = ['name', 'last_modified', 'version']
        missing = [f for f in required if f not in metadata]
        if missing:
            raise ValidationError(f"Missing metadata fields: {', '.join(missing)}")
            
        # Validate name
        Validator.validate_profile_name(metadata['name'])
        
        # Validate version format
        if not isinstance(metadata['version'], str):
            raise ValidationError("Version must be a string")
    
    @staticmethod
    def validate_products(products: List[Dict[str, Any]]) -> None:
        """Validate product list."""
        if not isinstance(products, list):
            raise ValidationError("Products must be a list")
            
        if not products:
            raise ValidationError("Profile must contain at least one product")
            
        for product in products:
            ProfileValidator.validate_product(product)
    
    @staticmethod
    def validate_product(product: Dict[str, Any]) -> None:
        """Validate individual product data."""
        required = ['url']
        missing = [f for f in required if f not in product]
        if missing:
            raise ValidationError(f"Missing product fields: {', '.join(missing)}")
            
        # Validate URL
        Validator.validate_url(product['url']) 