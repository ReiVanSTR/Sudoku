import subprocess
import random

class ADB():
    def __init__(self, emulator_name):
        self.emulator_name = emulator_name
    
    def launch_emulator(self, emulator_name):
        pass

    def click(self, x, y):
        subprocess.check_call(f"adb.exe -s {self.emulator_name} shell input tap {int(x)} {int(y)}", shell=True)
        print(f"Clicked on {x=}, {y=}")


    def random_click(self, positions: list[int]):
        x, y = random.randint(positions[0], positions[0]+positions[2]), random.randint(positions[1], positions[1]+positions[3])
        self.click(x, y)


    def OpenApp(self, emulator, package):
        subprocess.check_call(f"adb.exe -s {emulator} shell monkey -p {package} -c android.intent.category.LAUNCHER 1", shell=True)

    def input_text(self, emulator, text):
        subprocess.check_call(f"adb.exe -s {emulator} shell input text {text}", shell=True)

    def ScreenCapture(self, path: str = "./", name: str = None):
        if not name:
            name = self.emulator_name
        subprocess.call(f"adb.exe -s {self.emulator_name} shell screencap /sdcard/Download/{name}.png", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(f"adb.exe -s {self.emulator_name} pull /sdcard/Download/{name}.png {path}{name}.png", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"{name}.png"