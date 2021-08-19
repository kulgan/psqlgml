import sys

if sys.version_info >= (3, 8):
    from typing import (  # pylint: disable=no-name-in-module
        Final,
        Literal,
        Protocol,
        TypedDict,
    )
else:
    from typing_extensions import Final, Literal, Protocol, TypedDict

NODE_ID: Final = "node_id"
UniqueFieldType = Literal["node_id", "submitter_id"]
ValidatorType = Literal["ALL", "DATA", "SCHEMA"]
RenderFormat = Literal["jpeg", "pdf", "png"]
