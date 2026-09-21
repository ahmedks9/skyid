from gnomonic_projection import gnomonic_project
import numpy as np
from scipy.spatial import cKDTree
from itertools import combinations
import pickle

from star_catalog import load_star_catalog
from quad_hash import compute_quad_fingerprint


def radec_to_unit_vector(ra_deg, dec_deg):
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    return np.array([x, y, z])


def build_index(mag_limit_for_indexing=7.0, neighbor_radius_deg=4.0, max_neighbors=10):
    """
    Build a quad geometric-hash index over the star catalog.
    mag_limit_for_indexing: further restrict indexing to brighter stars than the full catalog,
                             to keep the number of generated quads manageable.
    neighbor_radius_deg: only consider quads made of stars within this angular radius of each other.
    max_neighbors: cap on how many nearby stars to consider per anchor (limits combinatorial blowup).
    """
    stars = load_star_catalog()
    stars = [s for s in stars if s["mag"] <= mag_limit_for_indexing]
    print(f"Indexing {len(stars)} stars (mag <= {mag_limit_for_indexing})")

    unit_vectors = np.array([radec_to_unit_vector(s["ra_deg"], s["dec_deg"]) for s in stars])

    # Convert angular radius to a 3D chord-length radius for the KD-tree query
    # (chord length between two unit vectors separated by angle theta = 2*sin(theta/2))
    radius_rad = np.radians(neighbor_radius_deg)
    chord_radius = 2 * np.sin(radius_rad / 2)

    tree = cKDTree(unit_vectors)

    quads = []
    seen_quad_keys = set()

    for anchor_idx in range(len(stars)):
        neighbor_indices = tree.query_ball_point(unit_vectors[anchor_idx], r=chord_radius)
        if len(neighbor_indices) < 4:
            continue

        
        # Keep the BRIGHTEST neighbors within radius, not the closest — matches how
        # detected-star quads are selected in Chapter 5 (brightest-first), fixing a real
        # bug where faint, tightly-clustered stars crowded out genuinely bright, useful ones.
        mags = [stars[i]["mag"] for i in neighbor_indices]
        neighbor_indices = [i for _, i in sorted(zip(mags, neighbor_indices))][:max_neighbors]

        # Tangent point for this neighborhood = the anchor star's own RA/Dec
        anchor_ra = stars[anchor_idx]["ra_deg"]
        anchor_dec = stars[anchor_idx]["dec_deg"]

        for combo in combinations(neighbor_indices, 4):
            key = tuple(sorted(combo))
            if key in seen_quad_keys:
                continue
            seen_quad_keys.add(key)

            # Proper per-neighborhood gnomonic projection (fixes the equator distortion bug)
            points_2d = []
            for i in combo:
                x, y = gnomonic_project(
                    anchor_ra, anchor_dec,
                    stars[i]["ra_deg"], stars[i]["dec_deg"]
                )
                points_2d.append((x, y))

            result = compute_quad_fingerprint(points_2d)

            star_ids = [stars[combo[result[k]]]["id"] for k in ["A_idx", "B_idx", "C_idx", "D_idx"]]

            quads.append({
                "star_ids": star_ids,
                "fingerprint": result["fingerprint"],
            })
    print(f"Generated {len(quads)} unique quads")

    fingerprint_array = np.array([q["fingerprint"] for q in quads])
    fingerprint_tree = cKDTree(fingerprint_array)

    with open("data/quad_index.pkl", "wb") as f:
        pickle.dump({"quads": quads, "fingerprint_tree": fingerprint_tree}, f)

    print("Saved index to data/quad_index.pkl")
    return quads, fingerprint_tree


if __name__ == "__main__":
    build_index()
