from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem


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