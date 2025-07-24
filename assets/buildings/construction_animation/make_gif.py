from PIL import Image
import os

base_path = os.path.dirname(__file__)
frames = [
    os.path.join(base_path, "frame(1).png"),
    os.path.join(base_path, "frame(2).png"),
    os.path.join(base_path, "frame(3).png"),
    os.path.join(base_path, "frame(4).png"),
    os.path.join(base_path, "frame(5).png"),
    os.path.join(base_path, "frame(6).png"),
    os.path.join(base_path, "frame(7).png"),
    os.path.join(base_path, "frame(8).png")
]

images = [Image.open(f) for f in frames]
images[0].save(
    os.path.join(base_path, "construction_animation.gif"),
    save_all=True,
    append_images=images[1:],
    duration=250,
    loop=0
)
print("GIF créé :", os.path.join(base_path, "construction_animation.gif"))