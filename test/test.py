import json
import pygame
import os
import xml.etree.ElementTree as ET


# === Setup
pygame.init()
pygame.mixer.init()

paused = False
pause_font = pygame.font.SysFont("consolas", 36)
hint_font = pygame.font.SysFont("consolas", 18)

# Your music files
music_playlist = [
    "Music/HappyJourney.mp3",
    "Music/MainTheme.mp3",
    "Music/windCatcher.mp3"
]

current_track = 0
pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)  # Custom event when song ends

def play_music(index):
    try:
        pygame.mixer.music.load(music_playlist[index])
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(fade_ms=3000)  # fade-in
        print(f"Now playing: {music_playlist[index]}")
    except pygame.error as e:
        print(f"Error loading music: {e}")


SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Camera Map Viewer")

# === Paths
MAP_FOLDER = "map"
MAP_FILE = os.path.join(MAP_FOLDER, "test.tmj")

# === Load map data
with open(MAP_FILE) as f:
    map_data = json.load(f)

tile_width = map_data["tilewidth"]
tile_height = map_data["tileheight"]
map_width = map_data["width"]
map_height = map_data["height"]

# === Load all external tilesets
tilesets = []
collidable_gids = set()

for ts in map_data["tilesets"]:
    tsx_path = os.path.normpath(os.path.join(MAP_FOLDER, ts["source"]))
    firstgid = ts["firstgid"]

    tree = ET.parse(tsx_path)
    root = tree.getroot()

    columns = int(root.attrib["columns"])
    image = root.find("image")
    image_path = os.path.normpath(os.path.join(os.path.dirname(tsx_path), image.attrib["source"]))
    image_surface = pygame.image.load(image_path).convert_alpha()

    # Check for collidable tiles
    for tile in root.findall("tile"):
        tile_id = int(tile.attrib["id"])
        properties = tile.find("properties")
        if properties:
            for prop in properties.findall("property"):
                if prop.attrib["name"].lower() == "collision" and prop.attrib["value"] == "true":
                    collidable_gids.add(firstgid + tile_id)

    tilesets.append({
        "firstgid": firstgid,
        "columns": columns,
        "image": image_surface,
        "tilewidth": tile_width,
        "tileheight": tile_height,
    })


def get_tileset_for_gid(gid):
    for i in range(len(tilesets) - 1, -1, -1):
        if gid >= tilesets[i]["firstgid"]:
            return tilesets[i]
    return None


def is_colliding(x, y):
    tile_x = x // tile_width
    tile_y = y // tile_height
    tile_index = tile_y * map_width + tile_x
    for layer in map_data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        if tile_index < len(layer["data"]):
            gid = layer["data"][tile_index]
            if gid in collidable_gids:
                return True
    return False


def draw_map(camera_offset):
    for layer in map_data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        for i, gid in enumerate(layer["data"]):
            if gid == 0:
                continue
            ts = get_tileset_for_gid(gid)
            if not ts:
                continue

            local_gid = gid - ts["firstgid"]
            col = local_gid % ts["columns"]
            row = local_gid // ts["columns"]
            tile_rect = pygame.Rect(
                col * ts["tilewidth"],
                row * ts["tileheight"],
                ts["tilewidth"],
                ts["tileheight"]
            )

            x = (i % map_width) * tile_width
            y = (i // map_width) * tile_height

            screen.blit(ts["image"], (x - camera_offset[0], y - camera_offset[1]), tile_rect)


# === Player setup
player_size = tile_width
player_pos = [tile_width * 5, tile_height * 5]  # Starting in tile coords
player_color = (0, 255, 0)
player_speed = 5

# === Fonts
font_title = pygame.font.SysFont("georgia", 72, bold=True)
font_sub = pygame.font.SysFont("georgia", 32)

def start_screen():
    # Fonts
    title_font = pygame.font.SysFont("consolas", 72, bold=True)
    subtitle_font = pygame.font.SysFont("consolas", 28)
    prompt_font = pygame.font.SysFont("consolas", 24)

    code_green = (0, 255, 0)
    clock = pygame.time.Clock()

    # --- Step 1: Fade in Title ---
    title_text = title_font.render("Hero of Codemere", True, code_green)
    alpha = 0
    while alpha < 255:
        screen.fill((0, 0, 0))
        fade_surface = title_text.copy()
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (
            SCREEN_WIDTH // 2 - title_text.get_width() // 2,
            SCREEN_HEIGHT // 3
        ))
        pygame.display.flip()
        alpha += 4
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    pygame.time.delay(500)

    # --- Step 2: Type subtitle with blinking cursor ---
    subtitle = "A triumphant coding Saga..."
    typed = ""
    index = 0
    cursor_visible = True
    cursor_timer = 0
    cursor_interval = 500  # ms

    typing = True
    while typing:
        screen.fill((0, 0, 0))

        # Redraw title
        screen.blit(title_text, (
            SCREEN_WIDTH // 2 - title_text.get_width() // 2,
            SCREEN_HEIGHT // 3
        ))

        # Type one character at a time
        if index < len(subtitle):
            typed += subtitle[index]
            index += 1
            pygame.time.delay(50)

        # Render typed subtitle
        subtitle_surface = subtitle_font.render(typed, True, code_green)
        screen.blit(subtitle_surface, (
            SCREEN_WIDTH // 2 - subtitle_surface.get_width() // 2,
            SCREEN_HEIGHT // 2
        ))

        # Blinking cursor
        cursor_timer += clock.get_time()
        if cursor_timer >= cursor_interval:
            cursor_visible = not cursor_visible
            cursor_timer = 0

        if cursor_visible:
            cursor_x = SCREEN_WIDTH // 2 + subtitle_surface.get_width() // 2 + 5
            cursor_y = SCREEN_HEIGHT // 2
            pygame.draw.rect(screen, code_green, (cursor_x, cursor_y + 5, 10, 24))

        pygame.display.flip()
        clock.tick(60)

        if index == len(subtitle):
            pygame.time.delay(600)
            typing = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    # --- Step 3: Fade in prompt ---
    prompt_text = prompt_font.render("Press Enter to Start", True, code_green)
    alpha = 0
    while True:
        screen.fill((0, 0, 0))

        # Draw title and subtitle
        screen.blit(title_text, (
            SCREEN_WIDTH // 2 - title_text.get_width() // 2,
            SCREEN_HEIGHT // 3
        ))
        screen.blit(subtitle_font.render(subtitle, True, code_green), (
            SCREEN_WIDTH // 2 - subtitle_surface.get_width() // 2,
            SCREEN_HEIGHT // 2
        ))

        # Fade in prompt
        if alpha < 255:
            alpha += 4
        prompt_surface = prompt_text.copy()
        prompt_surface.set_alpha(alpha)
        screen.blit(prompt_surface, (
            SCREEN_WIDTH // 2 - prompt_text.get_width() // 2,
            SCREEN_HEIGHT // 2 + 80
        ))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return # Exit the start screen and enter the game


def show_intro():
    intro_font = pygame.font.SysFont("consolas", 28)
    title_font = pygame.font.SysFont("consolas", 40, bold=True)
    code_green = (0, 255, 0)

    clock = pygame.time.Clock()

    intro_lines = [
        "Hero of Codemere",
        "In the kingdom of Codemere, peace reigned for centuries...",
        "But a shadow looms: corrupted code is spreading across the realm.",
        "You, brave Hero, are the last Compiler.",
        "You must seek the Scrolls of Syntax and restore order.",
        "Press Enter to begin your quest."
    ]

    for line in intro_lines:
        text = ""
        full_font = title_font if line == intro_lines[0] else intro_font

        # --- Typewriter effect ---
        for char in line:
            text += char
            screen.fill((0, 0, 0))
            render = full_font.render(text, True, code_green)
            screen.blit(render, (
                SCREEN_WIDTH // 2 - render.get_width() // 2,
                SCREEN_HEIGHT // 2 - render.get_height() // 2
            ))
            pygame.display.flip()
            pygame.time.delay(40)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

        # --- Blinking cursor while waiting ---
        waiting = True
        cursor_visible = True
        cursor_timer = 0
        cursor_interval = 500  # ms

        while waiting:
            screen.fill((0, 0, 0))
            render = full_font.render(text, True, code_green)
            text_x = SCREEN_WIDTH // 2 - render.get_width() // 2
            text_y = SCREEN_HEIGHT // 2 - render.get_height() // 2
            screen.blit(render, (text_x, text_y))

            # Blink cursor
            cursor_timer += clock.get_time()
            if cursor_timer >= cursor_interval:
                cursor_visible = not cursor_visible
                cursor_timer = 0

            if cursor_visible:
                cursor_x = text_x + render.get_width() + 6
                cursor_y = text_y + 5
                pygame.draw.rect(screen, code_green, (cursor_x, cursor_y, 10, 24))

            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    waiting = False

        # --- Backspace effect ---
        for i in range(len(text), -1, -1):
            screen.fill((0, 0, 0))
            render = full_font.render(text[:i], True, code_green)
            screen.blit(render, (
                SCREEN_WIDTH // 2 - render.get_width() // 2,
                SCREEN_HEIGHT // 2 - render.get_height() // 2
            ))
            pygame.display.flip()
            pygame.time.delay(20)

# === Main loop
start_screen()
show_intro()
play_music(current_track)
running = True
while running:
    dt = clock.tick(60)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 🔁 Track finished
        elif event.type == pygame.USEREVENT + 1:
            pygame.mixer_music.fadeout(2000)
            current_track = (current_track + 1) % len(music_playlist)
            play_music(current_track)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
            elif paused:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    paused = False

    if not paused:
        # --- Camera centers on player (top-centered)
        cam_x = player_pos[0] - SCREEN_WIDTH // 2 + player_size // 2
        cam_y = player_pos[1] - SCREEN_HEIGHT // 2 + player_size // 2

        # Get map pixel size
        map_pixel_width = map_width * tile_width
        map_pixel_height = map_height * tile_height

        # Clamp camera to map boundaries
        cam_x = max(0, min(cam_x, map_pixel_width - SCREEN_WIDTH))
        cam_y = max(0, min(cam_y, map_pixel_height - SCREEN_HEIGHT))

        camera_offset = (cam_x, cam_y)

        draw_map(camera_offset)

        # --- Handle movement
        old_pos = player_pos[:]
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]: player_pos[0] -= player_speed
        if keys[pygame.K_d]: player_pos[0] += player_speed
        if keys[pygame.K_w]: player_pos[1] -= player_speed
        if keys[pygame.K_s]: player_pos[1] += player_speed
        if is_colliding(player_pos[0], player_pos[1]):
            player_pos = old_pos[:]

        player_pos[0] = max(0, min(player_pos[0], map_width * tile_width - player_size))
        player_pos[1] = max(0, min(player_pos[1], map_height * tile_height - player_size))

        # --- Draw player
        player_screen_x = player_pos[0] - camera_offset[0]
        player_screen_y = player_pos[1] - camera_offset[1]

        pygame.draw.rect(screen, player_color, (player_screen_x, player_screen_y, player_size, player_size))

        # 👁️ Hint: ESC = pause
        hint_text = hint_font.render("Press ESC to Pause", True, (255, 255, 255))
        screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 10, SCREEN_HEIGHT - 30))

    else:
        # Pause Screen
        pause_text = pause_font.render("Game Paused", True, (0, 255, 0))
        resume_text = hint_font.render("Press R to Resume", True, (0, 255, 0))
        quit_text = hint_font.render("Press Q to Quit", True, (0, 255, 0))

        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

    pygame.display.flip()

pygame.quit()
