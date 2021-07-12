from psqlgml.models import Association, SchemaType


def test_schema_type_enum():
    gpas_schema = SchemaType.from_value("GPAS")

    assert {"aliquot", "project"} == {link.dst for link in gpas_schema.associations("case")}
    assert {"case", "raw_methylation_array", "read_group"} == {
        link.dst for link in gpas_schema.associations("aliquot")
    }
    assert {
        "aliquot_level_maf",
        "annotated_somatic_mutation_index",
        "annotated_somatic_mutation",
    } == {link.dst for link in gpas_schema.associations("vcf2maf_workflow")}


def test_association__instance():
    a1 = Association("src", "dst", "link1")
    a2 = Association("src", "dst", "link1")
    a3 = Association("src", "dst", "link2")

    assert a1 == a2
    assert a1 != a3
