# Gesture Warriors - Hand Gesture Rock Paper Scissors Game

A modern, interactive implementation of the classic Rock Paper Scissors game using computer vision and hand gesture recognition. Play against an AI opponent using your webcam!

## Features

- **Real-time Hand Gesture Recognition**: Play using natural hand gestures captured through your webcam
- **Dynamic Difficulty Levels**:
  - Easy Mode: Random computer choices
  - Hard Mode: AI learns from your play patterns with a 2x score multiplier
- **Rich Visual Feedback**:
  - Real-time gesture detection highlighting
  - Animated win/lose effects
  - Webcam feed with visual feedback
- **Score Tracking**:
  - Persistent high score system
  - Score multipliers for hard mode
  - New high score celebrations
- **Background Music & Sound Effects**:
  - Different music for menu and gameplay
  - Audio feedback for actions
- **Polished UI**:
  - Smooth state transitions
  - Intuitive menu navigation
  - Clear visual instructions

## Controls

- **Open Palm**: Cycle through menu options / Play Paper
- **Fist**: Play Rock
- **Peace Sign**: Exit/Back / Play Scissors
- **Thumbs Up**: Select menu option / Play again

## Requirements

- Python 3.7+
- OpenCV (cv2)
- PyGame
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Xoya0/Stone-Paper-Scissors-Using-Hand-Gesture-.git
cd Stone-Paper-Scissors-Using-Hand-Gesture-
```

2. Install required packages:
```bash
pip install opencv-python pygame numpy
```

3. Run the game:
```bash
python src/main.py
```

## Game Structure

- `src/main.py`: Main game loop and initialization
- `src/game_engine.py`: Core game logic and rendering
- `src/gesture_recognition.py`: Hand gesture detection and classification
- `src/feedback_module.py`: Visual and audio feedback system

## Optional Assets

The game looks for the following optional assets:
- `assets/images/`: Place your custom images for rock, paper, scissors
- `assets/music/`: Background music files (menu_music.ogg, game_music.ogg)
- `assets/sounds/`: Sound effect files

## Contributing

Feel free to fork the repository and submit pull requests. You can also open issues for bugs or feature requests.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with OpenCV for computer vision
- PyGame for game development
- NumPy for numerical operations 