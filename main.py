import random
import sqlite3
import sys
import time
from argparse import ArgumentError
from collections import namedtuple
from copy import deepcopy
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QRect, QPoint
from PySide6.QtWidgets import (QApplication, QMainWindow,
                               QPushButton, QGraphicsView, QVBoxLayout, QGraphicsRectItem, QGraphicsScene,
                               QGraphicsPixmapItem, QTabWidget, QLabel, QWidget, QGroupBox, QSplashScreen, QComboBox,
                               QFrame, QFormLayout, QSizePolicy, QRadioButton, QHBoxLayout, QGridLayout, QButtonGroup,
                               QLineEdit)
from PySide6.QtGui import QPixmap, Qt, QIcon

from components.widgets import ProfileView
from data_management.img_data import ICON_KEY, LANG_EN, LANG_JP, NAMEPLATE_KEY, FRAME_KEY, \
    get_profile_image_data, ProfileCustomisationDataManager



class ProfileExplorerWindow(QMainWindow):
    max_profile_name_length = 10

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        pixmap = QPixmap("./data/splash.png")
        splash = QSplashScreen(pixmap)
        splash.show()

        splash.showMessage("Loading Image Data...")
        self.data_manager = ProfileCustomisationDataManager(Path("./data"))

        splash.showMessage("Loading UI...")
        self.setWindowTitle("Finale Profile Explorer")

        self.profile_view = ProfileView()
        self.view_layout = QVBoxLayout()
        self.view_layout.addWidget(self.profile_view)
        self.view_box = QGroupBox("Preview")
        self.view_box.setLayout(self.view_layout)

        self.language_choice_group = QButtonGroup()
        self.english_language_choice = QRadioButton("English")
        self.japanese_language_choice = QRadioButton("日本語")
        self.language_choice_group.addButton(self.english_language_choice)
        self.language_choice_group.addButton(self.japanese_language_choice)
        self.language_choice_layout = QHBoxLayout()
        self.language_choice_layout.addWidget(self.english_language_choice, alignment=Qt.AlignmentFlag.AlignCenter)
        self.language_choice_layout.addWidget(self.japanese_language_choice, alignment=Qt.AlignmentFlag.AlignCenter)
        self.language_choice_box = QGroupBox("Language")
        self.language_choice_box.setLayout(self.language_choice_layout)
        self.language_choice_group.buttonClicked.connect(self.handleLanguageChanged)

        self.icon_objective_label = QLabel()
        self.nameplate_objective_label = QLabel()
        self.frame_objective_label = QLabel()
        self.objective_layout = QVBoxLayout()
        self.objective_layout.addWidget(self.icon_objective_label)
        self.objective_layout.addWidget(self.nameplate_objective_label)
        self.objective_layout.addWidget(self.frame_objective_label)
        self.objective_group_box = QGroupBox("Customisation Objectives")
        self.objective_group_box.setLayout(self.objective_layout)

        self.menu_tabs = QTabWidget()

        self.profile_name_entry = QLineEdit()
        self.profile_name_entry.setMaxLength(self.max_profile_name_length)
        self.profile_name_entry.setPlaceholderText(f"Max Characters: {self.max_profile_name_length}")
        self.profile_name_entry.textChanged.connect(self.handleProfileNameChanged)
        self.profile_name_entry.setText("PLAYER")
        self.icon_options_select = QComboBox()
        self.icon_options_select.currentIndexChanged.connect(self.handleIconSelectionChanged)
        self.nameplate_options_select = QComboBox()
        self.nameplate_options_select.currentIndexChanged.connect(self.handleNameplateSelectionChanged)
        self.frame_options_select = QComboBox()
        self.frame_options_select.currentIndexChanged.connect(self.handleFrameSelectionChanged)

        self.profile_options_layout = QFormLayout()
        self.profile_options_layout.addRow("Profile Name:", self.profile_name_entry)
        self.profile_options_layout.addRow("Icon:", self.icon_options_select)
        self.profile_options_layout.addRow("Nameplate:", self.nameplate_options_select)
        self.profile_options_layout.addRow("Frame:", self.frame_options_select)

        self.icon_options_widget = QWidget()
        self.icon_options_widget.setLayout(self.profile_options_layout)
        self.menu_tabs.addTab(self.icon_options_widget, "Options")

        splash.showMessage("Preparing raw_data for UI Elements...")

        # icon_selector_options = get_image_options_from_data_dict(self.data_manager.raw_data[ICON_KEY])
        self.english_language_choice.click()

        self.randomiser_button = QPushButton("Click me!")
        self.randomiser_button.clicked.connect(self.handleRandomiserButtonClicked)
        self.randomiser_button.click()

        splash.showMessage("Finishing up...")


        window_layout = QVBoxLayout()
        window_layout.addWidget(self.view_box)
        window_layout.addWidget(self.language_choice_box)
        window_layout.addWidget(self.objective_group_box)
        window_layout.addWidget(self.menu_tabs)
        window_layout.addWidget(self.randomiser_button)
        # layout.addStretch()

        window_central_widget = QWidget()
        window_central_widget.setLayout(window_layout)
        self.setCentralWidget(window_central_widget)

        self.show()
        splash.finish(self)

    def handleRandomiserButtonClicked(self):
        self.icon_options_select.setCurrentIndex(random.randint(0, self.icon_options_select.count() - 1))
        self.nameplate_options_select.setCurrentIndex(random.randint(0, self.nameplate_options_select.count() - 1))
        self.frame_options_select.setCurrentIndex(random.randint(0, self.frame_options_select.count() - 1))

    def handleLanguageChanged(self):
        # Deep copying is required, since Qt frees the options from memory when they are cleared from the combobox
        if self.english_language_choice.isChecked():
            icon_options = deepcopy(self.data_manager.english_icon_combobox_options)
            nameplate_options = deepcopy(self.data_manager.english_nameplate_combobox_options)
            frame_options = deepcopy(self.data_manager.english_frame_combobox_options)
        elif self.japanese_language_choice.isChecked():
            icon_options = deepcopy(self.data_manager.japanese_icon_combobox_options)
            nameplate_options = deepcopy(self.data_manager.japanese_nameplate_combobox_options)
            frame_options = deepcopy(self.data_manager.japanese_frame_combobox_options)
        else:
            raise RuntimeError("No valid language selected")

        cur_icon_idx = self.icon_options_select.currentIndex()
        cur_nameplate_idx = self.nameplate_options_select.currentIndex()
        cur_frame_idx = self.frame_options_select.currentIndex()

        self.icon_options_select.clear()
        self.nameplate_options_select.clear()
        self.frame_options_select.clear()

        for option in icon_options:
            self.icon_options_select.addItem(option.Text, option.ID)
        for option in nameplate_options:
            self.nameplate_options_select.addItem(option.Text, option.ID)
        for option in frame_options:
            self.frame_options_select.addItem(option.Text, option.ID)

        self.icon_options_select.setCurrentIndex(cur_icon_idx)
        self.nameplate_options_select.setCurrentIndex(cur_nameplate_idx)
        self.frame_options_select.setCurrentIndex(cur_frame_idx)


    def handleProfileNameChanged(self, name: str):
        self.profile_view.setProfileName(name)


    def handleIconSelectionChanged(self, index: int):
        img_id = self.icon_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setIcon(
            self.data_manager.raw_data[ICON_KEY][img_id]["img"],
            self.data_manager.raw_data[ICON_KEY][img_id]["deka"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{LANG_EN}"
        else:
            objective_key = f"description_{LANG_JP}"
        self.icon_objective_label.setText(f"<b>Icon:</b> {self.data_manager.raw_data[ICON_KEY][img_id][objective_key]}")

    def handleNameplateSelectionChanged(self, index: int):
        img_id = self.nameplate_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setNameplate(
            self.data_manager.raw_data[NAMEPLATE_KEY][img_id]["img"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{LANG_EN}"
        else:
            objective_key = f"description_{LANG_JP}"
        self.nameplate_objective_label.setText(f"<b>Nameplate:</b> {self.data_manager.raw_data[NAMEPLATE_KEY][img_id][objective_key]}")

    def handleFrameSelectionChanged(self, index: int):
        img_id = self.frame_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setFrame(
            self.data_manager.raw_data[FRAME_KEY][img_id]["img"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{LANG_EN}"
        else:
            objective_key = f"description_{LANG_JP}"
        self.frame_objective_label.setText(f"<b>Frame:</b> {self.data_manager.raw_data[FRAME_KEY][img_id][objective_key]}")

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("./data/icon.ico"))
    mainWindow = ProfileExplorerWindow()

    sys.exit(app.exec())