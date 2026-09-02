import os
from dotenv import load_dotenv

load_dotenv()

ASTROMETRY_API_KEY = os.getenv("ASTROMETRY_API_KEY")

if not ASTROMETRY_API_KEY:
    raise RuntimeError(
        "ASTROMETRY_API_KEY not found. Make sure you have a .env file "
        "in the project root with ASTROMETRY_API_KEY=your_key"
    )
