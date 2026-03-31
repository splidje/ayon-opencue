from ayon_server.settings import BaseSettingsModel, SettingsField

DEFAULT_VALUES = dict(
    rqd_os="Linux",
    show_name="",
)


class OpenCueSettings(BaseSettingsModel):
    rqd_os: str = SettingsField(
        "Linux",
        title="RQD OS",
        description="The OS running on the Opencue render nodes.",
    )
    show_name: str = SettingsField(
        "",
        title="Show Name",
        description="The name of the show under which to submit jobs.",
    )
