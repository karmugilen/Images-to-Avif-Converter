import sys
import os
import glob
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar, QListWidget, QLineEdit, QSlider
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import pillow_avif

class ConvertWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files, output_dir, quality):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.quality = quality
        self.is_cancelled = False

    def run(self):
        total_files = len(self.files)
        for i, file in enumerate(self.files):
            if self.is_cancelled:
                break
            self.status.emit(f'Converting: {os.path.basename(file)}')
            try:
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                image = Image.open(file)
                output_filename = os.path.splitext(os.path.basename(file))[0] + '.avif'
                output_path = os.path.join(self.output_dir, output_filename)
                image.save(output_path, 'AVIF', quality=self.quality)
            except Exception as e:
                self.status.emit(f'Error converting {os.path.basename(file)}: {e}')
            self.progress.emit(int(((i + 1) / total_files) * 100))
        self.finished.emit()

    def cancel(self):
        self.is_cancelled = True

class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.addItem(url.toLocalFile())

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Image Converter')
        self.setGeometry(100, 100, 500, 400)

        # Teenage Engineering Style
        self.setStyleSheet("""
            QWidget {
                background-color: #E0E0E0;
                color: #1E1E1E;
                font-family: 'Monospace';
                font-size: 12px;
            }
            QPushButton {
                background-color: #FF4500;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6347;
            }
            QPushButton:disabled {
                background-color: #A9A9A9;
            }
            QLabel {
                font-size: 12px;
            }
            QListWidget {
                background-color: #F5F5F5;
                border: 1px solid #D3D3D3;
            }
            QLineEdit {
                background-color: #F5F5F5;
                border: 1px solid #D3D3D3;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #D3D3D3;
                text-align: center;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #FF4500;
            }
            QSlider::groove:horizontal {
                border: 1px solid #D3D3D3;
                height: 8px;
                background: #F5F5F5;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #FF4500;
                border: 1px solid #FF4500;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # File Selection Layout
        selection_layout = QHBoxLayout()
        self.select_files_button = QPushButton('Select Files')
        self.select_files_button.clicked.connect(self.select_files)
        selection_layout.addWidget(self.select_files_button)

        self.select_folder_button = QPushButton('Select Folder')
        self.select_folder_button.clicked.connect(self.select_folder)
        selection_layout.addWidget(self.select_folder_button)

        self.clear_button = QPushButton('Clear')
        self.clear_button.clicked.connect(self.clear_files)
        selection_layout.addWidget(self.clear_button)
        main_layout.addLayout(selection_layout)

        self.file_list = FileListWidget()
        main_layout.addWidget(self.file_list)

        # Output Directory Layout
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel('Output Directory:')
        output_layout.addWidget(self.output_dir_label)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_layout.addWidget(self.output_dir_edit)
        self.browse_button = QPushButton('Browse...')
        self.browse_button.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(self.browse_button)
        main_layout.addLayout(output_layout)

        # Conversion Options
        quality_layout = QHBoxLayout()
        self.quality_label = QLabel('AVIF Quality:')
        quality_layout.addWidget(self.quality_label)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(80)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        quality_layout.addWidget(self.quality_slider)

        self.quality_value_label = QLabel("80")
        quality_layout.addWidget(self.quality_value_label)
        main_layout.addLayout(quality_layout)

        # Conversion Control
        control_layout = QHBoxLayout()
        self.convert_button = QPushButton('Convert to AVIF')
        self.convert_button.clicked.connect(self.convert_images)
        control_layout.addWidget(self.convert_button)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.cancel_button.setEnabled(False)
        control_layout.addWidget(self.cancel_button)
        main_layout.addLayout(control_layout)

        # Progress
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel('Ready')
        main_layout.addWidget(self.status_label)

        self.show()

    def update_quality_label(self, value):
        self.quality_value_label.setText(str(value))

    def select_files(self, files=None):
        if not files:
            files, _ = QFileDialog.getOpenFileNames(self, 'Select Images', '', 'Images (*.png *.jpg *.jpeg)')
        if files:
            self.file_list.addItems(files)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            for ext in ('*.png', '*.jpg', '*.jpeg'):
                self.file_list.addItems(glob.glob(os.path.join(folder, ext)))

    def clear_files(self):
        self.file_list.clear()

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        if directory:
            self.output_dir_edit.setText(directory)

    def convert_images(self):
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        output_dir = self.output_dir_edit.text()
        quality = self.quality_slider.value()

        if not files:
            self.status_label.setText('Error: No files selected.')
            return
        if not output_dir:
            self.status_label.setText('Error: No output directory selected.')
            return

        self.convert_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.worker = ConvertWorker(files, output_dir, quality)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def cancel_conversion(self):
        if hasattr(self, 'worker'):
            self.worker.cancel()

    def conversion_finished(self):
        self.convert_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText('Conversion finished.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
