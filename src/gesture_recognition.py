import cv2
import mediapipe as mp
import numpy as np
import time

class GestureRecognizer:
    def __init__(self):
        # Initialize mediapipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,  # Increased from 0.5
            min_tracking_confidence=0.6    # Increased from 0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.current_gesture = "None"
        self.prev_gesture = "None"
        
        # Gesture stability control
        self.gesture_history = []
        self.history_size = 5  # Number of frames to consider for stability
        self.gesture_confidence = {}
        self.min_gesture_duration = 0.3  # Minimum time (seconds) to confirm a gesture
        self.last_gesture_time = time.time()
        
    def process_frame(self, frame):
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame and find hands
        results = self.hands.process(rgb_frame)
        
        detected_gesture = "None"
        
        # Draw hand annotations on the frame
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Determine the gesture
                detected_gesture = self.recognize_gesture(hand_landmarks)
                
                # Draw fingertip points with different colors
                self._highlight_fingertips(frame, hand_landmarks)
        
        # Apply gesture stability logic
        stabilized_gesture = self._stabilize_gesture(detected_gesture)
        
        # Add text to display both raw and stabilized gestures
        cv2.putText(
            frame,
            f"Gesture: {stabilized_gesture}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )
        
        # Display confidence level for current gesture
        if stabilized_gesture != "None":
            confidence = self.gesture_confidence.get(stabilized_gesture, 0)
            cv2.putText(
                frame,
                f"Confidence: {confidence:.1f}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )
        
        return stabilized_gesture
    
    def _highlight_fingertips(self, frame, landmarks):
        """Highlight fingertips with different colors for better feedback"""
        h, w, _ = frame.shape
        fingertip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        
        for idx, fingertip_id in enumerate(fingertip_ids):
            # Get the landmark position
            landmark = landmarks.landmark[fingertip_id]
            # Convert to pixel coordinates
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            # Draw circle at fingertip
            cv2.circle(frame, (cx, cy), 12, colors[idx], -1)
            cv2.circle(frame, (cx, cy), 12, (255, 255, 255), 2)
    
    def _stabilize_gesture(self, detected_gesture):
        """Stabilize gesture recognition over multiple frames"""
        current_time = time.time()
        
        # Add current detection to history
        self.gesture_history.append(detected_gesture)
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)
        
        # Count occurrences of each gesture in history
        gesture_counts = {}
        for gesture in self.gesture_history:
            if gesture not in gesture_counts:
                gesture_counts[gesture] = 0
            gesture_counts[gesture] += 1
        
        # Update confidence levels for all gestures
        for gesture, count in gesture_counts.items():
            confidence = count / len(self.gesture_history)
            self.gesture_confidence[gesture] = confidence
            
        # Get the most frequent gesture in history
        if gesture_counts:
            most_common_gesture = max(gesture_counts, key=gesture_counts.get)
            confidence = gesture_counts[most_common_gesture] / len(self.gesture_history)
            
            # Only change gesture if it's stable enough or enough time has passed
            if (confidence >= 0.6 and most_common_gesture != self.current_gesture and 
                current_time - self.last_gesture_time >= self.min_gesture_duration):
                self.prev_gesture = self.current_gesture
                self.current_gesture = most_common_gesture
                self.last_gesture_time = current_time
        
        return self.current_gesture
    
    def recognize_gesture(self, landmarks):
        """
        Recognize gestures based on hand landmarks.
        
        Gestures implemented:
        - Open palm: All fingers extended
        - Fist: All fingers closed
        - Thumbs up: Only thumb extended
        - Peace sign: Index and middle finger extended
        """
        # Get landmark positions
        points = []
        for landmark in landmarks.landmark:
            points.append([landmark.x, landmark.y, landmark.z])
        points = np.array(points)
        
        # Get fingertip landmarks and corresponding base points
        fingertip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tip
        finger_base_ids = [2, 5, 9, 13, 17]  # Base points for comparison
        mcp_ids = [1, 5, 9, 13, 17]          # Metacarpophalangeal joints for better reference
        
        # Check if fingers are extended
        extended_fingers = []
        
        # Special case for thumb
        thumb_tip = points[4]
        thumb_ip = points[3]   # Inter-phalangeal joint
        thumb_mcp = points[2]  # Metacarpophalangeal joint
        thumb_cmc = points[1]  # Carpometacarpal joint
        
        # Calculate thumb direction vector (more accurate than simple comparison)
        thumb_direction = thumb_tip - thumb_mcp
        palm_cross = np.cross(points[5] - points[17], points[0] - points[17])
        
        # Check if the thumb is pointing away from the palm
        thumb_extended = np.dot(thumb_direction, palm_cross) < 0
        extended_fingers.append(thumb_extended)
        
        # For other fingers - use improved method with multiple joints
        for i in range(1, 5):  # Index, Middle, Ring, Pinky
            fingertip = points[fingertip_ids[i]]
            pip = points[fingertip_ids[i] - 2]  # Proximal interphalangeal joint
            mcp = points[mcp_ids[i]]            # Metacarpophalangeal joint
            
            # Vector from MCP to PIP
            v1 = pip - mcp
            # Vector from PIP to fingertip
            v2 = fingertip - pip
            
            # Angle between the two segments
            angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
            angle = np.degrees(angle)
            
            # Check if finger is extended based on angle and height
            finger_extended = angle > 160 and fingertip[1] < mcp[1]
            extended_fingers.append(finger_extended)
            
        # Determine gesture based on extended fingers
        if all(extended_fingers):
            return "Open Palm"
        elif not any(extended_fingers):
            return "Fist"
        elif extended_fingers[0] and not any(extended_fingers[1:]):
            return "Thumbs Up"
        elif not extended_fingers[0] and extended_fingers[1] and extended_fingers[2] and not extended_fingers[3] and not extended_fingers[4]:
            return "Peace Sign"
        else:
            return "Unknown" 