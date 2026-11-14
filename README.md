# Gesture Media Controller

Control music/video playback and system volume with hand gestures, using your webcam.
Built with [MediaPipe](https://developers.google.com/mediapipe) hand tracking, OpenCV, and PyAutoGUI.

## Gestures

Hold your palm facing the camera with fingers pointing up.

| Gesture | Action |
| --- | --- |
| Open palm, held still | Play / pause |
| Swipe open palm right | Next track |
| Swipe open palm left | Previous track |
| Index finger up | Volume up |
| Index + middle finger up | Volume down |
| Fist or anything else | Do nothing |

## Requirements

- Python 3.9 or newer
- A webcam
- Windows, macOS, or Linux

## Installation

```bash
git clone https://github.com/su4aiib/gesture_controller.git
cd gesture_controller
pip install opencv-python mediapipe pyautogui
```

## Usage

```bash
python gesture_controller.py
```

On the first run the script downloads the MediaPipe hand model (`hand_landmarker.task`, about 8 MB)
into the project folder. After that it runs offline.

A window called **Gesture Controller** opens showing your camera feed with the hand skeleton and
the current gesture. Press **q** in that window to quit.

## How it works

1. **Hand detection:** MediaPipe's Hand Landmarker finds one hand and returns 21 landmarks per frame.
2. **Finger detection:** a finger counts as "up" when its tip is above its middle knuckle.
   The four up/down states are mapped to a gesture (palm, index only, index + middle).
3. **Stability:** a gesture must hold for 8 frames before it triggers, which filters out flicker.
4. **Swipes:** the wrist's horizontal movement over the last 0.5 s is tracked. Moving more than
   30% of the frame width counts as a swipe.
5. **Actions:** the script sends media and volume key presses through PyAutoGUI, with cooldowns
   so one gesture doesn't fire repeatedly.

## Tuning

The constants in the "tuning knobs" section of `gesture_controller.py` (just above `main()`) control behaviour:

| Setting | Default | Meaning |
| --- | --- | --- |
| `HOLD_FRAMES` | 8 | Frames a gesture must stay steady before it counts |
| `SWIPE_DIST` | 0.30 | Horizontal hand travel (fraction of frame width) needed for a swipe |
| `SWIPE_WINDOW` | 0.5 | Time window in seconds for measuring a swipe |
| `STILL_DIST` | 0.05 | Maximum movement allowed for a "still" palm (play/pause) |
| `SWIPE_COOLDOWN` | 1.0 | Seconds between swipes |
| `VOL_REPEAT` | 0.25 | Seconds between volume steps while the gesture is held |

## Troubleshooting

- **Camera doesn't open:** the script uses camera index `0`. If you have several cameras, change
  `cv2.VideoCapture(0)` to another index.
- **Gestures trigger by accident:** raise `HOLD_FRAMES` or `SWIPE_DIST`.
- **Gestures are missed:** lower `min_hand_detection_confidence` in the `HandLandmarkerOptions`
  call, or improve the lighting. Keep your palm facing the camera.
- **Media keys do nothing:** some players only respond to keys when their window is focused.
  Media keys like `playpause` and `nexttrack` work system-wide on most setups.

## Project structure

```
.
├── gesture_controller.py   # main script
├── hand_landmarker.task    # MediaPipe model (auto-downloaded on first run, not committed)
├── .gitignore
└── README.md
```

## License

Add a license of your choice before publishing publicly.
