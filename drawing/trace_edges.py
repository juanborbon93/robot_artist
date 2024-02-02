from PIL import Image
import cv2
import numpy as np

def trace_image(img:Image):
    """
    Traces the edges of an image using OpenCV's findContours function.
    """
    # as grayscale
    img_grayscale = img.convert('L')
    # as array
    img_array = np.asarray(img_grayscale)
    # Convert image to binary using thresholding
    _, binary = cv2.threshold(img_array, 200, 255, cv2.THRESH_BINARY_INV)
    # Use cv2.findContours to find the outlines of the strokes
    contours, _ = cv2.findContours((binary * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # sort contours by length
    contours = sorted(contours, key=lambda x: cv2.arcLength(x, False), reverse=True)
    return contours