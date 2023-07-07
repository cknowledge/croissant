"""Join operation module."""

from collections.abc import Callable
import dataclasses
import re
from typing import Any

from ml_croissant._src.structure_graph.nodes import Source
from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd


def apply_transform_fn(value: str, source: Source | None = None) -> Callable[..., Any]:
    if source is None:
        return value
    if source.apply_transform_regex is not None:
        source_regex = re.compile(source.apply_transform_regex)
        match = source_regex.match(value)
        for group in match.groups():
            if group is not None:
                return group
    return value


@dataclasses.dataclass(frozen=True, repr=False)
class Join(Operation):
    """Joins pd.DataFrames."""

    def __call__(
        self, *args: pd.Series, left: Source | None = None, right: Source | None = None
    ) -> pd.Series:
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            assert left.reference is not None, (
                f'Reference for "{self.node.uid}" is None. It should be a valid'
                " reference."
            )
            left_key = left.reference[1]
            right_key = right.reference[1]
            # A priori, we cannot know which one is left and which one is right, because
            # topological sort is not reproducible in some case.
            df_left, df_right = args
            if left_key not in df_left.columns or right_key not in df_right.columns:
                df_left, df_right = df_right, df_left
            assert (
                len(left.reference) == 2
            ), "JOIN operation does not define a column name."
            assert left_key in df_left.columns, (
                f'Column "{left_key}" does not exist in node "{left.reference[0]}".'
                f" Existing columns: {df_left.columns}"
            )
            assert right_key in df_right.columns, (
                f'Column "{right_key}" does not exist in node "{right.reference[0]}".'
                f" Existing columns: {df_right.columns}"
            )
            df_left[left_key] = df_left[left_key].transform(
                apply_transform_fn, source=left
            )
            return df_left.merge(
                df_right, left_on=left_key, right_on=right_key, how="left"
            )
        else:
            raise NotImplementedError(
                f"Unsupported: Trying to joing {len(args)} pd.DataFrames."
            )