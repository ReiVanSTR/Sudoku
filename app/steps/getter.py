from .basic import Step, ScreenshotProcessor
from .enums import StepTypesEnums, OnFalseEnums


class ScreenGetterStep(Step, ScreenshotProcessor):
    def __init__(self, step_name, screenshot_name, type, required_screen_check = False, threshold = 0.75, on_false = OnFalseEnums.retry, retries_limit = 2, workspace_area=[]):
        super().__init__(step_name, screenshot_name, required_screen_check, threshold, on_false, retries_limit, workspace_area)
        self.type = StepTypesEnums(type)

    # def bitwise_screenshot_with_workspace_area(self, work_dir: str = "app/screenshots"):
    #     self.bitwise_screenshot = self.screenshot_to_bitwise(template_path = f"{work_dir}/{self.screenshot_name}")
    #     if self.validate_workspace_area():
    #         self.bitwise_screenshot = self.bitwise_crop(self.bitwise_screenshot, self.workspace_area)


    def __call__(self):
        pass

    def default_execute(self, adb):
        pass