import numpy as np

def gnomonic_project(ra0_deg, dec0_deg, ra_deg, dec_deg):
    """
    Project a star's RA/Dec onto the tangent plane centered at (ra0, dec0).
    All inputs in degrees. Returns (x, y) in radians.
    """
    ra0 = np.radians(ra0_deg)
    dec0 = np.radians(dec0_deg)
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)

    d_ra = ra - ra0

    cos_c = (np.sin(dec0) * np.sin(dec) +
              np.cos(dec0) * np.cos(dec) * np.cos(d_ra))

    x = (np.cos(dec) * np.sin(d_ra)) / cos_c
    y = (np.cos(dec0) * np.sin(dec) -
          np.sin(dec0) * np.cos(dec) * np.cos(d_ra)) / cos_c

    return x, y


if __name__ == "__main__":
    # Tangent point = Alnitak
    ra0, dec0 = 85.1896, -1.9428   # 5h40m45.5s, -1d56m34s in decimal degrees

    # Project Alnilam
    ra1, dec1 = 84.0533, -1.2019   # 5h36m12.8s, -1d12m07s in decimal degrees

    x, y = gnomonic_project(ra0, dec0, ra1, dec1)

    # Planar distance in radians -> degrees, for comparison with Step 1.1.3
    planar_dist_rad = np.sqrt(x**2 + y**2)
    planar_dist_deg = np.degrees(planar_dist_rad)

    print(f"x = {x:.6f} rad, y = {y:.6f} rad")
    print(f"Planar distance: {planar_dist_deg:.4f} deg")
