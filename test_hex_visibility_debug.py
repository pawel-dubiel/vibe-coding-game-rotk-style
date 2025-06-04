"""Debug script to test hex visibility issues when zooming."""
import pygame
import sys
from game.game_state import GameState
from game.input_handler import InputHandler
from game.renderer import Renderer

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Hex Visibility Debug")
    clock = pygame.time.Clock()
    
    # Create game state with a reasonable board size
    config = {
        'board_size': (20, 15),
        'knights': 0,
        'castles': 0
    }
    game_state = GameState(config)
    input_handler = InputHandler()
    renderer = Renderer(screen)
    
    # Initialize animation manager
    from game.state.animation_coordinator import AnimationCoordinator
    game_state.animation_manager = AnimationCoordinator()
    
    # Position camera to see bottom-right area
    game_state.camera_manager.set_camera_position(300, 200)
    
    running = True
    zoom_levels = [0.5, 1.0, 1.5, 2.0, 2.5]
    current_zoom_idx = 1
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    # Zoom in
                    if current_zoom_idx < len(zoom_levels) - 1:
                        current_zoom_idx += 1
                        game_state.camera_manager.set_zoom(zoom_levels[current_zoom_idx])
                        input_handler.update_zoom(game_state)
                        print(f"Zoom level: {zoom_levels[current_zoom_idx]}")
                elif event.key == pygame.K_DOWN:
                    # Zoom out
                    if current_zoom_idx > 0:
                        current_zoom_idx -= 1
                        game_state.camera_manager.set_zoom(zoom_levels[current_zoom_idx])
                        input_handler.update_zoom(game_state)
                        print(f"Zoom level: {zoom_levels[current_zoom_idx]}")
                elif event.key == pygame.K_LEFT:
                    game_state.camera_manager.move_camera(-50, 0)
                elif event.key == pygame.K_RIGHT:
                    game_state.camera_manager.move_camera(50, 0)
                elif event.key == pygame.K_w:
                    game_state.camera_manager.move_camera(0, -50)
                elif event.key == pygame.K_s:
                    game_state.camera_manager.move_camera(0, 50)
                elif event.key == pygame.K_c:
                    # Toggle coordinate display
                    game_state.show_coordinates = not getattr(game_state, 'show_coordinates', False)
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Render game state
        renderer.render(game_state)
        
        # Display debug info
        font = pygame.font.Font(None, 36)
        zoom_text = font.render(f"Zoom: {zoom_levels[current_zoom_idx]}x", True, (255, 255, 255))
        screen.blit(zoom_text, (10, 10))
        
        cam_text = font.render(f"Camera: ({int(game_state.camera_manager.camera_x)}, {int(game_state.camera_manager.camera_y)})", True, (255, 255, 255))
        screen.blit(cam_text, (10, 50))
        
        instructions = [
            "UP/DOWN: Zoom in/out",
            "Arrow keys: Move camera",
            "C: Toggle coordinates",
            "ESC: Quit"
        ]
        y = 100
        small_font = pygame.font.Font(None, 24)
        for inst in instructions:
            text = small_font.render(inst, True, (200, 200, 200))
            screen.blit(text, (10, y))
            y += 25
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()