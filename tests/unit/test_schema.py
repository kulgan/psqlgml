from psqlgml.models import SchemaType


def test_schema_type_enum():
    gdc_schema = SchemaType.from_value("GPAS")

    assert gdc_schema.links
    print(gdc_schema.GDC.associations("case"))
