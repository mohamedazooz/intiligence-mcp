from abc import ABC, abstractmethod


class BaseCartridge(ABC):
    name: str

    @abstractmethod
    async def run(self, goal: str, pool, ledger, mission_id) -> dict:
        ...
