import pygame
import random
from datetime import timedelta
import time
import json

# 初始化 Pygame
pygame.init()

# 定义常量
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 100
ROWS, COLS = 6, 6
FPS = 30
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (200, 200, 200)
TIMER_MAX = 3600  # 游戏倒计时总秒数
HIGH_SCORE_FILE = 'high_scores.json'

# 定义颜色
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 音乐设置
pygame.mixer.music.load('music.mp3')
pygame.mixer.music.play(-1)  # -1 表示循环播放

# 创建窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("打个蕉鲜小游戏")

# 加载背景图片
background_image = pygame.image.load('images/background.png')
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 加载图案图片
IMAGE_PATHS = ['images/1.png', 'images/2.png', 'images/3.png', 'images/4.png']
patterns = [pygame.image.load(path) for path in IMAGE_PATHS]
patterns = [pygame.transform.scale(p, (TILE_SIZE, TILE_SIZE)) for p in patterns]

# 加载字体
try:
    font = pygame.font.Font('msyh.ttf', 36)
except IOError as e:
    print("无法加载字体文件，请确保 msyh.ttf 存在于项目目录中或提供正确的路径。")
    raise e

def load_high_scores():
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_high_scores(scores):
    with open(HIGH_SCORE_FILE, 'w') as f:
        json.dump(scores, f)

def update_high_scores(score):
    scores = load_high_scores()
    scores.append(score)
    scores = sorted(scores, reverse=True)[:3]
    save_high_scores(scores)

def generate_board(mode, total_tiles):
    pattern_counts = {}
    remaining_tiles = total_tiles
    
    if mode == 2:
        pattern_options = [2, 4, 6, 8]
    elif mode == 3:
        pattern_options = [3, 6, 9]
    else:
        raise ValueError("Unsupported mode")

    basic_patterns = []
    
    while remaining_tiles > 0:
        pattern = random.choice(patterns)
        count = random.choice(pattern_options)
        count = min(count, remaining_tiles)
        pattern_counts[pattern] = count
        remaining_tiles -= count
        basic_patterns.extend([pattern] * count)
        
    if len(basic_patterns) != total_tiles:
        raise RuntimeError("Pattern generation failed to meet the required total tile count.")

    random.shuffle(basic_patterns)

    board = [[None for _ in range(COLS)] for _ in range(ROWS)]

    for i, pattern in enumerate(basic_patterns):
        row, col = divmod(i, COLS)
        board[row][col] = pattern

    return board


def draw_board(board):
    for row in range(ROWS):
        for col in range(COLS):
            tile = board[row][col]
            if tile is not None:
                screen.blit(tile, (col * TILE_SIZE, row * TILE_SIZE))

def check_match(selected, board, mode):
    if len(selected) == mode:
        coords = [selected[i] for i in range(mode)]
        if all(board[r][c] == board[coords[0][0]][coords[0][1]] for r, c in coords):
            for r, c in coords:
                board[r][c] = None
            return True
    return False

def draw_timer(timer):
    time_str = str(timedelta(seconds=int(timer)))
    text = font.render(time_str, True, BLACK)
    screen.blit(text, (SCREEN_WIDTH - 150, 10))

def draw_back_button():
    pygame.draw.rect(screen, (100, 100, 100), (SCREEN_WIDTH - 150, 60, 100, 40))
    back_text = font.render("返回", True, WHITE)
    text_rect = back_text.get_rect(center=(SCREEN_WIDTH - 100, 80))
    screen.blit(back_text, text_rect)

def check_back_button():
    mouse_pos = pygame.mouse.get_pos()
    return SCREEN_WIDTH - 150 <= mouse_pos[0] <= SCREEN_WIDTH - 50 and 60 <= mouse_pos[1] <= 100

def check_game_over(timer):
    return timer <= 0

#打印游戏状态消息
def draw_message(message, duration=2000):
    message_text = font.render(message, True, BLACK)
    screen.blit(message_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 50))
    pygame.display.flip()
    pygame.time.wait(duration)

def draw_score(score):
    score_text = font.render(f"积分: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH - 150, 110))  # 将积分绘制在返回键下方

BGM_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH - 150, 160, 80, 30)  # BGM 按钮的区域

#绘制BGM按钮
def draw_bgm_button(music_on):
    color = GREEN if music_on else RED
    pygame.draw.rect(screen, color, BGM_BUTTON_RECT)
    text = font.render('BGM', True, WHITE)
    screen.blit(text, (SCREEN_WIDTH - 150, 150))  # 调整 BGM 文本的位置

#绘制游戏音乐
def toggle_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        return False
    else:
        pygame.mixer.music.unpause()
        return True
    
#绘制游戏内容
def game_state(mode):
    global running, timer, selected, board, score
    running = True

    # 根据模式设置倒计时时间和总图片数
    if mode == 2:
        timer = 3600  # 简单模式 60 秒钟
        total_tiles = 4 * 6  # 36 张图
    elif mode == 3:
        timer = 1800  # 困难模式 30 秒钟
        total_tiles = ROWS * COLS  # 36 张图
    else:
        raise ValueError("Unsupported mode")
    
    selected = []
    board = generate_board(mode, total_tiles)
    score = 0
    music_on = True  # 默认音乐开启

    game_over = False
    game_complete = False
    start_time = time.time()
    last_clicked = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if BGM_BUTTON_RECT.collidepoint(x, y):
                    music_on = toggle_music()
                else:
                    col, row = x // TILE_SIZE, y // TILE_SIZE
                    if 0 <= row < ROWS and 0 <= col < COLS:
                        if board[row][col] is not None:
                            if (row, col) != last_clicked:
                                selected.append((row, col))
                                last_clicked = (row, col)
                                if len(selected) == mode:
                                    if check_match(selected, board, mode):
                                        if mode == 2:
                                            score += 1
                                        elif mode == 3:
                                            score += 3
                                    selected.clear()
                    elif check_back_button():
                        update_high_scores(score)
                        return 'menu'

        screen.blit(background_image, (0, 0))
        draw_board(board)
        draw_timer(timer)
        draw_score(score)  # 绘制当前积分
        draw_back_button()
        draw_bgm_button(music_on)  # 绘制BGM按钮

        if all(tile is None for row in board for tile in row):
            game_complete = True
            update_high_scores(score)
            draw_message("恭喜通关！即将返回主页！")
            return 'menu'

        if check_game_over(timer):
            game_over = True
            start_time = time.time()

        if game_over or game_complete:
            elapsed_time = int(time.time() - start_time)
            if elapsed_time >= 3:
                update_high_scores(score)
                return 'menu'
            
            message = "游戏失败！请点击返回重新开始！" if game_over else "恭喜通关！即将返回主页！"
            draw_message(message, duration=elapsed_time * 1000)
        
        timer -= 1 / FPS
        pygame.display.flip()

    return 'game_over'



#绘制游戏主页面
def menu_state():
    global running
    running = True
    high_scores = load_high_scores()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80 and SCREEN_HEIGHT // 2 - 50 <= y <= SCREEN_HEIGHT // 2 + 10:
                    return 'game'
                elif SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80 and SCREEN_HEIGHT // 2 + 60 <= y <= SCREEN_HEIGHT // 2 + 120:
                    return 'hard_game'

        screen.blit(background_image, (0, 0))
        menu_text = font.render("简单模式（配对）", True, BLACK)
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 50))
        
        hard_mode_text = font.render("困难模式（三消）", True, BLACK)
        screen.blit(hard_mode_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 60))

        # 显示排行榜
        high_scores_text = font.render("排行榜:", True, BLACK)
        screen.blit(high_scores_text, (50, 50))

        for i, score in enumerate(high_scores):
            score_text = font.render(f"{i + 1}. {score}", True, BLACK)
            screen.blit(score_text, (50, 100 + i * 30))

        pygame.display.flip()
    
    return 'exit'


def main():
    state = 'menu'
    clock = pygame.time.Clock()
    
    while True:
        if state == 'game':
            state = game_state(mode=2)
        elif state == 'hard_game':
            state = game_state(mode=3)
        elif state == 'menu':
            state = menu_state()
        elif state == 'exit':
            break
        
        clock.tick(FPS)

if __name__ == "__main__":
    main()