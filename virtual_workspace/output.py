import pygame
import random

# --- Constants ---
WIDTH = 600
HEIGHT = 600
CELL_SIZE = 20
FPS = 10

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# --- Directions ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Game States ---
GAME_RUNNING = 0
GAME_OVER = 1

# --- Maze Definition ---
maze = [
    "XXXXXXXXXXXXXXXXXXXX",
    "X..............X....X",
    "X.X.X.X.X.X.X.X.X.X",
    "X...X...X...X...X.X",
    "X.X.X.X.X.X.X.X.X.X",
    "X..............X....X",
    "X.X.X.X.X.X.X.X.X.X",
    "X...X...X...X...X.X",
    "X.X.X.X.X.X.X.X.X.X",
    "X..............X....X",
    "X.X.X.X.X.X.X.X.X.X",
    "X...X...X...X...X.X",
    "X.X.X.X.X.X.X.X.X.X",
    "X..............X....X",
    "XXXXXXXXXXXXXXXXXXXX",
]

# --- Pacman Class ---
class Pacman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = RIGHT
        self.open_mouth = True
        self.score = 0

    def move(self, direction):
        # Check if move is valid
        next_x = self.x + direction[0]
        next_y = self.y + direction[1]
        if self.is_valid_move(next_x, next_y):
            self.x = next_x
            self.y = next_y
            self.direction = direction
            self.open_mouth = not self.open_mouth

    def is_valid_move(self, x, y):
        # Check if move is within the maze bounds and not a wall
        if 0 <= x < len(maze[0]) and 0 <= y < len(maze) and maze[y][x] != "X":
            return True
        return False

    def draw(self, screen):
        # Draw pacman
        if self.open_mouth:
            pygame.draw.circle(screen, YELLOW, (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2)
            pygame.draw.polygon(screen, YELLOW, [(self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2),
                                                (self.x * CELL_SIZE + CELL_SIZE // 2 - CELL_SIZE // 4, self.y * CELL_SIZE + CELL_SIZE // 2 + CELL_SIZE // 4),
                                                (self.x * CELL_SIZE + CELL_SIZE // 2 + CELL_SIZE // 4, self.y * CELL_SIZE + CELL_SIZE // 2 + CELL_SIZE // 4)])
        else:
            pygame.draw.circle(screen, YELLOW, (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2)

    def eat_pellet(self, pellets):
        # Check if pacman is on a pellet and eat it
        for i, row in enumerate(pellets):
            for j, pellet in enumerate(row):
                if pellet and self.x == j and self.y == i:
                    pellets[i][j] = False
                    self.score += 1
                    return True
        return False

# --- Ghost Class ---
class Ghost:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.direction = RIGHT
        self.color = color
        self.scared = False
        self.scared_timer = 0

    def move(self, pacman):
        # Choose a random direction if not scared
        if not self.scared:
            possible_directions = [UP, DOWN, LEFT, RIGHT]
            valid_directions = []
            for direction in possible_directions:
                next_x = self.x + direction[0]
                next_y = self.y + direction[1]
                if self.is_valid_move(next_x, next_y):
                    valid_directions.append(direction)
            if valid_directions:
                self.direction = random.choice(valid_directions)

        # Move towards pacman if scared
        else:
            if self.x < pacman.x:
                self.direction = RIGHT
            elif self.x > pacman.x:
                self.direction = LEFT
            elif self.y < pacman.y:
                self.direction = DOWN
            elif self.y > pacman.y:
                self.direction = UP

        # Move in chosen direction
        next_x = self.x + self.direction[0]
        next_y = self.y + self.direction[1]
        if self.is_valid_move(next_x, next_y):
            self.x = next_x
            self.y = next_y

    def is_valid_move(self, x, y):
        # Check if move is within the maze bounds and not a wall
        if 0 <= x < len(maze[0]) and 0 <= y < len(maze) and maze[y][x] != "X":
            return True
        return False

    def draw(self, screen):
        # Draw ghost
        if self.scared:
            pygame.draw.circle(screen, BLUE, (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2)
        else:
            pygame.draw.circle(screen, self.color, (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2)

    def update_scared_timer(self):
        # Update scared timer
        if self.scared:
            self.scared_timer -= 1
            if self.scared_timer == 0:
                self.scared = False

# --- Game Initialization ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman")
clock = pygame.time.Clock()

# --- Game Objects ---
pacman = Pacman(1, 1)
ghosts = [
    Ghost(14, 1, RED),
    Ghost(14, 13, GREEN),
    Ghost(1, 13, BLUE),
]
pellets = [[True if maze[i][j] == "." else False for j in range(len(maze[0]))] for i in range(len(maze))]

# --- Game Loop ---
game_state = GAME_RUNNING
while game_state == GAME_RUNNING:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_state = GAME_OVER
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                pacman.move(UP)
            elif event.key == pygame.K_DOWN:
                pacman.move(DOWN)
            elif event.key == pygame.K_LEFT:
                pacman.move(LEFT)
            elif event.key == pygame.K_RIGHT:
                pacman.move(RIGHT)

    # --- Game Logic ---
    pacman.move(pacman.direction)
    pacman.eat_pellet(pellets)

    for ghost in ghosts:
        ghost.move(pacman)
        ghost.update_scared_timer()

        # Check if ghost caught pacman
        if ghost.x == pacman.x and ghost.y == pacman.y and not ghost.scared:
            game_state = GAME_OVER

    # --- Drawing ---
    screen.fill(BLACK)

    # Draw maze
    for i, row in enumerate(maze):
        for j, cell in enumerate(row):
            if cell == "X":
                pygame.draw.rect(screen, BLUE, (j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Draw pellets
    for i, row in enumerate(pellets):
        for j, pellet in enumerate(row):
            if pellet:
                pygame.draw.circle(screen, WHITE, (j * CELL_SIZE + CELL_SIZE // 2, i * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 4)

    # Draw pacman
    pacman.draw(screen)

    # Draw ghosts
    for ghost in ghosts:
        ghost.draw(screen)

    # --- Update Display ---
    pygame.display.flip()
    clock.tick(FPS)

# --- Game Over ---
if game_state == GAME_OVER:
    font = pygame.font.Font(None, 48)
    text = font.render("Game Over", True, RED)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.delay(3000)

pygame.quit()