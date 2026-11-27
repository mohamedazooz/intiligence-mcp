from .base import BaseCartridge


class OsintDarkCartridge(BaseCartridge):
    name = "OSINT_DARK"

    async def run(self, goal, pool, ledger, mission_id):
        ledger.record("osint_profile", "SKIPPED_PROFILE_OFF", 0, 0, "osint-dark profile not enabled")
        return {"cartridge": self.name, "findings": ["OSINT profile disabled"], "refs": []}
