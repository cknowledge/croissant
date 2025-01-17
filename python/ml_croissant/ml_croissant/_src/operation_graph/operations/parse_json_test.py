"""parse_json_test module."""

from ml_croissant._src.operation_graph.operations.parse_json import ParseJson
from ml_croissant._src.structure_graph.nodes.source import Extract, Source
from ml_croissant._src.tests.nodes import create_test_field, empty_record_set
import pandas as pd


def test_str_representation():
    operation = ParseJson(node=empty_record_set)
    assert str(operation) == "ParseJson(record_set_name)"


def test_parse_json():
    field1 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].id"))
    )
    field2 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].value"))
    )
    fields = [field1, field2]
    parse_json = ParseJson(node=empty_record_set)
    json = {
        "foo": "bar",
        "annotations": [
            {"id": 1, "value": 3},
            {"id": 2, "value": 4},
        ],
    }
    expected_df = pd.DataFrame(
        data={"$.annotations[*].id": [1, 2], "$.annotations[*].value": [3, 4]}
    )
    pd.testing.assert_frame_equal(parse_json(json, fields), expected_df)
