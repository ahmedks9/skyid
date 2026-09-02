# radec_to_altaz.py
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
from datetime import datetime, timezone
import astropy.units as u

def radec_to_altaz(ra_hms, dec_dms, lat_deg, lon_deg, when_utc=None):
    if when_utc is None:
        when_utc = datetime.now(timezone.utc)

    target = SkyCoord(ra_hms, dec_dms, frame="icrs")
    observer_location = EarthLocation(lat=lat_deg * u.deg, lon=lon_deg * u.deg)
    observation_time = Time(when_utc)

    altaz_frame = AltAz(obstime=observation_time, location=observer_location)
    target_altaz = target.transform_to(altaz_frame)

    return target_altaz.alt.degree, target_altaz.az.degree


if __name__ == "__main__":
    m42_ra = "5h35m17s"
    m42_dec = "-5d23m28s"
    tunis_lat, tunis_lon = 36.8065, 10.1815

    alt, az = radec_to_altaz(m42_ra, m42_dec, tunis_lat, tunis_lon)
    print(f"M42 Altitude: {alt:.2f}°, Azimuth: {az:.2f}°")