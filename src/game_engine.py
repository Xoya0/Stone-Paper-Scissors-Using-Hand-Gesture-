import pygame
import cv2
import numpy as np
import random
import os
import time
from collections import deque

# --- Constants ---
HIGHSCORE_FILE = "highscore.txt"
ASSETS_DIR = "assets"
IMAGE_DIR = os.path.join(ASSETS_DIR, "images")
SOUND_DIR = os.path.join(ASSETS_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

# Colors
C_BACKGROUND = (30, 30, 50)
C_TITLE = (255, 255, 255)
C_MENU_DEFAULT = (200, 200, 200)
C_MENU_SELECTED = (255, 255, 0)
C_INSTRUCTIONS = (180, 180, 200)
C_SCORE = (255, 255, 255)
C_WIN = (0, 255, 0)
C_LOSE = (255, 0, 0)
C_DRAW = (255, 255, 0)
C_HIGHSCORE = (255, 215, 0) # Gold
C_DIFFICULTY_EASY = (100, 255, 100)
C_DIFFICULTY_HARD = (255, 100, 100)
C_PLACEHOLDER_BG = (40, 40, 60)
C_WEBCAM_BORDER = (100, 100, 120, 180)
C_SCORE_BG = (0, 0, 0, 100)
C_CHOICE_HIGHLIGHT = (255, 255, 255, 100) # White highlight for detected choice

# Timings & Gameplay
MENU_COOLDOWN = 0.5 # seconds
RESULT_DELAY = 2.0  # seconds
TRANSITION_SPEED = 5 # Alpha change per frame (faster)
PLAYER_HISTORY_SIZE = 5 # For hard AI

# Game States
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_RESULT = "RESULT"
STATE_TRANSITION = "TRANSITION"

# Difficulty Levels
DIFF_EASY = "Easy"
DIFF_HARD = "Hard"
# -----------------

class GameEngine:
    def __init__(self, width, height, feedback_module):
        self.width = width
        self.height = height
        self.feedback = feedback_module
        
        # Game states
        self.current_state = STATE_MENU
        self.previous_state = STATE_MENU # For state-dependent logic
        self.next_state = None
        self.transition_alpha = 0
        
        # Menu options & Settings
        self.menu_options = ["Play Game", "Difficulty", "Exit"]
        self.selected_option = 0
        self.difficulty = DIFF_EASY
        self.difficulty_options = [DIFF_EASY, DIFF_HARD]
        self.is_selecting_difficulty = False # Sub-state for menu
        self.last_menu_change_time = 0
        
        # Game variables
        self.user_choice = None
        self.computer_choice = None
        self.result = None
        self.gesture_map = {
            "Fist": "Rock",
            "Open Palm": "Paper",
            "Peace Sign": "Scissors"
        }
        self.choices = list(self.gesture_map.values())
        self.player_choice_history = deque(maxlen=PLAYER_HISTORY_SIZE)
        self.win_counters = {"Rock": "Paper", "Paper": "Scissors", "Scissors": "Rock"}
        
        # Timer
        self.timer = 0
        
        # Score tracking
        self.user_score = 0
        self.computer_score = 0
        self.high_score = self._load_high_score()
        self.new_highscore_achieved = False
        
        # Ensure asset directories exist
        os.makedirs(IMAGE_DIR, exist_ok=True)
        os.makedirs(MUSIC_DIR, exist_ok=True)
            
        # Load assets
        self.images = {}
        self._initialize_images()
        self._initialize_fonts()
        self._initialize_music()

    def _initialize_fonts(self):
         # Fonts
        try:
            self.font_title = pygame.font.SysFont('Arial', 64, bold=True)
            self.font_menu = pygame.font.SysFont('Arial', 48)
            self.font_instr = pygame.font.SysFont('Arial', 28)
            self.font_score = pygame.font.SysFont('Arial', 36)
            self.font_choice = pygame.font.SysFont('Arial', 32)
            self.font_highscore = pygame.font.SysFont('Arial', 30, italic=True)
            self.font_difficulty = pygame.font.SysFont('Arial', 30, bold=True)
        except Exception as e:
            print(f"Warning: Could not load Arial font, using default. {e}")
            self.font_title = pygame.font.SysFont(None, 72)
            self.font_menu = pygame.font.SysFont(None, 54)
            self.font_instr = pygame.font.SysFont(None, 32)
            self.font_score = pygame.font.SysFont(None, 40)
            self.font_choice = pygame.font.SysFont(None, 36)
            self.font_highscore = pygame.font.SysFont(None, 34, italic=True)
            self.font_difficulty = pygame.font.SysFont(None, 34, bold=True)

    def _initialize_music(self):
        """Load and potentially start background music."""
        self.music_files = {
            STATE_MENU: os.path.join(MUSIC_DIR, "menu_music.ogg"), # Example filenames
            STATE_PLAYING: os.path.join(MUSIC_DIR, "game_music.ogg")
        }
        self.current_music = None
        # Start menu music immediately if available
        self._play_music_for_state(STATE_MENU)

    def _play_music_for_state(self, state):
        """Plays background music corresponding to the game state."""
        if state in self.music_files and os.path.exists(self.music_files[state]):
            if self.current_music != self.music_files[state]:
                try:
                    pygame.mixer.music.load(self.music_files[state])
                    pygame.mixer.music.play(-1) # Loop indefinitely
                    self.current_music = self.music_files[state]
                    print(f"Playing music: {self.current_music}")
                except pygame.error as e:
                    print(f"Error loading/playing music {self.music_files[state]}: {e}")
                    self.current_music = None
        elif self.current_music is not None:
             try:
                 pygame.mixer.music.stop()
                 self.current_music = None
             except pygame.error as e:
                 print(f"Error stopping music: {e}")

    def _load_high_score(self):
        """Load high score from file."""
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    return int(f.read().strip())
            else:
                return 0
        except (ValueError, IOError) as e:
            print(f"Error loading high score: {e}. Resetting to 0.")
            return 0

    def save_high_score(self):
        """Save the current high score to file."""
        try:
            with open(HIGHSCORE_FILE, 'w') as f:
                f.write(str(self.high_score))
        except IOError as e:
            print(f"Error saving high score: {e}")

    def _start_transition(self, next_state):
        self.previous_state = self.current_state # Store previous state *before* transition
        self.next_state = next_state
        self.current_state = STATE_TRANSITION
        self.transition_alpha = 0
        if self.previous_state == STATE_RESULT:
             self.new_highscore_achieved = False # Reset flag when leaving result screen

    def _initialize_images(self):
        """Initialize with default images or create placeholder ones"""
        image_files = {
            "Rock": "rock.png",
            "Paper": "paper.png",
            "Scissors": "scissors.png",
            "Background": "background.png",
            "HighscoreIcon": "highscore_icon.png" # Optional icon
        }
        
        for name, filename in image_files.items():
            path = os.path.join(IMAGE_DIR, filename)
            try:
                if os.path.exists(path):
                    self.images[name] = pygame.image.load(path).convert_alpha()
                elif name != "HighscoreIcon":
                    self.images[name] = self._create_placeholder_image(name)
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                if name != "HighscoreIcon":
                     self.images[name] = self._create_placeholder_image(name)
        
        if "Background" in self.images:
            try:
                self.images["Background"] = pygame.transform.scale(self.images["Background"], (self.width, self.height))
            except Exception as e:
                print(f"Error scaling background image: {e}")
                self.images["Background"] = self._create_placeholder_image("Background")

    def _create_placeholder_image(self, name):
        """Create a simple placeholder surface for missing images"""
        if name == "Background":
            surf = pygame.Surface((self.width, self.height))
            for y in range(self.height):
                color_val = 30 + int(40 * (y / self.height))
                surf.fill((color_val, color_val, color_val + 20), (0, y, self.width, 1))
        else:
            surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            
            color = C_MENU_DEFAULT
            radius = 45
            center = (50, 50)
            
            if name == "Rock": color = (150, 150, 150); pygame.draw.circle(surf, color, center, radius)
            elif name == "Paper": color = (255, 255, 255); pygame.draw.rect(surf, color, (5, 5, 90, 90), border_radius=10)
            elif name == "Scissors": color = (200, 200, 250); pygame.draw.polygon(surf, color, [(50, 5), (95, 95), (5, 95)])
            
            try:
                font = pygame.font.SysFont(None, 24)
                text_surf = font.render(name, True, (0, 0, 0))
                text_rect = text_surf.get_rect(center=(50, 50))
                surf.blit(text_surf, text_rect)
            except Exception: pass
        return surf
    
    def update(self, gesture):
        """Update game state based on detected gesture and state"""
        if self.current_state == STATE_TRANSITION:
            self._update_transition()
        elif self.current_state == STATE_MENU:
            self._update_menu(gesture)
        elif self.current_state == STATE_PLAYING:
            self._update_game(gesture)
        elif self.current_state == STATE_RESULT:
            self._update_result(gesture)

    def _update_transition(self):
        """Handle fade in/out transitions and music changes"""
        self.transition_alpha += TRANSITION_SPEED
        if self.transition_alpha >= 255:
            self.transition_alpha = 255
            self.current_state = self.next_state
            self.next_state = None
            self._play_music_for_state(self.current_state) # Update music for new state
            
            # Reset timers or states needed for the new state
            if self.current_state == STATE_PLAYING:
                self.user_choice, self.computer_choice, self.result = None, None, None
                # Reset score only if coming from menu
                if self.previous_state == STATE_MENU:
                     self.user_score = 0
                     self.computer_score = 0
                     self.new_highscore_achieved = False
                     self.player_choice_history.clear()
            elif self.current_state == STATE_RESULT:
                 self.timer = time.time() # Start timer for result display
            elif self.current_state == STATE_MENU:
                 self.is_selecting_difficulty = False # Ensure difficulty selection is reset

    def _update_menu(self, gesture):
        """Handle menu navigation and selection, including difficulty"""
        current_time = time.time()
        confirmed = self.feedback.gesture_confirmed
        
        if self.is_selecting_difficulty:
            # Handle difficulty selection submenu
            if gesture == "Open Palm" and confirmed:
                 if current_time - self.last_menu_change_time > MENU_COOLDOWN:
                     current_diff_index = self.difficulty_options.index(self.difficulty)
                     next_diff_index = (current_diff_index + 1) % len(self.difficulty_options)
                     self.difficulty = self.difficulty_options[next_diff_index]
                     self.last_menu_change_time = current_time
                     self.feedback.gesture_confirmed = False
            elif gesture == "Thumbs Up" and confirmed: # Confirm difficulty
                 self.is_selecting_difficulty = False
                 self.feedback.gesture_confirmed = False
            elif gesture == "Peace Sign" and confirmed: # Cancel difficulty selection
                 self.is_selecting_difficulty = False
                 self.feedback.gesture_confirmed = False
        else:
            # Handle main menu options
            if gesture == "Open Palm" and confirmed:
                if current_time - self.last_menu_change_time > MENU_COOLDOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                    self.last_menu_change_time = current_time
                    self.feedback.gesture_confirmed = False

            elif gesture == "Thumbs Up" and confirmed:
                selected_action = self.menu_options[self.selected_option]
                if selected_action == "Play Game":
                    self._start_transition(STATE_PLAYING)
                elif selected_action == "Difficulty":
                    self.is_selecting_difficulty = True
                    self.last_menu_change_time = current_time # Reset cooldown timer
                elif selected_action == "Exit":
                    self.save_high_score()
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                self.feedback.gesture_confirmed = False
            
            elif gesture == "Peace Sign" and confirmed:
                self.save_high_score()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                self.feedback.gesture_confirmed = False
    
    def _get_computer_choice(self):
        """Determine computer's choice based on difficulty"""
        if self.difficulty == DIFF_HARD and len(self.player_choice_history) > 2:
             # Try to predict and counter player's most frequent recent move
             most_frequent = max(set(self.player_choice_history), key=self.player_choice_history.count)
             # Choose the move that beats the player's likely move
             counter_move = self.win_counters.get(most_frequent)
             # Add some randomness: 75% chance to counter, 25% random
             if counter_move and random.random() < 0.75:
                 return counter_move
             else:
                 return random.choice(self.choices)
        else: # Easy mode or not enough history
            return random.choice(self.choices)

    def _update_game(self, gesture):
        """Handle game input, determine winner, and transition"""
        confirmed = self.feedback.gesture_confirmed

        if confirmed and gesture in self.gesture_map:
            self.user_choice = self.gesture_map[gesture]
            self.player_choice_history.append(self.user_choice) # Record player choice
            self.feedback.gesture_confirmed = False 
            
            self.computer_choice = self._get_computer_choice()
            
            score_multiplier = 2 if self.difficulty == DIFF_HARD else 1

            if self.user_choice == self.computer_choice:
                self.result = "Draw"
            elif self.win_counters[self.computer_choice] == self.user_choice:
                self.result = "You Win!"
                self.user_score += score_multiplier
                if self.user_score > self.high_score:
                     self.high_score = self.user_score
                     self.new_highscore_achieved = True
            else:
                self.result = "Computer Wins!"
                self.computer_score += 1
            
            self._start_transition(STATE_RESULT)
        
        elif gesture == "Peace Sign" and confirmed:
             self._start_transition(STATE_MENU)
             self.feedback.gesture_confirmed = False

    def _update_result(self, gesture):
        """Handle result state, wait, and return to menu or playing state"""
        confirmed = self.feedback.gesture_confirmed

        if self.timer > 0 and time.time() - self.timer >= RESULT_DELAY:
            self._start_transition(STATE_PLAYING)
            self.timer = 0
        
        elif gesture == "Peace Sign" and confirmed:
            self._start_transition(STATE_MENU)
            self.feedback.gesture_confirmed = False
        elif gesture == "Thumbs Up" and confirmed:
            self._start_transition(STATE_PLAYING)
            self.feedback.gesture_confirmed = False
    
    def render(self, display, frame):
        """Render the game based on the current state, applying transitions"""
        # Draw background
        if "Background" in self.images: display.blit(self.images["Background"], (0, 0))
        else: display.fill(C_BACKGROUND)
        
        # --- Render main state content onto a separate surface --- 
        state_render_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if self.current_state == STATE_MENU:
            self._render_menu(state_render_surface)
        elif self.current_state == STATE_PLAYING:
            # Pass the *raw* detected gesture for highlighting choices
            self._render_game(state_render_surface, self.feedback.last_gesture)
        elif self.current_state == STATE_RESULT:
            self._render_result(state_render_surface)
        
        # Apply alpha for state transitions
        if self.current_state == STATE_TRANSITION:
             alpha = max(0, 255 - self.transition_alpha * (255 // (TRANSITION_SPEED or 1))) # Adjust alpha calculation
             state_render_surface.set_alpha(int(alpha))
        elif self.next_state is not None:
             state_render_surface.set_alpha(int(self.transition_alpha * (255 // (TRANSITION_SPEED or 1))))
        
        display.blit(state_render_surface, (0,0))
        # ----------------------------------------------------------

        # --- Render Overlay elements (Webcam, Score, Highscore) --- 
        overlay_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._render_webcam(overlay_surface, frame)
        self._render_score(overlay_surface)
        if self.current_state in [STATE_MENU, STATE_RESULT]:
             self._render_highscore(overlay_surface)
        
        # Apply transition alpha to the overlay as well (fade out with old state)
        if self.current_state == STATE_TRANSITION:
            alpha = max(0, 255 - self.transition_alpha * (255 // (TRANSITION_SPEED or 1)))
            overlay_surface.set_alpha(int(alpha))
        # No fade-in needed for overlay usually, it appears with the new state

        display.blit(overlay_surface, (0,0))
        # -----------------------------------------------------------

    def _render_webcam(self, display, frame):
        """Render the processed webcam frame onto the display"""
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pygame = pygame.surfarray.make_surface(np.rot90(frame_rgb))
            
            cam_width = int(self.width * 0.25)
            cam_height = int(cam_width * (frame.shape[0] / frame.shape[1]))
            cam_x = self.width - cam_width - 20
            cam_y = 20
            
            frame_scaled = pygame.transform.scale(frame_pygame, (cam_width, cam_height))
            
            border_rect = pygame.Rect(cam_x - 2, cam_y - 2, cam_width + 4, cam_height + 4)
            pygame.draw.rect(display, C_WEBCAM_BORDER, border_rect, border_radius=5)
            display.blit(frame_scaled, (cam_x, cam_y))
        except Exception as e: print(f"Error rendering webcam feed: {e}")

    def _render_score(self, display):
        """Render the current score with background"""
        score_text = self.font_score.render(f"Score: You {self.user_score} - Comp {self.computer_score}", True, C_SCORE)
        score_rect = score_text.get_rect(bottomleft=(20, self.height - 20))
        bg_rect = score_rect.inflate(10, 5)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill(C_SCORE_BG)
        display.blit(bg_surf, bg_rect.topleft)
        display.blit(score_text, score_rect)

    def _render_highscore(self, display):
         """Render the high score with icon."""
         text = f"High Score: {self.high_score}"
         highscore_surf = self.font_highscore.render(text, True, C_HIGHSCORE)
         highscore_rect = highscore_surf.get_rect(topright=(self.width - 20, self.height - 50))
         
         icon_offset = 0
         if "HighscoreIcon" in self.images:
             try:
                 icon = pygame.transform.scale(self.images["HighscoreIcon"], (30, 30))
                 icon_rect = icon.get_rect(right=highscore_rect.left - 10, centery=highscore_rect.centery)
                 display.blit(icon, icon_rect)
                 icon_offset = icon_rect.width + 10
             except Exception as e: print(f"Error rendering highscore icon: {e}")

         display.blit(highscore_surf, highscore_rect)
         
         # Flashing "New High Score!" on Result screen
         if self.new_highscore_achieved and self.current_state == STATE_RESULT:
             if int(time.time() * 2) % 2 == 0:
                 new_hs_text = self.font_score.render("New High Score!", True, C_HIGHSCORE)
                 new_hs_rect = new_hs_text.get_rect(center=(self.width // 2, self.height * 0.3))
                 display.blit(new_hs_text, new_hs_rect)

    def _render_menu(self, display):
        """Render the main menu screen, including difficulty selection"""
        # Title
        title = self.font_title.render("Gesture Warriors", True, C_TITLE)
        title_rect = title.get_rect(center=(self.width // 2, self.height * 0.15))
        display.blit(title, title_rect)
        
        # Instructions
        instr_y = title_rect.bottom + 40
        instr1_text = "Open Palm: Cycle | Thumbs Up: Select | Peace Sign: Exit/Back"
        instr1 = self.font_instr.render(instr1_text, True, C_INSTRUCTIONS)
        instr1_rect = instr1.get_rect(center=(self.width // 2, instr_y))
        display.blit(instr1, instr1_rect)
        
        # Menu options / Difficulty Selection
        menu_start_y = self.height * 0.45
        if self.is_selecting_difficulty:
            # Show difficulty options
             diff_title = self.font_menu.render("Select Difficulty:", True, C_TITLE)
             diff_rect = diff_title.get_rect(center=(self.width // 2, menu_start_y))
             display.blit(diff_title, diff_rect)

             for i, diff_option in enumerate(self.difficulty_options):
                 is_selected = (diff_option == self.difficulty)
                 color = C_DIFFICULTY_HARD if diff_option == DIFF_HARD else C_DIFFICULTY_EASY
                 text = self.font_menu.render(diff_option, True, color)
                 text_rect = text.get_rect(center=(self.width // 2, menu_start_y + 80 + i * 80))
                 
                 if is_selected:
                      highlight_rect = text_rect.inflate(40, 20)
                      highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
                      highlight_surf.fill((color[0], color[1], color[2], 50))
                      pygame.draw.rect(highlight_surf, (color[0], color[1], color[2], 150), highlight_surf.get_rect(), 3, border_radius=10)
                      display.blit(highlight_surf, highlight_rect.topleft)
                 display.blit(text, text_rect)
        else:
            # Show main menu options
            for i, option in enumerate(self.menu_options):
                selected = (i == self.selected_option)
                color = C_MENU_SELECTED if selected else C_MENU_DEFAULT
                option_text = option
                if option == "Difficulty":
                    option_text += f": {self.difficulty}"
                    color = C_DIFFICULTY_HARD if self.difficulty == DIFF_HARD else C_DIFFICULTY_EASY
                    if selected: color = C_MENU_SELECTED # Override color if selected
                
                text = self.font_menu.render(option_text, True, color)
                text_rect = text.get_rect(center=(self.width // 2, menu_start_y + i * 80))
                
                if selected:
                    highlight_rect = text_rect.inflate(40, 20)
                    highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
                    highlight_surf.fill((C_MENU_SELECTED[0], C_MENU_SELECTED[1], C_MENU_SELECTED[2], 50))
                    pygame.draw.rect(highlight_surf, (C_MENU_SELECTED[0], C_MENU_SELECTED[1], C_MENU_SELECTED[2], 150), highlight_surf.get_rect(), 3, border_radius=10)
                    display.blit(highlight_surf, highlight_rect.topleft)
                display.blit(text, text_rect)
    
    def _render_game(self, display, current_gesture):
        """Render the main game playing screen with choice highlighting"""
        title = self.font_title.render("Show Your Hand!", True, C_TITLE)
        title_rect = title.get_rect(center=(self.width // 2, self.height * 0.15))
        display.blit(title, title_rect)
        
        instr_y = title_rect.bottom + 20
        instr_map = self.gesture_map
        instr_text = " | ".join([f"{g} = {c}" for g, c in instr_map.items()])
        instr = self.font_instr.render(instr_text, True, C_INSTRUCTIONS)
        instr_rect = instr.get_rect(center=(self.width // 2, instr_y))
        display.blit(instr, instr_rect)
        instr2 = self.font_instr.render("Hold Gesture to Confirm", True, C_INSTRUCTIONS)
        instr2_rect = instr2.get_rect(center=(self.width // 2, instr_y + 35))
        display.blit(instr2, instr2_rect)
        
        choice_size = int(self.width * 0.15)
        spacing = int(self.width * 0.05)
        total_width = 3 * choice_size + 2 * spacing
        start_x = (self.width - total_width) // 2
        choices_y = self.height * 0.45
        
        detected_choice = self.gesture_map.get(current_gesture, None)
        
        for i, choice in enumerate(self.choices):
            img_rect = pygame.Rect(start_x + i * (choice_size + spacing), choices_y, choice_size, choice_size)
            
            # Draw image
            if choice in self.images:
                try:
                    img = pygame.transform.scale(self.images[choice], (choice_size, choice_size))
                    display.blit(img, img_rect.topleft)
                    # Add highlight if this choice matches current raw gesture
                    if choice == detected_choice:
                         highlight_surf = pygame.Surface(img_rect.size, pygame.SRCALPHA)
                         highlight_surf.fill(C_CHOICE_HIGHLIGHT)
                         display.blit(highlight_surf, img_rect.topleft)
                except Exception as e: print(f"Error rendering choice image {choice}: {e}"); pygame.draw.rect(display, C_PLACEHOLDER_BG, img_rect, border_radius=10)
            else: pygame.draw.rect(display, C_PLACEHOLDER_BG, img_rect, border_radius=10)
            
            # Add label
            text = self.font_choice.render(choice, True, C_TITLE)
            text_rect = text.get_rect(center=(img_rect.centerx, img_rect.bottom + 25))
            display.blit(text, text_rect)
    
    def _render_result(self, display):
        """Render the result screen with simple win/loss animation indication"""
        result_color = C_DRAW
        if self.result == "You Win!": result_color = C_WIN
        elif self.result == "Computer Wins!": result_color = C_LOSE
            
        title = self.font_title.render(self.result, True, result_color)
        title_rect = title.get_rect(center=(self.width // 2, self.height * 0.15))
        display.blit(title, title_rect)
        
        choice_y = title_rect.bottom + 50
        font = self.font_score
        user_text = font.render(f"You: {self.user_choice}", True, C_TITLE)
        comp_text = font.render(f"Comp: {self.computer_choice}", True, C_TITLE)
        user_rect = user_text.get_rect(center=(self.width // 2, choice_y))
        comp_rect = comp_text.get_rect(center=(self.width // 2, choice_y + 45))
        display.blit(user_text, user_rect)
        display.blit(comp_text, comp_rect)
        
        choice_size = int(self.width * 0.2)
        spacing = int(self.width * 0.1)
        img_y = comp_rect.bottom + 40
        user_img_x = self.width // 2 - choice_size - spacing // 2
        comp_img_x = self.width // 2 + spacing // 2

        # Determine winner/loser scale factor for subtle animation
        user_scale = 1.0
        comp_scale = 1.0
        if self.result == "You Win!": user_scale = 1.1; comp_scale = 0.9
        elif self.result == "Computer Wins!": user_scale = 0.9; comp_scale = 1.1
        # Apply pulsing effect to scales
        pulse = 1.0 + 0.05 * np.sin(time.time() * 5) # Small pulse
        user_scale *= pulse
        comp_scale *= pulse

        # User choice image
        if self.user_choice in self.images:
             try:
                 img_user_orig = self.images[self.user_choice]
                 scaled_size = (int(choice_size * user_scale), int(choice_size * user_scale))
                 img_user = pygame.transform.smoothscale(img_user_orig, scaled_size)
                 img_rect = img_user.get_rect(center=(user_img_x + choice_size//2, img_y + choice_size//2))
                 display.blit(img_user, img_rect)
             except Exception as e: print(f"Error rendering result image {self.user_choice}: {e}"); pygame.draw.rect(display, C_PLACEHOLDER_BG, (user_img_x, img_y, choice_size, choice_size), border_radius=10)
        
        # Computer choice image
        if self.computer_choice in self.images:
             try:
                 img_comp_orig = self.images[self.computer_choice]
                 scaled_size = (int(choice_size * comp_scale), int(choice_size * comp_scale))
                 img_comp = pygame.transform.smoothscale(img_comp_orig, scaled_size)
                 img_rect = img_comp.get_rect(center=(comp_img_x + choice_size//2, img_y + choice_size//2))
                 display.blit(img_comp, img_rect)
             except Exception as e: print(f"Error rendering result image {self.computer_choice}: {e}"); pygame.draw.rect(display, C_PLACEHOLDER_BG, (comp_img_x, img_y, choice_size, choice_size), border_radius=10)
        
        instr_y = img_y + choice_size + 60 # Adjusted Y
        instr1 = self.font_instr.render("Hold Thumbs Up to Play Again", True, C_INSTRUCTIONS)
        instr1_rect = instr1.get_rect(center=(self.width // 2, instr_y))
        display.blit(instr1, instr1_rect)
        instr2 = self.font_instr.render("Hold Peace Sign for Menu", True, C_INSTRUCTIONS)
        instr2_rect = instr2.get_rect(center=(self.width // 2, instr_y + 35))
        display.blit(instr2, instr2_rect) 