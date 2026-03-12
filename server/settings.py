from ayon_server.settings import BaseSettingsModel, SettingsField

DEFAULT_VALUES = dict(
    cuebot_hosts="",
    rqd_os="Linux",
)


class OpenCueSettings(BaseSettingsModel):
    cuebot_hosts: str = SettingsField(
        "",
        title="Cuebot Hosts",
        description="Comma-separated hostname / IP addresses for Cuebot hosts.",
    )
    rqd_os: str = SettingsField(
        "Linux",
        title="RQD OS",
        description="The OS running on the Opencue render nodes.",
    )
