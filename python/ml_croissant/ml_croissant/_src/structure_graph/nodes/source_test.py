"""source_test module."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes.source import (
    apply_transforms_fn,
    Extract,
    FileProperty,
    is_file_property,
    Source,
    Transform,
)
import pytest


def test_source_bool():
    empty_source = Source(transforms=(Transform(replace="\\n/<eos>"),))
    assert not empty_source

    whole_source = Source(uid="one/two")
    assert whole_source


@pytest.mark.parametrize(
    ["json_ld", "expected_source"],
    [
        [
            {
                "field": "token-files/content",
            },
            Source(uid="token-files/content"),
        ],
        [
            {
                "field": "token-files/content",
                "apply_transform": [{"replace": "\\n/<eos>"}, {"separator": " "}],
            },
            Source(
                uid="token-files/content",
                transforms=(
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ),
            ),
        ],
        [
            [
                {
                    "field": "token-files/content",
                    "apply_transform": [{"replace": "\\n/<eos>"}, {"separator": " "}],
                }
            ],
            Source(
                uid="token-files/content",
                transforms=(
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ),
            ),
        ],
        [
            {
                "distribution": "my-csv",
                "apply_transform": [{"replace": "\\n/<eos>", "separator": " "}],
                "data_extraction": {"csv_column": "my-column"},
            },
            Source(
                extract=Extract(csv_column="my-column"),
                uid="my-csv",
                transforms=(Transform(replace="\\n/<eos>", separator=" "),),
            ),
        ],
    ],
)
def test_source_parses_list(json_ld, expected_source):
    issues = Issues()
    assert Source.from_json_ld(issues, json_ld) == expected_source
    assert not issues.errors
    assert not issues.warnings


def test_declaring_multiple_sources_in_one():
    issues = Issues()
    json_ld = {"distribution": "my-csv", "field": "my-record-set/my-field"}
    assert Source.from_json_ld(issues, json_ld) == Source()
    assert issues.errors == {
        "Every http://mlcommons.org/schema/source should declare either"
        " http://mlcommons.org/schema/field or https://schema.org/distribution"
    }


def test_declaring_multiple_data_extraction_in_one():
    issues = Issues()
    json_ld = {
        "distribution": "my-csv",
        "data_extraction": {
            "csv_column": "csv_column",
            "json_path": "json_path",
        },
    }
    assert Source.from_json_ld(issues, json_ld) == Source(
        uid="my-csv",
        extract=Extract(csv_column="csv_column", json_path="json_path"),
    )
    assert len(issues.errors) == 1
    assert (
        "http://mlcommons.org/schema/dataExtraction should have one of the following"
        " properties"
        in list(issues.errors)[0]
    )


def test_declaring_wrong_file_property():
    issues = Issues()
    json_ld = {
        "distribution": "my-csv",
        "data_extraction": {
            "file_property": "foo",
        },
    }
    Source.from_json_ld(issues, json_ld)
    assert (
        "Property http://mlcommons.org/schema/fileProperty can only have values in"
        " `fullpath`, `filepath` and `content`. Got: foo"
        in issues.errors
    )


@pytest.mark.parametrize(
    ["value", "source", "expected_value"],
    [
        # No source
        ["this is a value", None, "this is a value"],
        # Capturing group
        [
            "train1234",
            Source(transforms=(Transform(regex="(train|val)\\d\\d\\d\\d"),)),
            "train",
        ],
        # Non working capturing group
        [
            "foo1234",
            Source(transforms=(Transform(regex="(train|val)\\d\\d\\d\\d"),)),
            "foo1234",
        ],
    ],
)
def test_apply_transforms_fn(value, source, expected_value):
    assert apply_transforms_fn(value, source) == expected_value


@pytest.mark.parametrize(
    ["source", "expected_field"],
    [
        [
            Source(uid="my-csv", extract=Extract(csv_column="my-csv-column")),
            "my-csv-column",
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(file_property=FileProperty.content),
            ),
            "content",
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(json_path="/some/json/path"),
            ),
            "/some/json/path",
        ],
        [
            Source(uid="record_set/field_name"),
            "field_name",
        ],
    ],
)
def test_get_field(source: Source, expected_field: str):
    assert source.get_field() == expected_field


def test_is_file_property():
    assert is_file_property("content")
    assert is_file_property("filename")
    assert is_file_property("filepath")
    assert is_file_property("fullpath")
    assert not is_file_property("foo")


def test_check_source_for_valid_json_path():
    issues = Issues()
    Source(uid="uid", extract=Extract(json_path="*.first.second")).check_source(
        issues.add_error
    )
    assert not issues.errors


def test_check_source_for_invalid_json_path():
    issues = Issues()
    Source(uid="uid", extract=Extract(json_path="invalid/json/path")).check_source(
        issues.add_error
    )
    errors = list(issues.errors)
    assert len(errors) == 1
    assert "Wrong JSONPath" in errors[0]
