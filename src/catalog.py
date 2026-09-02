import csv
import math
from astropy.coordinates import SkyCoord
import astropy.units as u


def load_catalog(csv_path="data/messier_catalog.csv"):
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def objects_in_frame(wcs_solution, catalog_path="data/messier_catalog.csv"):
    """
    Given a WCSSolution, return catalog objects whose angular distance from
    the frame center is within the frame's approximate radius.
    """
    catalog = load_catalog(catalog_path)
    center = SkyCoord(wcs_solution.crval_ra * u.deg, wcs_solution.crval_dec * u.deg)

    # Approximate frame radius as half the diagonal FOV
    diagonal_deg = math.sqrt(wcs_solution.fov_width_deg**2 + wcs_solution.fov_height_deg**2)
    frame_radius_deg = diagonal_deg / 2

    matches = []
    for obj in catalog:
        obj_coord = SkyCoord(float(obj["ra_deg"]) * u.deg, float(obj["dec_deg"]) * u.deg)
        sep_deg = center.separation(obj_coord).degree
        if sep_deg <= frame_radius_deg:
            matches.append({**obj, "separation_from_center_deg": round(sep_deg, 3)})

    matches.sort(key=lambda o: o["separation_from_center_deg"])
    return matches
