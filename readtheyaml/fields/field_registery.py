import re
from functools import partial
from typing import Optional

from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField

FIELD_REGISTRY = {
    "int": partial(NumericalField, int),
    "float": partial(NumericalField, float),
    "str": StringField,
    "bool": BoolField,
    # We handle 'list(...)' dynamically
}

