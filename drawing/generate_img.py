from project_init import SharedLogger
log = SharedLogger.get_logger()
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO

def make_prompt(human_prompt):
  drawing_prompt = f"""Create a drawing of the following prompt: {human_prompt}
  The drawing should be composed of distinct, non-overlapping lines with uniform thickness, ideally suited for vectorization. 
  Avoid any shading, gradients, or intricate details that would complicate the vectorization process. Only black and white colors should be used.
  The lines should be continuous without breaks, with clear separations where lines start and end to facilitate easy tracing by vector graphic software.
  This image should be created in a continuous line art style, which is characterized by a single unbroken line that forms various shapes and outlines without lifting the drawing instrument from the paper.
  The continuous line creates a fluid, abstract form that gives life to the subjects with minimalism and elegance.
  It should be emphasized that the line count should be kept to a minimum, with the fewest number of lines possible to convey the subject matter."""
  return drawing_prompt

def get_img_from_url(url):

    # Get the content of the image
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Open the image
        image = Image.open(BytesIO(response.content))
    else:
        raise Exception("failed to retreive image")
    return image

def generate_drawing(human_prompt):
    log.info(f"Generating drawing for prompt: {human_prompt}")
    prompt = make_prompt(human_prompt)
    client = OpenAI()
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    log.info(f"Generated image at {image_url}")

    return get_img_from_url(image_url)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--prompt", type=str, default="a cat", help="Prompt for the drawing")
    args = parser.parse_args()
    img = generate_drawing(args.prompt)
    img.show()