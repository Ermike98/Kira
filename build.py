"""
Kira cross-platform packaging script.
Compiles Kira into a single-file executable for Windows, macOS, or Linux.
"""
import os
import sys
import argparse
import shutil

def main():
    parser = argparse.ArgumentParser(description="Build and package the Kira application.")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Build with console window enabled (useful for debugging tracebacks)"
    )
    args = parser.parse_args()

    print("==================================================")
    print("           Kira Packaging System                  ")
    print("==================================================")

    # 1. Verify environment and import PyInstaller programmatically
    try:
        import PyInstaller.__main__
    except ImportError:
        print("\n[ERROR] PyInstaller is not installed in the active environment.")
        print("Please install development dependencies using: uv sync")
        sys.exit(1)

    # 2. Define target files and paths
    entry_point = "run_gui.py"
    app_name = "Kira"
    
    if not os.path.exists(entry_point):
        print(f"\n[ERROR] Entrypoint '{entry_point}' not found in the current directory.")
        sys.exit(1)

    # 3. Determine OS-specific separator for PyInstaller --add-data
    # Windows uses ';', while Unix (macOS/Linux) uses ':'
    data_sep = ";" if os.name == "nt" else ":"
    
    # 4. Construct path arguments for assets
    # We bundle gui/icons and gui/font under the same directory structure inside the executable
    icons_src = os.path.join("gui", "icons")
    fonts_src = os.path.join("gui", "font")
    
    add_data_args = []
    if os.path.exists(icons_src):
        add_data_args.append(f"--add-data={icons_src}{data_sep}{icons_src}")
        print(f"[INFO] Bundling assets: {icons_src}")
    else:
        print(f"[WARNING] Icons directory '{icons_src}' not found.")
        
    if os.path.exists(fonts_src):
        add_data_args.append(f"--add-data={fonts_src}{data_sep}{fonts_src}")
        print(f"[INFO] Bundling assets: {fonts_src}")
    else:
        print(f"[WARNING] Fonts directory '{fonts_src}' not found.")

    # 5. Build base PyInstaller arguments
    pyinstaller_args = [
        entry_point,
        f"--name={app_name}",
        "--onefile",
        "--clean",
    ]

    # Add resources to pack
    pyinstaller_args.extend(add_data_args)

    # Handle console window settings
    # For a GUI app, we hide the terminal console by default (windowed / noconsole)
    # If --debug is passed, we leave the console enabled
    if args.debug:
        print("[INFO] Building in DEBUG mode (console enabled).")
    else:
        print("[INFO] Building in PRODUCTION mode (console suppressed).")
        pyinstaller_args.append("--noconsole")

    print(f"[INFO] Running PyInstaller with arguments: {pyinstaller_args}")
    print("==================================================")
    
    # 6. Execute PyInstaller
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n==================================================")
        print("[SUCCESS] Kira application built successfully!")
        
        # Output directory info
        dist_dir = "dist"
        if os.name == "nt":
            output_file = os.path.join(dist_dir, f"{app_name}.exe")
        elif sys.platform == "darwin":
            output_file = os.path.join(dist_dir, f"{app_name}.app")
        else:
            output_file = os.path.join(dist_dir, app_name)
            
        if os.path.exists(output_file):
            print(f"[INFO] Output binary is available at: {os.path.abspath(output_file)}")
        print("==================================================")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred during the build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
