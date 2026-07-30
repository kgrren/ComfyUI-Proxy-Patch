import os
import folder_paths

# webディレクトリの絶対パスを取得
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

# ComfyUIがカスタムノードとして認識するためのダミーマッピング
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
