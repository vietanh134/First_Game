import os
from PIL import Image

brain_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\b965e400-f776-435f-bd61-c41cdb30fc25"
files = [
    "media__1779207651718.png",
    "media__1779207657799.png",
    "media__1779207911074.png",
    "media__1779207920132.png",
    "media__1779207924813.png"
]

for f in files:
    path = os.path.join(brain_dir, f)
    if os.path.exists(path):
        img = Image.open(path)
        print(f"{f}: size={img.size}, format={img.format}, mode={img.mode}")
    else:
        print(f"{f} does not exist!")
