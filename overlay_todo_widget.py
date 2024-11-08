import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QListWidget, QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor
import keyboard

# TODO: add delete button for todoitem

class TodoListWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.todo_list = QListWidget()
        self.item_input = QLineEdit()
        self.add_button = QPushButton("Add Item")
        self.collapse_button = QPushButton("-")
        self.delete_button = QPushButton("X")
        
        # Make collapse and delete buttons smaller
        self.collapse_button.setFixedSize(25, 25)
        self.delete_button.setFixedSize(25, 25)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.collapse_button)
        button_layout.addStretch()  # Add stretch to push delete button right
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)  # Move buttons to top
        layout.addWidget(self.todo_list)
        layout.addWidget(self.item_input)
        layout.addWidget(self.add_button)
        
        self.add_button.clicked.connect(self.add_item)
        self.delete_button.clicked.connect(self.delete_self)
        self.collapse_button.clicked.connect(self.toggle_collapse)
        self.item_input.returnPressed.connect(self.add_item)  # Allow Enter to add items
        
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 40, 180);
                border-radius: 10px;
                padding: 10px;
            }
            QListWidget {
                background-color: rgba(40, 40, 40, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit {
                background-color: rgba(60, 60, 60, 180);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
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

    def add_item(self):
        text = self.item_input.text().strip()
        if text:
            self.todo_list.addItem(text)
            self.item_input.clear()
            
    def delete_self(self):
        reply = QMessageBox.question(self, "Delete Confirmation",
                                   "Are you sure you want to delete this todo list?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.deleteLater()
    
    def toggle_collapse(self):
        collapsed = self.todo_list.isHidden()
        self.todo_list.setVisible(collapsed)
        self.item_input.setVisible(collapsed)
        self.add_button.setVisible(collapsed)
        self.collapse_button.setText("-" if collapsed else "+")
        
        # Adjust size after collapse
        if not collapsed:
            self.setMaximumHeight(50)
        else:
            self.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.is_visible = False
        self.resizing = False
        self.resize_margin = 15
        keyboard.on_press_key("enter", self.handle_hotkey, suppress=True)
        keyboard.on_press_key("esc", self.close_program, suppress=True)
        
    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 15, 15)
        
        # Create top button layout to keep create_todo_button at top
        top_layout = QHBoxLayout()
        self.create_todo_button = QPushButton("+ Create Todo")
        self.create_todo_button.setStyleSheet("""
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
        top_layout.addWidget(self.create_todo_button)
        top_layout.addStretch()
        
        self.create_todo_button.clicked.connect(self.create_todo_list)
        
        # Add layouts to main layout
        self.layout.addLayout(top_layout)
        self.layout.addStretch()  # Push todo lists up
        
        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
            }
        """)
        
        self.resize(300, 400)
        self.move(100, 100)
        self.setMinimumSize(200, 300)
        self.setMaximumSize(800, 600)

    def create_todo_list(self):
        todo_widget = TodoListWidget()
        # Insert widget before the stretch at the end
        self.layout.insertWidget(self.layout.count() - 1, todo_widget)

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

    def handle_hotkey(self, e):
        if keyboard.is_pressed('shift'):
            self.toggle_visibility()
    
    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setVisible(self.is_visible)
    
    def close_program(self, e):
        keyboard.unhook_all()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()
    sys.exit(app.exec_())