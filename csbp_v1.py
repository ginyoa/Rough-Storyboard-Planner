import io
import sys
import json

from PIL import Image, ImageDraw, ImageFont

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox, QColorDialog,
    QCheckBox, QDialog, QSizePolicy, QLineEdit, QMenuBar, QAbstractItemView, QSlider
)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QAction, QPainter, QIcon

from images import FAVICON

from ctypes import windll

windll.shell32.SetCurrentProcessExplicitAppUserModelID('Ginyoa.Crappy.Storyboard.Planner')



DEFAULT_FPS = 24
ROWS_PER_PAGE = 6
COLS = 4
TOTAL_PAGES = 4

# NOTE - StevenPince - Using 854 x 480 (FWVGA) resolution at 16:9 aspect ratio
DEFAULT_WIDTH = 854
DEFAULT_HEIGHT = 480

COLOR_WHITE = (255, 255, 255, 255)
COLOR_BLACK = (0, 0, 0, 255)


class DrawingWidget(QWidget):
    def __init__(self, width, height, brush_color=COLOR_BLACK, brush_size=2, eraser_mode=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.image = Image.new("RGBA", (width, height), COLOR_WHITE)
        self.draw = ImageDraw.Draw(self.image)
        self.brush_color = brush_color
        self.brush_size = brush_size
        self.eraser_mode = eraser_mode
        self.last_pos = None

        self.label = QLabel(self)
        self.label.setFixedSize(width, height)
        self.label.move(0,0)

        self.update_pixmap()

        self.label.mousePressEvent = self.mousePressEvent
        self.label.mouseMoveEvent = self.mouseMoveEvent
        self.label.mouseReleaseEvent = self.mouseReleaseEvent

    @property
    def fill_color(self):
        return (255, 255, 255, 0) if self.eraser_mode else self.brush_color

    def update_pixmap(self):
        data = self.image.tobytes("raw", "RGBA")
        qimg = QImage(data, self.image.width, self.image.height, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)
        self.label.setPixmap(pix)

    def get_pil_image(self):
        return self.image.copy()

    def mouseMoveEvent(self, event):
        if self.last_pos is not None:
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            self.draw_line(self.last_pos, pos)
            self.last_pos = pos

    def mouseReleaseEvent(self, event):
        self.last_pos = None

    def draw_point(self, pos):
        self.draw.ellipse(xy=[pos.x() - self.brush_size,
                              pos.y() - self.brush_size,
                              pos.x() + self.brush_size,
                              pos.y() + self.brush_size],
                          fill=self.fill_color)

        self.update_pixmap()

    def draw_line(self, start, end):
        self.draw.line([start.x(), start.y(), end.x(), end.y()], fill=self.fill_color, width=self.brush_size * 2)

        self.update_pixmap()

class BigDrawingDialog(QDialog):
    def __init__(self, pil_image=None, brush_color=COLOR_BLACK, brush_size=5, eraser_mode=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Storyboard Canvas")
        self.canvas_width = DEFAULT_WIDTH
        self.canvas_height = DEFAULT_HEIGHT
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        layout = QVBoxLayout(self)

        if pil_image:
            self.image = pil_image.resize((self.canvas_width, self.canvas_height), Image.LANCZOS).copy()
        else:
            self.image = Image.new("RGBA", (self.canvas_width, self.canvas_height), COLOR_WHITE)

        self.draw = ImageDraw.Draw(self.image)

        self.label = QLabel()
        self.label.setFixedSize(self.canvas_width, self.canvas_height)
        self.label.setMouseTracking(True)
        layout.addWidget(self.label)

        toolbar = QHBoxLayout()

        self.color_btn = QPushButton("Brush Color")
        self.color_btn.clicked.connect(self.open_color_picker)
        toolbar.addWidget(self.color_btn)

        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setMinimum(1)
        self.brush_slider.setMaximum(30)
        self.brush_slider.setValue(brush_size)
        self.brush_slider.valueChanged.connect(self.update_brush_size)
        toolbar.addWidget(QLabel("Brush Size"))
        toolbar.addWidget(self.brush_slider)

        self.eraser_checkbox = QCheckBox("Eraser")
        self.eraser_checkbox.setChecked(eraser_mode)
        self.eraser_checkbox.toggled.connect(self.eraser_toggled)
        toolbar.addWidget(self.eraser_checkbox)

        layout.addLayout(toolbar)

        btn_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Confirm")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)


        layout.addLayout(btn_layout)

        self.brush_color = brush_color
        self.brush_size = brush_size
        self.eraser_mode = eraser_mode

        self.last_pos = None

        self.update_pixmap()

        self.label.mousePressEvent = self.mousePressEvent
        self.label.mouseMoveEvent = self.mouseMoveEvent
        self.label.mouseReleaseEvent = self.mouseReleaseEvent

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = (color.red(), color.green(), color.blue(), 255)

    def update_brush_size(self, val):
        self.brush_size = val

    def eraser_toggled(self, checked):
        self.eraser_mode = checked

    def update_pixmap(self):
        data = self.image.tobytes("raw", "RGBA")
        qimg = QImage(data, self.image.width, self.image.height, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)
        self.label.setPixmap(pix)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            self.last_pos = pos
            self.draw_point(pos)

    def mouseMoveEvent(self, event):
        if self.last_pos:
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            self.draw_line(self.last_pos, pos)
            self.last_pos = pos

    def mouseReleaseEvent(self, event):
        self.last_pos = None

    def draw_point(self, pos):
        self.draw.ellipse(
            [pos.x() - self.brush_size, pos.y() - self.brush_size,
             pos.x() + self.brush_size, pos.y() + self.brush_size],
            fill=COLOR_WHITE if self.eraser_mode else self.brush_color)

        self.update_pixmap()

    def draw_line(self, start, end):
        self.draw.line([start.x(), start.y(), end.x(), end.y()],
                       fill=COLOR_WHITE if self.eraser_mode else self.brush_color,
                       width=self.brush_size * 2)

        self.update_pixmap()

    def get_image(self):
        return self.image.copy()

class DurationWidget(QWidget):
    def __init__(self, fps=DEFAULT_FPS, parent=None):
        super().__init__(parent)
        self.fps = fps
        layout = QHBoxLayout(self)
        self.seconds_edit = QLineEdit("0")
        self.frames_edit = QLineEdit("0")

        for edit in (self.seconds_edit, self.frames_edit):
            edit.setFixedWidth(30)

        layout.addWidget(QLabel("("))
        layout.addWidget(self.seconds_edit)
        layout.addWidget(QLabel("+"))
        layout.addWidget(self.frames_edit)
        layout.addWidget(QLabel(")"))
        layout.setContentsMargins(0,0,0,0)
        self.on_change_callbacks = []

        self.seconds_edit.textChanged.connect(self.emit_changed)
        self.frames_edit.textChanged.connect(self.emit_changed)

    def emit_changed(self):
        for callback in self.on_change_callbacks:
            callback()

    def on_value_changed(self, callback):
        self.on_change_callbacks.append(callback)

    def get_duration(self):
        try:
            s = int(self.seconds_edit.text())
        except ValueError:
            s = 0
        try:
            f = int(self.frames_edit.text())
        except ValueError:
            f = 0
        return s, f

class StoryboardTable(QTableWidget):
    def __init__(self, page_number=1, fps=DEFAULT_FPS, start_number=1, parent=None):
        super().__init__(ROWS_PER_PAGE, COLS, parent)
        self.page_number = page_number
        self.fps = fps
        self.start_number = start_number
        self.duration_widgets = []
        self.uploaded_images = [None] * ROWS_PER_PAGE
        self.draw_widgets = [None] * ROWS_PER_PAGE  # Store drawing widgets if in draw mode
        self.mode = "upload"  # def

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.setHorizontalHeaderLabels(["#", "Storyboard", "Description", "Duration"])
        self.verticalHeader().setVisible(False)

        for row in range(ROWS_PER_PAGE):
            self.setItem(row, 0, self.create_number_item(self.start_number + row))
            self._add_upload_button(row)
            self._add_description_placeholder(row)
            self._add_duration_widget(row)

    def create_number_item(self, num):
        item = QTableWidgetItem(str(num))
        item.setFlags(Qt.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)

        return item

    def update_geometry(self):
        total_width = self.viewport().width() or DEFAULT_WIDTH  # fallback if zero
        total_height = self.viewport().height() or 600

        margin_width = 20
        margin_height = 40

        total_width = max(0, total_width - margin_width)
        total_height = max(0, total_height - margin_height)

        row_height = total_height // ROWS_PER_PAGE
        for row in range(ROWS_PER_PAGE):
            self.setRowHeight(row, row_height)

        col1_width = int(total_width * 0.07)
        storyboard_width = int((16 / 9) * row_height)

        if storyboard_width > total_width - col1_width:
            storyboard_width = total_width - col1_width

        rest_width = total_width - (col1_width + storyboard_width)
        col3_width = int(rest_width * 0.7)
        col4_width = rest_width - col3_width

        self.setColumnWidth(0, col1_width)
        self.setColumnWidth(1, storyboard_width)
        self.setColumnWidth(2, col3_width)
        self.setColumnWidth(3, col4_width)

        # Resize drawing widgets if any
        for dw in self.draw_widgets:
            if dw:
                dw.setFixedSize(storyboard_width, row_height)

    def create_fixed_size_button(self, text=None, pixmap=None, row=None):
        btn = QPushButton()
        btn.setProperty("row", row)
        btn.setFlat(True)
        btn.setCheckable(False)  # 🔹 Make sure it's not a toggle button
        btn.setDown(False)     
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if pixmap:
            btn.setIcon(pixmap)
            btn.setIconSize(pixmap.size())
            btn.setText("")
        else:
            btn.setText("Upload Image")
        btn.clicked.connect(self.handle_upload_clicked)

        return btn

    def _add_upload_button(self, row):
        btn = self.create_fixed_size_button(text="Upload Image", row=row)
        btn.setFixedSize(150, 85)
        self.setCellWidget(row, 1, btn)

    def _add_description_placeholder(self, row):
        item = QTableWidgetItem(" ")
        self.setItem(row, 2, item)

    def _add_duration_widget(self, row):
        dur_widget = DurationWidget(fps=self.fps)
        dur_widget.on_value_changed(self.notify_parent_to_update_total)
        cell_width = self.columnWidth(3) or 80
        cell_height = self.rowHeight(row) or 50
        dur_widget.setFixedSize(cell_width, cell_height)
        self.setCellWidget(row, 3, dur_widget)
        self.duration_widgets.append(dur_widget)

    def notify_parent_to_update_total(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "update_totals_for_page"):
                parent.update_totals_for_page(self)
                break
            parent = parent.parent()

    def update_page_total_duration(self):
        total_seconds = 0
        total_frames = 0
        for dur_widget in self.duration_widgets:
            s, f = dur_widget.get_duration()
            total_seconds += s
            total_frames += f

        extra_seconds = total_frames // self.fps
        total_seconds += extra_seconds
        total_frames = total_frames % self.fps
        return total_seconds, total_frames

    def handle_upload_clicked(self):
        button = self.sender()

        if not button:
            return

        button.setDown(False)  # 🔹 reset visual press

        row = button.property("row")
        if row is None:
            return

        if self.mode != "upload":
            # in draw mode, do nothing on upload button clicks
            return

        file_path, _ = QFileDialog.getOpenFileName(self,
                                                   "Select Storyboard Image",
                                                   "",
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not file_path:
            return

        pil_img = Image.open(file_path).convert("RGBA")
        self.uploaded_images[row] = pil_img

        cell_width = self.columnWidth(1) or 150
        cell_height = self.rowHeight(row) or 50
        qt_pixmap = self.pil_to_qpixmap_scaled(pil_img, cell_width, cell_height)

        img_btn = self.create_fixed_size_button(pixmap=qt_pixmap, row=row)
        img_btn.setFixedSize(cell_width, cell_height)
        img_btn.setToolTip(file_path)
        self.setCellWidget(row, 1, img_btn)

        # Clear draw widget if any
        if self.draw_widgets[row]:
            self.draw_widgets[row].deleteLater()
            self.draw_widgets[row] = None

    def pil_to_qpixmap_scaled(self, pil_img, width, height):
        img_ratio = pil_img.width / pil_img.height
        target_ratio = width / height

        if img_ratio > target_ratio:
            new_width = width
            new_height = int(width / img_ratio)
        else:
            new_height = height
            new_width = int(height * img_ratio)

        resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        data = resized_img.tobytes("raw", "RGBA")
        qimg = QImage(data, resized_img.width, resized_img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def switch_to_draw_mode(self):
        self.mode = "draw"
        # Replace storyboard column widgets with DrawingWidgets or blank if none
        for row in range(ROWS_PER_PAGE):
            if self.draw_widgets[row] is None:
                dw = DrawingWidget(self.columnWidth(1), self.rowHeight(row))
                self.draw_widgets[row] = dw
            else:
                dw = self.draw_widgets[row]
                dw.setFixedSize(self.columnWidth(1), self.rowHeight(row))
            self.setCellWidget(row, 1, self.draw_widgets[row])
            self.uploaded_images[row] = None  # Clear uploaded images in draw mode

    def switch_to_upload_mode(self):
        self.mode = "upload"
        # Replace storyboard column widgets with upload buttons or uploaded image buttons
        for row in range(ROWS_PER_PAGE):
            if self.draw_widgets[row]:
                self.draw_widgets[row].deleteLater()
                self.draw_widgets[row] = None
            if self.uploaded_images[row]:
                pil_img = self.uploaded_images[row]
                cell_width = self.columnWidth(1) or 150
                cell_height = self.rowHeight(row) or 50
                qt_pixmap = self.pil_to_qpixmap_scaled(pil_img, cell_width, cell_height)
                img_btn = self.create_fixed_size_button(pixmap=qt_pixmap, row=row)
                img_btn.setFixedSize(cell_width, cell_height)
                self.setCellWidget(row, 1, img_btn)
            else:
                self._add_upload_button(row)

    def mousePressEvent(self, event):
        if self.mode != "draw":
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        index = self.indexAt(pos)
        if not index.isValid():
            super().mousePressEvent(event)
            return

        row = index.row()
        col = index.column()
        if col == 1 and 0 <= row < ROWS_PER_PAGE:
            # Load full-res image from uploaded_images, fallback to blank canvas
            current_img = self.uploaded_images[row]
            if current_img is None:
                current_img = Image.new("RGBA", (DEFAULT_WIDTH, DEFAULT_HEIGHT), COLOR_WHITE)

            dlg = BigDrawingDialog(
                pil_image=current_img,
                brush_color=self.draw_widgets[row].brush_color if self.draw_widgets[row] else COLOR_BLACK,
                brush_size=self.draw_widgets[row].brush_size if self.draw_widgets[row] else 5,
                eraser_mode=self.draw_widgets[row].eraser_mode if self.draw_widgets[row] else False,
                parent=self
            )
            if dlg.exec() == QDialog.Accepted:
                new_img = dlg.get_image()

                # Store full-res image for playback/export
                self.uploaded_images[row] = new_img

                # Create thumbnail sized to cell
                thumb_width = self.columnWidth(1)
                thumb_height = self.rowHeight(row)
                thumbnail_img = new_img.resize((thumb_width, thumb_height), Image.LANCZOS)

                # Update or create the draw widget thumbnail
                if self.draw_widgets[row]:
                    self.draw_widgets[row].image = thumbnail_img
                    self.draw_widgets[row].draw = ImageDraw.Draw(self.draw_widgets[row].image)
                    self.draw_widgets[row].update_pixmap()
                else:
                    dw = DrawingWidget(thumb_width, thumb_height)
                    dw.image = thumbnail_img
                    dw.draw = ImageDraw.Draw(dw.image)
                    dw.update_pixmap()
                    self.draw_widgets[row] = dw
                    self.setCellWidget(row, 1, dw)

                # Update draw widget image resized to widget size for thumbnail
                if self.draw_widgets[row]:
                    self.draw_widgets[row].image = new_img.resize(
                        (self.draw_widgets[row].width(), self.draw_widgets[row].height()),
                        Image.LANCZOS
                    )
                    self.draw_widgets[row].draw = ImageDraw.Draw(self.draw_widgets[row].image)
                    self.draw_widgets[row].update_pixmap()
                    # Store full res big image in uploaded_images for player
                    self.uploaded_images[row] = new_img
                else:
                    # Justincase
                    dw = DrawingWidget(self.columnWidth(1), self.rowHeight(row))
                    dw.image = new_img.resize(
                        (dw.width(), dw.height()), Image.LANCZOS)
                    dw.draw = ImageDraw.Draw(dw.image)
                    dw.update_pixmap()
                    self.draw_widgets[row] = dw
                    self.setCellWidget(row, 1, dw)
                    self.uploaded_images[row] = new_img
        else:
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        total_width = self.viewport().width()
        total_height = self.viewport().height()

        margin_width = 20
        margin_height = 40

        total_width = max(0, total_width - margin_width)
        total_height = max(0, total_height - margin_height)

        row_height = total_height // ROWS_PER_PAGE
        for row in range(ROWS_PER_PAGE):
            self.setRowHeight(row, row_height)

        col1_width = int(total_width * 0.07)
        storyboard_width = int((16 / 9) * row_height)

        if storyboard_width > total_width - col1_width:
            storyboard_width = total_width - col1_width

        rest_width = total_width - (col1_width + storyboard_width)
        col3_width = int(rest_width * 0.7)
        col4_width = rest_width - col3_width

        self.setColumnWidth(0, col1_width)
        self.setColumnWidth(1, storyboard_width)
        self.setColumnWidth(2, col3_width)
        self.setColumnWidth(3, col4_width)

        # Resize drawing widgets if any
        for dw in self.draw_widgets:
            if dw:
                dw.setFixedSize(storyboard_width, row_height)

        super().resizeEvent(event)

class PlayerWindow(QDialog):
    def __init__(self, frames, durations, numbers, descriptions, fps=DEFAULT_FPS, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Storyboard Playback")
        self.fps = fps
        self.frames = frames
        self.numbers = numbers
        self.durations = durations
        self.descriptions = descriptions
        self.current_index = 0
        self.elapsed_ms = 0

        self.resize(960, 540)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.current_image = None

        self.start_playback()

    def start_playback(self):
        self.current_index = 0
        self.elapsed_ms = 0
        self.show_frame(self.current_index)
        self.timer.start(40)

    def update_frame(self):
        if self.current_index >= len(self.frames):
            self.timer.stop()
            return

        s, f = self.durations[self.current_index]
        total_ms = int((s + f / self.fps) * 1000)

        if total_ms <= 0:
            self.current_index += 1
            self.elapsed_ms = 0
            if self.current_index < len(self.frames):
                self.show_frame(self.current_index)
            return

        self.elapsed_ms += 40

        if self.elapsed_ms >= total_ms:
            self.current_index += 1
            self.elapsed_ms = 0
            if self.current_index < len(self.frames):
                self.show_frame(self.current_index)
            else:
                self.timer.stop()
                return

        self.update_timecode_display()

    def show_frame(self, index):
        pil_image = self.frames[index]
        target_w, target_h = self.width(), self.height()
        target_ratio = 16 / 9
        new_h = target_h
        new_w = int(new_h * target_ratio)
        if new_w > target_w:
            new_w = target_w
            new_h = int(new_w / target_ratio)

        img_resized = pil_image.resize((new_w, new_h), Image.LANCZOS).convert("RGBA")

        self.current_image = img_resized
        self.elapsed_ms = 0
        self.update_timecode_display(force=True)

        bg = Image.new("RGBA", (target_w, target_h), COLOR_BLACK)

        if pil_image:
            img_ratio = pil_image.width / pil_image.height
            if img_ratio > target_ratio:
                new_w = target_w
                new_h = int(target_w / img_ratio)
            else:
                new_h = target_h
                new_w = int(target_h * img_ratio)

            resized_img = pil_image.resize((new_w, new_h), Image.LANCZOS)
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            bg.paste(resized_img, (x_offset, y_offset))
        else:
            # blank black frame
            pass

        # Draw storyboard number on top-left
        draw = ImageDraw.Draw(bg)
        font_size = max(10, target_h // 20)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        text = f"Cut no. {self.numbers[index]}"
        margin = 10
        text_pos = (margin, margin)
        shadow_color = COLOR_BLACK
        text_color = COLOR_WHITE

        for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            pos = (text_pos[0] + offset[0], text_pos[1] + offset[1])
            draw.text(pos, text, font=font, fill=shadow_color)

        draw.text(text_pos, text, font=font, fill=text_color)

        self.current_image = bg
        self.elapsed_ms = 0  # reset timecode count on new frame
        self.update_timecode_display(force=True)
    

    def update_timecode_display(self, force=False):
        if not self.current_image:
            return

        img = self.current_image.copy()
        draw = ImageDraw.Draw(img)

        font_size = max(24, img.height // 20)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        s, f = self.durations[self.current_index]
        total_ms = int((s + f / self.fps) * 1000)
        elapsed_ms = min(self.elapsed_ms, total_ms)
        elapsed_sec = elapsed_ms // 1000
        elapsed_frame = int((elapsed_ms % 1000) / (1000 / self.fps))

        timecode_text = f"{elapsed_sec:02d}s + {elapsed_frame:02d}f"
        margin = img.height // 30
        x = margin
        y = img.height - margin - font_size

        shadow_color = COLOR_BLACK
        text_color = COLOR_WHITE

        for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            draw.text((x + offset[0], y + offset[1]), timecode_text, font=font, fill=shadow_color)
        draw.text((x, y), timecode_text, font=font, fill=text_color)

        # Draw description bottom-left aligned left
        description = self.descriptions[self.current_index]
        if description:
            desc_font_size = max(18, img.height // 30)
            try:
                desc_font = ImageFont.truetype("arial.ttf", desc_font_size)
            except IOError:
                desc_font = ImageFont.load_default()

            desc_margin = 15
            # Get bounding box: (left, top, right, bottom)
            bbox = desc_font.getbbox(description)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            desc_pos = (img.width - desc_margin - text_width, img.height - desc_margin - text_height)

                # Draw shadow for readability
            for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                pos = (desc_pos[0] + offset[0], desc_pos[1] + offset[1])
                draw.text(pos, description, font=desc_font, fill=shadow_color)

             # Draw main text
            draw.text(desc_pos, description, font=desc_font, fill=text_color)
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def render_frame_for_export(self, index):
        pil_image = self.frames[index]
        target_w, target_h = 1920, 1080  # fixed export size
        target_ratio = 16 / 9

        bg = Image.new("RGBA", (target_w, target_h), COLOR_BLACK)

        if pil_image:
            img_ratio = pil_image.width / pil_image.height
            if img_ratio > target_ratio:
                new_w = target_w
                new_h = int(target_w / img_ratio)
            else:
                new_h = target_h
                new_w = int(target_h * img_ratio)
            resized_img = pil_image.resize((new_w, new_h), Image.LANCZOS)
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            bg.paste(resized_img, (x_offset, y_offset))

        draw = ImageDraw.Draw(bg)

        # Draw storyboard number
        font_size = max(24, target_h // 20)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        text = f"#{self.numbers[index]}"
        margin = 10
        text_pos = (margin, margin)
        shadow_color = COLOR_BLACK
        text_color = COLOR_WHITE

        for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            pos = (text_pos[0] + offset[0], text_pos[1] + offset[1])
            draw.text(pos, text, font=font, fill=shadow_color)
        draw.text(text_pos, text, font=font, fill=text_color)

        # Draw description bottom-right
        description = self.descriptions[index] if hasattr(self, "descriptions") else ""
        if description:
            desc_font_size = max(18, target_h // 30)
            try:
                desc_font = ImageFont.truetype("arial.ttf", desc_font_size)
            except IOError:
                desc_font = ImageFont.load_default()
            desc_w, desc_h = draw.textsize(description, font=desc_font)
            desc_pos = (target_w - desc_w - 15, target_h - desc_h - 15)
            for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                pos = (desc_pos[0] + offset[0], desc_pos[1] + offset[1])
                draw.text(pos, description, font=desc_font, fill=shadow_color)
            draw.text(desc_pos, description, font=desc_font, fill=text_color)

        return bg

class StoryboardPlanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ginyoa\'s Crappy Storyboard Planner")
        self.setWindowIcon(QIcon(FAVICON))

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # File menu bar
        menubar = QMenuBar()
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        load_action = QAction("Load Project", self)
        load_action.triggered.connect(self.load_project)
        file_menu.addAction(load_action)

        export_video_action = QAction("i wouldve made export mp4 but idk how", self)
        file_menu.addAction(export_video_action)

        export_spread_action = QAction("Export Spread (JPG/PNG)", self)
        export_spread_action.triggered.connect(self.export_spread)
        file_menu.addAction(export_spread_action)

        top_bar = QHBoxLayout()
        self.main_layout.addLayout(top_bar)


        # Title box
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Title: Enter storyboard title here...")
        top_bar.addWidget(self.title_edit)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Upload", "Draw"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        top_bar.addWidget(QLabel("Modes:"))
        top_bar.addWidget(self.mode_combo)
        top_bar.addStretch()

        top_bar.addWidget(QLabel("@ginyoagoldie 2025"))

        self.spread_layout = QHBoxLayout()
        self.spread_layout.setContentsMargins(0, 0, 0, 0)
        self.spread_layout.setSpacing(10)
        self.main_layout.addLayout(self.spread_layout)

        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setContentsMargins(0, 0, 0, 0)
        self.pagination_layout.setSpacing(10)
        self.main_layout.addLayout(self.pagination_layout)

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.go_previous)
        self.pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        self.pagination_layout.addWidget(self.page_label, 1)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.go_next)
        self.pagination_layout.addWidget(self.next_btn)

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_storyboard)
        self.pagination_layout.addWidget(self.play_btn)

        self.pages = []
        self.page_containers = []
        self.total_labels = []

        

        for page in self.pages:
           page.update_geometry()

        for i in range(TOTAL_PAGES):
            start_num = i * ROWS_PER_PAGE + 1
            page = StoryboardTable(page_number=i + 1, fps=DEFAULT_FPS, start_number=start_num)
            total_label = QLabel("Total Duration: 0 s + 0 f")
            total_label.setAlignment(Qt.AlignRight)
            total_label.setStyleSheet("font-weight: bold; padding-right: 5px;")

            container = QWidget()
            vlayout = QVBoxLayout(container)
            vlayout.setContentsMargins(0, 0, 0, 0)
            vlayout.setSpacing(2)
            vlayout.addWidget(page)
            vlayout.addWidget(total_label)

            self.pages.append(page)
            self.total_labels.append(total_label)
            self.page_containers.append(container)

        self.current_spread_index = 0
        self.update_view()
        self.resize(1200, 700)

        # Set default mode for all pages
        self.on_mode_changed(self.mode_combo.currentIndex())


    def on_mode_changed(self, index):
        mode_text = self.mode_combo.currentText()
        if "Draw" in mode_text:
            for page in self.pages:
                page.switch_to_draw_mode()
        else:
            for page in self.pages:
                page.switch_to_upload_mode()
        self.update_view()

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if not color.isValid():
            return

        rgba = (color.red(), color.green(), color.blue(), 255)
        self.current_brush_color = rgba
        # Update all drawing widgets brush color
        for page in self.pages:
            for dw in page.draw_widgets:
                if dw:
                    dw.set_brush_color(rgba)

    def brush_size_changed(self, value):
        self.current_brush_size = value
        for page in self.pages:
            for dw in page.draw_widgets:
                if dw:
                    dw.brush_size = value

    def eraser_toggled(self, checked):
        self.eraser_mode = checked
        for page in self.pages:
            for dw in page.draw_widgets:
                if dw:
                    dw.set_eraser_mode(checked)

    def update_view(self):
        for i in reversed(range(self.spread_layout.count())):
            item = self.spread_layout.takeAt(i)
            widget = item.widget()
            if widget:
                widget.hide()

        left_idx = self.current_spread_index * 2
        right_idx = left_idx + 1

        def show_page(idx):
            if idx < 0 or idx >= len(self.page_containers):
                return
            container = self.page_containers[idx]
            s, f = self.pages[idx].update_page_total_duration()
            self.total_labels[idx].setText(f"Total Duration: {s} s + {f} f")
            container.show()
            self.spread_layout.addWidget(container, 1)

        show_page(left_idx)
        show_page(right_idx)

        total_spreads = (len(self.pages) + 1) // 2
        self.page_label.setText(f"Spread {self.current_spread_index + 1} / {total_spreads}")

        self.prev_btn.setEnabled(self.current_spread_index > 0)
        self.next_btn.setEnabled(self.current_spread_index < total_spreads - 1)

    def update_totals_for_page(self, page):
        try:
            idx = self.pages.index(page)
        except ValueError:
            return
        s, f = page.update_page_total_duration()
        self.total_labels[idx].setText(f"Total Duration: {s} s + {f} f")

    def go_previous(self):
        if self.current_spread_index > 0:
            self.current_spread_index -= 1
            self.update_view()

    def go_next(self):
        total_spreads = (len(self.pages) + 1) // 2
        if self.current_spread_index < total_spreads - 1:
            self.current_spread_index += 1
            self.update_view()

    def play_storyboard(self):
        frames = []
        durations = []
        numbers = []
        descriptions = []

        for page in self.pages:
            for i in range(ROWS_PER_PAGE):
                s, f = page.duration_widgets[i].get_duration()

                # Force a minimum duration if the user hasn't set one
                if s == 0 and f == 0:
                    continue 

                img = page.uploaded_images[i]
                if img is None:
                    img = Image.new("RGBA", (DEFAULT_WIDTH, DEFAULT_HEIGHT), COLOR_WHITE)

                frames.append(img)
                durations.append((s, f))
                storyboard_number = page.start_number + i
                numbers.append(storyboard_number)

                # Always add description, even if it's empty
                desc_item = page.item(i, 2)
                descriptions.append(desc_item.text() if desc_item else "")

        if not frames:
            return

        self.player = PlayerWindow(frames, durations, numbers, descriptions, fps=DEFAULT_FPS)
        self.player.show()

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Storyboard Project (*.json)")
        if not filename:
            return
        if not filename.endswith(".json"):
            filename += ".json"

        data = {
            "title": self.title_edit.text(),
            "pages": []
        }

        for page in self.pages:
            page_data = {
                "start_number": page.start_number,
                "mode": page.mode,
                "rows": []
            }
            for row in range(ROWS_PER_PAGE):
                s, f = page.duration_widgets[row].get_duration()
                description = page.item(row, 2).text() if page.item(row, 2) else ""
                img_data = None
                if page.uploaded_images[row]:
                    with io.BytesIO() as output:
                        page.uploaded_images[row].save(output, format="PNG")
                        img_bytes = output.getvalue()
                    img_data = img_bytes.hex()
                row_data = {
                    "duration": (s, f),
                    "description": description,
                    "image_data": img_data,
                    "mode": page.mode,
                }
                page_data["rows"].append(row_data)
            data["pages"].append(page_data)

        try:
            with open(filename, "w") as f:
                json.dump(data, f)
            QMessageBox.information(self, "Save Project", "Project saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Project", f"Failed to save project:\n{str(e)}")



    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Storyboard Project (*.json)")
        if not filename:
            return

        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Load Project", f"Failed to load project:\n{str(e)}")
            return

        self.title_edit.setText(data.get("title", ""))

        pages_data = data.get("pages", [])
        for i, page_data in enumerate(pages_data):
            if i >= len(self.pages):
                break
            page = self.pages[i]
            page.start_number = page_data.get("start_number", page.start_number)
            mode = page_data.get("mode", "upload")
            if "draw" in mode:
                page.switch_to_draw_mode()
            else:
                page.switch_to_upload_mode()
            rows = page_data.get("rows", [])
            for row_idx, row_data in enumerate(rows):
                if row_idx >= ROWS_PER_PAGE:
                    break
                s, f = row_data.get("duration", (0, 0))
                page.duration_widgets[row_idx].seconds_edit.setText(str(s))
                page.duration_widgets[row_idx].frames_edit.setText(str(f))
                description = row_data.get("description", "")
                if page.item(row_idx, 2):
                    page.item(row_idx, 2).setText(description)
                else:
                    page.setItem(row_idx, 2, QTableWidgetItem(description))

                img_data_hex = row_data.get("image_data")
                if img_data_hex:
                    img_bytes = bytes.fromhex(img_data_hex)
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                    page.uploaded_images[row_idx] = img
                    if page.mode == "upload":
                        cell_width = page.columnWidth(1) or 150
                        cell_height = page.rowHeight(row_idx) or 50
                        qt_pixmap = page.pil_to_qpixmap_scaled(img, cell_width, cell_height)
                        btn = page.create_fixed_size_button(pixmap=qt_pixmap, row=row_idx)
                        btn.setFixedSize(cell_width, cell_height)
                        page.setCellWidget(row_idx, 1, btn)
                    elif page.mode == "draw":
                        dw = DrawingWidget(page.columnWidth(1), page.rowHeight(row_idx))
                        dw.image = img.resize((dw.width(), dw.height()), Image.LANCZOS)
                        dw.draw = ImageDraw.Draw(dw.image)
                        dw.update_pixmap()
                        page.draw_widgets[row_idx] = dw
                        page.setCellWidget(row_idx, 1, dw)
                else:
                    page.uploaded_images[row_idx] = None
                    if page.mode == "upload":
                        page._add_upload_button(row_idx)
                    else:
                        if page.draw_widgets[row_idx] is None:
                            dw = DrawingWidget(page.columnWidth(1), page.rowHeight(row_idx))
                            page.draw_widgets[row_idx] = dw
                            page.setCellWidget(row_idx, 1, dw)

        self.update_view()
        QMessageBox.information(self, "Load Project", "Project loaded successfully.")


    def render_frame_for_export(self, index):
        from PIL import Image, ImageDraw, ImageFont

        pil_image = self.frames[index]
        target_w, target_h = 1920, 1080
        target_ratio = 16 / 9

        bg = Image.new("RGBA", (target_w, target_h), COLOR_BLACK)

        if pil_image:
            img_ratio = pil_image.width / pil_image.height
            if img_ratio > target_ratio:
                new_w = target_w
                new_h = int(target_w / img_ratio)
            else:
                new_h = target_h
                new_w = int(target_h * img_ratio)
            resized_img = pil_image.resize((new_w, new_h), Image.LANCZOS)
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            bg.paste(resized_img, (x_offset, y_offset))

        draw = ImageDraw.Draw(bg)

        # Storyboard number
        font_size = max(24, target_h // 20)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        text = f"#{self.numbers[index]}"
        margin = 10
        text_pos = (margin, margin)
        shadow_color = COLOR_BLACK
        text_color = COLOR_WHITE

        for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            pos = (text_pos[0] + offset[0], text_pos[1] + offset[1])
            draw.text(pos, text, font=font, fill=shadow_color)
        draw.text(text_pos, text, font=font, fill=text_color)

        # Description bottom-right
        description = getattr(self, "descriptions", [""] * len(self.frames))[index]
        if description:
            desc_font_size = max(18, target_h // 30)
            try:
                desc_font = ImageFont.truetype("arial.ttf", desc_font_size)
            except IOError:
                desc_font = ImageFont.load_default()
            desc_w, desc_h = draw.textbbox((0, 0), description, font=desc_font)[2:]
            desc_pos = (target_w - desc_w - 15, target_h - desc_h - 15)
            for offset in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                pos = (desc_pos[0] + offset[0], desc_pos[1] + offset[1])
                draw.text(pos, description, font=desc_font, fill=shadow_color)
            draw.text(desc_pos, description, font=desc_font, fill=text_color)

        return bg

    def export_spread(self):
        left_idx = self.current_spread_index * 2
        right_idx = left_idx + 1

        containers_to_export = []
        if left_idx < len(self.page_containers):
            containers_to_export.append(self.page_containers[left_idx])
        if right_idx < len(self.page_containers):
            containers_to_export.append(self.page_containers[right_idx])

        if not containers_to_export:
            QMessageBox.warning(self, "Export Spread", "No spread to export.")
            return

        filename, filter_ = QFileDialog.getSaveFileName(self, "Export Spread as Image", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if not filename:
            return

        # Export both pages in spread horizontally combined
        pixmaps = [container.grab() for container in containers_to_export]
        total_width = sum(p.width() for p in pixmaps)
        max_height = max(p.height() for p in pixmaps)

        result_img = QPixmap(total_width, max_height)
        result_img.fill(Qt.transparent)
        painter = QPainter(result_img)

        x_offset = 0
        for p in pixmaps:
            painter.drawPixmap(x_offset, 0, p)
            x_offset += p.width()
        painter.end()

        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            result_img.save(filename, "JPEG")
        else:
            result_img.save(filename, "PNG")

        QMessageBox.information(self, "Export Spread", f"Spread exported successfully to:\n{filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    window = StoryboardPlanner()
    window.show()
    sys.exit(app.exec())
