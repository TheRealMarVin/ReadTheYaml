from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.base.enum_field import EnumField
from readtheyaml.fields.base.none_field import NoneField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.composite.tuple_field import TupleField
from readtheyaml.fields.composite.union_field import UnionField


class FieldFactory:
    def __init__(self):
        self.builders = [BoolField, EnumField, NoneField, NumericalField, ObjectField, StringField,
                         ListField, TupleField, UnionField]

    def create_field(self, type_str: str, name: str, **kwargs):
        for builder in self._builders:
            field = builder.from_type_string(type_str, name, self, **kwargs)
            if field:
                return builder(type_str, self)

        raise ValueError(f"Unknown field type: {type_str}")