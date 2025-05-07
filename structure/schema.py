import yaml
from typing import Any, Dict

from .fields import Field
from .sections import Section


class Schema(Section):
    """
    A Schema is a top-level Section that can be constructed from Python or a YAML schema definition.
    """

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Schema":
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Schema":
        name = data.get("name", "root")
        description = data.get("description", "")
        required = data.get("required", True)

        fields = {}
        for field_name, field_data in data.get("fields", {}).items():
            fields[field_name] = Field(
                name=field_name,
                description=field_data.get("description", ""),
                required=field_data.get("required", True),
                default=field_data.get("default"),
                value_type=eval(field_data.get("type", "str")),
                value_range=tuple(field_data.get("range", [])) or None,
            )

        subsections = {}
        for section_name, section_data in data.get("subsections", {}).items():
            subsections[section_name] = Section(
                name=section_name,
                description=section_data.get("description", ""),
                required=section_data.get("required", True),
                fields={
                    fname: Field(
                        name=fname,
                        description=fdata.get("description", ""),
                        required=fdata.get("required", True),
                        default=fdata.get("default"),
                        value_type=eval(fdata.get("type", "str")),
                        value_range=tuple(fdata.get("range", [])) or None,
                    )
                    for fname, fdata in section_data.get("fields", {}).items()
                },
                subsections={
                    sname: cls._from_dict(sdata)
                    for sname, sdata in section_data.get("subsections", {}).items()
                }
            )

        return cls(
            name=name,
            description=description,
            required=required,
            fields=fields,
            subsections=subsections
        )

    def validate_file(self, yaml_path: str) -> Dict[str, Any]:
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return self.build_and_validate(config)
