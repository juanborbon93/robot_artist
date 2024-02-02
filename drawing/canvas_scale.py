import numpy as np
import cv2
from typing import Union

def scale_contours_to_canvas(contours, canvas_width:float = 550.0, canvas_height:float = 850, margin:float = 100.0, small_area_cutoff:Union[None,float] = None):
    """
    Scales a list of contours to fit within a canvas of a given size,
    with a margin around the edges.
    """
    
    canvas_dims = (canvas_width - margin*2, canvas_height - margin*2)

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

    if small_area_cutoff is not None:
        # remove small areas
        contours = [contour for contour in contours if cv2.contourArea(contour) * scaling_factor**2 > small_area_cutoff]

    for contour in contours:
        scaled_contour = np.zeros_like(contour).astype("float")
        for i in range(2):
            scaled_contour[:, :, i] = contour[:, :, i].astype("float") * scaling_factor - bbox[i] * scaling_factor - pixel_dims[i] * scaling_factor / 2
        scaled_contours.append(scaled_contour)
    
    return scaled_contours