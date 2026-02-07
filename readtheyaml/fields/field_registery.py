from functools import partial

from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.base.enum_field import EnumField
from readtheyaml.fields.base.none_field import NoneField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.composite.tuple_field import TupleField

FIELD_REGISTRY = {
    "int": partial(NumericalField, int),
    "float": partial(NumericalField, float),
    "str": StringField,
    "bool": BoolField,
    "enum": EnumField,
    "None": NoneField,
    "tuple": TupleField,
    # We handle "list(...)" dynamically
}

