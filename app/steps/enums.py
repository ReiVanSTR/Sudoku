from enum import Enum

class OnFalseEnums(Enum):
    skip = "skip"
    retry = "retry"

class StepTypesEnums(Enum):
    button = "button"
    input_filed = "input_field"
    validator = "validator"
    screen_getter = "screen_getter"
