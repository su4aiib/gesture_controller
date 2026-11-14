"""
Gesture media controller (MediaPipe Tasks API version)

Install:  pip install opencv-python mediapipe pyautogui
Run:      python gesture_controller.py      (press q in the window to quit)

Gestures (palm facing the camera, fingers pointing up):
  Open palm, held still   -> play / pause
  Swipe open palm right   -> next track
  Swipe open palm left    -> previous track
  Index finger up         -> volume up
  Index + middle up       -> volume down
  Fist / anything else    -> do nothing
"""

import os
import time
import urllib.request
from collections import deque

import cv2
import mediapipe as mp
import pyautogui
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ======================= PHASE 2: hand detection setup =======================
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

if not os.path.exists(MODEL_PATH):
    print("Downloading hand model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
)
landmarker = vision.HandLandmarker.create_from_options(options)

# ======================= PHASE 3: finger detection ===========================
FINGER_TIPS = [8, 12, 16, 20]   # index, middle, ring, pinky
FINGER_PIPS = [6, 10, 14, 18]   # middle knuckle of each finger


def fingers_up(lm):
    """[index, middle, ring, pinky] -> True if that finger is extended."""
    return [lm[t].y < lm[p].y for t, p in zip(FINGER_TIPS, FINGER_PIPS)]


def classify(up):
    if all(up):
        return "PALM"
    if up == [True, False, False, False]:
        return "VOL_UP"
    if up == [True, True, False, False]:
        return "VOL_DOWN"
    return "NONE"


# ======================= PHASE 4: laptop control =============================
last_fire = {}


def fire(name, key, gap, now):
    """Press a key if its cooldown has passed. Returns True if it fired."""
    if now - last_fire.get(name, 0) >= gap:
        pyautogui.press(key)
        last_fire[name] = now
        return True
    return False


# ======================= PHASE 5: tuning knobs ===============================
HOLD_FRAMES = 8        # frames a gesture must stay the same before it counts
SWIPE_DIST = 0.30      # hand travel (fraction of frame width) to count as swipe
SWIPE_WINDOW = 0.5     # ...within this many seconds
STILL_DIST = 0.05      # max movement allowed for a "still" palm
SWIPE_COOLDOWN = 1.0   # seconds between swipes
VOL_REPEAT = 0.25      # seconds between volume steps while held


def main():
    cap = cv2.VideoCapture(0)
    start = time.time()

    current, streak = "NONE", 0
    palm_armed = True
    wrist_hist = deque()          # (time, wrist_x) for swipe detection
    label, label_until = "", 0

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)

        # ---- Phase 2: detect + draw hand ----
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        now = time.time()
        result = landmarker.detect_for_video(mp_image, int((now - start) * 1000))

        h, w = frame.shape[:2]
        gesture = "NONE"

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]
            pts = [(int(p.x * w), int(p.y * h)) for p in lm]
            for a, b in CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (0, 255, 120), 2)
            for pt in pts:
                cv2.circle(frame, pt, 4, (255, 255, 255), -1)

            # ---- Phase 3: which gesture? ----
            gesture = classify(fingers_up(lm))
            wrist_hist.append((now, lm[0].x))
        else:
            wrist_hist.clear()

        # ---- Phase 5: stability + swipe tracking ----
        while wrist_hist and now - wrist_hist[0][0] > SWIPE_WINDOW:
            wrist_hist.popleft()

        streak = streak + 1 if gesture == current else 1
        current = gesture
        stable = streak >= HOLD_FRAMES

        dx = wrist_hist[-1][1] - wrist_hist[0][1] if len(wrist_hist) > 1 else 0

        # ---- Phase 4 + 5: actions ----
        if gesture == "PALM":
            if dx > SWIPE_DIST and fire("swipe", "nexttrack", SWIPE_COOLDOWN, now):
                label, label_until = "NEXT >>", now + 1
                wrist_hist.clear()
                palm_armed = False
            elif dx < -SWIPE_DIST and fire("swipe", "prevtrack", SWIPE_COOLDOWN, now):
                label, label_until = "<< PREVIOUS", now + 1
                wrist_hist.clear()
                palm_armed = False
            elif stable and palm_armed and abs(dx) < STILL_DIST:
                pyautogui.press("playpause")
                label, label_until = "PLAY / PAUSE", now + 1
                palm_armed = False
        else:
            palm_armed = True   # re-arm once the palm is lowered

        if stable and gesture == "VOL_UP" and fire("vol", "volumeup", VOL_REPEAT, now):
            label, label_until = "VOLUME +", now + 0.5
        if stable and gesture == "VOL_DOWN" and fire("vol", "volumedown", VOL_REPEAT, now):
            label, label_until = "VOLUME -", now + 0.5

        # ---- on-screen feedback ----
        cv2.putText(frame, f"Gesture: {gesture}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        if now < label_until:
            cv2.putText(frame, label, (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 120), 3)

        cv2.imshow("Gesture Controller", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()