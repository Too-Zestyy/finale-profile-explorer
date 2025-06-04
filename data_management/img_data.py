import sqlite3
from collections import namedtuple
from pathlib import Path

from PySide6.QtGui import QPixmap

ComboboxOption = namedtuple('ComboboxOption', ['ID', 'Text'])

ICON_KEY = "Icon"
NAMEPLATE_KEY = "Nameplate"
FRAME_KEY = "Frame"

LANG_EN = "en"
LANG_JP = "jp"

def get_profile_screen_pixmaps(data_path: Path) -> dict[str, dict[int, dict]]:
    pixmap_dict = {
        ICON_KEY: {},
        NAMEPLATE_KEY: {},
        FRAME_KEY: {}
    }

    icon_path = data_path / 'user_icons'
    deka_icon_path = data_path / 'user_icons_deka'
    nameplate_path = data_path / 'user_nameplates'
    frame_path = data_path / 'user_frames'

    for file in deka_icon_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[ICON_KEY][int(file.stem)] = {"img": QPixmap(str(file.absolute())), "deka": True}
    for file in icon_path.iterdir():
        if file.is_file() and file.suffix == '.png' and int(file.stem) not in pixmap_dict[ICON_KEY].keys():
            pixmap_dict[ICON_KEY][int(file.stem)] = {"img": QPixmap(str(file.absolute())), "deka": False}

    for file in nameplate_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[NAMEPLATE_KEY][int(file.stem)] = {"img": QPixmap(str(file.absolute()))}

    for file in frame_path.iterdir():
        if file.is_file() and file.suffix == '.png':
            pixmap_dict[FRAME_KEY][int(file.stem)] = {"img": QPixmap(str(file.absolute()))}

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

class ProfileCustomisationDataManager:

    def __init__(self, data_path: Path):
        # TODO: Refactor use of `raw_data` to using a separate field that only holds image data
        self.raw_data = get_profile_image_data(data_path)

        icon_combobox_options = self.build_image_combobox_options(self.raw_data[ICON_KEY])
        self.english_icon_combobox_options = self.get_english_options(icon_combobox_options)
        self.japanese_icon_combobox_options = self.get_japanese_options(icon_combobox_options)

        nameplate_combobox_options = self.build_image_combobox_options(self.raw_data[NAMEPLATE_KEY])
        self.english_nameplate_combobox_options = self.get_english_options(nameplate_combobox_options)
        self.japanese_nameplate_combobox_options = self.get_japanese_options(nameplate_combobox_options)

        frame_combobox_options = self.build_image_combobox_options(self.raw_data[FRAME_KEY])
        self.english_frame_combobox_options = self.get_english_options(frame_combobox_options)
        self.japanese_frame_combobox_options = self.get_japanese_options(frame_combobox_options)



    def build_image_combobox_options(self, customisation_options: dict[int, dict[str, str | QPixmap]]):
        options = []

        for image_id in customisation_options:
            options.append(
                (
                    image_id,
                    f"[{image_id}] {customisation_options[image_id][f"name_{LANG_EN}"]}",
                    f"[{image_id}] {customisation_options[image_id][f"name_{LANG_JP}"]}",
                )
            )

        return sorted(options, key=lambda x: x[0])


    def get_language_options(self, multi_lang_options, lang=LANG_EN) -> tuple[ComboboxOption]:
        if lang == LANG_EN:
            text_idx = 1
        elif lang == LANG_JP:
            text_idx = 2
        else:
            raise ValueError("Invalid language selected.")

        return [ComboboxOption(ID=option[0], Text=option[text_idx]) for option in multi_lang_options]

    def get_english_options(self, multi_lang_options):
        return self.get_language_options(multi_lang_options, LANG_EN)

    def get_japanese_options(self, multi_lang_options):
        return self.get_language_options(multi_lang_options, LANG_JP)