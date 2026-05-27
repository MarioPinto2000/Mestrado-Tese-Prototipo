import cv2

def listar_camaras():
    indices = []
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            indices.append(i)
        cap.release()
    return indices