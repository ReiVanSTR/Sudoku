from abc import ABC, abstractmethod
from enum import Enum
import cv2, numpy
from cv2.mat_wrapper import Mat as MatLike

from .enums import OnFalseEnums
from app.adb import ADB


class WorkSpaceArea():
    def __call__(self, workspace_area):
        if sum(workspace_area) > 0:
            x, y, w, h = workspace_area
            return f"{x}x{y}+{w}+{h}"
        return []
    


class ColorTypes(Enum):
    BGR = "BGR"
    BINARY = "BINARY"
    GRAYSCALE = "GRAYSCALE"
    UNKNOWN = "UNKNOWN"


class BitwiseScreenshotProcessor():
    def check_image_format(self, image):
        # if not isinstance(image, numpy.ndarray):
        #     image = numpy.ndarray(image[0][0])

        if len(image.shape) == 3 and image.shape[2] == 3:
            return ColorTypes.BGR
        
        elif len(image.shape) == 2:
            unique_values = numpy.unique(image)
            if set(unique_values).issubset({0, 255}):
                return ColorTypes.BINARY
            else:
                return ColorTypes.GRAYSCALE
        else:
            return ColorTypes.UNKNOWN
    
    def screenshot_to_bitwise(self, template_path: str | numpy.ndarray, convert_to_grayscale: bool = False, convert_to_binary: bool = False):
        if isinstance(template_path, str):
            bitwise_screenshot = cv2.imread(template_path, cv2.IMREAD_COLOR)

        if convert_to_grayscale:
            bitwise_screenshot = cv2.cvtColor(bitwise_screenshot, cv2.COLOR_BGR2GRAY)

        if convert_to_binary:
            # Преобразование изображения в черно-белое (бинарное)
            _, bitwise_screenshot = cv2.threshold(bitwise_screenshot, 127, 255, cv2.THRESH_BINARY)
        
        return bitwise_screenshot
    
    def bitwise_find_image_in_screen(self, screenshot: MatLike | str, template: MatLike, workspace_area = [], threshold=0.8):

        if isinstance(screenshot, str):
            template_type = self.check_image_format(template)

            if template_type == ColorTypes.BGR:
                screenshot = self.screenshot_to_bitwise(screenshot)
            
            if template_type == ColorTypes.BINARY:
                screenshot = self.screenshot_to_bitwise(screenshot, convert_to_binary=True, convert_to_grayscale=True)

            if template_type == ColorTypes.GRAYSCALE:
                screenshot = self.screenshot_to_bitwise(screenshot, convert_to_grayscale=True)
        
        if not (screen_type := self.check_image_format(screenshot)) == (template_type := self.check_image_format(template)):
            return ValueError(f"Template and screenshot must have one template format! Screenshot type: {screen_type} != Template type {template_type}")
        
        if workspace_area:
            screenshot = self.bitwise_crop(screenshot, workspace_area)

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        location = numpy.where(result >= threshold)

        matched_coordinates = []
        for pt in zip(*location[::-1]):
            matched_coordinates.append((pt[0], pt[1]))

        if matched_coordinates:
            return True 
        return False
    
    def bitwise_crop(self, screenshot: MatLike, coordinates: list[int]):
        x, y, w, h = coordinates
        return screenshot[y:y + h, x:x + w]
    
    def bitwise_crop(self, screenshot: MatLike, coordinates: list[int]):
        x, y, w, h = coordinates
        return screenshot[y:y + h, x:x + w]
    
    

class ScreenshotProcessor(BitwiseScreenshotProcessor):
    def crop(self, screenshot_path: str, coordinates: list[int], output_path: str):
        # Read the image from the specified path
        screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
        
        # Check if the image was loaded successfully
        if screenshot is None:
            raise FileNotFoundError(f"Could not load image at path: {screenshot_path}")

        # Ensure the coordinates are valid
        if len(coordinates) != 4:
            raise ValueError("Coordinates should be a list of four integers: [x, y, width, height].")
        
        x, y, w, h = coordinates
        height, width = screenshot.shape[:2]
        print(height, width)
        print(coordinates)
        # Check if the coordinates are within the bounds of the image
        if x < 0 or y < 0 or x + w > screenshot.shape[1] or y + h > screenshot.shape[0]:
            raise ValueError("Crop coordinates are out of bounds.")

        # Crop the image
        cropped_image = screenshot[y:y + h, x:x + w]

        # Save the cropped image to the specified output path
        success = cv2.imwrite(output_path, cropped_image)

        if not success:
            raise IOError(f"Failed to write image to path: {output_path}")

        return success  # Return whether the writing was successful
    
    def find_image_in_screenshot(screenshot_path: str, template_path: str, threshold=0.8):
        # Load the screenshot and the template imageё
        screenshot = cv2.imread(screenshot_path)  
        template = cv2.imread(template_path)

        # Convert both images to grayscale
        # screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        # template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Match the template using cv2.matchTemplate
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        # Find the locations where the match exceeds the threshold
        loc = numpy.where(result >= threshold)

        # Collecting the coordinates of matched areas
        matched_coordinates = []
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            matched_coordinates.append((pt[0], pt[1]))  # Append (x, y) coordinates

        if matched_coordinates:
            return True

        return False



class Step(ABC, BitwiseScreenshotProcessor):
    def __init__(self, step_name: str, screenshot_name: str, required_screen_check: bool = False, threshold: float = 0.75, on_false: OnFalseEnums = OnFalseEnums.retry, retries_limit: int = 2, workspace_area = []):
        self.step_name = step_name
        self.screenshot_name = screenshot_name
        self.required_screen_check = required_screen_check
        self.threshold = threshold
        self.retries_limit = retries_limit
        self.workspace_area = workspace_area
        self.on_false = on_false
        if on_false:
            self.on_false = OnFalseEnums(on_false)
    
    def validate_workspace_area(self):
        if WorkSpaceArea()(self.workspace_area):
            return True
        return False
    
    
    def init_bitwise(self, work_dir: str, convert_to_grayscale: bool = False, convert_to_binary: bool = False):
        self.bitwise_screenshot = self.screenshot_to_bitwise(
            template_path = f"{work_dir}/{self.screenshot_name}", 
            convert_to_grayscale = convert_to_grayscale, 
            convert_to_binary = convert_to_binary)
    
    @abstractmethod
    def default_execute(self, adb: ADB):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass