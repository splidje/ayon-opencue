import pyblish.api

import ayon_applications
import ayon_core

from ayon_core.pipeline import Anatomy
from ayon_core.pipeline.publish import AYONPyblishPluginMixin


class NukeSubmitOpenCue(
    pyblish.api.InstancePlugin,
    AYONPyblishPluginMixin,
):
    label = "Submit Nuke to OpenCue"
    order = pyblish.api.IntegratorOrder + 0.1
    hosts = ["nuke"]

    def process(self, instance):
        # Opencue
        from opencue import Cuebot

        import outline
        import outline.modules.shell

        if not instance.data.get("farm"):
            self.log.debug("Should not be processed on farm, skipping.")
            return

        application_full_name = instance.context.data["appName"]
        application_name, application_variant_name = application_full_name.split("/")
        if application_name != "nuke":
            raise ValueError(
                f"Expecting application name to be 'nuke', but instead it's: {application_full_name}"
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

        Cuebot.setHosts(settings["cuebot_hosts"].split(","))
        rqd_os = settings["rqd_os"]

        # TODO: applications addons has this function: `macos_executable_prep`
        # Which discovers the true path to the executable. However,
        # if submitting machine isn't Mac OS it won't work, as it won't
        # find the .app on disk which is required.
        nuke_executable_path = variant_settings["executables"][rqd_os.lower()]

        project_name = instance.context.data["projectName"]
        version_string = (
            Anatomy(project_name)
            .templates["version"]
            .format(version=instance.context.data["version"])
        )
        job = outline.Outline(
            f'{instance.context.data["task"]}_{version_string}_{instance.name}',
            shot=instance.context.data["folderEntity"]["name"],
            show="testing",
        )
        layer = outline.modules.shell.Shell(
            "layer",
            command=[
                nuke_executable_path,
                "-t",
            ],
        )
        job.add_layer(layer)

        outline.cuerun.launch(job, os=rqd_os)
