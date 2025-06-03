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
                               QFrame, QFormLayout, QSizePolicy, QRadioButton, QHBoxLayout, QGridLayout, QButtonGroup)
from PySide6.QtGui import QPixmap, Qt, QIcon

icon_key = "Icon"
nameplate_key = "Nameplate"
frame_key = "Frame"

english_lang = "en"
japanese_lang = "jp"

def get_profile_screen_pixmaps(data_path: Path) -> dict[str, dict[int, dict]]:
    pixmap_dict = {
        icon_key: {},
        nameplate_key: {},
        frame_key: {}
    }

    icon_path = data_path / 'user_icons'
    deka_icon_path = data_path / 'user_icons_deka'
    nameplate_path = data_path / 'user_nameplates'
    frame_path = data_path / 'user_frames'

    for file in deka_icon_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[icon_key][int(file.stem)] = {"img": QPixmap(str(file.absolute())), "deka": True}
    for file in icon_path.iterdir():
        if file.is_file() and file.suffix == '.png' and int(file.stem) not in pixmap_dict[icon_key].keys():
            pixmap_dict[icon_key][int(file.stem)] = {"img": QPixmap(str(file.absolute())), "deka": False}

    for file in nameplate_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[nameplate_key][int(file.stem)] = {"img": QPixmap(str(file.absolute()))}

    for file in frame_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[frame_key][int(file.stem)] = {"img": QPixmap(str(file.absolute()))}

    return pixmap_dict



def get_profile_image_data(data_path: Path):
    pixmap_dict = get_profile_screen_pixmaps(data_path)

    with sqlite3.connect(data_path / "customisations.db") as conn:
        cur = conn.cursor()

        for customisation_type in pixmap_dict:
            q = (f"SELECT id, name_en, description_en, name_jp, description_jp FROM customisations"
                 f"   WHERE customisation_type_id = "
                 f"       (SELECT id "
                 f"           FROM customisation_types "
                 f"           WHERE name_en = ?)"
                 # Make a wildcard for each image, and fill it using `pixmap_dict`
                 f"    AND id IN ({",".join(["?"] * len(pixmap_dict[customisation_type]))});")
            image_info = cur.execute(q,
                                     (customisation_type, *pixmap_dict[customisation_type].keys(),)
                                     ).fetchall()

            for row in image_info:
                image_dict = pixmap_dict[customisation_type][row[0]]

                image_dict["name_en"] = row[1]
                image_dict["description_en"] = row[2]
                image_dict["name_jp"] = row[3]
                image_dict["description_jp"] = row[4]

    return pixmap_dict


def get_image_options_from_data_dict(data_dict: dict[int, dict[str, str | QPixmap]]):
    options = []

    for image_id in data_dict:
        options.append(
            (
                image_id,
                f"[{image_id}] {data_dict[image_id]["name_en"]}",
            )
        )

    return sorted(options, key=lambda x: x[0])


ComboboxOption = namedtuple('ComboboxOption', ['ID', 'Text'])


class ProfileCustomisationDataManager:

    def __init__(self, data: dict[str, dict[int, dict[str, str | QPixmap]]]):
        self.data = data

        icon_combobox_options = self.build_image_combobox_options(data[icon_key])
        self.english_icon_combobox_options = self.get_english_options(icon_combobox_options)
        self.japanese_icon_combobox_options = self.get_japanese_options(icon_combobox_options)

        nameplate_combobox_options = self.build_image_combobox_options(data[nameplate_key])
        self.english_nameplate_combobox_options = self.get_english_options(nameplate_combobox_options)
        self.japanese_nameplate_combobox_options = self.get_japanese_options(nameplate_combobox_options)

        frame_combobox_options = self.build_image_combobox_options(data[frame_key])
        self.english_frame_combobox_options = self.get_english_options(frame_combobox_options)
        self.japanese_frame_combobox_options = self.get_japanese_options(frame_combobox_options)



    def build_image_combobox_options(self, customisation_options: dict[int, dict[str, str | QPixmap]]):
        options = []

        for image_id in customisation_options:
            options.append(
                (
                    image_id,
                    f"[{image_id}] {customisation_options[image_id][f"name_{english_lang}"]}",
                    f"[{image_id}] {customisation_options[image_id][f"name_{japanese_lang}"]}",
                )
            )

        return sorted(options, key=lambda x: x[0])


    def get_language_options(self, multi_lang_options, lang=english_lang) -> tuple[ComboboxOption]:
        if lang == english_lang:
            text_idx = 1
        elif lang == japanese_lang:
            text_idx = 2
        else:
            raise ValueError("Invalid language selected.")

        return [ComboboxOption(ID=option[0], Text=option[text_idx]) for option in multi_lang_options]

    def get_english_options(self, multi_lang_options):
        return self.get_language_options(multi_lang_options, english_lang)

    def get_japanese_options(self, multi_lang_options):
        return self.get_language_options(multi_lang_options, japanese_lang)


class ProfileView(QGraphicsView):
    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setGeometry(0, 0, 720, 300)
        # Set minimum dimensions to account for both profile and border (at 1px per side)
        self.setMinimumSize(722, 302)
        # Unnecessary with minimum size enforcement
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.profile_scene = QGraphicsScene()
        self.setScene(self.profile_scene)

        self.icon_graphics_item = QGraphicsPixmapItem()
        self.nameplate_graphics_item = QGraphicsPixmapItem()
        self.nameplate_graphics_item.setPos(QPoint(143, 0))
        self.frame_graphics_item = QGraphicsPixmapItem()

        self.profile_scene.addItem(self.frame_graphics_item)
        self.profile_scene.addItem(self.icon_graphics_item)
        self.profile_scene.addItem(self.nameplate_graphics_item)

    def setIcon(self, icon: QPixmap, is_deka_icon: bool):
        self.icon_graphics_item.setPixmap(icon)
        if not is_deka_icon:
            self.icon_graphics_item.setPos(QPoint(15, 15))
        else:
            self.icon_graphics_item.setPos(QPoint(0, 0))

    def setNameplate(self, nameplate: QPixmap):
        self.nameplate_graphics_item.setPixmap(nameplate)

    def setFrame(self, frame: QPixmap):
        self.frame_graphics_item.setPixmap(frame)

    def setProfileCustomisations(self, icon: QPixmap, nameplate: QPixmap, frame: QPixmap, is_deka_icon: bool):
        self.setFrame(frame)
        self.setNameplate(nameplate)
        self.setIcon(icon, is_deka_icon)



class ProfileExplorerWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        pixmap = QPixmap("./data/splash.png")
        splash = QSplashScreen(pixmap)
        splash.show()

        splash.showMessage("Loading Image Data...")
        self.image_data = get_profile_image_data(Path("./data"))
        self.data_manager = ProfileCustomisationDataManager(self.image_data)

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

        self.icon_options_select = QComboBox()
        self.icon_options_select.currentIndexChanged.connect(self.handleIconSelectionChanged)
        self.nameplate_options_select = QComboBox()
        self.nameplate_options_select.currentIndexChanged.connect(self.handleNameplateSelectionChanged)
        self.frame_options_select = QComboBox()
        self.frame_options_select.currentIndexChanged.connect(self.handleFrameSelectionChanged)

        self.icon_options_layout = QFormLayout()
        self.icon_options_layout.addRow("Icon:", self.icon_options_select)
        self.icon_options_layout.addRow("Nameplate:", self.nameplate_options_select)
        self.icon_options_layout.addRow("Frame:", self.frame_options_select)

        self.icon_options_widget = QWidget()
        self.icon_options_widget.setLayout(self.icon_options_layout)
        self.menu_tabs.addTab(self.icon_options_widget, "Options")

        splash.showMessage("Preparing data for UI Elements...")

        # icon_selector_options = get_image_options_from_data_dict(self.image_data[icon_key])
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


    def handleIconSelectionChanged(self, index: int):
        img_id = self.icon_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setIcon(
            self.image_data[icon_key][img_id]["img"],
            self.image_data[icon_key][img_id]["deka"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{english_lang}"
        else:
            objective_key = f"description_{japanese_lang}"
        self.icon_objective_label.setText(f"<b>Icon:</b> {self.image_data[icon_key][img_id][objective_key]}")

    def handleNameplateSelectionChanged(self, index: int):
        img_id = self.nameplate_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setNameplate(
            self.image_data[nameplate_key][img_id]["img"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{english_lang}"
        else:
            objective_key = f"description_{japanese_lang}"
        self.nameplate_objective_label.setText(f"<b>Nameplate:</b> {self.image_data[nameplate_key][img_id][objective_key]}")

    def handleFrameSelectionChanged(self, index: int):
        img_id = self.frame_options_select.currentData()

        # Avoid error from clearing the combobox options
        if img_id is None:
            return

        self.profile_view.setFrame(
            self.image_data[frame_key][img_id]["img"],
        )

        if self.english_language_choice.isChecked():
            objective_key = f"description_{english_lang}"
        else:
            objective_key = f"description_{japanese_lang}"
        self.frame_objective_label.setText(f"<b>Frame:</b> {self.image_data[frame_key][img_id][objective_key]}")

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("./data/icon.ico"))
    mainWindow = ProfileExplorerWindow()

    sys.exit(app.exec())