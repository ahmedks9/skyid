from astropy.coordinates import SkyCoord
import astropy.units as u

def angular_distance(ra1_hms, dec1_dms, ra2_hms, dec2_dms):
    star1 = SkyCoord(ra1_hms, dec1_dms, frame="icrs")
    star2 = SkyCoord(ra2_hms, dec2_dms, frame="icrs")
    sep = star1.separation(star2)
    return sep.degree, sep.arcsecond


if __name__ == "__main__":
    # Two stars near each other in Orion's belt: Alnitak and Alnilam
    alnitak_ra, alnitak_dec = "5h40m45.5s", "-1d56m34s"
    alnilam_ra, alnilam_dec = "5h36m12.8s", "-1d12m07s"

    deg, arcsec = angular_distance(alnitak_ra, alnitak_dec, alnilam_ra, alnilam_dec)
    print(f"Angular separation: {deg:.4f}° ({arcsec:.1f} arcsec)")