"""VM Status Updater Job for Nautobot."""

from nautobot.apps.jobs import Job, BooleanVar, register_jobs
from nautobot.virtualization.models import VirtualMachine
from nautobot.extras.models import Status  # For status choices
from ping3 import ping

name = "Network Diagnostic Jobs"  # Group name in UI

class VMStatusUpdaterJob(Job):
    dry_run = BooleanVar(
        default=True,
        label="Dry Run",
        description="Preview changes without applying them.",
    )

    class Meta:
        name = "Update VM Statuses via Ping"
        description = "Pings all VMs and updates their status to Active (success) or Offline (failure)."
        supports_dryrun = True  # Enables dry-run in UI

    def run(self, dry_run, **kwargs):
        # Cache status objects for efficiency (use name instead of slug)
        active_status = Status.objects.get(name="Active")
        offline_status = Status.objects.get(name="Offline")

        vms = VirtualMachine.objects.all()
        self.logger.info(f"Checking {vms.count()} VMs (dry_run={dry_run})")

        for vm in vms:
            ip = vm.primary_ip.host if vm.primary_ip else None
            if not ip:
                self.logger.warning(f"No primary IP for {vm.name}. Would set to Offline.")
                if not dry_run:
                    vm.status = offline_status
                    vm.save()
                continue

            result = self.ping_vm(ip)
            new_status = active_status if result.startswith("Success") else offline_status
            action = f"Would set" if dry_run else "Setting"
            self.logger.info(f"Ping {ip} ({vm.name}) - {result}. {action} status to {new_status.name}.")

            if not dry_run:
                vm.status = new_status
                vm.save()

    def ping_vm(self, ip):
        try:
            delay = ping(ip, timeout=2)
            if delay is not False:
                return f"Success ({delay:.2f} ms)"
            else:
                return "Failed (no response)"
        except Exception as e:
            return f"Failed ({str(e)})"

register_jobs(VMStatusUpdaterJob)