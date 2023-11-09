from pathlib import Path
from pycomfort.files import *

class Locations:
    base: Path
    data: Path
    papers: Path
    keys: Path
    service_key: Path
    client_key: Path

    def __init__(self, base: Path):
        self.base = base.absolute().resolve()
        self.data = self.base / "data"
        self.keys = self.data / "keys"
        self.client_key = self.keys / "cf_client.json"
        self.service_key = self.keys / "service.json"
        self.papers = self.data / "papers"
        if not self.papers.exists():
            self.papers.mkdir(parents=True, exist_ok=True)