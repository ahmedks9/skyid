from dataclasses import dataclass

@dataclass
class WCSSolution:
    crval_ra: float      # RA (deg) at the reference pixel  -- your tangent point's RA
    crval_dec: float     # Dec (deg) at the reference pixel -- your tangent point's Dec
    crpix_x: float       # reference pixel column
    crpix_y: float       # reference pixel row
    pixel_scale: float   # degrees per pixel
    rotation_deg: float  # rotation of image "up" relative to north, degrees
    fov_width_deg: float # computed field of view width, for convenience
    fov_height_deg: float

    def summary(self):
        return (f"Center: RA={self.crval_ra:.4f}, Dec={self.crval_dec:.4f} | "
                f"Scale: {self.pixel_scale*3600:.2f} arcsec/px | "
                f"Rotation: {self.rotation_deg:.2f} deg | "
                f"FOV: {self.fov_width_deg:.2f} x {self.fov_height_deg:.2f} deg")
