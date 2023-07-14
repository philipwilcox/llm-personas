import dataclasses


@dataclasses.dataclass
class MethodSummary:
    name: str
    description: str
    method_signature: str
    input_description: str
    output_description: str
    module_path: str
