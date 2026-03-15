"""
Preview panel - displays previews of selected elements.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from typing import Any, List, Optional, Dict

from ..previews.base_preview import BasePreview
from ..previews.table_preview import TablePreview
from ..previews.literal_preview import LiteralPreview
from ..previews.node_preview import NodePreview
from ..previews.error_preview import ErrorPreview
from .preview_card import PreviewCard


class PreviewPanel(QFrame):
    """
    Right panel showing previews of selected elements.
    Can display multiple preview panels simultaneously, each with a close button.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self._preview_factories: List[type] = []
        self._active_cards: List[PreviewCard] = []
        self._element_to_card: Dict[Any, PreviewCard] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("Preview")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding: 5px 5px 5px 5px;")
        layout.addWidget(title)
        
        # Scroll area for multiple preview cards
        scroll_area = QScrollArea()
        scroll_area.setObjectName("PreviewScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for preview cards
        self._container = QWidget()
        self._container.setObjectName("PreviewScrollContainer")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(5)
        self._container_layout.addStretch()  # Push cards to top
        
        scroll_area.setWidget(self._container)
        layout.addWidget(scroll_area)
        
        # Register preview factory types
        self._register_preview_factories()
    
    def _register_preview_factories(self):
        """Register all available preview widget types."""
        # ErrorPreview should be checked first since error elements might match other types
        self._preview_factories = [
            ErrorPreview,
            TablePreview,
            LiteralPreview,
            NodePreview
        ]
    
    def show_preview(self, element: Any):
        """
        Add a preview for the given element.
        If the element already has a preview, it will not add a duplicate.
        
        Args:
            element: The element to preview (KData, KNode, etc.)
        """
        if element is None:
            return
        
        # Check if this element already has a preview
        if element in self._element_to_card:
            # Element already has a preview, don't add duplicate
            return
        
        # Find appropriate preview widget type
        preview_class = self._find_preview_class(element)
        
        if preview_class is None:
            return
        
        # Get element name and type info for the card
        element_name = self._get_element_name(element)
        element_type = self._get_element_type(element)
        
        # Create a new preview instance
        preview_instance = preview_class()
        preview_instance.update_preview(element)
        
        # Create a preview card with close button and title
        card = PreviewCard(preview_instance, element_name, element_type, self._container)
        card.close_requested.connect(self._on_card_close_requested)
        
        # Add to layout (before stretch)
        self._container_layout.insertWidget(self._container_layout.count() - 1, card)
        
        # Track the card
        self._active_cards.append(card)
        self._element_to_card[element] = card
    
    def _get_element_type(self, element: Any) -> str:
        """Get the type string for an element."""
        from kira.kdata.kdata import KData
        from kira.knodes.knode import KNode
        
        if isinstance(element, KData):
            if element.value is None:
                return "error"
            from kira.kdata.ktable import KTable
            from kira.kdata.kliteral import KLiteral
            if isinstance(element.value, KTable):
                return "table"
            elif isinstance(element.value, KLiteral):
                return "literal"
            return "data"
        elif isinstance(element, KNode):
            return "node"
        else:
            return "unknown"
    
    def _get_element_name(self, element: Any) -> str:
        """
        Get the display name for an element.
        
        Args:
            element: The element to get the name for
            
        Returns:
            The element's name or a default string
        """
        # Try to get name attribute (KData, KNode, etc. have this)
        if hasattr(element, 'name'):
            return element.name
        
        # Fallback to string representation
        return str(element)
    
    def _find_preview_class(self, element: Any) -> Optional[type]:
        """
        Find the appropriate preview widget class for an element.
        
        Args:
            element: The element to find a preview for
            
        Returns:
            The preview widget class that can handle this element, or None
        """
        # Try each preview factory to see if it can handle the element
        for preview_class in self._preview_factories:
            # Create a temporary instance to check if it can preview
            temp_instance = preview_class()
            if temp_instance.can_preview(element):
                return preview_class
        
        return None
    
    def _on_card_close_requested(self, card: PreviewCard):
        """Handle close button click on a preview card."""
        # Remove from layout
        self._container_layout.removeWidget(card)
        
        # Remove from tracking lists
        if card in self._active_cards:
            self._active_cards.remove(card)
        
        # Remove from element mapping
        element_to_remove = None
        for element, mapped_card in self._element_to_card.items():
            if mapped_card == card:
                element_to_remove = element
                break
        if element_to_remove is not None:
            del self._element_to_card[element_to_remove]
        
        # Delete the card
        card.deleteLater()
    
    def clear_all_previews(self):
        """Clear all preview panels."""
        # Close all cards
        cards_to_close = self._active_cards.copy()
        for card in cards_to_close:
            self._on_card_close_requested(card)
    
    def remove_preview(self, element: Any):
        """
        Remove the preview for a specific element.
        
        Args:
            element: The element whose preview should be removed
        """
        if element in self._element_to_card:
            card = self._element_to_card[element]
            self._on_card_close_requested(card)

