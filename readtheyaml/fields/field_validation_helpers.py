from functools import partial

from readtheyaml.exceptions.format_error import FormatError


def find_and_validate_bounds(value_range, min_value, max_value):
    if value_range is not None and len(value_range) != 2:
        raise FormatError(f"Range must have 2 values, {len(value_range)} provided.")

    if value_range is not None and (min_value is not None or max_value is not None):
        if min_value is None:
            raise FormatError(f"You are using range and upper bound only. This is unsafe. Only use upper bound or range!")
        if max_value is None:
            raise FormatError(f"You are using range and lower bound only. This is unsafe. Only use lower bound or range!")
        if min_value != value_range[0]:
            raise FormatError(f"Lower bound value is not matching lower bound of range.")
        if max_value != value_range[1]:
            raise FormatError(f"Upper bound value is not matching upper bound of range.")

    if value_range is not None:
        min_value = value_range[0]
        max_value = value_range[1]

    if min_value is not None and max_value is not None:
        if min_value > max_value:
            raise FormatError(f"Minimal value greater than maximal value. ({min_value} > {max_value})")

    return min_value, max_value


def get_target_class(field_obj_or_partial):
    if isinstance(field_obj_or_partial, partial):
        return field_obj_or_partial.func
    return type(field_obj_or_partial)

