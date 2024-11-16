import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
import time

from app.adb import ADB
from app.adb import LDConnector
from app.steps.enums import OnFalseEnums, StepTypesEnums
from app.steps import ClickStep, ValidatorStep, InputStep, ScreenGetterStep, Step, BitwiseScreenshotProcessor, ScreenshotProcessor
from config import load_config

@dataclass(init=False)
class StepData:
    step_name: str
    screenshot_name: str
    type: str
    extra_args: list = field(default_factory=list)
    extra_kwargs: dict = field(default_factory=dict)

    def __init__(self, step_name: str, screenshot_name: str, type: str, *args, **kwargs):
        self.step_name = step_name
        self.screenshot_name = screenshot_name
        self.type = type
        self.extra_args = args
        self.extra_kwargs = kwargs
        

class StepManager():
    def __init__(self, config: str):
        self.adb = ADB(emulator_name="emulator-5554")
        self.ldplayer = LDConnector()
        self.emulator_name = "emulator-5554"
        self.steps = []
        self.config = load_config(config)
        self.screenshots_path = self.config.get("screenshots_path")
        self.work_dir = self.config.get("work_dir")
        self.screen_processor = ScreenshotProcessor()
        self.bitwise_screen_processor = BitwiseScreenshotProcessor()

        for step in self.config.get("steps"):
            data = StepData(**step)

            if data.type == StepTypesEnums.button.value:
                self.steps.append(ClickStep(**step))

            if data.type == StepTypesEnums.input_filed.value:
                self.steps.append(InputStep(**step))

            if data.type == StepTypesEnums.validator.value:
                self.steps.append(ValidatorStep(**step))

    def initialize_steps_binary(self, screenshots_work_dir):
        for step in self.steps:
            try:
                step.bitwise_screenshot_with_workspace_area(screenshots_work_dir)
            except:
                ValueError(f"Step {step.step_name} not initialized")

    def validate_screenshot(self, step: Step, attemp_delay = 0.25):
        attemps = 1
        print(f"Validating {step.step_name}")
        print(step.on_false)
        while attemps <= step.retries_limit:
            self.adb.ScreenCapture(self.adb.emulator_name, self.work_dir, self.emulator_name)
            self.screen_processor.crop(f"{self.screenshots_path}{self.emulator_name}.png", step.workspace_area, f"{self.screenshots_path}{self.emulator_name}.png")
            if hasattr(step, "bitwise_screenshot"):
                temp = self.bitwise_screen_processor.screenshot_to_bitwise(f"{self.screenshots_path}{step.screenshot_name}")
                result = self.bitwise_screen_processor.bitwise_find_image_in_screen(
                    step.bitwise_screenshot, 
                    f"{self.work_dir}{self.emulator_name}.png", 
                    step.threshold)
            else:
                print(f"screenshot: {self.screenshots_path}{step.screenshot_name}")
                print(f"{self.work_dir}{self.emulator_name}.png")

                result = self.screen_processor.find_image_in_screenshot(f"{self.screenshots_path}{step.screenshot_name}", f"{self.work_dir}{self.emulator_name}.png", step.threshold)

            if not result and step.on_false == OnFalseEnums.skip:
                logging.debug(f"Skipping {step.step_name}")
                return OnFalseEnums.skip

            if not result:
                logging.debug(f"State of {step.step_name} screenshot not valid, trying again. Retries {attemps}")
                attemps += 1
                logging.debug(attemp_delay)
                continue

            if result:
                logging.debug(f"Valide state of {step.step_name} after {attemps} retries")
                return True

        return False

    def set_step_handler(self, step_name):
        for step in self.steps:
            if step.step_name == step_name:
                def wrapper(func):
                    def inner_wrapper(adb, *args, **kwargs):
                        # Вызываем декорированную функцию с adb, args и kwargs
                        return func(adb, step, *args, **kwargs)

                    step._func = inner_wrapper  # Сохраняем обертку функции в шаге
                    return inner_wrapper  # Возвращаем обертку функции

                return wrapper  # Возвращаем обертку для функции

        raise ValueError(f"Step with name '{step_name}' not found.")

        


    def execute_step(self, step: Step, *args, **kwargs):
        print(step.step_name)
        if hasattr(step, "__call__"):
            return step(self.adb, *args, **kwargs)
        
        if hasattr(step, "default_execute"):
            return step.default_execute(self.adb)
        
        raise ValueError(f"{step.step_name} has no execute options")
        

    def start(self, delay = 0.3, start_from: str = None):
        active_steps = self.steps
        if start_from:
            for k in range(0, len(active_steps)-1):
                if active_steps[k].step_name == start_from:
                    active_steps = active_steps[k::]
                    break

        for step in active_steps:
            time.sleep(delay)
            if step.required_screen_check:
                is_valid = self.validate_screenshot(step)

                if is_valid: 
                    self.execute_step(step = step)

                if is_valid == OnFalseEnums.skip:
                    print(f"Skipping {step.step_name}")
                    continue

                if not is_valid:
                    return f"Error on {step.step_name}, {is_valid}"
            
            else:
                self.execute_step(step = step) 