import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import BASE_DIR, _configured_path


class ConfiguredPathTests(unittest.TestCase):
    def test_relative_path_is_resolved_from_backend_directory(self):
        with patch.dict(os.environ, {"BROCHURES_DIR": "..\\brochures"}):
            configured_path = _configured_path(
                "BROCHURES_DIR", BASE_DIR.parent / "brochures"
            )

        self.assertEqual(configured_path, (BASE_DIR / "..\\brochures").resolve())


if __name__ == "__main__":
    unittest.main()
