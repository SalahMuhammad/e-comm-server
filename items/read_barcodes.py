from pyzbar import pyzbar
# import cv2
import numpy as np


def main():
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    
    while ret:
        ret, frame = camera.read()
        frame = read_barcodes(frame)
        cv2.imshow('Barcode/QR code reader', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    camera.release()
    cv2.destroyAllWindows()

def read_barcodes(frame):
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y , w, h = barcode.rect
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
        
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 2.0, (255, 255, 255), 1)
        
        print("Detected barcode:", barcode_info)
    return frame


if __name__ == '__main__':
    main()




def read_barcode(image_path):
    # Read the image using OpenCV
	image = cv2.imread(image_path)
	print(image)
    # Convert to grayscale
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
	thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Noise removal
	kernel = np.ones((3,3), np.uint8)
	opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Find contours
	contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
	barcodes = []
	for contour in contours:
        # Get rectangle bounding contour
		x, y, w, h = cv2.boundingRect(contour)
        
        # Create ROI
		roi = image[y:y+h, x:x+w]
        
        # Decode the barcode
		decoded_objects = pyzbar.decode(roi)
        
		for obj in decoded_objects:
			barcode_data = obj.data.decode('utf-8')
			barcode_type = obj.type
			print(f"Found {barcode_type} barcode: {barcode_data}")
			barcodes.append(obj)
	return barcodes