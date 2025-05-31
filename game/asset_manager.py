import pygame
import os
from typing import Dict, Optional

class AssetManager:
    """Manages loading and caching of game assets"""
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = assets_path
        self.image_cache: Dict[str, pygame.Surface] = {}
        
    def load_image(self, filename: str, scale_size: Optional[tuple] = None) -> Optional[pygame.Surface]:
        """
        Load an image from the assets directory with optional scaling
        
        Args:
            filename: Name of the image file (e.g., "water.png")
            scale_size: Optional tuple (width, height) to scale the image
            
        Returns:
            pygame.Surface or None if loading fails
        """
        cache_key = f"{filename}_{scale_size}" if scale_size else filename
        
        # Return cached image if available
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
            
        # Construct full path
        file_path = os.path.join(self.assets_path, filename)
        
        try:
            # Load the image
            image = pygame.image.load(file_path)
            
            # Convert for better performance
            if image.get_alpha() is not None:
                image = image.convert_alpha()
            else:
                image = image.convert()
            
            # Scale if requested
            if scale_size:
                image = pygame.transform.scale(image, scale_size)
            
            # Cache and return
            self.image_cache[cache_key] = image
            return image
            
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not load image {file_path}: {e}")
            return None
    
    def get_terrain_image(self, terrain_name: str, hex_size: int) -> Optional[pygame.Surface]:
        """
        Get a terrain image scaled to fit a hex of the given size
        
        Args:
            terrain_name: Name of terrain (e.g., "water")
            hex_size: Size of the hex to fit the image to
            
        Returns:
            Scaled pygame.Surface or None if not found
        """
        filename = f"{terrain_name}.png"
        # Scale to roughly fit within hex bounds
        scale_size = (int(hex_size * 1.8), int(hex_size * 1.8))
        return self.load_image(filename, scale_size)
    
    def clear_cache(self):
        """Clear the image cache"""
        self.image_cache.clear()