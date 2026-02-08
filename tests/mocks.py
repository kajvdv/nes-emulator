


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