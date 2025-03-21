import qrcode.image.base
from PIL import Image, ImageDraw


class PilImage(qrcode.image.base.BaseImage):
    """
    PIL image builder, default format is PNG.
    """

    kind = "PNG"

    needs_context = True

    def new_image(self, **kwargs):
        if not Image:
            raise ImportError("PIL library not found.")

        back_color = kwargs.get("back_color", "white")
        fill_color = kwargs.get("fill_color", "black")

        try:
            fill_color = fill_color.lower()
        except AttributeError:
            pass

        try:
            back_color = back_color.lower()
        except AttributeError:
            pass

        # L mode (1 mode) color = (r*299 + g*587 + b*114)//1000
        if fill_color == "black" and back_color == "white":
            mode = "1"
            fill_color = 0
            if back_color == "white":
                back_color = 255
        elif back_color == "transparent":
            mode = "RGBA"
            back_color = None
        else:
            mode = "RGB"

        img = Image.new(mode, (self.pixel_size, self.pixel_size), back_color)
        self.fill_color = fill_color
        self.back_color = back_color
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col):
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=self.fill_color)

    def small_rect(self, outer_rect, inner_width, inner_height):
        """
        Generate a smaller rectangle centered within a given rectangle.

        Parameters:
        - outer_rect: A tuple ((x0, y0), (x1, y1)) specifying the outer rectangle.
        - inner_width: The width of the smaller rectangle.
        - inner_height: The height of the smaller rectangle.

        Returns:
        - A tuple representing the smaller rectangle as ((x0, y0), (x1, y1)), or None if no valid rectangle can fit.
        """
        (x0, y0), (x1, y1) = outer_rect

        # Check if the smaller rectangle can fit within the outer rectangle
        if inner_width > (x1 - x0) or inner_height > (y1 - y0):
            return None  # No valid rectangle can fit

        # Calculate the center of the outer rectangle
        outer_center_x = (x0 + x1) // 2
        outer_center_y = (y0 + y1) // 2

        # Calculate the top-left corner of the smaller rectangle so that it is centered
        small_x0 = outer_center_x - (inner_width // 2)
        small_y0 = outer_center_y - (inner_height // 2)

        # Calculate the bottom-right corner of the smaller rectangle
        small_x1 = small_x0 + inner_width
        small_y1 = small_y0 + inner_height

        return ((small_x0, small_y0), (small_x1, small_y1))

    def drawrect_context(self, row, col, qr):
        small_box_size = min(2, self.box_size // 2)
        bit = qr.modules[row][col]
        match bit:
            case True:
                box = self.pixel_box(row, col)
                self._idr.rectangle(box, fill=self.fill_color)
            case { "real": True }:
                # Draw box with white dot in middle
                if qr.debug:
                    print(f"drawing white in black in ({row}, {col})")
                box = self.pixel_box(row, col)
                small_box = self.small_rect(box, small_box_size, small_box_size)
                self._idr.rectangle(box, fill=self.fill_color)
                self._idr.rectangle(small_box, fill=self.back_color)
            case { "real": False }:
                # Draw black dot in middle
                if qr.debug:
                    print(f"drawing black in white in ({row}, {col})")
                box = self.pixel_box(row, col)
                small_box = self.small_rect(box, small_box_size, small_box_size)
                self._idr.rectangle(small_box, fill=self.fill_color)

    def save(self, stream, format=None, **kwargs):
        kind = kwargs.pop("kind", self.kind)
        if format is None:
            format = kind
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)
