from functools import partial

from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.enum_field import EnumField
from readtheyaml.fields.none_field import NoneField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField
from readtheyaml.fields.tuple_field import TupleField
from readtheyaml.fields.union_field import UnionField

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

