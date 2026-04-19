from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget, QStyle
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QFont
from gui import style_system
from gui.utils import colors

class ConnectionItem(QGraphicsPathItem):
    """A Bezier curve connecting two ports."""
    def __init__(self, start_port: 'PortItem', parent=None):
        super().__init__(parent)
        self.start_port = start_port
        self.end_port = None
        self._temp_end_pos = None
        
        start_port.connections.append(self)

        self.setPen(QPen(QColor(colors.text_tertiary), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setZValue(-1) # Behind nodes
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.remove()
        super().mousePressEvent(event)

    def remove(self):
        """Cleanly removes the connection from ports and scene."""
        if self.start_port and self in self.start_port.connections:
            self.start_port.connections.remove(self)
        if self.end_port and self in self.end_port.connections:
            self.end_port.connections.remove(self)
        if self.scene():
            self.scene().removeItem(self)

    def set_end_pos(self, pos: QPointF):
        self._temp_end_pos = pos
        self.update_path()

    def set_end_port(self, port: 'PortItem'):
        self.end_port = port
        self._temp_end_pos = None
        self.update_path()

    def update_path(self):
        start_pos = self.start_port.scene_pos()
        end_pos = self.end_port.scene_pos() if self.end_port else self._temp_end_pos

        if start_pos is None or end_pos is None:
            return

        path = QPainterPath()
        path.moveTo(start_pos)

        # Control points for the Bezier curve
        dx = abs(end_pos.x() - start_pos.x()) * 0.5
        c1 = QPointF(start_pos.x() + dx, start_pos.y())
        c2 = QPointF(end_pos.x() - dx, end_pos.y())

        path.cubicTo(c1, c2, end_pos)
        self.setPath(path)

class PortItem(QGraphicsItem):
    """The 'dot' on a node for connections."""
    def __init__(self, name: str, is_input: bool, node: QGraphicsItem):
        super().__init__(node)
        self.name = name
        self.is_input = is_input
        self.node = node
        self.connections = [] # Support multiple connections
        
        self.radius = 6
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        painter.setRenderHint(QPainter.Antialiasing)
        if option.state & QStyle.State_MouseOver:
            painter.setBrush(QBrush(QColor(colors.accent_hover)))
        else:
            painter.setBrush(QBrush(QColor(colors.accent_base)))
        painter.setPen(QPen(QColor("white"), 1.5))
        painter.drawEllipse(self.boundingRect())

    def scene_pos(self) -> QPointF:
        return self.mapToScene(0, 0)

class WorkflowBoundaryItem(QGraphicsRectItem):
    """Left or Right panel for workflow inputs/outputs."""
    def __init__(self, is_input: bool, names: list[str]):
        # Base height calculated from ports
        port_height = 40
        width = 120
        header_height = 30
        total_height = header_height + len(names) * port_height + 10
        
        super().__init__(0, 0, width, total_height)
        self.is_input = is_input
        self.setBrush(QBrush(QColor(colors.bg_base)))
        self.setPen(QPen(QColor(colors.border_medium), 1))
        self.setZValue(100) # In front of regular nodes to act as overlay
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)

        # Header label
        title_text = "WORKFLOW INPUTS" if is_input else "WORKFLOW OUTPUTS"
        title = QGraphicsTextItem(self)
        title.setHtml(f"<div style='text-align: center; color: {colors.text_secondary}; font-family: Segoe UI, Roboto, sans-serif; font-size: {style_system.font_xsmall}; font-weight: bold;'>"
                      f"{title_text}</div>")
        title.setTextWidth(width)
        title.setPos(0, 5)

        self.ports = []
        for i, name in enumerate(names):
            # Panel inputs are sources (outputs), Panel outputs are sinks (inputs)
            port = PortItem(name, is_input=not self.is_input, node=self)
            # Left panel dots on right, Right panel dots on left
            px = width if is_input else 0
            py = header_height + i * port_height + port_height/2
            port.setPos(px, py)
            self.ports.append(port)
            
            label = QGraphicsTextItem(name, self)
            label.setFont(QFont("Segoe UI", 9))
            label.setDefaultTextColor(QColor(colors.text_secondary))
            if is_input:
                label.setPos(width - 5 - label.boundingRect().width(), py - 12)
            else:
                label.setPos(5, py - 12)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for port in self.ports:
                for conn in port.connections:
                    conn.update_path()
        return super().itemChange(change, value)

class WorkflowNodeItem(QGraphicsRectItem):
    """A visual node representing a KNodeInstance."""
    def __init__(self, instance_name: str, knode_name: str, inputs: list[str], outputs: list[str]):
        # Base dimensions
        width = 180
        header_height = 35
        port_height = 25
        content_height = max(len(inputs), len(outputs)) * port_height + 10
        total_height = header_height + content_height
        
        super().__init__(0, 0, width, total_height)
        self.instance_name = instance_name
        self.knode_name = knode_name
        
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor(colors.border_medium), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges) # Crucial for lines
        self.setAcceptHoverEvents(True)
        
        # Instance Name label (Below the node) - Editable
        self.instance_label = QGraphicsTextItem(self)
        self.instance_label.setPlainText(instance_name)
        self.instance_label.setFont(QFont("Segoe UI", 10))
        self.instance_label.setDefaultTextColor(QColor(colors.text_secondary))
        self.instance_label.setTextInteractionFlags(Qt.TextEditorInteraction)
        
        # Center horizontally below node
        label_width = self.instance_label.boundingRect().width()
        self.instance_label.setPos((width - label_width) / 2, total_height + 5)
        
        # Update center on change
        self.instance_label.document().contentsChanged.connect(self._center_instance_label)
        
        self.title = QGraphicsTextItem(self)
        self.title.setHtml(f"<div style='text-align: center; color: {colors.text_primary}; font-family: Segoe UI, Roboto, sans-serif; font-size: {style_system.font_xsmall};'>"
                           f"<b>{knode_name}</b></div>")
        self.title.setTextWidth(width)
        self.title.setPos(0, 5)

        self._setup_ports(inputs, outputs, header_height, port_height, width)

    def _center_instance_label(self):
        label_width = self.instance_label.boundingRect().width()
        self.instance_label.setPos((180 - label_width) / 2, self.instance_label.y())

    def _setup_ports(self, inputs, outputs, header_height, port_height, width):
        # Create Ports
        self.input_ports = []
        for i, name in enumerate(inputs):
            port = PortItem(name, True, self)
            y_pos = header_height + i * port_height + port_height/2
            port.setPos(0, y_pos)
            
            label = QGraphicsTextItem(name, self)
            label.setFont(QFont("Segoe UI", 9))
            label.setDefaultTextColor(QColor(colors.text_secondary))
            label.setPos(12, y_pos - 12)
            self.input_ports.append(port)

        self.output_ports = []
        for i, name in enumerate(outputs):
            port = PortItem(name, False, self)
            y_pos = header_height + i * port_height + port_height/2
            port.setPos(width, y_pos)
            
            label = QGraphicsTextItem(name, self)
            label.setFont(QFont("Segoe UI", 9))
            label.setDefaultTextColor(QColor(colors.text_secondary))
            # Align right: calculate width
            label_width = label.boundingRect().width()
            label.setPos(width - 12 - label_width, y_pos - 12)
            self.output_ports.append(port)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for port in self.input_ports + self.output_ports:
                for conn in port.connections:
                    conn.update_path()
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        # Draw shadow-like border
        if self.isSelected():
            painter.setPen(QPen(QColor(colors.accent_base), 2))
        else:
            painter.setPen(QPen(QColor(colors.border_light), 1))
            
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), float(style_system.radius_xlarge_i), float(style_system.radius_xlarge_i))
        
        # Draw header separator
        painter.setPen(QPen(QColor(colors.bg_surface), 1))
        painter.drawLine(0, 40, 180, 40)

