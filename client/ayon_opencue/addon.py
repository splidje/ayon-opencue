from pathlib import Path
from typing import List, Optional

from ayon_core.addon import AYONAddon, IPluginPaths

from .version import __version__


class OpenCueAddon(AYONAddon, IPluginPaths):
    name = "opencue"
    version = __version__

    def get_publish_plugin_paths(self, host_name: Optional[str] = None) -> List[str]:
        publish_folder_path = Path(__file__).parent / "plugins" / "publish"
        paths = [str(publish_folder_path / "global")]
        if host_name:
            paths.append(str(publish_folder_path / host_name))
        return paths
