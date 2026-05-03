import os
from PySide6.QtGui import QFontDatabase

def load_fonts():
    """
    Registers font files in the gui/font directory.
    To avoid rendering issues on Windows, we prioritize static fonts over variable fonts.
    """
    font_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "font")
    if not os.path.exists(font_root):
        return

    # Process each font family folder (e.g., 'inter', 'roboto')
    for family_name in os.listdir(font_root):
        family_path = os.path.join(font_root, family_name)
        if not os.path.isdir(family_path):
            continue
            
        static_dir = os.path.join(family_path, "static")
        
        # If static folder exists, load ONLY from it
        if os.path.isdir(static_dir):
            target_dirs = [static_dir]
        else:
            target_dirs = [family_path]
            
        for target_dir in target_dirs:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.lower().endswith(".ttf"):
                        # Skip variable fonts if we are in the root (unlikely if static exists)
                        if "VariableFont" in file and os.path.isdir(static_dir):
                            continue
                            
                        font_path = os.path.join(root, file)
                        QFontDatabase.addApplicationFont(font_path)
