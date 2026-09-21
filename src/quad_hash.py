import numpy as np
from itertools import combinations


def compute_quad_fingerprint(points):
    """
    Given 4 (x, y) points, compute the astrometry.net-style invariant fingerprint.
    points: list of 4 (x, y) tuples
    Returns: dict with 'A_idx', 'B_idx', 'C_idx', 'D_idx' (indices into input list)
             and 'fingerprint' = (Cx, Cy, Dx, Dy) in the normalized frame.
    """
    points = np.array(points, dtype=np.float64)
    assert len(points) == 4, "Quad fingerprint requires exactly 4 points"

    # Step 1: find the farthest-apart pair among all 6 possible pairs
    max_dist = -1
    best_pair = None
    for i, j in combinations(range(4), 2):
        dist = np.linalg.norm(points[i] - points[j])
        if dist > max_dist:
            max_dist = dist
            best_pair = (i, j)

    a_idx, b_idx = best_pair
    remaining = [i for i in range(4) if i not in best_pair]
    c_idx, d_idx = remaining

    A, B = points[a_idx], points[b_idx]
    C, D = points[c_idx], points[d_idx]

    # Step 2: build the transform that sends A -> (0,0), B -> (1,1)
    # This means: translate by -A, then rotate/scale so (B - A) maps to (1,1)
    AB = B - A
    ab_length = np.linalg.norm(AB)

    # Target vector (1,1) has length sqrt(2) and angle 45 degrees
    target_angle = np.pi / 4
    current_angle = np.arctan2(AB[1], AB[0])
    rotation = target_angle - current_angle
    scale = np.sqrt(2) / ab_length

    cos_r, sin_r = np.cos(rotation), np.sin(rotation)
    rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])

    def transform(point):
        shifted = point - A
        rotated = rot_matrix @ shifted
        scaled = rotated * scale
        return scaled

    C_norm = transform(C)
    D_norm = transform(D)

    return {
        "A_idx": a_idx, "B_idx": b_idx, "C_idx": c_idx, "D_idx": d_idx,
        "fingerprint": (float(C_norm[0]), float(C_norm[1]), float(D_norm[0]), float(D_norm[1])),
    }


if __name__ == "__main__":
    # Simple test: a known square, side length 1, corners at (0,0),(1,0),(1,1),(0,1)
    test_points = [(0, 0), (1, 0), (1, 1), (0, 1)]
    result = compute_quad_fingerprint(test_points)
    print("Test quad (unit square):")
    print(f"  A_idx={result['A_idx']}, B_idx={result['B_idx']} (farthest pair, should be a diagonal)")
    print(f"  C_idx={result['C_idx']}, D_idx={result['D_idx']}")
    print(f"  Fingerprint (Cx,Cy,Dx,Dy) = {result['fingerprint']}")
