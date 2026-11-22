"""允许通过 ``python -m phonics`` 运行命令行。"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
