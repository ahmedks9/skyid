import time
import requests
from config import ASTROMETRY_API_KEY

API_URL = "http://nova.astrometry.net/api"


def _login():
    resp = requests.post(f"{API_URL}/login", data={
        "request-json": f'{{"apikey": "{ASTROMETRY_API_KEY}"}}'
    })
    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError(
            f"Login did not return JSON. Status: {resp.status_code}, "
            f"Body: {resp.text[:200]}"
        )
    if data["status"] != "success":
        raise RuntimeError(f"Login failed: {data}")
    return data["session"]


def _submit_image(session_key, image_path):
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{API_URL}/upload",
            data={"request-json": f'{{"session": "{session_key}"}}'},
            files={"file": f}
        )
    data = resp.json()
    if data["status"] != "success":
        raise RuntimeError(f"Upload failed: {data}")
    return data["subid"]


def _poll_for_job_id(subid, timeout_sec=120, interval_sec=5):
    waited = 0
    while waited < timeout_sec:
        resp = requests.get(f"{API_URL}/submissions/{subid}")
        data = resp.json()
        if data.get("jobs") and data["jobs"][0] is not None:
            return data["jobs"][0]
        time.sleep(interval_sec)
        waited += interval_sec
    raise TimeoutError("Timed out waiting for a job_id to be assigned.")


def _poll_for_solution(job_id, timeout_sec=180, interval_sec=5):
    waited = 0
    while waited < timeout_sec:
        resp = requests.get(f"{API_URL}/jobs/{job_id}")
        data = resp.json()
        status = data.get("status")
        if status == "success":
            return job_id
        elif status == "failure":
            raise RuntimeError("astrometry.net failed to solve this image.")
        time.sleep(interval_sec)
        waited += interval_sec
    raise TimeoutError("Timed out waiting for the job to finish solving.")


def solve_image(image_path):
    """
    Submit an image to astrometry.net and wait for it to be solved.
    Returns the raw calibration dict from the API.
    """
    session_key = _login()
    print("Logged in, session acquired.")

    subid = _submit_image(session_key, image_path)
    print(f"Image submitted, subid={subid}. Waiting for job assignment...")

    job_id = _poll_for_job_id(subid)
    print(f"Job assigned: job_id={job_id}. Waiting for solve to finish...")

    solved_job_id = _poll_for_solution(job_id)
    print("Solved! Fetching calibration data...")

    resp = requests.get(f"{API_URL}/jobs/{solved_job_id}/calibration")
    calibration = resp.json()
    return calibration

from PIL import Image
from wcs import WCSSolution


def calibration_to_wcs(calibration, image_path):
    """
    Convert astrometry.net's raw calibration dict into our WCSSolution structure.
    """
    with Image.open(image_path) as img:
        width_px, height_px = img.size

    pixscale_arcsec = calibration["pixscale"]
    pixscale_deg = pixscale_arcsec / 3600.0

    fov_width_deg = width_px * pixscale_deg
    fov_height_deg = height_px * pixscale_deg

    return WCSSolution(
        crval_ra=calibration["ra"],
        crval_dec=calibration["dec"],
        crpix_x=width_px / 2,
        crpix_y=height_px / 2,
        pixel_scale=pixscale_deg,
        rotation_deg=calibration["orientation"],
        fov_width_deg=fov_width_deg,
        fov_height_deg=fov_height_deg,
    )