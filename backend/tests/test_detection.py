import numpy as np
from app.detection import CentroidTracker, estimate_speed_kmh, detect_objects


def test_centroid_tracker_registers_new_track():
    tracker = CentroidTracker()
    detections = [("car", 0.9, (10, 10, 50, 50))]
    tracks = tracker.update(detections, frame_no=1)
    assert len(tracks) == 1


def test_centroid_tracker_follows_moving_object():
    tracker = CentroidTracker(max_distance=100)
    tracker.update([("car", 0.9, (10, 10, 50, 50))], frame_no=1)
    tracks = tracker.update([("car", 0.9, (20, 10, 60, 50))], frame_no=2)
    assert len(tracks) == 1
    track = list(tracks.values())[0]
    assert len(track.history) == 2


def test_estimate_speed_zero_with_no_movement():
    history = [(1, (10, 10)), (2, (10, 10))]
    speed = estimate_speed_kmh(history, fps=25, pixels_per_meter=8)
    assert speed == 0.0


def test_estimate_speed_positive_with_movement():
    history = [(1, (0, 0)), (2, (40, 0))]
    speed = estimate_speed_kmh(history, fps=25, pixels_per_meter=8)
    assert speed > 0


def test_detect_objects_runs_on_blank_frame():
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    results = detect_objects(frame, confidence_threshold=0.9)
    assert isinstance(results, list)
