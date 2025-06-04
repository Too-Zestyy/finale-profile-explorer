from PySide6 import QtGui
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap, QBrush, QColor, QPen, Qt, QFont, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsSimpleTextItem, \
    QGraphicsTextItem, QStyleOptionGraphicsItem, QWidget, QGraphicsItem


# class ProfileNameTextGraphicsItem(QGraphicsSimpleTextItem):
#     def __init__(self, parent=None):
#         super(ProfileNameTextGraphicsItem, self).__init__(parent)
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
#         self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
#         self.setAcceptHoverEvents(True)
#         self.font_family = 'Arial'
#         self.font_size = 24
#
#         self.setBrush(QColor("white"))
#         self.setPen(QColor("black"))
#
#     def hoverLeaveEvent(self, event):
#         self.setBrush(QtGui.QColor("black"))
#
#     def mousePressEvent(self, event):
#         self.setBrush(QtGui.QColor("gray"))
#
#     def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
#         custom_font = QFont(self.font_family)
#         custom_font.setPointSizeF(self.font_size)
#         painter.setFont(custom_font)
#         painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignLeft, self.text())

class ProfileView(QGraphicsView):
    profile_name_font_size = 24

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

        self.profile_name_graphics_item = QGraphicsSimpleTextItem()
        self.profile_name_graphics_item.setFont(QFont('SansSerif', self.profile_name_font_size))
        self.profile_name_fill_brush = QBrush()
        self.profile_name_fill_brush.setColor(QColor(255, 255, 255))
        self.profile_name_fill_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self.profile_name_outline_pen = QPen()
        self.profile_name_outline_pen.setColor(QColor(0, 0, 0))
        self.profile_name_outline_pen.setWidth(1)
        self.profile_name_graphics_item.setBrush(self.profile_name_fill_brush)
        self.profile_name_graphics_item.setPen(self.profile_name_outline_pen)

        self.profile_scene.addItem(self.frame_graphics_item)
        self.profile_scene.addItem(self.icon_graphics_item)
        self.profile_scene.addItem(self.nameplate_graphics_item)
        self.profile_scene.addItem(self.profile_name_graphics_item)

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

    def __transformProfileName(self, plain_name: str):
        """
        Uses `plain_name` to generate a string that only contains characters used within Maimai (i.e full-width characters)

        :param plain_name: The plain-text name to transform
        :return: A transformed string that only uses characters allowed within maimai profiles
        """
        WIDE_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
        WIDE_MAP[0x20] = 0x3000

        return plain_name.translate(WIDE_MAP)

    def setProfileName(self, name: str):
        self.profile_name_graphics_item.setText(self.__transformProfileName(name))

        text_width = self.profile_name_graphics_item.boundingRect().width()
        if name != "":
            self.profile_name_graphics_item.setPos(QPoint(
                int(421 - text_width),
                60))


