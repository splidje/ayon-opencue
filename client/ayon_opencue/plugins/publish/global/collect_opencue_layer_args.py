import pyblish.api

from ayon_core.lib.attribute_definitions import BoolDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class CollectOpenCueLayerArgs(pyblish.api.InstancePlugin, AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.420
    label = "Collect OpenCue Layer Args"
    targets = ["local"]
    hosts = ["nuke"]
    families = ["plate", "render", "prerender"]

    def process(self, instance):
        instance.data["requires_gpu"] = self.get_attr_values_from_data(instance.data)[
            "requires_gpu"
        ]

    @classmethod
    def get_attribute_defs(cls):
        return [
            BoolDef("requires_gpu", label="Requires GPU", default=False),
        ]
