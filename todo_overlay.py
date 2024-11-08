import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QListWidget, QPushButton, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor
import keyboard

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
        self.resize_margin = 15
        
        keyboard.on_press_key("enter", self.handle_hotkey, suppress=False)
        keyboard.on_press_key("`", self.close_program, suppress=True)
        
        # Load saved items
        self.load_items()
        
    def save_items(self):
        """Save todo items to XML file"""
        root = ET.Element("todo_list")
        
        for i in range(self.todo_list.count()):
            item = ET.SubElement(root, "item")
            item.text = self.todo_list.item(i).text()
            
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.save_file, encoding="utf-8", xml_declaration=True)
        
    def load_items(self):
        """Load todo items from XML file"""
        if not self.save_file.exists():
            return
            
        try:
            tree = ET.parse(self.save_file)
            root = tree.getroot()
            
            for item in root.findall("item"):
                if item.text:
                    self.todo_list.addItem(item.text)
        except ET.ParseError:
            QMessageBox.warning(
                self,
                "Load Error",
                "Could not load saved items. File may be corrupted."
            )
        
    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.layout.setContentsMargins(10, 10, 15, 15)
        
        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
            }
        """)
        
        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(40, 40, 40, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        self.item_input = QLineEdit()
        self.item_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.item_input.returnPressed.connect(self.add_item)
        
        self.add_button = QPushButton("Add Item")
        self.delete_button = QPushButton("Delete Selected")
        
        for button in [self.add_button, self.delete_button]:
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
        
        self.add_button.clicked.connect(self.add_item)
        self.delete_button.clicked.connect(self.delete_selected_item)
        
        self.layout.addWidget(self.todo_list)
        self.layout.addWidget(self.item_input)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.delete_button)
        
        self.resize(300, 400)
        self.move(100, 100)
        
        self.setMinimumSize(200, 300)
        self.setMaximumSize(800, 600)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        handle_color = QColor(255, 0, 255, 255) 
        painter.setPen(Qt.NoPen)
        painter.setBrush(handle_color)
        
        x = self.width() - 15
        y = self.height() - 15
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
            row = self.todo_list.row(item)
            self.todo_list.takeItem(row)
        
        self.save_items()  # Save after deleting
    
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