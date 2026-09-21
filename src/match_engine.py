from itertools import combinations


def select_detection_quads(detections, top_n=30, pixel_radius=180, max_neighbors=8):
    """
    Generate quads only from SPATIALLY LOCAL groups of bright detected stars —
    mirrors the catalog index's own local-neighborhood construction (Chapter 4),
    fixing a real bug where combining globally-brightest-but-far-apart stars
    produced quads with no possible true match in the index.
    """
    brightest = sorted(detections, key=lambda d: -d["brightness"])[:top_n]

    quads = []
    seen_quad_keys = set()

    for anchor in brightest:
        neighbors = []
        for other in brightest:
            if other is anchor:
                continue
            dist = ((other["x"] - anchor["x"])**2 + (other["y"] - anchor["y"])**2) ** 0.5
            if dist <= pixel_radius:
                neighbors.append(other)

        if len(neighbors) < 3:
            continue

        # Keep the brightest max_neighbors nearby stars (same bias as the catalog index)
        neighbors = sorted(neighbors, key=lambda d: -d["brightness"])[:max_neighbors]
        group = [anchor] + neighbors

        for combo in combinations(range(len(group)), 4):
            key = tuple(sorted(id(group[i]) for i in combo))
            if key in seen_quad_keys:
                continue
            seen_quad_keys.add(key)
            quads.append([group[i] for i in combo])

    return quads

from quad_hash import compute_quad_fingerprint


def fingerprint_detection_quads(quads):
    """
    Compute the invariant fingerprint for each detected-star quad.
    quads: list of quads, each a list of 4 detection dicts (with 'x', 'y' keys)
    Returns: list of dicts: {detections: [...], fingerprint: (Cx,Cy,Dx,Dy)}
    """
    fingerprinted = []
    for quad in quads:
        points = [(d["x"], d["y"]) for d in quad]
        result = compute_quad_fingerprint(points)

        # Re-order the original detections to match A, B, C, D roles from the result
        ordered_detections = [
            quad[result["A_idx"]],
            quad[result["B_idx"]],
            quad[result["C_idx"]],
            quad[result["D_idx"]],
        ]

        fingerprinted.append({
            "detections": ordered_detections,
            "fingerprint": result["fingerprint"],
        })

    return fingerprinted


import pickle
import numpy as np


def load_catalog_index(index_path="data/quad_index.pkl"):
    with open(index_path, "rb") as f:
        return pickle.load(f)


def find_nearest_catalog_matches(fingerprinted_quads, catalog_index):
    """
    For each detected quad, find the nearest catalog quad in fingerprint-space.
    Returns a list of dicts: {detections, fingerprint, catalog_star_ids, distance}
    """
    quads = catalog_index["quads"]
    tree = catalog_index["fingerprint_tree"]

    results = []
    for fq in fingerprinted_quads:
        fingerprint = np.array(fq["fingerprint"])
        distance, index = tree.query(fingerprint, k=1)

        matched_quad = quads[index]

        results.append({
            "detections": fq["detections"],
            "fingerprint": fq["fingerprint"],
            "catalog_star_ids": matched_quad["star_ids"],
            "distance": float(distance),
        })

    return results


from star_catalog import load_star_catalog


def annotate_matches_with_positions(matches, top_n=10):
    """
    Look up real RA/Dec for each match's catalog stars, so we can check
    whether independent matches agree on the same region of sky.
    """
    catalog = load_star_catalog()
    catalog_by_id = {s["id"]: s for s in catalog}

    annotated = []
    for m in matches[:top_n]:
        star_positions = []
        for star_id in m["catalog_star_ids"]:
            star = catalog_by_id.get(star_id)
            if star:
                star_positions.append((star["ra_deg"], star["dec_deg"]))
        annotated.append({**m, "star_positions": star_positions})

    return annotated


from collections import defaultdict


def find_consensus_match(fingerprinted_quads, catalog_index, catalog_by_id, grid_deg=2.0):
    """
    Match every detected quad against the index, bucket each match's approximate
    sky position onto a coarse grid, and return the grid cell with the most votes.
    This is far more robust than trusting the single nearest-neighbor match alone.
    """
    quads = catalog_index["quads"]
    tree = catalog_index["fingerprint_tree"]

    votes = defaultdict(list)

    for fq in fingerprinted_quads:
        fingerprint = np.array(fq["fingerprint"])
        distance, index = tree.query(fingerprint, k=1)
        matched_quad = quads[index]

        positions = []
        for star_id in matched_quad["star_ids"]:
            star = catalog_by_id.get(star_id)
            if star:
                positions.append((star["ra_deg"], star["dec_deg"]))
        if not positions:
            continue

        avg_ra = sum(p[0] for p in positions) / len(positions)
        avg_dec = sum(p[1] for p in positions) / len(positions)

        cell = (round(avg_ra / grid_deg), round(avg_dec / grid_deg))
        votes[cell].append({
            "distance": float(distance),
            "star_ids": matched_quad["star_ids"],
            "ra": avg_ra, "dec": avg_dec,
        })

    best_cell = max(votes.keys(), key=lambda c: len(votes[c]))
    return best_cell, votes[best_cell], len(votes)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")
    from preprocessing import load_grayscale_normalized, subtract_background
    from detect_stars import compute_threshold_mask, extract_blobs, filter_detections
    from star_catalog import load_star_catalog

    path = sys.argv[1]
    img = load_grayscale_normalized(path)
    subtracted, _ = subtract_background(img)
    mask, _ = compute_threshold_mask(subtracted)
    detections = extract_blobs(subtracted, mask)
    detections, _ = filter_detections(detections)

    quads = select_detection_quads(detections)
    fingerprinted = fingerprint_detection_quads(quads)

    catalog_index = load_catalog_index()
    catalog = load_star_catalog()
    catalog_by_id = {s["id"]: s for s in catalog}

    print(f"Total detections: {len(detections)}, {len(fingerprinted)} quads fingerprinted")
    print(f"Loaded catalog index: {len(catalog_index['quads'])} quads")

    best_cell, cell_votes, total_cells = find_consensus_match(fingerprinted, catalog_index, catalog_by_id)
    print(f"\n{len(cell_votes)} of {len(fingerprinted)} quads agree on the winning region "
          f"(out of {total_cells} distinct regions voted for)")
    print(f"Winning region (grid cell): RA~{best_cell[0]*2.0:.1f}, Dec~{best_cell[1]*2.0:.1f}")
    print("\nMatches contributing to this consensus:")
    for v in sorted(cell_votes, key=lambda v: v["distance"])[:10]:
        print(f"  distance={v['distance']:.5f}, RA={v['ra']:.2f}, Dec={v['dec']:.2f}, star_ids={v['star_ids']}")

