import csv


def load_star_catalog(csv_path="data/star_catalog.csv"):
    """
    Load the magnitude-limited star catalog into a list of dicts.
    Each star: {id, hip, proper_name, ra_deg, dec_deg, mag}
    """
    stars = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stars.append({
                "id": row["id"],
                "hip": row["hip"],
                "proper_name": row["proper_name"],
                "ra_deg": float(row["ra_deg"]),
                "dec_deg": float(row["dec_deg"]),
                "mag": float(row["mag"]),
            })
    return stars


if __name__ == "__main__":
    stars = load_star_catalog()
    print(f"Loaded {len(stars)} stars.")
    print("Brightest 5:")
    for s in stars[:5]:
        name = s["proper_name"] or f"HIP {s['hip']}"
        print(f"  {name}: RA={s['ra_deg']:.4f}, Dec={s['dec_deg']:.4f}, mag={s['mag']}")
        