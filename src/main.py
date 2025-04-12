import cv2
import pygame
import sys
from gesture_recognition import GestureRecognizer
from game_engine import GameEngine
from feedback_module import FeedbackModule

def main():
    # --- Pygame Initialization ---
    pygame.init()
    pygame.mixer.init() # Initialize mixer *before* other modules that use sound
    
    # --- Game Setup ---
    width, height = 800, 600
    game_display = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Gesture Warriors')
    
    # --- Module Initialization ---
    # Initialize these *after* pygame.mixer.init
    gesture_recognizer = GestureRecognizer()
    feedback = FeedbackModule() # Feedback module uses mixer for synthetic sounds
    game_engine = GameEngine(width, height, feedback) # Game engine uses mixer for music
    
    # --- Webcam Setup ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        pygame.quit()
        return
    
    # --- Game Loop Setup ---
    clock = pygame.time.Clock()
    running = True

    # --- Main Game Loop ---
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        
        # --- Frame Capture & Processing ---
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        frame = cv2.flip(frame, 1) # Mirror frame
        frame_processed = frame.copy() # Copy for processing
        
        # --- Gesture Recognition & Feedback ---
        gesture = gesture_recognizer.process_frame(frame_processed)
        frame_feedback = feedback.provide_visual_feedback(frame_processed, gesture)
        
        # --- Game State Update ---
        game_engine.update(gesture)
        
        # --- Rendering ---
        game_engine.render(game_display, frame_feedback)
        
        # --- Display Update & Clock Tick ---
        pygame.display.update()
        clock.tick(60)
    
    # --- Cleanup ---
    print("Exiting game...")
    game_engine.save_high_score()
    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop() # Stop music
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 