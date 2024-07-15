import cv2
from ultralytics import YOLO

from sort.sort import *
from util import get_car, read_license_plate, write_csv

results = {}

mot_tracker = Sort()

#load models
coco_model = YOLO('yolov10n.pt')
license_plate_detector = YOLO('E:/intel/iup_project/license_plate_detector.pt')

#load video
vd = cv2.VideoCapture('E:/intel/video.mp4')
vehicles = [1,2,3,5,7,8]
#read frames
frame_no = -1
ret = True
while ret:
    frame_no +=1
    ret, frame = vd.read()
    if ret and frame_no < 10:
        results[frame_no] = {}
        # detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])

        # track vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))

        # detect license plates
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate

            # assign license plate to car
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

            if car_id != -1:

                # crop license plate
                license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

                # process license plate
                license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255,cv2.THRESH_BINARY_INV)



                # read license plate number
                license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)

                if license_plate_text is not None:
                    results[frame_no][car_id] = {'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                                                'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                    'text': license_plate_text,
                                                                    'bbox_score': score,
                                                                    'text_score': license_plate_text_score}}

#write results
write_csv(results, 'E:/intel/test.csv')
