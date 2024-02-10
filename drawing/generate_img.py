from project_init import SharedLogger, LOG_DIR
log = SharedLogger.get_logger()
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO

def make_prompt(human_prompt):
  drawing_prompt = f"""Create a drawing of a {human_prompt}, using a continuous line art style. 
  The artwork should consist of distinct, non-overlapping lines with uniform thickness, making it ideal for vectorization. 
  Use only black lines on a white background, avoiding any shading, gradients, or intricate details to simplify the vectorization process.
  Lines must be continuous without breaks, clearly indicating where they start and end to facilitate easy tracing by vector graphic software.
  Aim for minimalism and elegance, using the fewest number of lines possible to convey the subject matter effectively. 
  The continuous line should create fluid, abstract forms that bring the subjects to life with minimal lines.
  """
  return drawing_prompt

def get_img_from_url(url:str)->Image:

    # Get the content of the image
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Open the image
        image = Image.open(BytesIO(response.content))
    else:
        raise Exception("failed to retreive image")
    return image

def generate_drawing(human_prompt:str)->Image:
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
    log.debug(f"Generated image at {image_url}")
    img = get_img_from_url(image_url)
    # save 
    save_path = LOG_DIR / "drawing.png"
    img.save(save_path)
    log.info(f"Saved image to {save_path}")
    return img

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--prompt", type=str, default="a cat", help="Prompt for the drawing")
    args = parser.parse_args()
    img = generate_drawing(args.prompt)
    img.show()