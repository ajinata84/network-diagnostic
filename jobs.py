"""Ping VMs Job for Nautobot."""

from nautobot.apps.jobs import Job, MultiObjectVar, register_jobs
from nautobot.virtualization.models import VirtualMachine
from ping3 import ping

name = "Network Diagnostic Jobs"

class PingVMsJob(Job):
    vms = MultiObjectVar(
        model=VirtualMachine,
        required=True,
        query_params={"status": "active"},
    )

    class Meta:
        name = "Ping VMs"
        description = "Ping selected virtual machines using their primary IPs and log results."

    def run(self, vms, **kwargs):
        self.logger.info(f"Starting ping test on {vms.count()} VMs")
        for vm in vms:
            ip = vm.primary_ip.address if vm.primary_ip else None
            if not ip:
                self.logger.warning(f"No primary IP for {vm.name}. Skipping.")
                continue
            result = self.ping_device(ip)
            self.logger.info(f"Ping {ip} ({vm.name}) - {result}")

    def ping_device(self, ip):
        try:
            delay = ping(ip, timeout=2)
            if delay is not False:
                return f"Success ({delay:.2f} ms)"
            else:
                return "Failed (no response)"
        except Exception as e:
            return f"Error: {str(e)}"

register_jobs(PingVMsJob)