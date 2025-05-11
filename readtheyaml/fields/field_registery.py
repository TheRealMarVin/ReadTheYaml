from functools import partial

from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.enum_field import EnumField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField

FIELD_REGISTRY = {
    "int": partial(NumericalField, int),
    "float": partial(NumericalField, float),
    "str": StringField,
    "bool": BoolField,
    "enum": EnumField,
    # We handle 'list(...)' dynamically
}

