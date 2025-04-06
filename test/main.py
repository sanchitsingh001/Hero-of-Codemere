import json
import pygame
import os
import xml.etree.ElementTree as ET
import io
import contextlib

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

# === Game state
scene = "map"
active_npc = None
dialogue_index = 0
dialogue_lines = []
challenge_prompt = []
code_lines = [""]
cursor_line = 0
cursor_col = 0
cursor_visible = True
output_message = ""
challenge_solved = False
show_congrats = False
continue_button_rect = pygame.Rect(550, 370, 180, 40)
run_button_rect = pygame.Rect(SCREEN_WIDTH - 140, 20, 120, 40)

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

def draw_popup():
    popup_rect = pygame.Rect(400, 300, 480, 150)
    pygame.draw.rect(screen, (0, 100, 0), popup_rect)
    pygame.draw.rect(screen, (255, 255, 255), popup_rect, 3)
    text = font.render("🎉 Congrats! You solved it!", True, (255, 255, 255))
    screen.blit(text, (popup_rect.centerx - text.get_width() // 2, popup_rect.y + 30))
    pygame.draw.rect(screen, (0, 80, 0), continue_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), continue_button_rect, 2)
    continue_text = font.render("Continue", True, (255, 255, 255))
    screen.blit(continue_text, (continue_button_rect.centerx - continue_text.get_width() // 2, continue_button_rect.centery - 10))

def draw_error_message():
    if output_message:
        error_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, SCREEN_WIDTH - 40, 40)
        pygame.draw.rect(screen, (80, 0, 0), error_rect)
        pygame.draw.rect(screen, (255, 255, 255), error_rect, 2)
        text = font.render(output_message, True, (255, 255, 255))
        screen.blit(text, (error_rect.x + 10, error_rect.y + 8))

def draw_run_button():
    button_rect = pygame.Rect(SCREEN_WIDTH - 140, 20, 120, 40)
    pygame.draw.rect(screen, (30, 120, 30), button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)
    text = font.render("▶ Run Code", True, (255, 255, 255))
    screen.blit(text, (button_rect.x + 10, button_rect.y + 8))
    return button_rect

def check_challenge_answer():
    global output_message, challenge_solved, show_congrats, code_lines
    code = "\n".join(code_lines)
    namespace = {}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code, {}, namespace)

        if active_npc["name"] == "Old Man Cedric":
            rune = namespace.get("rune", None)
            if rune == "single":
                output_message = "✅ Correct!"
                challenge_solved = True
                show_congrats = True
            else:
                output_message = "❌ Try again. Make sure 'rune' is correct."
        elif active_npc["name"] == "Bugsy the Apprentice":
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code, {}, {})
            result = output.getvalue().strip().splitlines()
            if result == [str(i) for i in range(1, 11)]:
                output_message = "✅ Correct!"
                challenge_solved = True
                show_congrats = True
            else:
                output_message = "❌ That doesn't include 10."
        elif active_npc["name"] == "Torchbearer Korr":
            func = namespace.get("add", None)
            if callable(func) and func(2, 3) == 5 and func(-1, 1) == 0:
                output_message = "✅ Correct!"
                challenge_solved = True
                show_congrats = True
            else:
                output_message = "❌ Check your 'add' function."
    except Exception as e:
        output_message = f"⚠️ Error: {e}"

    # Provide starter code when entering the challenge
    if active_npc["name"] == "Old Man Cedric":
        code_lines = ["rune = 'elgnis'"]
    elif active_npc["name"] == "Bugsy the Apprentice":
        code_lines = ["for i in range(1, 10):", "    print(i)"]
    elif active_npc["name"] == "Torchbearer Korr":
        code_lines = ["def add(a, b):", "    return a - b"]

def draw_dialogue_box():
    box_height = 120
    pygame.draw.rect(screen, (30, 30, 30), (50, SCREEN_HEIGHT - box_height - 50, SCREEN_WIDTH - 100, box_height))
    pygame.draw.rect(screen, (255, 255, 255), (50, SCREEN_HEIGHT - box_height - 50, SCREEN_WIDTH - 100, box_height), 2)
    if dialogue_index < len(dialogue_lines):
        line = dialogue_lines[dialogue_index]
        rendered = font.render(line, True, (255, 255, 255))
        screen.blit(rendered, (70, SCREEN_HEIGHT - box_height - 20))

def draw_challenge_screen():
    padding = 20
    box_width = (SCREEN_WIDTH - 3 * padding) // 2
    box_height = SCREEN_HEIGHT // 2
    box_top = (SCREEN_HEIGHT - box_height) // 2

    prompt_rect = pygame.Rect(padding, box_top, box_width, box_height)
    pygame.draw.rect(screen, (40, 40, 40), prompt_rect)
    pygame.draw.rect(screen, (255, 255, 255), prompt_rect, 2)
    y = box_top + 10
    for line in challenge_prompt:
        rendered = font.render(line, True, (255, 255, 255))
        screen.blit(rendered, (prompt_rect.x + 10, y))
        y += 28

    code_rect = pygame.Rect(padding * 2 + box_width, box_top, box_width, box_height)
    pygame.draw.rect(screen, (20, 20, 20), code_rect)
    pygame.draw.rect(screen, (255, 255, 255), code_rect, 2)
    line_height = 28
    for i, line in enumerate(code_lines):
        rendered = font.render(line, True, (0, 255, 0))
        screen.blit(rendered, (code_rect.x + 10, code_rect.y + 10 + i * line_height))
    if cursor_visible and cursor_line < len(code_lines):
        text_before_cursor = font.render(code_lines[cursor_line][:cursor_col], True, (0, 255, 0))
        cursor_x = code_rect.x + 10 + text_before_cursor.get_width()
        cursor_y = code_rect.y + 10 + cursor_line * line_height
        pygame.draw.line(screen, (0, 255, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 4), 2)

    # Exit hint
    exit_text = font.render("Press ESC to exit", True, (180, 180, 180))
    screen.blit(exit_text, (code_rect.right - exit_text.get_width() - 10, code_rect.bottom - 30))

    draw_run_button()

    # --- Error Message (if any)
    draw_error_message()

    # --- Success Popup
    if show_congrats:
        draw_popup()
# === Player setup
player_size = tile_width
player_pos = [tile_width * 58, tile_height * 4]
player_color = (0, 255, 0)
player_speed = 5

# === NPC setup
npc_size = tile_width
npc_color = (255, 0, 0)
npcs = [
    {
        "x": 42, "y": 4,
        "name": "Old Man Cedric",
        "dialogue": [
            "Old Man Cedric: Ah, a fresh traveler at last.",
            "Old Man Cedric: The gates of Codemire test all who enter.",
            "Old Man Cedric: To pass, you must prove your mind is not easily scrambled.",
            "Old Man Cedric: I present to you... the Rune of Reversal."
        ],
        "challenge_prompt": [
            "The Rune of Reversal",
            "An ancient word lies before you, written backwards by time.",
            "Your task: Return the correct form of the word by reversing it.",
            "Example:",
            "  rune = 'elgnis' => 'single'"
        ]
    },
    {
        "x": 53, "y": 19,
        "name": "Bugsy the Apprentice",
        "dialogue": [
            "Bugsy: Oh no, not again...",
            "Bugsy: My loop won’t include 10. It’s cursed!",
            "Bugsy: Can you take a look?"
        ],
        "challenge_prompt": [
            "Loop of Frustration",
            "Bugsy’s code:",
            "  for i in range(1, 10):",
            "      print(i)",
            "He wants it to print numbers from 1 to 10 **including** 10.",
            "Your task: Fix the code so it includes 10."
        ]
    },
    {
        "x": 49, "y": 35,
        "name": "Torchbearer Korr",
        "dialogue": [
            "Torchbearer Korr: Halt.",
            "Torchbearer Korr: Beyond here lies the Forest of Broken Functions.",
            "Torchbearer Korr: Solve this, and I’ll let you pass."
        ],
        "challenge_prompt": [
            "The Broken Function",
            "A traveler left this behind before disappearing into the forest:",
            "  def add(a, b):",
            "      return a - b",
            "But they meant for it to **add** the two numbers.",
            "Your task: Fix the function so it returns the correct sum."
        ]
    }
]

# === Font
font = pygame.font.SysFont(None, 28)

# === Main loop
start_screen()
show_intro()
play_music(current_track)

running = True

while running:
    dt = clock.tick(60)
    screen.fill((0, 0, 0))

    cam_x = player_pos[0] - SCREEN_WIDTH // 2 + player_size // 2
    cam_y = player_pos[1] - SCREEN_HEIGHT // 2 + player_size // 2

    # Get map pixel size
    map_pixel_width = map_width * tile_width
    map_pixel_height = map_height * tile_height

    cam_x = max(0, min(cam_x, map_pixel_width - SCREEN_WIDTH))
    cam_y = max(0, min(cam_y, map_pixel_height - SCREEN_HEIGHT))

    camera_offset = (cam_x, cam_y)

    draw_map(camera_offset)

    for npc in npcs:
        screen_x = npc["x"] * tile_width - camera_offset[0]
        screen_y = npc["y"] * tile_height - camera_offset[1]
        pygame.draw.rect(screen, npc_color, (screen_x, screen_y, npc_size, npc_size))

    old_pos = player_pos[:]
    keys = pygame.key.get_pressed()
    if scene == "map":
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

    if scene == "map":
        player_tile = (player_pos[0] // tile_width, player_pos[1] // tile_height)
        for npc in npcs:
            if player_tile == (npc["x"], npc["y"]):
                active_npc = npc
                dialogue_lines = npc["dialogue"]
                dialogue_index = 0
                scene = "dialogue"
                break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.USEREVENT + 1:
            current_track = (current_track + 1) % len(music_playlist)
            play_music(current_track)

        elif scene == "dialogue" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                dialogue_index += 1
                if dialogue_index >= len(dialogue_lines):
                    challenge_prompt = active_npc["challenge_prompt"]
                    if active_npc["name"] == "Old Man Cedric":
                        code_lines = ["rune = 'elgnis'"]
                    elif active_npc["name"] == "Bugsy the Apprentice":
                        code_lines = ["for i in range(1, 10):", "    print(i)"]
                    elif active_npc["name"] == "Torchbearer Korr":
                        code_lines = ["def add(a, b):", "    return a - b"]
                    else:
                        code_lines = [""]
                    cursor_line = 0
                    output_message = ""
                    cursor_col = 0
                    scene = "challenge"
        elif scene == "challenge" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                scene = "map"
                active_npc = None
                player_pos[0] += 20
                player_pos[1] += 20
            elif event.key == pygame.K_RETURN:
                code_lines.insert(cursor_line + 1, "")
                cursor_line += 1
                cursor_col = 0
            elif event.key == pygame.K_BACKSPACE:
                if cursor_col > 0:
                    code_lines[cursor_line] = (
                        code_lines[cursor_line][:cursor_col - 1] + code_lines[cursor_line][cursor_col:]
                    )
                    cursor_col -= 1
                elif cursor_line > 0:
                    prev_line = code_lines[cursor_line - 1]
                    cursor_col = len(prev_line)
                    code_lines[cursor_line - 1] += code_lines[cursor_line]
                    del code_lines[cursor_line]
                    cursor_line -= 1
            elif event.key == pygame.K_LEFT:
                if cursor_col > 0:
                    cursor_col -= 1
            elif event.key == pygame.K_RIGHT:
                if cursor_col < len(code_lines[cursor_line]):
                    cursor_col += 1
            elif event.key == pygame.K_UP:
                if cursor_line > 0:
                    cursor_line -= 1
                    cursor_col = min(cursor_col, len(code_lines[cursor_line]))
            elif event.key == pygame.K_DOWN:
                if cursor_line < len(code_lines) - 1:
                    cursor_line += 1
                    cursor_col = min(cursor_col, len(code_lines[cursor_line]))
            else:
                char = event.unicode
                if char.isprintable():
                    code_lines[cursor_line] = (
                        code_lines[cursor_line][:cursor_col] + char + code_lines[cursor_line][cursor_col:]
                    )
                    cursor_col += 1
        elif event.type == pygame.MOUSEBUTTONDOWN and scene == "challenge":
            if run_button_rect.collidepoint(event.pos):
                check_challenge_answer()
            if show_congrats and continue_button_rect.collidepoint(event.pos):
                show_congrats = False
                scene = "map"
                active_npc = None
                player_pos[0] += 20
                player_pos[1] += 20

    cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0

    if scene == "dialogue":
        draw_dialogue_box()
    elif scene == "challenge":
        draw_challenge_screen()

    pygame.display.flip()

pygame.quit()
