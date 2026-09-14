"""
Vehicle detection, tracking and speed estimation.

Detector: OpenCV DNN + MobileNet-SSD (Caffe, VOC-trained, ~23MB).
Tracker:  lightweight centroid tracker (nearest-centroid matching across
          frames, IoU tie-break) - a standard, well-documented technique
          for MVP-grade multi-object tracking without a full SORT/DeepSORT
          dependency.
Speed:    estimated from pixel displacement per frame, converted to km/h
          using a configurable pixels-per-meter calibration value and the
          source video's FPS. Uncalibrated (default) results are always
          labeled "estimated" - see README "Limitations".
"""
import os
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
PROTOTXT = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
CAFFEMODEL = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

VOC_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
    "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]
VEHICLE_CLASSES = {"bicycle", "bus", "car", "motorbike"}

_net = None


def get_net():
    global _net
    if _net is None:
        if not (os.path.exists(PROTOTXT) and os.path.exists(CAFFEMODEL)):
            raise FileNotFoundError(
                "MobileNet-SSD model files missing from backend/models/. "
                "See README 'Installation' to fetch them."
            )
        _net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)
    return _net


def detect_objects(frame, confidence_threshold: float = 0.4) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    net = get_net()
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < confidence_threshold:
            continue
        class_id = int(detections[0, 0, i, 1])
        label = VOC_CLASSES[class_id] if class_id < len(VOC_CLASSES) else "unknown"
        if label not in VEHICLE_CLASSES:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        startX, startY, endX, endY = box.astype(int)
        startX, startY = max(0, startX), max(0, startY)
        endX, endY = min(w - 1, endX), min(h - 1, endY)
        results.append((label, confidence, (startX, startY, endX, endY)))
    return results


@dataclass
class Track:
    track_id: int
    label: str
    centroid: Tuple[int, int]
    history: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    misses: int = 0


class CentroidTracker:
    """Nearest-centroid multi-object tracker with a max-distance gate."""

    def __init__(self, max_disappeared: int = 8, max_distance: int = 80):
        self.next_id = 0
        self.tracks: Dict[int, Track] = {}
        self.retired: Dict[int, Track] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def _register(self, label, centroid, frame_no):
        t = Track(track_id=self.next_id, label=label, centroid=centroid)
        t.history.append((frame_no, centroid))
        self.tracks[self.next_id] = t
        self.next_id += 1

    def update(self, detections: List[Tuple[str, float, Tuple[int, int, int, int]]], frame_no: int):
        input_centroids = []
        input_labels = []
        for label, conf, (x1, y1, x2, y2) in detections:
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            input_centroids.append((cx, cy))
            input_labels.append(label)

        if not self.tracks:
            for label, c in zip(input_labels, input_centroids):
                self._register(label, c, frame_no)
            return self.tracks

        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[tid].centroid for tid in track_ids]

        if input_centroids:
            D = np.zeros((len(track_centroids), len(input_centroids)))
            for i, tc in enumerate(track_centroids):
                for j, ic in enumerate(input_centroids):
                    D[i, j] = np.linalg.norm(np.array(tc) - np.array(ic))

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue
                tid = track_ids[row]
                self.tracks[tid].centroid = input_centroids[col]
                self.tracks[tid].history.append((frame_no, input_centroids[col]))
                self.tracks[tid].misses = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_cols = set(range(len(input_centroids))) - used_cols
            for col in unused_cols:
                self._register(input_labels[col], input_centroids[col], frame_no)

            unused_rows = set(range(len(track_centroids))) - used_rows
            for row in unused_rows:
                tid = track_ids[row]
                self.tracks[tid].misses += 1
        else:
            for tid in track_ids:
                self.tracks[tid].misses += 1

        for tid in list(self.tracks.keys()):
            if self.tracks[tid].misses > self.max_disappeared:
                self.retired[tid] = self.tracks.pop(tid)

        return self.tracks

    def all_tracks(self) -> Dict[int, Track]:
        """Active + retired tracks - use this once a video is fully processed."""
        return {**self.retired, **self.tracks}


def estimate_speed_kmh(history: List[Tuple[int, Tuple[int, int]]], fps: float, pixels_per_meter: float) -> float:
    """
    Median of per-step speeds across a track's observed history. Median
    (rather than a single total-displacement/total-time average) resists
    the occasional bad step - e.g. a merged-track seam or one noisy
    detection - skewing the whole estimate.
    """
    if len(history) < 2 or fps <= 0 or pixels_per_meter <= 0:
        return 0.0
    step_speeds = []
    for (f1, c1), (f2, c2) in zip(history, history[1:]):
        frames_elapsed = max(f2 - f1, 1)
        px = float(np.linalg.norm(np.array(c2) - np.array(c1)))
        px_per_frame = px / frames_elapsed
        step_speeds.append((px_per_frame * fps / pixels_per_meter) * 3.6)
    if not step_speeds:
        return 0.0
    return round(float(np.median(step_speeds)), 1)


def merge_fragmented_tracks(
    tracks: Dict[int, Track],
    max_gap_frames: int = 20,
    max_gap_distance: float = 150.0,
) -> List[Track]:
    """
    The centroid tracker can lose and re-register the same physical vehicle
    if detection confidence dips for a few frames (a known limitation of
    simple centroid tracking vs. a Kalman-filter tracker like SORT). This
    stitches tracks of the same class back together when one starts very
    soon after another ends, close to where it left off.
    """
    ordered = sorted(tracks.values(), key=lambda t: t.history[0][0])
    chains: List[Track] = []
    for t in ordered:
        merged = False
        for chain in chains:
            if chain.label != t.label:
                continue
            last_frame, last_pos = chain.history[-1]
            first_frame, first_pos = t.history[0]
            gap_frames = first_frame - last_frame
            if 0 <= gap_frames <= max_gap_frames:
                dist = float(np.linalg.norm(np.array(first_pos) - np.array(last_pos)))
                if dist <= max_gap_distance:
                    chain.history.extend(t.history)
                    merged = True
                    break
        if not merged:
            chains.append(Track(track_id=t.track_id, label=t.label, centroid=t.centroid, history=list(t.history)))
    return chains


def process_video(
    video_path: str,
    speed_limit_kmh: float,
    pixels_per_meter: float,
    evidence_dir: Optional[str] = None,
    sample_every_n_frames: int = 2,
) -> dict:
    """Runs detection+tracking over a whole video and returns finalized events."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tracker = CentroidTracker(max_disappeared=15, max_distance=100)
    frame_no = 0
    seen_labels: Dict[int, str] = {}
    evidence_saved: Dict[int, str] = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_no += 1
        if frame_no % sample_every_n_frames != 0:
            continue

        detections = detect_objects(frame)
        tracks = tracker.update(detections, frame_no)

        for label, conf, box in detections:
            cx = int((box[0] + box[2]) / 2)
            cy = int((box[1] + box[3]) / 2)
            for tid, t in tracks.items():
                if t.centroid == (cx, cy):
                    seen_labels[tid] = label
                    if evidence_dir and tid not in evidence_saved:
                        os.makedirs(evidence_dir, exist_ok=True)
                        fname = f"track_{tid}_{uuid.uuid4().hex[:8]}.jpg"
                        crop = frame[box[1]:box[3], box[0]:box[2]]
                        if crop.size > 0:
                            cv2.imwrite(os.path.join(evidence_dir, fname), crop)
                            evidence_saved[tid] = fname
                    break

    cap.release()

    chains = merge_fragmented_tracks(tracker.all_tracks())

    events = []
    speeds = []
    for t in chains:
        speed = estimate_speed_kmh(t.history, fps, pixels_per_meter)
        if speed <= 0:
            continue
        speeds.append(speed)
        events.append({
            "vehicle_track_id": t.track_id,
            "vehicle_class": seen_labels.get(t.track_id, t.label),
            "estimated_speed_kmh": speed,
            "is_speeding": speed > speed_limit_kmh,
            "frame_number": t.history[-1][0],
            "evidence_path": evidence_saved.get(t.track_id),
        })

    return {
        "fps": fps,
        "total_vehicles": len(events),
        "max_speed_kmh": max(speeds) if speeds else 0.0,
        "avg_speed_kmh": round(sum(speeds) / len(speeds), 1) if speeds else 0.0,
        "speeding_count": sum(1 for s in speeds if s > speed_limit_kmh),
        "events": events,
    }
