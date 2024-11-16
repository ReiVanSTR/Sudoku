from .basic import Step
from .enums import StepTypesEnums, OnFalseEnums
from app.adb import ADB

class ClickStep(Step):
    def __init__(self, step_name: str, screenshot_name:str, type, workspace_area = [], required_screen_check = False, threshold = 0.75, on_false = OnFalseEnums.retry, retries_limit = 2):
        super().__init__(step_name, screenshot_name, required_screen_check, threshold, on_false, retries_limit)
        self.workspace_area = workspace_area
        self._func = None
        self.type = StepTypesEnums(type)


    def __call__(self, *args, **kwargs):
        if self._func:
            return self._func(*args, **kwargs)
        else:
            return self.default_execute(*args, **kwargs)
        
    def default_execute(self, adb: ADB):
        adb.random_click(self.workspace_area)

    def bitwise_screenshot_with_workspace_area(self, work_dir: str = "app/screenshots"):
        self.bitwise_screenshot = self.screenshot_to_bitwise(template_path = f"{work_dir}/{self.screenshot_name}")
        if self.validate_workspace_area():
            self.bitwise_screenshot = self.bitwise_crop(self.bitwise_screenshot, self.workspace_area)