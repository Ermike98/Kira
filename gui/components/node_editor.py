from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QFrame, QVBoxLayout, QWidget, QLineEdit
)
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from gui.components.node_items import ConnectionItem, PortItem, WorkflowNodeItem
from gui import style_system
from gui.utils import colors

class NodeScene(QGraphicsScene):
    """The canvas carrying nodes and connections."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QBrush(QColor("white")))
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # Draw grid
        painter.setPen(QPen(QColor(colors.slate_100), 1))
        left = int(rect.left()) - (int(rect.left()) % 20)
        top = int(rect.top()) - (int(rect.top()) % 20)
        
        for x in range(left, int(rect.right()), 20):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), 20):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

class NodeView(QGraphicsView):
    """The viewer for the node canvas with panning/zooming."""
    def __init__(self, scene: NodeScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        self.active_connection = None
        self._is_panning = False
        self._pan_start = None

        self.boundaries = [] # (item, is_left)
        
        # Connect to scrollbar changes
        self.horizontalScrollBar().valueChanged.connect(self._update_boundaries)
        self.verticalScrollBar().valueChanged.connect(self._update_boundaries)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
            self._update_boundaries()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        
        if event.button() == Qt.LeftButton:
            if isinstance(item, PortItem):
                # Rule: Input dots can only have one. 
                # If we click an occupied input dot, we 'grab' the existing connection 
                # to move it, or delete it if we don't drop it elsewhere.
                if item.is_input and item.connections:
                    existing_conn = item.connections[0]
                    # We want to 'move' the end of the connection.
                    # For simplicity in this event-based model, we remove the old and start new.
                    existing_conn.remove()
                
                # Start new connection (from either input or output)
                self.active_connection = ConnectionItem(item)
                self.scene().addItem(self.active_connection)
                self.active_connection.set_end_pos(self.mapToScene(event.position().toPoint()))
                return
            elif item is None:
                # Start panning
                if event.modifiers() == Qt.NoModifier:
                    self._is_panning = True
                    self._pan_start = event.position().toPoint()
                    self.setCursor(Qt.ClosedHandCursor)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active_connection:
            self.active_connection.set_end_pos(self.mapToScene(event.position().toPoint()))
            return
        
        if self._is_panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active_connection:
            item = self.itemAt(event.position().toPoint())
            start_port = self.active_connection.start_port
            
            # Rule: Source can only connect to Sink (Input != Output)
            if isinstance(item, PortItem) and item.is_input != start_port.is_input:
                # Rule: Input dots must have only one.
                target_input = item if item.is_input else start_port
                if target_input.is_input:
                    # If target input already has a connection (that isn't this one), remove it.
                    for conn in list(target_input.connections):
                        if conn != self.active_connection:
                            conn.remove()
                
                self.active_connection.set_end_port(item)
                item.connections.append(self.active_connection)
            else:
                # Invalid connection or dropped in space -> Cleanup
                self.active_connection.remove()
            
            self.active_connection = None
            
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        item = self.itemAt(event.position().toPoint())
        if item is None:
            self._show_node_search(event.position().toPoint())
        else:
            super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_boundaries()

    def _update_boundaries(self):
        """Anchors the boundary panels to the view borders, ignoring scene scaling."""
        if not self.boundaries:
            return
            
        view_rect = self.viewport().rect()
        view_w = view_rect.width()
        view_h = view_rect.height()
        
        for item, is_left in self.boundaries:
            item_rect = item.rect()
            item_w = item_rect.width()
            item_h = item_rect.height()
            
            # Calculate the viewport position we want (in pixels)
            view_x = 0 if is_left else (view_w - item_w)
            view_y = (view_h - item_h) / 2
            
            # Map that viewport position to a scene position
            scene_pos = self.mapToScene(int(view_x), int(view_y))
            item.setPos(scene_pos)
            
            # Force update of all connections attached to this boundary
            if hasattr(item, "ports"):
                for port in item.ports:
                    for conn in port.connections:
                        conn.update_path()

    def _show_node_search(self, pos):
        """Shows a floating search box to add new nodes."""
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search node...")
        self.search_box.setFixedWidth(200)
        self.search_box.setObjectName("NodeSearchBox")
        self.search_box.setStyleSheet(f"""
            #NodeSearchBox {{
                padding: {style_system.spacing_small};
                border: {style_system.border_medium} solid {colors.sky_500};
                border-radius: {style_system.radius_large};
                background: white;
                font-family: inherit;
                font-size: {style_system.font_small};
            }}
        """)
        
        # Position centered
        self.search_box.move(pos.x() - 100, pos.y() - 15)
        self.search_box.setFocus()
        self.search_box.show()
        
        def on_finished():
            node_name = self.search_box.text().strip()
            if node_name:
                self._create_node_from_name(node_name, pos)
            self.search_box.deleteLater()
            self.search_box = None

        self.search_box.returnPressed.connect(on_finished)
        self.search_box.editingFinished.connect(lambda: self.search_box.deleteLater() if self.search_box else None)

    def _create_node_from_name(self, name: str, pos, is_scene_pos=False):
        """Discovers knode metadata and creates a visual item."""
        scene = self.scene()
        editor = self.parent()
        if not hasattr(editor, "project"):
            return
            
        project = editor.project.kproject
        sm = project.state_manager
        
        knode = None
        # Check workflows
        if name in sm.workflows:
            knode = sm.workflows[name].kobject
        elif name in sm.variables:
             obj = sm.variables[name].kobject
             from kira.knodes.knode import KNode
             if isinstance(obj, KNode):
                 knode = obj
        
        # Check built-in functions
        if not knode:
            try:
                obj = project.get_value(name)
                from kira.knodes.knode import KNode
                if isinstance(obj, KNode):
                    knode = obj
            except:
                pass

        if knode:
            scene_pos = pos if is_scene_pos else self.mapToScene(pos)
            instance_name = f"{name}_{len(scene.items())}"
            
            node_item = WorkflowNodeItem(
                instance_name=instance_name,
                knode_name=name,
                inputs=knode.input_names,
                outputs=knode.output_names
            )
            node_item.setPos(scene_pos)
            scene.addItem(node_item)
            node_item.setFlag(WorkflowNodeItem.ItemSendsScenePositionChanges)
        else:
            # Optional: provide visual feedback that node was not found
            pass
