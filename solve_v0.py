import sys
sys.path.insert(0, "src")

from astrometry_client import solve_image, calibration_to_wcs
from catalog import objects_in_frame

def main(image_path):
    calibration = solve_image(image_path)
    wcs = calibration_to_wcs(calibration, image_path)
    print(wcs.summary())

    matches = objects_in_frame(wcs)
    if not matches:
        print("\nNo known Messier objects found in this frame.")
        return

    print(f"\nFound {len(matches)} Messier object(s) in frame:")
    for obj in matches:
        name = obj["common_name"] or obj["id"]
        print(f"  - {obj['id']} ({name}) — {obj['object_type']}, "
              f"{obj['separation_from_center_deg']}° from center")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python solve_v0.py <path_to_image>")
        sys.exit(1)
    main(sys.argv[1])
