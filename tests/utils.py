from pathlib import Path

from PIL import Image


DATA_DIR = Path("data/snapshots")
DATA_DIR.mkdir(exist_ok=True)


def save_frame_as_image(frame: bytes, width: int, height: int, filename: str):
    img = Image.frombytes('RGB', (width, height), frame)
    img.save(DATA_DIR / filename)


class MockScreen:
    def __init__(self) -> None:
        self.rendered = False
        self.frame = bytes()
        self.render_count = 0
    
    def display(self, frame: bytes) -> None:
        print("rendering frame")
        self.rendered = True
        self.frame = frame
        self.render_count += 1