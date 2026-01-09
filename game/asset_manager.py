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
            
            # Scale if requested using high-quality smoothscale
            if scale_size:
                try:
                    # Use smoothscale for better quality (bilinear filtering)
                    image = pygame.transform.smoothscale(image, scale_size)
                except pygame.error:
                    # Fallback to regular scale if smoothscale fails
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
        # Calculate proper hex dimensions
        import math
        hex_width = int(math.sqrt(3) * hex_size)
        hex_height = int(2 * hex_size)
        
        # Scale to fit properly within hex boundaries 
        # Use the inscribed circle diameter (hex_size * 2 * 0.866) for best fit
        inscribed_diameter = int(hex_size * 1.732)  # sqrt(3) ≈ 1.732
        # Scale assets aggressively with zoom - fill entire hex
        target_size = max(16, inscribed_diameter)  # 100% of inscribed circle, min 16px
        scale_size = (target_size, target_size)
        
        return self.load_image(filename, scale_size)
    
    def clear_cache(self):
        """Clear the image cache"""
        self.image_cache.clear()

    def get_unit_icon(self, unit_class_name: str, player_id: int, facing_angle: float, size: int) -> Optional[pygame.Surface]:
        """
        Get a rotated unit icon
        
        Args:
            unit_class_name: e.g. "warrior", "archer"
            player_id: 1 or 2
            facing_angle: Angle in degrees (0=East, clockwise)
            size: Target size in pixels
            
        Returns:
            Rotated pygame.Surface
        """
        p_prefix = "p1" if player_id == 1 else "p2"
        filename = f"{p_prefix}_{unit_class_name.lower()}.png"
        path = os.path.join(self.assets_path, "units", filename)
        
        # Cache key includes rotation and size
        cache_key = f"unit_{filename}_{size}_{facing_angle}"
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
            
        try:
            # Load base image (unscaled) if not in cache
            base_key = f"base_{filename}"
            if base_key in self.image_cache:
                image = self.image_cache[base_key]
            else:
                image = pygame.image.load(path).convert_alpha()
                self.image_cache[base_key] = image
            
            # Scale first
            scaled = pygame.transform.smoothscale(image, (size, size))
            
            # Rotate
            # Pygame rotates CCW, our angles are CW. So use negative angle.
            rotated = pygame.transform.rotate(scaled, -facing_angle)
            
            # Cache and return
            self.image_cache[cache_key] = rotated
            return rotated
            
        except (pygame.error, FileNotFoundError):
            # Fallback if icon not generated
            return None