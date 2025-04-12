import pygame
import os
import cv2
import numpy as np
import random
import time

class FeedbackModule:
    def __init__(self):
        # Initialize pygame mixer for sounds
        pygame.mixer.init()
        
        # Create sounds directory if it doesn't exist
        if not os.path.exists('assets/sounds'):
            os.makedirs('assets/sounds', exist_ok=True)
        
        # Load sound effects
        self.sounds = {}
        self._initialize_default_sounds()
        
        # Visual feedback elements
        self.last_gesture = None
        self.gesture_confirmed = False
        self.flash_counter = 0
        
        # Enhanced visual effects
        self.particles = []  # For particle effects
        self.gesture_hold_time = 0  # For tracking how long a gesture is held
        self.hold_threshold = 1.0   # Seconds to consider a gesture "held"
        self.last_gesture_time = time.time()
        
        # Animation settings
        self.animation_frame = 0
        self.animation_speed = 0.5  # Seconds per animation frame
        self.last_animation_time = time.time()
        
        # Generate synthetic sounds if none exist
        self._generate_missing_sounds()
        
    def _initialize_default_sounds(self):
        """Initialize with default sounds if files don't exist"""
        sound_files = {
            "Open Palm": "open_palm.wav",
            "Fist": "fist.wav",
            "Thumbs Up": "thumbs_up.wav",
            "Peace Sign": "peace_sign.wav",
            "Gesture Change": "gesture_change.wav",
            "Gesture Hold": "gesture_hold.wav"
        }
        
        # Try to load existing sound files
        for gesture, filename in sound_files.items():
            try:
                # Try to load existing sound file
                if os.path.exists(f"assets/sounds/{filename}"):
                    self.sounds[gesture] = pygame.mixer.Sound(f"assets/sounds/{filename}")
                else:
                    # Set volume to zero for non-existing sounds to avoid errors
                    self.sounds[gesture] = None
            except:
                self.sounds[gesture] = None
    
    def _generate_missing_sounds(self):
        """Generate synthetic sound effects for missing sound files using pygame"""
        # Define frequencies for different gestures
        sound_frequencies = {
            "Open Palm": 440,      # A4 note
            "Fist": 261.63,        # C4 note
            "Thumbs Up": 329.63,   # E4 note
            "Peace Sign": 391.99,  # G4 note
            "Gesture Change": 587.33,  # D5 note
            "Gesture Hold": 880    # A5 note
        }
        
        # Check which sounds we need to create
        for gesture, freq in sound_frequencies.items():
            if gesture not in self.sounds or self.sounds[gesture] is None:
                try:
                    # Create a simple pygame sound array
                    sample_rate = 44100
                    duration = 0.3  # seconds
                    n_samples = int(round(duration * sample_rate))
                    
                    # Create a simple waveform
                    buf = np.zeros(n_samples, dtype=np.int16)
                    
                    # Different waveform based on gesture
                    if gesture == "Open Palm":
                        # Ascending tone
                        for i in range(n_samples):
                            t = float(i) / sample_rate
                            frequency = freq + 100 * t  # Increase frequency over time
                            buf[i] = int(32767.0 * np.sin(2.0 * np.pi * frequency * t))
                    elif gesture == "Gesture Hold":
                        # Pulsing tone
                        for i in range(n_samples):
                            t = float(i) / sample_rate
                            amplitude = 0.5 + 0.5 * np.sin(2.0 * np.pi * 5.0 * t)
                            buf[i] = int(32767.0 * amplitude * np.sin(2.0 * np.pi * freq * t))
                    else:
                        # Standard tone with envelope
                        for i in range(n_samples):
                            t = float(i) / sample_rate
                            # Apply ADSR envelope
                            if t < 0.05:  # Attack
                                amplitude = t / 0.05
                            elif t < 0.2:  # Decay
                                amplitude = 1.0 - 0.3 * ((t - 0.05) / 0.15)
                            elif t < 0.25:  # Release
                                amplitude = 0.7 * (1 - ((t - 0.2) / 0.05))
                            else:
                                amplitude = 0
                            buf[i] = int(32767.0 * amplitude * np.sin(2.0 * np.pi * freq * t))
                    
                    # Create sound from buffer
                    sound = pygame.mixer.Sound(buffer=buf)
                    # Set volume based on gesture type
                    sound.set_volume(0.5)
                    self.sounds[gesture] = sound
                except Exception as e:
                    print(f"Failed to create synthetic sound for {gesture}: {e}")
                    self.sounds[gesture] = None
    
    def play_sound(self, gesture):
        """Play a sound effect based on the detected gesture"""
        if gesture in self.sounds and self.sounds[gesture] is not None:
            # Play the sound if it exists
            self.sounds[gesture].play()
    
    def provide_visual_feedback(self, frame, gesture):
        """Add visual feedback to the frame based on gesture"""
        current_time = time.time()
        
        # Update animation frame if needed
        if current_time - self.last_animation_time > self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % 10  # 10 frames of animation
            self.last_animation_time = current_time
        
        # Handle gesture change or hold
        if gesture != self.last_gesture:
            self.gesture_confirmed = False
            self.flash_counter = 10  # Number of frames to flash
            self.gesture_hold_time = 0
            self.last_gesture_time = current_time
            self.last_gesture = gesture
            # Play sound when gesture changes
            self.play_sound(gesture)
            self.play_sound("Gesture Change")
            # Reset particles
            self.particles = []
        else:
            # Update hold time for the current gesture
            self.gesture_hold_time = current_time - self.last_gesture_time
            
            # If gesture is held for a certain time, trigger confirmation
            if self.gesture_hold_time >= self.hold_threshold and not self.gesture_confirmed:
                self.gesture_confirmed = True
                self.play_sound("Gesture Hold")
                # Generate particles for confirmed gesture
                self._generate_particles(frame)
        
        # Apply common visual enhancements
        self._enhance_hand_visibility(frame)
        
        # Add visual effect based on gesture
        if gesture == "Open Palm":
            self._render_open_palm_feedback(frame)
        elif gesture == "Fist":
            self._render_fist_feedback(frame)
        elif gesture == "Thumbs Up":
            self._render_thumbs_up_feedback(frame)
        elif gesture == "Peace Sign":
            self._render_peace_sign_feedback(frame)
        
        # Update and draw particles if any
        self._update_particles(frame)
        
        # Add progress bar if holding a gesture
        if self.gesture_hold_time > 0 and self.gesture_hold_time < self.hold_threshold:
            progress = min(self.gesture_hold_time / self.hold_threshold, 1.0)
            self._draw_hold_progress(frame, progress)
        
        return frame
    
    def _enhance_hand_visibility(self, frame):
        """Apply enhancements to make hand landmarks more visible"""
        # Apply a subtle vignette effect
        rows, cols = frame.shape[:2]
        
        # Create a radial gradient mask from center
        kernel_x = cv2.getGaussianKernel(cols, cols/4)
        kernel_y = cv2.getGaussianKernel(rows, rows/4)
        kernel = kernel_y * kernel_x.T
        mask = 255 * kernel / np.linalg.norm(kernel)
        
        # Normalize the mask to the range [0.7, 1.0] so it's subtle
        mask = 0.7 + 0.3 * (mask / 255)
        
        # Apply the mask to each channel
        for i in range(3):
            frame[:, :, i] = frame[:, :, i] * mask
    
    def _generate_particles(self, frame):
        """Generate particles for visual effects based on current gesture"""
        num_particles = 30
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Different particle colors based on gesture
        if self.last_gesture == "Open Palm":
            color = (0, 255, 0)  # Green
        elif self.last_gesture == "Fist":
            color = (0, 0, 255)  # Red
        elif self.last_gesture == "Thumbs Up":
            color = (0, 255, 255)  # Yellow
        elif self.last_gesture == "Peace Sign":
            color = (255, 0, 0)  # Blue
        else:
            color = (255, 255, 255)  # White
        
        # Create particles
        for _ in range(num_particles):
            # Random position near the center
            x = center_x + random.randint(-100, 100)
            y = center_y + random.randint(-100, 100)
            
            # Random velocity
            vx = random.uniform(-3, 3)
            vy = random.uniform(-3, 3)
            
            # Random size and lifespan
            size = random.randint(3, 10)
            lifespan = random.uniform(0.5, 2.0)
            
            self.particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'size': size,
                'color': color,
                'lifespan': lifespan,
                'age': 0
            })
    
    def _update_particles(self, frame):
        """Update and draw particles"""
        current_time = time.time()
        dt = min(1/30, current_time - self.last_animation_time)  # Limit to 30fps for physics
        
        # Update each particle
        new_particles = []
        for p in self.particles:
            # Update position
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # Apply gravity
            p['vy'] += 0.1
            
            # Update age
            p['age'] += dt
            
            # Draw particle if still alive
            if p['age'] < p['lifespan']:
                # Fade out based on age
                alpha = 1.0 - (p['age'] / p['lifespan'])
                # Adjust color with alpha
                color = (
                    int(p['color'][0] * alpha),
                    int(p['color'][1] * alpha),
                    int(p['color'][2] * alpha)
                )
                
                # Draw the particle
                cv2.circle(
                    frame,
                    (int(p['x']), int(p['y'])),
                    int(p['size'] * (1 - p['age'] / p['lifespan'])),  # Shrink over time
                    color,
                    -1
                )
                
                new_particles.append(p)
        
        # Replace particles list with only living particles
        self.particles = new_particles
    
    def _draw_hold_progress(self, frame, progress):
        """Draw a progress bar showing gesture hold progress"""
        h, w = frame.shape[:2]
        bar_width = int(w * 0.6)
        bar_height = 15
        x = (w - bar_width) // 2
        y = h - 50
        
        # Draw background
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), -1)
        
        # Draw progress
        progress_width = int(bar_width * progress)
        
        # Color the bar based on progress
        if progress < 0.5:
            # Gradient from red to yellow
            g = int(255 * (progress * 2))
            color = (0, g, 255)
        else:
            # Gradient from yellow to green
            r = int(255 * (2 - progress * 2))
            color = (0, 255, r)
            
        cv2.rectangle(frame, (x, y), (x + progress_width, y + bar_height), color, -1)
        
        # Draw border
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 1)
        
        # Draw text
        cv2.putText(
            frame,
            "HOLD",
            (x + bar_width // 2 - 20, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
    
    def _render_open_palm_feedback(self, frame):
        """Render feedback specific to the Open Palm gesture"""
        h, w = frame.shape[:2]
        
        # Add navigation arrows
        cv2.putText(frame, "NAVIGATE", (w//2-60, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Draw animated navigation arrows
        arrow_size = 30
        thickness = 2
        
        # Top arrow with animation
        arrow_y = 80 + int(5 * np.sin(time.time() * 4))
        pts_top = np.array([
            [w//2, arrow_y],
            [w//2 - arrow_size//2, arrow_y + arrow_size],
            [w//2 + arrow_size//2, arrow_y + arrow_size]
        ], np.int32)
        cv2.fillPoly(frame, [pts_top], (0, 255, 0))
        
        # Only show these arrows if gesture is confirmed (held long enough)
        if self.gesture_confirmed:
            # Left arrow
            pts_left = np.array([
                [arrow_size * 2, h//2],
                [arrow_size * 3, h//2 - arrow_size//2],
                [arrow_size * 3, h//2 + arrow_size//2]
            ], np.int32)
            cv2.fillPoly(frame, [pts_left], (0, 255, 0))
            
            # Right arrow
            pts_right = np.array([
                [w - arrow_size * 2, h//2],
                [w - arrow_size * 3, h//2 - arrow_size//2],
                [w - arrow_size * 3, h//2 + arrow_size//2]
            ], np.int32)
            cv2.fillPoly(frame, [pts_right], (0, 255, 0))
    
    def _render_fist_feedback(self, frame):
        """Render feedback specific to the Fist gesture"""
        h, w = frame.shape[:2]
        
        # Add selection box with pulsing effect
        pulse = 0.5 + 0.5 * np.sin(time.time() * 5)  # Value between 0 and 1
        thickness = int(3 + 3 * pulse)
        
        if self.flash_counter > 0:
            # Flash effect
            thickness = 6 if self.flash_counter % 2 == 0 else 3
            self.flash_counter -= 1
        
        # Draw selection box
        cv2.rectangle(frame, (50, 50), (w-50, h-50), 
                     (0, 0, int(200 + 55 * pulse)), thickness)
        
        # Text feedback with size animation
        text_size = 1.0 + 0.2 * pulse
        cv2.putText(frame, "SELECT", (w//2-70, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 255), 2, cv2.LINE_AA)
        
        # Add target icon in the center if gesture is confirmed
        if self.gesture_confirmed:
            center_x, center_y = w//2, h//2
            
            # Draw concentric circles
            cv2.circle(frame, (center_x, center_y), 40, (0, 0, 255), 2)
            cv2.circle(frame, (center_x, center_y), 20, (0, 0, 255), 3)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Draw crosshairs
            cv2.line(frame, (center_x - 60, center_y), (center_x + 60, center_y), (0, 0, 255), 1)
            cv2.line(frame, (center_x, center_y - 60), (center_x, center_y + 60), (0, 0, 255), 1)
    
    def _render_thumbs_up_feedback(self, frame):
        """Render feedback specific to the Thumbs Up gesture"""
        h, w = frame.shape[:2]
        
        if self.flash_counter > 0:
            # Flash effect
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
            self.flash_counter -= 1
            
        # Add a pulsing green ring
        center_x, center_y = w//2, h//2
        pulse = 0.5 + 0.5 * np.sin(time.time() * 4)  # Value between 0 and 1
        radius = int(100 + 20 * pulse)
        thickness = int(2 + 3 * pulse)
        
        cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), thickness)
        
        # Text effect
        text_opacity = int(200 + 55 * pulse)
        cv2.putText(frame, "CONFIRM", (w//2-80, 50), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, text_opacity, 0), 2, cv2.LINE_AA)
        
        # Show checkmark animation when confirmed
        if self.gesture_confirmed:
            # Create checkmark points
            check_size = 60
            check_x = w//2
            check_y = h//2
            
            # Animate the check mark drawing
            animation_progress = min(1.0, self.animation_frame / 10)
            
            # Calculate points for the checkmark
            pt1 = (int(check_x - check_size), int(check_y))
            pt2 = (int(check_x - check_size//2), int(check_y + check_size//2))
            pt3 = (int(check_x + check_size), int(check_y - check_size//2))
            
            # Draw first part of checkmark
            if animation_progress > 0.5:
                first_progress = min(1.0, (animation_progress - 0.5) * 2)
                cv2.line(frame, pt1, 
                        (int(pt1[0] + (pt2[0] - pt1[0]) * first_progress),
                         int(pt1[1] + (pt2[1] - pt1[1]) * first_progress)),
                        (0, 255, 0), 6)
            
            # Draw second part of checkmark
            if animation_progress > 0.0:
                second_progress = min(1.0, animation_progress * 2)
                cv2.line(frame, pt2, 
                        (int(pt2[0] + (pt3[0] - pt2[0]) * second_progress),
                         int(pt2[1] + (pt3[1] - pt2[1]) * second_progress)),
                        (0, 255, 0), 6)
    
    def _render_peace_sign_feedback(self, frame):
        """Render feedback specific to the Peace Sign gesture"""
        h, w = frame.shape[:2]
        
        if self.flash_counter > 0:
            # Flash effect with blue overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (255, 0, 0), -1)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
            self.flash_counter -= 1
            
        # Create animated X to show cancellation
        center_x, center_y = w//2, h//2
        x_size = 50
        
        # Pulse effect for the X
        pulse = 0.5 + 0.5 * np.sin(time.time() * 5)  # Value between 0 and 1
        thickness = int(2 + 4 * pulse)
        
        # Draw X
        cv2.line(frame, (center_x - x_size, center_y - x_size), 
                (center_x + x_size, center_y + x_size), (255, 0, 0), thickness)
        cv2.line(frame, (center_x + x_size, center_y - x_size), 
                (center_x - x_size, center_y + x_size), (255, 0, 0), thickness)
        
        # Text effect with animation
        text_opacity = int(200 + 55 * pulse)
        cv2.putText(frame, "CANCEL", (w//2-80, 50), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1.2, (text_opacity, 0, 0), 2, cv2.LINE_AA)
        
        # Extra effect when confirmed - circle with slash
        if self.gesture_confirmed:
            # Draw circle
            cv2.circle(frame, (center_x, center_y), 80, (255, 0, 0), 3)
            
            # Draw diagonal line through the circle
            cv2.line(frame, (center_x - 100, center_y - 80), 
                    (center_x + 100, center_y + 80), (255, 0, 0), 6) 