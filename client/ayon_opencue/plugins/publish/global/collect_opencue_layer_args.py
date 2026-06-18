import pyblish.api

from ayon_core.lib.attribute_definitions import BoolDef, NumberDef
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class CollectOpenCueLayerArgs(pyblish.api.InstancePlugin, AYONPyblishPluginMixin):
    order = pyblish.api.CollectorOrder + 0.420
    label = "Collect OpenCue Layer Args"
    targets = ["local"]
    hosts = ["nuke"]
    families = ["plate", "render", "prerender"]

    def process(self, instance):
        attr_values_by_name = self.get_attr_values_from_data(instance.data)
        for attr_name in ("requires_gpu", "chunk_size"):
            instance.data[attr_name] = attr_values_by_name[
                attr_name
            ]

    @classmethod
    def get_attribute_defs(cls):
        return [
            BoolDef("requires_gpu", label="Requires GPU", default=False),
            NumberDef("chunk_size", label="Chunk Size", default=5, minimum=1),
        ]
