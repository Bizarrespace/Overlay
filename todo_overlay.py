import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QListWidget, QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QLabel, QFileDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPixmap
from datetime import datetime
import keyboard


class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Enable drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        # Notify the parent window to save the new order
        if isinstance(self.parent(), OverlayWindow):
            self.parent().save_items()
            
class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.save_file = Path("todo_items.xml")
        self.initUI()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.is_visible = True
        self.resizing = False
        self.resize_margin = 30
        
        keyboard.on_press_key("enter", self.handle_hotkey, suppress=False)
        keyboard.on_press_key("`", self.close_program, suppress=True)
        
        # Load saved items
        self.load_items()
        
    def save_items(self):
        """Save todo items and image paths to XML file"""
        root = ET.Element("todo_list")
        
        for i in range(self.todo_list.count()):
            item = ET.SubElement(root, "item")
            list_item = self.todo_list.item(i)
            # Save text
            text = ET.SubElement(item, "text")
            text.text = list_item.text()
            # Save image path if exists
            image_path = list_item.data(Qt.UserRole)
            if image_path:
                image = ET.SubElement(item, "image")
                image.text = image_path
                
                if "clipboard_image_" in image_path:
                    image.set("source", "clipboard")
                else:
                    image.set("source", "file")
                
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.save_file, encoding="utf-8", xml_declaration=True)

    def load_items(self):
        """Load todo items and image paths from XML file"""
        if not self.save_file.exists():
            return
            
        try:
            tree = ET.parse(self.save_file)
            root = tree.getroot()
            
            for item in root.findall("item"):
                text_elem = item.find("text")
                image_elem = item.find("image")
                
                if text_elem is not None and text_elem.text:
                    list_item = QListWidgetItem(text_elem.text)
                    if image_elem is not None and image_elem.text:
                        # Store the image path in the item's data
                        image_path = image_elem.text
                        if Path(image_path).exists():  # Verify image file exists
                            list_item.setData(Qt.UserRole, image_path)
                    self.todo_list.addItem(list_item)
                    
            # If there are items, select the first one to show its image
            if self.todo_list.count() > 0:
                self.todo_list.setCurrentRow(0)
                self.on_item_selected()
                
        except ET.ParseError:
            QMessageBox.warning(self, "Load Error", 
                            "Could not load saved items.")
        
    def initUI(self):
        # Main widget and layout setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Left panel (Todo List)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(10, 10, 5, 15)
        
        # Right panel (Image Display)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(5, 10, 15, 15)
        self.right_panel.hide()  # Initially hide the right panel
        
        # Style both panels
        for panel in [self.left_panel, self.right_panel]:
            panel.setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 0, 0, 180);
                    border-radius: 10px;
                }
            """)
        
        # Replace QListWidget with DraggableListWidget
        self.todo_list = DraggableListWidget()
        self.todo_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(40, 40, 40, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: rgba(60, 60, 60, 180);
                border-radius: 3px;
                margin: 2px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: rgba(70, 130, 180, 180);
            }
            QListWidget::item:hover {
                background-color: rgba(80, 80, 80, 180);
            }
        """)
        
        # Input field
        self.item_input = QLineEdit()
        self.item_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 100, 60, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.item_input.returnPressed.connect(self.add_item)
        
        # Todo list buttons
        self.add_button = QPushButton("Add Item")
        self.delete_button = QPushButton("Delete Selected")
        self.upload_image_button = QPushButton("Add Image")  # Moved to left panel
        
        # Image display setup
        self.image_label = QLabel()
        self.image_label.setMinimumWidth(300)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 180);
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
        """)
        
        # Image control buttons
        self.clear_image_button = QPushButton("Clear Image")
        
        # Style all buttons
        for button in [self.add_button, self.delete_button, 
                    self.upload_image_button, self.clear_image_button]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(70, 130, 180, 180);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(70, 130, 180, 220);
                }
            """)
        
        # Connect all signals
        self.add_button.clicked.connect(self.add_item)
        self.delete_button.clicked.connect(self.delete_selected_item)
        self.upload_image_button.clicked.connect(self.upload_image)
        self.clear_image_button.clicked.connect(self.clear_image)
        self.todo_list.itemSelectionChanged.connect(self.on_item_selected)
        
        # Populate left panel
        self.left_layout.addWidget(self.todo_list)
        self.left_layout.addWidget(self.item_input)
        self.left_layout.addWidget(self.add_button)
        self.left_layout.addWidget(self.delete_button)
        self.left_layout.addWidget(self.upload_image_button)  # Added to left panel
        
        # Populate right panel
        self.right_layout.addWidget(self.image_label)
        self.right_layout.addWidget(self.clear_image_button)
        
        # Add panels to main layout
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel)
        
        # Set window properties
        self.setMinimumSize(350, 400)  # Reduced minimum width
        self.setMaximumSize(1200, 800)
        self.resize(350, 500)  # Default size with only left panel

    def update_window_size(self, show_image=False):
        """Update window size based on whether image panel is shown"""
        current_pos = self.pos()
        if show_image:
            new_width = 900  # Width with image panel
            self.setMinimumSize(700, 400)
        else:
            new_width = 350  # Width without image panel
            self.setMinimumSize(350, 400)
        
        self.resize(new_width, self.height())
        # Keep the window position centered on the same point
        width_diff = new_width - self.width()
        self.move(current_pos.x() - (width_diff // 2), current_pos.y())
    
    def show_image_panel(self, show=True):
        """Show or hide the image panel"""
        if show:
            self.right_panel.show()
            self.update_window_size(True)
        else:
            self.right_panel.hide()
            self.update_window_size(False)
            
    def upload_image(self, from_clipboard=False):
        current_item = self.todo_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", 
                            "Please select a todo item first.")
            return

        if from_clipboard:
            print("Attempting to get image from clipboard...")  # Debug print
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                print("Found image in clipboard")  # Debug print
                pixmap = QPixmap(clipboard.image())
            else:
                QMessageBox.warning(self, "Clipboard Empty", 
                                "No image found in clipboard.")
                print("No image found in clipboard")  # Debug print
                return
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)"
            )
            if not file_path:
                return
            pixmap = QPixmap(file_path)

        # Add error checking for pixmap
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", 
                            "Failed to load image from clipboard.")
            print("Failed to create pixmap from clipboard image")  # Debug print
            return

        try:
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
            if from_clipboard:
                # Create images directory if it doesn't exist
                save_dir = Path("images")
                save_dir.mkdir(exist_ok=True)
                
                # Generate unique filename using timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = save_dir / f"clipboard_image_{timestamp}.png"
                
                if pixmap.save(str(file_path), "PNG"):
                    print(f"Successfully saved clipboard image to: {file_path}")
                else:
                    print(f"Failed to save clipboard image to: {file_path}")
                    return
                    
            current_item.setData(Qt.UserRole, str(file_path))
            self.show_image_panel(True)
            self.save_items()
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            QMessageBox.warning(self, "Error", 
                            f"Error processing image: {str(e)}")

    def keyPressEvent(self, event):
        # Check for Ctrl+V
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.upload_image(from_clipboard=True)
            event.accept()
        else:
            super().keyPressEvent(event)
            
    def clear_image(self):
        current_item = self.todo_list.currentItem()
        if current_item:
            # Get the image path before clearing the data
            image_path = current_item.data(Qt.UserRole)
            if image_path:
                try:
                    # Convert string path to Path object
                    path = Path(image_path)
                    # Only delete if it's in our images directory
                    if path.exists() and "images" in str(path):
                        path.unlink()  # Delete the file
                        print(f"Deleted image file: {path}")
                except Exception as e:
                    print(f"Error deleting image file: {e}")
            
            current_item.setData(Qt.UserRole, None)
            self.image_label.clear()
            self.show_image_panel(False)
            self.save_items()

    def on_item_selected(self):
        current_item = self.todo_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and Path(image_path).exists():
                pixmap = QPixmap(image_path)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.show_image_panel(True)
            else:
                self.image_label.clear()
                self.show_image_panel(False)
        else:
            self.image_label.clear()
            self.show_image_panel(False)
                
    def paintEvent(self, event):
        # Used to draw three red dots on the bottom right of the overlay to show
        # That we can make it bigger or smaller
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        handle_color = QColor(255, 0, 255, 255) 
        painter.setPen(Qt.NoPen)
        painter.setBrush(handle_color)
        
        x = self.width() - 25
        y = self.height() - 25
        for i in range(3):
            painter.drawRect(x + (i * 4), y + 10 - (i * 4), 2, 2)
    
    def add_item(self):
        text = self.item_input.text().strip()
        if text:
            self.todo_list.addItem(text)
            self.item_input.clear()
            self.save_items()  # Save after adding
            
    def delete_selected_item(self):
        selected_items = self.todo_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return
        
        for item in selected_items:
            # Clean up associated image before deleting the item
            image_path = item.data(Qt.UserRole)
            if image_path:
                try:
                    path = Path(image_path)
                    # Only delete if it's in our images directory
                    if path.exists() and "images" in str(path):
                        path.unlink()  # Delete the file
                        print(f"Deleted image file: {path}")
                except Exception as e:
                    print(f"Error deleting image file: {e}")
            
            # Remove the item from the list
            row = self.todo_list.row(item)
            self.todo_list.takeItem(row)
        
        self.save_items()
    
    def handle_hotkey(self, e):
        if keyboard.is_pressed('shift'):
            self.toggle_visibility()
            return False  # Don't propagate the event when we use it
        return True  # Propagate the event in all other cases
    
    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setVisible(self.is_visible)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if (self.width() - event.x() <= self.resize_margin and 
                self.height() - event.y() <= self.resize_margin):
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_size = self.size()
            else:
                self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.resizing = False

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.globalPos() - self.resize_start_pos
            new_width = max(200, min(800, self.resize_start_size.width() + delta.x()))
            new_height = max(300, min(600, self.resize_start_size.height() + delta.y()))
            self.resize(new_width, new_height)
        elif hasattr(self, 'oldPos'):
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
        else:
            if (self.width() - event.x() <= self.resize_margin and 
                self.height() - event.y() <= self.resize_margin):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def close_program(self, e):
        self.save_items()  # Save items before closing
        keyboard.unhook_all()
        QApplication.quit()
        
    def main():
        app = QApplication(sys.argv)
        overlay = OverlayWindow()
        overlay.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    OverlayWindow.main()