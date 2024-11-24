from typing import Annotated, Any

from fastapi import Depends

from ...db import prepare_db


class SqliteRepositoryBase:
    def __init__(self, db: Annotated[Any, Depends(prepare_db)]):
        self.db = db
        self.row_factory = None

    def __call__(self):
        self._setup()
        return self

    def _setup(self):
        pass
