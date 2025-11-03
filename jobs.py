"""Ping Devices Job for Nautobot."""

from nautobot.apps.jobs import Job, MultiObjectVar, register_jobs
from nautobot.dcim.models import Device
from ping3 import ping

name = "Network Diagnostic Jobs"

class PingDevicesJob(Job):
    devices = MultiObjectVar(
        model=Device,
        required=True,
        query_params={"status": "active"},
    )

    class Meta:
        name = "Ping Devices"
        description = "Ping selected devices using their primary IPs and log results."

    def run(self, devices, **kwargs):
        self.logger.info(f"Starting ping test on {devices.count()} devices")
        for device in devices:
            ip = device.primary_ip.address if device.primary_ip else None
            if not ip:
                self.logger.warning(f"No primary IP for {device.name}. Skipping.")
                continue
            result = self.ping_device(ip)
            self.logger.info(f"Ping {ip} ({device.name}) - {result}")

    def ping_device(self, ip):
        try:
            delay = ping(ip, timeout=2)
            if delay is not False:
                return f"Success ({delay:.2f} ms)"
            else:
                return "Failed (no response)"
        except Exception as e:
            return f"Error: {str(e)}"

register_jobs(PingDevicesJob)