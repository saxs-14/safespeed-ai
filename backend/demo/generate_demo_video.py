"""
Builds a synthetic-but-real demo clip for SafeSpeed AI: a real car photo
(sourced from Wikimedia Commons, CC-licensed) composited onto a real road
photo, sliding at a known pixel velocity. Because the velocity is chosen by
this script, the resulting "ground truth" speed at the app's default
calibration (8 px/meter) is known in advance and printed at the end - useful
to sanity-check the detection+tracking+speed pipeline end-to-end.

This is intentionally NOT presented as real traffic footage - see the
project README's "Demo mode" and "Limitations" sections.
"""
import os
import sys
import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.detection import detect_objects  # noqa: E402

DEMO_DIR = os.path.dirname(__file__)
CANVAS_W, CANVAS_H = 1280, 720
FPS = 20
PIXELS_PER_METER = 8.0


def load_car_crop():
    img = cv2.imread(os.path.join(DEMO_DIR, "sedan_car_side_view_0.jpg"))
    dets = detect_objects(img, confidence_threshold=0.3)
    dets.sort(key=lambda d: d[1], reverse=True)
    x1, y1, x2, y2 = dets[0][2]
    crop = img[y1:y2, x1:x2]
    h, w = crop.shape[:2]
    target_w = 300
    target_h = int(h * (target_w / w))
    return cv2.resize(crop, (target_w, target_h))


def kmh_to_px_per_frame(kmh, fps=FPS, px_per_m=PIXELS_PER_METER):
    mps = kmh / 3.6
    return (mps * px_per_m) / fps


def main():
    road = cv2.imread(os.path.join(DEMO_DIR, "straight_asphalt_road_highway_2.jpg"))
    road = cv2.resize(road, (CANVAS_W, CANVAS_H))
    car = load_car_crop()
    ch, cw = car.shape[:2]

    lanes = [
        {"y": 260, "speed_kmh": 48.0, "start": -cw},
        {"y": 460, "speed_kmh": 82.0, "start": -cw - 400},
    ]
    for lane in lanes:
        lane["px_per_frame"] = kmh_to_px_per_frame(lane["speed_kmh"])

    n_frames = 260
    out_path = os.path.join(DEMO_DIR, "traffic-demo.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, FPS, (CANVAS_W, CANVAS_H))

    for frame_no in range(n_frames):
        frame = road.copy()
        for lane in lanes:
            x = int(lane["start"] + lane["px_per_frame"] * frame_no)
            y = lane["y"]
            if -cw < x < CANVAS_W:
                x0, y0 = max(x, 0), max(y, 0)
                x1, y1 = min(x + cw, CANVAS_W), min(y + ch, CANVAS_H)
                cx0, cy0 = x0 - x, y0 - y
                cx1, cy1 = cx0 + (x1 - x0), cy0 + (y1 - y0)
                if x1 > x0 and y1 > y0:
                    frame[y0:y1, x0:x1] = car[cy0:cy1, cx0:cx1]
        writer.write(frame)

    writer.release()

    print(f"Wrote {out_path} ({n_frames} frames @ {FPS}fps, {CANVAS_W}x{CANVAS_H})")
    for i, lane in enumerate(lanes):
        print(f"  lane {i}: target speed {lane['speed_kmh']} km/h "
              f"-> {lane['px_per_frame']:.2f} px/frame (at {PIXELS_PER_METER} px/m calibration)")


if __name__ == "__main__":
    main()
