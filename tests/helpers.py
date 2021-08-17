import attr


@attr.s(auto_attribs=True)
class SchemaInfo:
    name: str
    version: str
    source_dir: str
