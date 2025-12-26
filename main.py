import asyncio
import pygame
import sys
import random
import math

# Initialize pygame at module level (required)
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Beautiful Flappy Bird")

# Clock
clock = pygame.time.Clock()

# Colors
SKY_BLUE = (135, 206, 235)
CLOUD_WHITE = (250, 250, 250, 200)
GRASS_GREEN = (34, 139, 34)
PIPE_GREEN = (34, 139, 34)
BIRD_YELLOW = (255, 215, 0)
BIRD_ORANGE = (255, 140, 0)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
GOLD = (255, 215, 0)
SCORE_BG = (0, 0, 0, 128)

# SAFE FONT: Use default font (SysFont fails in browser)
font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 30)
title_font = pygame.font.Font(None, 70)

async def main():
    # Game variables (must be inside main for reset on reload)
    gravity = 0.5
    bird_movement = 0
    score = 0
    high_score = 0
    game_active = False
    game_started = False
    scroll_speed = 3
    pipe_gap = 200
    pipe_frequency = 1800  # milliseconds
    last_pipe = pygame.time.get_ticks() - pipe_frequency
    last_score_sound = 0
    score_sound_cooldown = 500

    # Create surfaces
    cloud_surface = pygame.Surface((100, 60), pygame.SRCALPHA)
    pygame.draw.ellipse(cloud_surface, CLOUD_WHITE, (0, 0, 100, 60))
    pygame.draw.ellipse(cloud_surface, CLOUD_WHITE, (20, -15, 60, 50))
    pygame.draw.ellipse(cloud_surface, CLOUD_WHITE, (60, -10, 50, 40))

    # Bird class
    class Bird:
        def __init__(self):
            self.x = 150
            self.y = HEIGHT // 2
            self.radius = 20
            self.flap_power = -8
            self.tilt = 0
            self.flap_count = 0
            
        def draw(self):
            # Draw bird body
            pygame.draw.circle(screen, BIRD_YELLOW, (self.x, self.y), self.radius)
            
            # Draw wing
            wing_y = self.y + math.sin(self.flap_count * 0.2) * 3
            pygame.draw.ellipse(screen, BIRD_ORANGE, (self.x - 15, wing_y - 10, 25, 15))
            
            # Draw eye
            pygame.draw.circle(screen, (0, 0, 0), (self.x + 10, self.y - 5), 6)
            pygame.draw.circle(screen, (255, 255, 255), (self.x + 12, self.y - 7), 2)
            
            # Draw beak
            beak_points = [(self.x + 20, self.y), (self.x + 35, self.y - 5), (self.x + 35, self.y + 5)]
            pygame.draw.polygon(screen, (255, 140, 0), beak_points)
            
            # Draw tail feathers
            tail_offset = math.sin(self.flap_count * 0.2) * 2
            tail_points = [
                (self.x - 20, self.y),
                (self.x - 35, self.y - 10 + tail_offset),
                (self.x - 35, self.y + 10 + tail_offset)
            ]
            pygame.draw.polygon(screen, BIRD_ORANGE, tail_points)
            
            self.flap_count += 1
            
        def flap(self):
            nonlocal bird_movement
            bird_movement = self.flap_power
            
        def update(self):
            nonlocal bird_movement
            bird_movement += gravity
            self.y += bird_movement
            
            # Tilt bird based on movement
            self.tilt = min(bird_movement * 3, 30)
            
            # Keep bird on screen
            if self.y < 0:
                self.y = 0
                bird_movement = 0
            if self.y > HEIGHT - 100:
                self.y = HEIGHT - 100
                bird_movement = 0

    # Pipe class
    class Pipe:
        def __init__(self):
            self.x = WIDTH
            self.height = random.randint(150, 400)
            self.top_pipe = pygame.Rect(self.x, 0, 80, self.height - pipe_gap // 2)
            self.bottom_pipe = pygame.Rect(self.x, self.height + pipe_gap // 2, 80, HEIGHT)
            self.passed = False
            
        def draw(self):
            # Draw top pipe
            pygame.draw.rect(screen, PIPE_GREEN, self.top_pipe)
            pygame.draw.rect(screen, (0, 100, 0), self.top_pipe, 3)
            # Draw cap
            cap_rect = pygame.Rect(self.x - 5, self.height - pipe_gap // 2 - 30, 90, 30)
            pygame.draw.rect(screen, (0, 100, 0), cap_rect)
            
            # Draw bottom pipe
            pygame.draw.rect(screen, PIPE_GREEN, self.bottom_pipe)
            pygame.draw.rect(screen, (0, 100, 0), self.bottom_pipe, 3)
            # Draw cap
            cap_rect = pygame.Rect(self.x - 5, self.height + pipe_gap // 2, 90, 30)
            pygame.draw.rect(screen, (0, 100, 0), cap_rect)
            
        def update(self):
            self.x -= scroll_speed
            self.top_pipe.x = self.x
            self.bottom_pipe.x = self.x
            
        def collide(self, bird):
            bird_rect = pygame.Rect(bird.x - bird.radius, bird.y - bird.radius, 
                                    bird.radius * 2, bird.radius * 2)
            return bird_rect.colliderect(self.top_pipe) or bird_rect.colliderect(self.bottom_pipe)

    # Particle system for effects
    class Particle:
        def __init__(self, x, y, color):
            self.x = x
            self.y = y
            self.color = color
            self.size = random.randint(2, 5)
            self.speed_x = random.uniform(-2, 2)
            self.speed_y = random.uniform(-3, -1)
            self.life = 30
            
        def update(self):
            self.x += self.speed_x
            self.y += self.speed_y
            self.life -= 1
            self.size = max(0, self.size - 0.1)
            
        def draw(self):
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

    # Create bird
    bird = Bird()

    # Lists
    pipes = []
    particles = []

    # Cloud positions
    clouds = []
    for _ in range(5):
        x = random.randint(0, WIDTH)
        y = random.randint(50, 200)
        speed = random.uniform(0.2, 0.8)
        clouds.append([x, y, speed])

    # Button class
    class Button:
        def __init__(self, x, y, width, height, text):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.hovered = False
            
        def draw(self):
            color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
            # AVOID border_radius (not well supported in web)
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 3)
            
            text_surf = font.render(self.text, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)
            
        def check_hover(self, pos):
            self.hovered = self.rect.collidepoint(pos)
            
        def check_click(self, pos, event):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.rect.collidepoint(pos)
            return False

    # Create buttons
    start_button = Button(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60, "Start Game")
    restart_button = Button(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60, "Play Again")

    # Draw background
    def draw_background():
        # Sky gradient
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(135 - ratio * 40)
            g = int(206 - ratio * 60)
            b = int(235 - ratio * 80)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
        
        # Draw sun
        pygame.draw.circle(screen, (255, 255, 200), (700, 80), 60)
        pygame.draw.circle(screen, (255, 220, 100), (700, 80), 50)
        
        # Draw clouds
        for cloud in clouds:
            screen.blit(cloud_surface, (cloud[0], cloud[1]))
            cloud[0] -= cloud[2]
            if cloud[0] < -100:
                cloud[0] = WIDTH + 50
                cloud[1] = random.randint(50, 200)
        
        # Draw distant mountains
        for i in range(0, WIDTH, 100):
            height = 100 + math.sin(i * 0.02) * 30
            pygame.draw.polygon(screen, (100, 100, 120), [
                (i, HEIGHT - 100),
                (i + 50, HEIGHT - 100 - height),
                (i + 100, HEIGHT - 100)
            ])
        
        # Draw grass
        pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT - 100, WIDTH, 100))
        
        # Draw grass details
        for i in range(0, WIDTH, 20):
            height = random.randint(10, 30)
            pygame.draw.line(screen, (20, 100, 20), (i, HEIGHT - 100), (i, HEIGHT - 100 - height), 2)

    # Draw ground details
    def draw_ground():
        for i in range(0, WIDTH, 40):
            pygame.draw.rect(screen, (20, 80, 20), (i, HEIGHT - 80, 20, 20))
            pygame.draw.rect(screen, (20, 80, 20), (i + 20, HEIGHT - 60, 20, 20))

    # Draw score
    def draw_score():
        score_surface = font.render(str(score), True, TEXT_COLOR)
        score_rect = score_surface.get_rect(center=(WIDTH//2, 50))
        # AVOID border_radius for score bg
        pygame.draw.rect(screen, (0, 0, 0, 180), score_rect.inflate(20, 10))
        screen.blit(score_surface, score_rect)
        
        if not game_active and not game_started:
            high_score_surface = small_font.render(f"Best: {high_score}", True, TEXT_COLOR)
            high_score_rect = high_score_surface.get_rect(center=(WIDTH//2, 100))
            screen.blit(high_score_surface, high_score_rect)

    # Draw title
    def draw_title():
        title_surface = title_font.render("Beautiful Flappy Bird", True, GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH//2, 100))
        screen.blit(title_surface, title_rect)
        
        subtitle = small_font.render("Press SPACE or Click to Flap", True, TEXT_COLOR)
        subtitle_rect = subtitle.get_rect(center=(WIDTH//2, 160))
        screen.blit(subtitle, subtitle_rect)

    # Create particles
    def create_particles(x, y, color, count=10):
        for _ in range(count):
            particles.append(Particle(x, y, color))

    # Main game loop
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_active:
                        bird.flap()
                        create_particles(bird.x, bird.y, BIRD_ORANGE, 5)
                    else:
                        if not game_started:
                            game_started = True
                            game_active = True
                            score = 0
                            pipes = []
                            bird.y = HEIGHT // 2
                            bird_movement = 0
                        else:
                            game_active = True
                            score = 0
                            pipes = []
                            bird.y = HEIGHT // 2
                            bird_movement = 0
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_active:
                        bird.flap()
                        create_particles(bird.x, bird.y, BIRD_ORANGE, 5)
                    else:
                        mouse_pos = pygame.mouse.get_pos()
                        if not game_started:
                            if start_button.check_click(mouse_pos, event):
                                game_started = True
                                game_active = True
                                score = 0
                                pipes = []
                                bird.y = HEIGHT // 2
                                bird_movement = 0
                        else:
                            if restart_button.check_click(mouse_pos, event):
                                game_active = True
                                score = 0
                                pipes = []
                                bird.y = HEIGHT // 2
                                bird_movement = 0
        
        # Draw background
        draw_background()
        draw_ground()
        
        # Update and draw particles
        for particle in particles[:]:
            particle.update()
            particle.draw()
            if particle.life <= 0:
                particles.remove(particle)
        
        # Game logic
        if game_active:
            bird.update()
            
            if current_time - last_pipe > pipe_frequency:
                pipes.append(Pipe())
                last_pipe = current_time
            
            for pipe in pipes[:]:
                pipe.update()
                
                if not pipe.passed and pipe.x + 80 < bird.x:
                    pipe.passed = True
                    score += 1
                    create_particles(pipe.x + 40, pipe.height, (255, 215, 0), 15)
                    if current_time - last_score_sound > score_sound_cooldown:
                        last_score_sound = current_time
                
                if pipe.collide(bird):
                    game_active = False
                    create_particles(bird.x, bird.y, (255, 0, 0), 30)
                    if score > high_score:
                        high_score = score
            
            pipes = [pipe for pipe in pipes if pipe.x > -100]
        
        # Draw pipes
        for pipe in pipes:
            pipe.draw()
        
        # Draw bird
        bird.draw()
        
        # Draw score
        draw_score()
        
        # Draw UI
        if not game_active:
            if not game_started:
                draw_title()
                bird.y = HEIGHT // 2
                bird.draw()
                start_button.check_hover(pygame.mouse.get_pos())
                start_button.draw()
            else:
                game_over_surface = title_font.render("Game Over!", True, (220, 20, 60))
                game_over_rect = game_over_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
                screen.blit(game_over_surface, game_over_rect)
                
                score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
                score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
                screen.blit(score_text, score_rect)
                
                high_score_text = font.render(f"Best: {high_score}", True, GOLD)
                high_score_rect = high_score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
                screen.blit(high_score_text, high_score_rect)
                
                restart_button.check_hover(pygame.mouse.get_pos())
                restart_button.draw()
        
        # Update display
        pygame.display.flip()
        
        # REQUIRED FOR PYGBAG: Yield control to browser
        await asyncio.sleep(0)
        
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

# REQUIRED: Run async main
asyncio.run(main())