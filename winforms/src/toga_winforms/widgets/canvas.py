import math

from travertino.colors import WHITE

from toga.widgets.canvas import Context, FillRule
from toga_winforms.colors import native_color
from toga_winforms.libs import (
    Bitmap,
    Drawing2D,
    FillMode,
    GraphicsPath,
    ImageFormat,
    Matrix,
    MemoryStream,
    Pen,
    PointF,
    Rectangle,
    RectangleF,
    SolidBrush,
    StringFormat,
    WinForms,
    win_font_family,
)

from ..libs.fonts import win_font_style
from .box import Box


class WinformContext(Context):
    def __init__(self):
        super().__init__()
        self.graphics = None
        self.paths = []
        self.start_point = None
        self.last_point = None
        self.matrix = None

    @property
    def current_path(self):
        if len(self.paths) == 0:
            self.add_path()
        return self.paths[-1]

    def add_path(self):
        self.paths.append(GraphicsPath())

    @property
    def matrix(self):
        if self._matrix is None:
            self._matrix = Matrix()
        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        self._matrix = matrix


class Canvas(Box):
    def create(self):
        super().create()
        self.native.DoubleBuffered = True
        self.native.Paint += self.winforms_paint
        self.native.Resize += self.winforms_resize
        self.native.MouseDown += self.winforms_mouse_down
        self.native.MouseMove += self.winforms_mouse_move
        self.native.MouseUp += self.winforms_mouse_up
        self.clicks = 0

    def set_on_resize(self, handler):
        pass

    def set_on_press(self, handler):
        pass

    def set_on_release(self, handler):
        pass

    def set_on_drag(self, handler):
        pass

    def set_on_alt_press(self, handler):
        pass

    def set_on_alt_release(self, handler):
        pass

    def set_on_alt_drag(self, handler):
        pass

    def winforms_paint(self, panel, event, *args):
        context = WinformContext()
        context.graphics = event.Graphics
        context.graphics.Clear(native_color(WHITE))
        context.graphics.SmoothingMode = Drawing2D.SmoothingMode.AntiAlias
        self.interface._draw(self, draw_context=context)

    def winforms_resize(self, *args):
        """Called on widget resize, and calls the handler set on the interface,
        if any."""
        if self.interface.on_resize:
            self.interface.on_resize(self.interface)

    def winforms_mouse_down(self, obj, mouse_event):
        self.clicks = mouse_event.Clicks
        if mouse_event.Button == WinForms.MouseButtons.Left and self.interface.on_press:
            self.interface.on_press(
                self.interface, mouse_event.X, mouse_event.Y, mouse_event.Clicks
            )
        if (
            mouse_event.Button == WinForms.MouseButtons.Right
            and self.interface.on_alt_press
        ):
            self.interface.on_alt_press(
                self.interface, mouse_event.X, mouse_event.Y, mouse_event.Clicks
            )

    def winforms_mouse_move(self, obj, mouse_event):
        if self.clicks == 0:
            return
        if mouse_event.Button == WinForms.MouseButtons.Left and self.interface.on_drag:
            self.interface.on_drag(
                self.interface, mouse_event.X, mouse_event.Y, self.clicks
            )
        if (
            mouse_event.Button == WinForms.MouseButtons.Right
            and self.interface.on_alt_drag
        ):
            self.interface.on_alt_drag(
                self.interface, mouse_event.X, mouse_event.Y, self.clicks
            )

    def winforms_mouse_up(self, obj, mouse_event):
        if (
            mouse_event.Button == WinForms.MouseButtons.Left
            and self.interface.on_release
        ):
            self.interface.on_release(
                self.interface, mouse_event.X, mouse_event.Y, self.clicks
            )
        if (
            mouse_event.Button == WinForms.MouseButtons.Right
            and self.interface.on_alt_release
        ):
            self.interface.on_alt_release(
                self.interface, mouse_event.X, mouse_event.Y, self.clicks
            )
        self.clicks = 0

    def redraw(self):
        self.native.Invalidate()

    def create_pen(self, color=None, line_width=None, line_dash=None, line_cap=None, line_join=None, miter_limit=None):
        pen = Pen(native_color(color))
        if line_width is not None:
            pen.Width = line_width
        if line_dash is not None:
            pen.DashPattern = tuple(map(float, line_dash))
        if line_cap is not None:
            line_cap = str(line_cap).lower()
            if line_cap in ("butt", "flat"):
                pen.set_StartCap(pen.StartCap.Flat)
                pen.set_EndCap(pen.EndCap.Flat)
            elif line_cap == "round":
                pen.set_StartCap(pen.StartCap.Round)
                pen.set_EndCap(pen.EndCap.Round)
            elif line_cap == "square":
                pen.set_StartCap(pen.StartCap.Square)
                pen.set_EndCap(pen.EndCap.Square)
        if line_join is not None:
            line_join = str(line_join).lower()
            if line_join == "miter":
                pen.set_LineJoin(pen.LineJoin.Miter)
            elif line_join == "round":
                pen.set_LineJoin(pen.LineJoin.Round)
            elif line_join == "bevel":
                pen.set_LineJoin(pen.LineJoin.Bevel)
        if miter_limit is not None:
            pen.set_MiterLimit(float(miter_limit))
        return pen

    def create_brush(self, color):
        return SolidBrush(native_color(color))

    # Basic paths

    def new_path(self, draw_context, *args, **kwargs):
        draw_context.add_path()

    def closed_path(self, x, y, draw_context, *args, **kwargs):
        self.line_to(x, y, draw_context, *args, **kwargs)

    def move_to(self, x, y, draw_context, *args, **kwargs):
        draw_context.add_path()
        draw_context.last_point = (x, y)

    def line_to(self, x, y, draw_context, *args, **kwargs):
        draw_context.current_path.AddLine(
            draw_context.last_point[0], draw_context.last_point[1], x, y
        )
        draw_context.last_point = (x, y)

    # Basic shapes

    def bezier_curve_to(
        self, cp1x, cp1y, cp2x, cp2y, x, y, draw_context, *args, **kwargs
    ):
        draw_context.current_path.AddBezier(
            PointF(draw_context.last_point[0], draw_context.last_point[1]),
            PointF(cp1x, cp1y),
            PointF(cp2x, cp2y),
            PointF(x, y),
        )
        draw_context.last_point = (x, y)

    def quadratic_curve_to(self, cpx, cpy, x, y, draw_context, *args, **kwargs):
        draw_context.current_path.AddCurve(
            [
                PointF(draw_context.last_point[0], draw_context.last_point[1]),
                PointF(cpx, cpy),
                PointF(x, y),
            ]
        )
        draw_context.last_point = (x, y)

    def arc(
        self,
        x,
        y,
        radius,
        startangle,
        endangle,
        anticlockwise,
        draw_context,
        *args,
        **kwargs
    ):
        self.ellipse(
            x,
            y,
            radius,
            radius,
            0,
            startangle,
            endangle,
            anticlockwise,
            draw_context,
            *args,
            **kwargs
        )

    def ellipse(
        self,
        x,
        y,
        radiusx,
        radiusy,
        rotation,
        startangle,
        endangle,
        anticlockwise,
        draw_context,
        *args,
        **kwargs
    ):
        rect = RectangleF(x - radiusx, y - radiusy, 2 * radiusx, 2 * radiusy)
        draw_context.current_path.AddArc(
            rect, math.degrees(startangle), math.degrees(endangle - startangle)
        )
        draw_context.last_point = (
            x + radiusx * math.cos(endangle),
            y + radiusy * math.sin(endangle),
        )

    def rect(self, x, y, width, height, draw_context, *args, **kwargs):
        rect = RectangleF(x, y, width, height)
        draw_context.current_path.AddRectangle(rect)

    # Drawing Paths

    def apply_color(self, color, draw_context, *args, **kwargs):
        self.interface.factory.not_implemented("Canvas.apply_color()")

    def fill(self, color, fill_rule, preserve, draw_context, *args, **kwargs):
        brush = self.create_brush(color)
        fill_mode = self.native_fill_rule(fill_rule)
        for path in draw_context.paths:
            if fill_mode is not None:
                path.FillMode = fill_mode
            if draw_context.matrix is not None:
                path.Transform(draw_context.matrix)
            draw_context.graphics.FillPath(brush, path)
        draw_context.paths.clear()

    def native_fill_rule(self, fill_rule):
        if fill_rule == FillRule.EVENODD:
            return FillMode.Alternate
        if fill_rule == FillRule.NONZERO:
            return FillMode.Winding
        return None

    def stroke(self, color, line_width, line_dash, draw_context, *args, **kwargs):
        pen = self.create_pen(color=color, line_width=line_width, line_dash=line_dash,
                              line_cap=kwargs.get("line_cap", None), line_join=kwargs.get("line_join", None),
                              miter_limit=kwargs.get("miter_limit", None))

        for path in draw_context.paths:
            if draw_context.matrix is not None:
                path.Transform(draw_context.matrix)
            draw_context.graphics.DrawPath(pen, path)
        draw_context.paths.clear()

    # Transformations

    def rotate(self, radians, draw_context, *args, **kwargs):
        draw_context.matrix.Rotate(math.degrees(radians))

    def scale(self, sx, sy, draw_context, *args, **kwargs):
        draw_context.matrix.Scale(sx, sy)

    def translate(self, tx, ty, draw_context, *args, **kwargs):
        draw_context.matrix.Translate(tx, ty)

    def reset_transform(self, draw_context, *args, **kwargs):
        draw_context.matrix = None

    # Text
    def write_text(self, text, x, y, font, draw_context, *args, **kwargs):
        full_height = 0
        font_family = win_font_family(font.family)
        font_style = win_font_style(font.weight, font.style, font_family)
        for line in text.splitlines():
            _, height = self.measure_text(line, font)
            origin = PointF(x, y + full_height - height)
            draw_context.current_path.AddString(
                line, font_family, font_style.value__, height, origin, StringFormat()
            )
            full_height += height

    def measure_text(self, text, font, tight=False):
        sizes = [
            WinForms.TextRenderer.MeasureText(line, font._impl.native)
            for line in text.splitlines()
        ]
        width = max([size.Width for size in sizes])
        height = sum([size.Height for size in sizes])
        return (
            self._points_to_pixels(width),
            self._points_to_pixels(height),
        )

    def get_image_data(self):
        width, height = (
            self.interface.layout.content_width,
            self.interface.layout.content_height,
        )
        bitmap = Bitmap(width, height)
        rect = Rectangle(0, 0, width, height)
        self.native.DrawToBitmap(bitmap, rect)
        stream = MemoryStream()
        bitmap.Save(stream, ImageFormat.Png)
        return stream.ToArray()

    def _points_to_pixels(self, points):
        return points * 72 / self.container.viewport.dpi
