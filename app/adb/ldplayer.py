import subprocess
import numpy
import cv2

class LDConnector():
    def __init__(self):
        self.emulators_list = []
        self.update_emulators_list()

    @staticmethod
    def execute_command(command: str, **kwargs):
        command_arguments = " ".join([f"--{key} {value}" for key, value in kwargs.items()])
        try:
            return subprocess.check_call(f"ldconsole.exe {command} {command_arguments}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            return f"error {e}"

    def update_emulators_list(self):
        # self.emulators_list = self.execute_command(command="list").decode().split("\r\n")
        response = subprocess.run("ldconsole.exe list", shell=True, text=True, capture_output=True)
        if response != 0:
            self.emulators_list = response.stdout.split()
            return


    def isrunning(self, emulator_name: str):
        response = self.execute_command(command="isrunning", name = emulator_name)

        if response == "running":
            return True
        
        return False

    def launch(self, emulator_name: str):
        if self.isrunning(emulator_name):
            return f"emulator {emulator_name} already running!"

        if emulator_name in self.emulators_list:
            self.execute_command(command="launch", name = emulator_name)
            return f"Emulator {emulator_name} succesfully running!"

        return f"Emulator {emulator_name} not found in emulators list,  try to update or create"
    
    def FindImg(self, emulator, target_pic_name, threshold = 0.75):
        try:
            img = cv2.imread(target_pic_name)
            img2 = cv2.imread(self.ScreenCapture(emulator))
            w, h = img.shape[1], img.shape[0]
            result = cv2.matchTemplate(img, img2, cv2.TM_CCOEFF_NORMED)
            location = numpy.where(result >= threshold)
            data = list(zip(*location[::-1]))
            is_match = len(data) > 0
            if is_match:
                x, y = data[0][0], data[0][1]  
                return x + int(w/2), y + int(h/2)
            else:
                return False, False
        except:
            return False, False