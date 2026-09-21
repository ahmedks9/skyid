import numpy as np
import cv2


def compute_threshold_mask(img, sigma_multiplier=5.0):
    """
    Compute a statistical threshold and return a binary mask of pixels above it.
    img is expected to be background-subtracted already (mostly near-zero, with star peaks).
    """
    median = np.median(img)
    std = np.std(img)
    threshold = median + sigma_multiplier * std

    mask = img > threshold
    return mask, threshold


def extract_blobs(img, mask):
    """
    Group connected mask pixels into blobs, computing centroid and brightness for each.
    img: background-subtracted grayscale image (for brightness weighting)
    mask: boolean array from compute_threshold_mask
    Returns a list of dicts: {x, y, brightness, area}
    """
    mask_uint8 = mask.astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_uint8, connectivity=8)

    detections = []
    for label_id in range(1, num_labels):  # label 0 is the background, skip it
        area = stats[label_id, cv2.CC_STAT_AREA]
        blob_mask = (labels == label_id)

        # Brightness-weighted centroid, using actual pixel values as weights
        ys, xs = np.nonzero(blob_mask)
        weights = img[ys, xs]
        x_centroid = np.sum(xs * weights) / np.sum(weights)
        y_centroid = np.sum(ys * weights) / np.sum(weights)

        total_brightness = np.sum(weights)

        detections.append({
            "x": float(x_centroid),
            "y": float(y_centroid),
            "brightness": float(total_brightness),
            "area": int(area),
        })

    return detections

def filter_detections(detections, min_area=2, max_area=500):
    """
    Reject detections with implausible pixel area (likely noise or artifacts).
    """
    filtered = [d for d in detections if min_area <= d["area"] <= max_area]
    rejected_count = len(detections) - len(filtered)
    return filtered, rejected_count


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")
    from preprocessing import load_grayscale_normalized, subtract_background

    path = sys.argv[1]
    img = load_grayscale_normalized(path)
    subtracted, _ = subtract_background(img)

    mask, threshold = compute_threshold_mask(subtracted)
    print(f"Threshold value: {threshold:.4f}")
    print(f"Pixels above threshold: {mask.sum()} out of {mask.size} "
          f"({100 * mask.sum() / mask.size:.3f}%)")

    detections = extract_blobs(subtracted, mask)
    detections, rejected_count = filter_detections(detections)
    print(f"Filtered out {rejected_count} implausible detection(s), {len(detections)} remain.")
    print(f"\nDetected {len(detections)} blob(s):")
    for d in sorted(detections, key=lambda d: -d["brightness"])[:15]:
        print(f"  x={d['x']:.1f}, y={d['y']:.1f}, "
              f"brightness={d['brightness']:.3f}, area={d['area']}px")
    

    mask_visual = (mask * 255).astype(np.uint8)
    cv2.imwrite("debug_mask.png", mask_visual)