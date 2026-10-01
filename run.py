"""PyInstaller 打包入口。用绝对导入，避免相对导入找不到父包。"""
from ops_toolkit.app import main

if __name__ == "__main__":
    main()
