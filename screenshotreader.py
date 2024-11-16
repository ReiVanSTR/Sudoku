import cv2
from app.steps import ScreenshotProcessor
from app.adb import ADB

working_dir = "./screenshots/"
img_name = input("Image name: ")

adb = ADB("emulator-5554")
adb.ScreenCapture(working_dir, img_name)
# Переменные для хранения начальных и конечных координат
drawing = False  # True, когда мышь нажата
start_point = (-1, -1)  # Начальная точка
end_point = (-1, -1)  # Конечная точка

# Функция для обработки событий мыши
def draw_rectangle(event, x, y, flags, param):
    global start_point, end_point, drawing

    if event == cv2.EVENT_LBUTTONDOWN:  # ЛКМ нажата
        drawing = True
        start_point = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:  # Мышь перемещается
        if drawing:
            end_point = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:  # ЛКМ отпущена
        drawing = False
        end_point = (x, y)

# Открываем изображение с помощью OpenCV

screenshot = cv2.imread(f"{working_dir}{img_name}.png")

# Копия изображения для отображения
image_copy = screenshot.copy()

# Назначаем функцию обратного вызова для окна
cv2.namedWindow('Draw Rectangle')
cv2.setMouseCallback('Draw Rectangle', draw_rectangle)

while True:
    # Копируем изображение для отрисовки прямоугольника
    img_to_show = image_copy.copy()

    # Если есть конечная точка, рисуем прямоугольник
    if start_point != (-1, -1) and end_point != (-1, -1):
        cv2.rectangle(img_to_show, start_point, end_point, (0, 255, 0), 2)

    # Показываем изображение
    cv2.imshow('Draw Rectangle', img_to_show)

    # Если нажать 'q', программа завершится
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# Вычисляем ширину и высоту прямоугольника
x, y = start_point
w = abs(end_point[0] - start_point[0])
h = abs(end_point[1] - start_point[1])

coordinates = [x,y,w,h]

ScreenshotProcessor().crop(f"{working_dir}{img_name}.png", coordinates, f"{working_dir}{img_name}.png")
# Закрываем все окна
print(coordinates)
cv2.destroyAllWindows()