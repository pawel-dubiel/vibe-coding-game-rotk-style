import pygame
import os
import math

def setup_pygame():
    pygame.init()
    # Create a dummy display surface so we can use convert_alpha()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_base_icon(size, color, outline_color=(30, 30, 30)):
    """Create the base circle with facing indicator"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    radius = size // 2 - 2
    
    # Draw main circle
    pygame.draw.circle(surface, color, (center, center), radius)
    pygame.draw.circle(surface, outline_color, (center, center), radius, 2)
    
    # Draw facing indicator (triangle pointing right/East - 0 degrees)
    # Points: (Right edge, Center), (Right edge - 10, Center - 5), (Right edge - 10, Center + 5)
    # Actually, let's make it a noticeable arrow on the rim
    arrow_len = size // 4
    tip_x = size - 2
    tip_y = center
    
    points = [
        (tip_x, tip_y),
        (tip_x - arrow_len, tip_y - arrow_len // 2),
        (tip_x - arrow_len, tip_y + arrow_len // 2)
    ]
    pygame.draw.polygon(surface, (255, 255, 200), points)
    pygame.draw.polygon(surface, outline_color, points, 1)
    
    return surface

def draw_sword(surface, center_x, center_y, size):
    """Draw a sword icon"""
    color = (220, 220, 220) # Steel
    hilt_color = (139, 69, 19) # Brown
    outline = (0, 0, 0)
    
    length = size * 0.6
    width = size * 0.1
    
    # Blade (pointing right)
    blade_rect = pygame.Rect(center_x - length//4, center_y - width//2, length, width)
    pygame.draw.rect(surface, color, blade_rect)
    pygame.draw.rect(surface, outline, blade_rect, 1)
    
    # Tip (triangle)
    tip_points = [
        (blade_rect.right, blade_rect.top),
        (blade_rect.right + width, center_y),
        (blade_rect.right, blade_rect.bottom)
    ]
    pygame.draw.polygon(surface, color, tip_points)
    pygame.draw.polygon(surface, outline, tip_points, 1)
    
    # Guard (vertical bar)
    guard_h = size * 0.3
    guard_w = size * 0.05
    guard_rect = pygame.Rect(blade_rect.left - guard_w, center_y - guard_h//2, guard_w, guard_h)
    pygame.draw.rect(surface, (200, 200, 0), guard_rect) # Gold guard
    pygame.draw.rect(surface, outline, guard_rect, 1)
    
    # Hilt
    hilt_len = size * 0.15
    hilt_rect = pygame.Rect(guard_rect.left - hilt_len, center_y - width//2, hilt_len, width)
    pygame.draw.rect(surface, hilt_color, hilt_rect)
    pygame.draw.rect(surface, outline, hilt_rect, 1)
    
    # Pommel
    pygame.draw.circle(surface, (200, 200, 0), (int(hilt_rect.left), center_y), int(width))
    pygame.draw.circle(surface, outline, (int(hilt_rect.left), center_y), int(width), 1)

def draw_bow(surface, center_x, center_y, size):
    """Draw a bow icon"""
    wood_color = (139, 69, 19)
    string_color = (200, 200, 200)
    
    radius = size * 0.35
    rect = pygame.Rect(center_x - radius, center_y - radius, radius*2, radius*2)
    
    # Draw wood arc (right side open)
    # Arc draws counter-clockwise. To face right, we want the curve on the left.
    # Start angle 270 (top), stop 90 (bottom)? No, radians.
    # 3pi/2 to pi/2.
    pygame.draw.arc(surface, wood_color, rect, math.pi/2, 3*math.pi/2, 3)
    
    # Draw string (vertical line on right)
    # Actually, Bow usually faces the target. If target is East (Right), 
    # the curve is on the Right (D shape) or Left (C shape)?
    # Archer holds bow: Curve is away from archer. String is near face.
    # So if facing right, curve is on right. String is on left.
    # Let's draw ')' shape.
    
    # Curve on right
    # Angle -pi/2 to pi/2
    rect.x -= radius/2 # Shift left slightly
    pygame.draw.arc(surface, wood_color, rect, -math.pi/2, math.pi/2, 4)
    
    # String
    string_x = rect.centerx 
    # Points on arc at -90 and 90
    top_y = rect.centery - radius
    bot_y = rect.centery + radius
    pygame.draw.line(surface, string_color, (string_x, top_y), (string_x, bot_y), 1)
    
    # Arrow
    arrow_len = size * 0.5
    pygame.draw.line(surface, (200, 200, 200), (center_x - arrow_len//2, center_y), (center_x + arrow_len//2, center_y), 2)
    # Arrowhead
    head_x = center_x + arrow_len//2
    pygame.draw.polygon(surface, (150, 150, 150), [
        (head_x, center_y),
        (head_x - 5, center_y - 3),
        (head_x - 5, center_y + 3)
    ])

def draw_lance(surface, center_x, center_y, size):
    """Draw a cavalry lance/pennant"""
    pole_color = (160, 82, 45)
    tip_color = (192, 192, 192)
    flag_color = (255, 0, 0) # Red pennant
    
    length = size * 0.7
    
    # Lance pole
    start = (center_x - length//2, center_y)
    end = (center_x + length//2, center_y)
    pygame.draw.line(surface, pole_color, start, end, 3)
    
    # Tip
    pygame.draw.polygon(surface, tip_color, [
        end,
        (end[0] - 10, end[1] - 3),
        (end[0] - 10, end[1] + 3)
    ])
    
    # Pennant (flag)
    flag_start_x = end[0] - 15
    pygame.draw.polygon(surface, flag_color, [
        (flag_start_x, center_y),
        (flag_start_x - 15, center_y - 10),
        (flag_start_x, center_y - 10)
    ])

def draw_staff(surface, center_x, center_y, size):
    """Draw a mage staff"""
    wood_color = (100, 50, 0)
    orb_color = (100, 255, 255) # Cyan glow
    
    length = size * 0.6
    
    # Staff
    start = (center_x - length//2, center_y)
    end = (center_x + length//2, center_y)
    pygame.draw.line(surface, wood_color, start, end, 3)
    
    # Orb at end
    pygame.draw.circle(surface, orb_color, (int(end[0]), int(end[1])), 6)
    # Glow ring
    pygame.draw.circle(surface, orb_color, (int(end[0]), int(end[1])), 9, 1)
    
    # Sparkles
    import random
    for _ in range(4):
        sx = end[0] + random.randint(-8, 8)
        sy = end[1] + random.randint(-8, 8)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 1)

def generate_icons():
    setup_pygame()
    
    base_path = "assets/units"
    ensure_dir(base_path)
    
    size = 64
    
    # Define unit types and their drawing functions
    units = {
        "warrior": draw_sword,
        "archer": draw_bow,
        "cavalry": draw_lance,
        "mage": draw_staff
    }
    
    # Define player colors (Backgrounds)
    # Player 1: Blue-ish, Player 2: Red-ish
    # We will generate "p1_warrior.png", "p2_warrior.png", etc.
    players = {
        "p1": (60, 60, 180), # Blue
        "p2": (180, 60, 60)  # Red
    }
    
    for p_name, p_color in players.items():
        for u_name, draw_func in units.items():
            # Create base
            icon = create_base_icon(size, p_color)
            
            # Draw symbol
            center = size // 2
            draw_func(icon, center, center, size)
            
            # Save base icon (Facing East/Right is default 0 degrees)
            filename = f"{p_name}_{u_name}.png"
            full_path = os.path.join(base_path, filename)
            pygame.image.save(icon, full_path)
            print(f"Generated {full_path}")

if __name__ == "__main__":
    generate_icons()
