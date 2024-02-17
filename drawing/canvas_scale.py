import numpy as np
import cv2
from typing import Union
from settings.settings_base import BaseSettingsModel

class CanvasScaleSettings(BaseSettingsModel):
    canvas_width_mm: float = 550.0
    canvas_height_mm: float = 850
    margin_mm: float = 100.0
    small_area_cutoff_sqr_mm: Union[None, float] = None

    @property
    def canvas_dims(self):
        return (self.canvas_width_mm-2*self.margin_mm, self.canvas_height_mm-2*self.margin_mm)


def scale_contours_to_canvas(contours):
    """
    Scales a list of contours to fit within a canvas of a given size,
    with a margin around the edges.
    """
    SETTINGS:CanvasScaleSettings = CanvasScaleSettings.load()
    canvas_dims = SETTINGS.canvas_dims

    # find the pixel space bounding box of all of the contours
    min_x = min([np.min(contour[:, :, 0]) for contour in contours])
    min_y = min([np.min(contour[:, :, 1]) for contour in contours])
    max_x = max([np.max(contour[:, :, 0]) for contour in contours])
    max_y = max([np.max(contour[:, :, 1]) for contour in contours])
    bbox = (min_x, min_y, max_x, max_y)
    pixel_dims = (max_x - min_x, max_y - min_y)

    # calculate scaling factor so that now instead of pixels, we have mm
    max_pixel_dim_index = pixel_dims.index(max(pixel_dims))
    scaling_factor = canvas_dims[max_pixel_dim_index] / pixel_dims[max_pixel_dim_index]
    scaled_contours = []

    if SETTINGS.small_area_cutoff_sqr_mm is not None:
        # remove small areas
        contours = [
            contour
            for contour in contours
            if cv2.contourArea(contour) * scaling_factor**2 > SETTINGS.small_area_cutoff_sqr_mm 
        ]
    #scale each contour
    for contour in contours:
        scaled_contour = np.zeros_like(contour).astype("float")
        for i in range(2):
            scaled_contour[:, :, i] = (
                contour[:, :, i].astype("float") * scaling_factor
                - bbox[i] * scaling_factor
                - pixel_dims[i] * scaling_factor / 2
            )
        scaled_contours.append(scaled_contour)

    return scaled_contours
