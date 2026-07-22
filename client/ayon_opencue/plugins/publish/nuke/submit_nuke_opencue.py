import json
import os

from pathlib import Path

import pyblish.api

import ayon_applications
import ayon_core

from ayon_core.pipeline import Anatomy, registered_host
from ayon_core.pipeline.create import CreateContext
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class NukeSubmitOpenCue(
    pyblish.api.InstancePlugin,
    AYONPyblishPluginMixin,
):
    label = "Submit Nuke to OpenCue"
    order = pyblish.api.IntegratorOrder + 0.1
    hosts = ["nuke"]
    families = ["plate", "render", "prerender"]

    @classmethod
    def register_create_context_callbacks(cls, create_context: "CreateContext"):
        create_context.add_instances_added_callback(_on_create_instances_added)
        create_context.add_value_changed_callback(_on_create_instance_values_changed)

    def process(self, instance):
        if not instance.data.get("farm"):
            self.log.debug("Should not be processed on farm, skipping.")
            return

        # Opencue
        import outline
        import outline.modules.shell

        application_full_name = instance.context.data["appName"]
        application_name, application_variant_name = application_full_name.split("/")
        if application_name not in ("nuke", "nukex"):
            raise ValueError(
                f"Expecting application name to be 'nuke' or 'nukex', but instead it's: {application_full_name}"
            )

        variant_settings = next(
            (
                settings
                for settings in ayon_applications.manager.get_studio_settings()[
                    "applications"
                ]["applications"]["nuke"]["variants"]
                if settings["name"] == application_variant_name
            ),
            None,
        )
        if variant_settings is None:
            raise ValueError(
                f"Failed to find Application variant settings for: {application_full_name}"
            )

        settings = ayon_core.settings.get_current_project_settings()["opencue"]

        rqd_os = settings["rqd_os"]
        show_name = settings["show_name"]

        # TODO: applications addons has this function: `macos_executable_prep`
        # Which discovers the true path to the executable. However,
        # if submitting machine isn't Mac OS it won't work, as it won't
        # find the .app on disk which is required.
        nuke_executable_path = variant_settings["executables"][rqd_os.lower()][0]

        project_name = instance.context.data["projectName"]
        version_string = (
            Anatomy(project_name)
            .templates["version"]
            .format(version=instance.context.data["version"])
        )
        node_name = instance.data["transientData"]["node"].name()
        output_path = Path(instance.data["path"])
        job = outline.Outline(
            f'{instance.context.data["task"]}_{version_string}_{instance.name}',
            shot=instance.context.data["folderEntity"]["name"],
            show=show_name,
        )
        layer = outline.modules.shell.Shell(
            node_name,
            command=[
                nuke_executable_path,
                "-t",
                "-X",
                node_name,
                "-F",
                "#FRAMESPEC#",
                instance.context.data["currentFile"],
            ],
            range=f'{instance.data["frameStartHandle"]}-{instance.data["frameEndHandle"]}',
            tags=["general"],
            limits=["nuke"],
            memory="50G",
            chunk=instance.data["chunk_size"],
        )
        layer.set_arg("gpus", int(instance.data["requires_gpu"]))
        layer.set_env("AYON_PROJECT_ROOT_WORK", os.environ["AYON_PROJECT_ROOT_WORK"])
        for key, value in json.loads(variant_settings["environment"]).items():
            layer.set_env(key, value)
        layer.add_output(node_name, outline.io.FileSpec(output_path))
        job.add_layer(layer)
        launcher = outline.cuerun.OutlineLauncher(
            job, os=rqd_os, priority=50, maxretries=10
        )
        launcher.launch(use_pycuerun=False)


def initialise_nuke():
    import nuke

    # add callback for opencue requires gpu knob
    nuke.addKnobChanged(_group_node_knob_changed, nodeClass="Group")


def _on_create_instances_added(event):
    import nuke

    for instance in event["instances"]:
        collect_opencue_layer_args = instance.publish_attributes.get(
            "CollectOpenCueLayerArgs"
        )
        if (
            not collect_opencue_layer_args
            or "requires_gpu" not in collect_opencue_layer_args
        ):
            continue

        node = instance.transient_data["node"]
        if "opencue_label" not in node.knobs():
            node.addKnob(nuke.Text_Knob("opencue_label", "OpenCue"))

        if "requires_gpu" not in node.knobs():
            requires_gpu_knob = nuke.Boolean_Knob("requires_gpu", "Requires GPU")
            node.addKnob(requires_gpu_knob)
            requires_gpu_knob.setFlag(nuke.STARTLINE)
            requires_gpu_knob.setValue(collect_opencue_layer_args["requires_gpu"])

        if "chunk_size" not in node.knobs():
            chunk_size_knob = nuke.Int_Knob("chunk_size", "Chunk Size")
            node.addKnob(chunk_size_knob)
            chunk_size_knob.clearFlag(nuke.STARTLINE)
            chunk_size_knob.setValue(collect_opencue_layer_args["chunk_size"])


def _on_create_instance_values_changed(event):
    for change in event["changes"]:
        instance = change["instance"]
        for name, value in (
            change["changes"]
            .get("publish_attributes", {})
            .get("CollectOpenCueLayerArgs", {})
            .items()
        ):
            if name not in ("requires_gpu", "chunk_size"):
                continue

            node = instance.transient_data["node"]
            knob = node.knob(name)
            if knob and knob.value() != value:
                knob.setValue(value)


def _group_node_knob_changed():
    import nuke

    from ayon_nuke.api.lib import get_node_data, INSTANCE_DATA_KNOB

    knob = nuke.thisKnob()
    knob_name = knob.name()

    if knob_name not in ("requires_gpu", "chunk_size"):
        return

    instance_id = get_node_data(nuke.thisNode(), INSTANCE_DATA_KNOB).get("instance_id")
    if not instance_id:
        return

    with nuke.Root():
        create_context = CreateContext(registered_host())
        instance = create_context.instances_by_id.get(instance_id)
    if not instance:
        return

    collect_opencue_layer_args = instance.publish_attributes.get(
        "CollectOpenCueLayerArgs"
    )
    if not collect_opencue_layer_args:
        return

    value = knob.value()
    if collect_opencue_layer_args.get(knob_name) == value:
        return

    collect_opencue_layer_args[knob_name] = value
    create_context.save_changes()
