from abc import ABC, abstractmethod
from typing import Any


class RepositoryConnector(ABC):

    @abstractmethod
    def list_files(self) -> list[dict[str, Any]]:
        """Return files currently accessible to this repository connector."""
        raise NotImplementedError
