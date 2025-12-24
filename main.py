import sys
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QLabel,
    QSizePolicy, QFrame, QDockWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
import pyqtgraph as pg

# --- 1. Dark Theme QSS Styling ---
# A modern, dark theme for a slick, professional appearance.
DARK_THEME_QSS = """
    /* Main Window and General Background */
    QMainWindow, QWidget, QDockWidget {
        background-color: #2e2e2e; /* Dark Gray Background */
        color: #f0f0f0; /* Light Text */
    }

    /* Control Panel Styling (QFrame/QDockWidget content) */
    QFrame#ControlPanel {
        border: none;
        background-color: #222222; /* Slightly darker panel */
    }

    /* Buttons */
    QPushButton {
        background-color: #007acc; /* Microsoft Azure / Deep Blue */
        border: 1px solid #005f99;
        color: #ffffff;
        padding: 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0088e5; /* Lighter on hover */
    }
    QPushButton:pressed {
        background-color: #005f99; /* Darker on press */
    }

    /* ComboBoxes (Dropdowns) */
    QComboBox {
        background-color: #3a3a3a;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 4px;
        color: #f0f0f0;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: #555555;
        border-left-style: solid; /* just a line */
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QComboBox::down-arrow {
        /* Placeholder for a custom arrow icon */
        image: url(placeholder_down_arrow.png); /* Using placeholder */
    }

    /* Labels */
    QLabel {
        color: #aaaaaa; /* Lighter gray for labels */
        font-size: 12px;
    }

    /* PyQtGraph area styling (transparent background to see QWidget's color) */
    PlotWidget {
        background-color: #2e2e2e;
        border: 1px solid #444444; /* Subtle border for the main area */
        border-radius: 4px;
    }
"""


class MainWindow(QMainWindow):
    """
    Main window for the data analysis application.
    Implements a sleek dark theme, a control panel, and the main
    PyQtGraph visualization area.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Analysis Desktop App - PySide6/PyQtGraph")
        self.setGeometry(100, 100, 1200, 800)

        # --- 1. Data Setup (Pandas/NumPy Mock Data) ---
        self.data = self._generate_mock_data()

        # --- 2. Main Layout Setup ---
        self._setup_ui()

        # --- 3. Apply Styling ---
        self.setStyleSheet(DARK_THEME_QSS)

    def _generate_mock_data(self):
        """Generates mock time-series data using NumPy and Pandas."""
        # Mocking time steps
        time_steps = np.arange(0, 100, 0.1)
        # Mocking a noisy sine wave for 'Value'
        value = (np.sin(time_steps / 5) * 50) + (np.random.randn(len(time_steps)) * 5)

        # Create a pandas DataFrame
        df = pd.DataFrame({
            'Time': time_steps,
            'Value': value,
            'Category': np.random.choice(['A', 'B', 'C'], size=len(time_steps))
        })
        print(f"Mock DataFrame created with {len(df)} rows.")
        return df

    def _setup_ui(self):
        """Sets up the main window structure: Central Widget and Dock Widget."""

        # --- A. Control Panel (Left Dock) ---
        self._create_control_panel()

        # --- B. Visualization Area (Center) ---
        self._create_visualization_area()

        # Set the main container as the central widget
        self.setCentralWidget(self.plot_widget)

        # Disable QDockWidget moving and floating for a fixed UI
        self.control_dock.setFeatures(QDockWidget.DockWidgetClosable)

    def _create_control_panel(self):
        """Creates the slim vertical Control Panel using a QDockWidget."""
        self.control_dock = QDockWidget("Controls", self)
        self.control_dock.setObjectName("ControlDock")
        self.control_dock.setAllowedAreas(Qt.LeftDockWidgetArea)

        # Dock content widget
        control_widget = QFrame()
        control_widget.setObjectName("ControlPanel")  # Used for QSS targeting
        control_widget.setFixedWidth(200)  # Slim vertical panel width

        control_layout = QVBoxLayout(control_widget)
        control_layout.setSpacing(10)
        control_layout.setContentsMargins(15, 15, 15, 15)

        # 1. "Load Dataset" Button
        self.load_button = QPushButton("Load Dataset")
        self.load_button.clicked.connect(self._simulate_load)
        control_layout.addWidget(self.load_button)
        control_layout.addSpacing(20)

        # 2. X-Axis Selection ComboBox
        control_layout.addWidget(QLabel("Select Column (X-Axis):"))
        self.x_axis_combo = QComboBox()
        # Use column names from the mock data
        self.x_axis_combo.addItems(self.data.columns)
        self.x_axis_combo.setCurrentText('Time')  # Default selection
        self.x_axis_combo.setEditable(False)
        self.x_axis_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.x_axis_combo.currentIndexChanged.connect(self._update_plot)
        control_layout.addWidget(self.x_axis_combo)

        # 3. Y-Axis Selection ComboBox (Added for completeness)
        control_layout.addWidget(QLabel("Select Column (Y-Axis):"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItems(self.data.columns)
        self.y_axis_combo.setCurrentText('Value')  # Default selection
        self.y_axis_combo.setEditable(False)
        self.y_axis_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.y_axis_combo.currentIndexChanged.connect(self._update_plot)
        control_layout.addWidget(self.y_axis_combo)

        control_layout.addStretch(1)  # Pushes everything to the top

        self.control_dock.setWidget(control_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_dock)

    def _create_visualization_area(self):
        """Creates the main PyQtGraph PlotWidget for data visualization."""

        # A. Configure PyQtGraph globally for a dark theme
        pg.setConfigOption('background', '#2e2e2e')  # Background color
        pg.setConfigOption('foreground', '#f0f0f0')  # Text/line color

        # B. Create the PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setObjectName("PlotWidget")
        self.plot_widget.setLabel('left', 'Value', units='u')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setTitle("Mock Time-Series Analysis", size='18pt')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # C. Plot the initial mock data
        self.plot_curve = self.plot_widget.plot(
            self.data['Time'].values,
            self.data['Value'].values,
            pen=pg.mkPen(color='#14e5a9', width=2)  # Bright Cyan/Green line
        )

    def _simulate_load(self):
        """Simulates a dataset load event."""
        print("Dataset Load simulated. Data is already in memory.")
        self.load_button.setText("Dataset Loaded (1000 pts)")

    def _update_plot(self):
        """Updates the plot based on ComboBox selection."""
        x_col = self.x_axis_combo.currentText()
        y_col = self.y_axis_combo.currentText()

        x_data = self.data[x_col].values
        y_data = self.data[y_col].values

        # Update the curve data
        self.plot_curve.setData(x_data, y_data)

        # Update the axis labels
        self.plot_widget.setLabel('bottom', x_col)
        self.plot_widget.setLabel('left', y_col)
        self.plot_widget.setTitle(f"{y_col} vs {x_col} Analysis")

        print(f"Plot updated: {y_col} vs {x_col}")


if __name__ == '__main__':
    # Ensure PyQtGraph has the appropriate settings for performance
    pg.setConfigOptions(antialias=True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())