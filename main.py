import numpy as np
import cv2
import matplotlib.pyplot as plt
import winsound

# Closest proximity check function
def find_if_close(cnt1,cnt2, d = 10):
    x, y, w, h = cv2.boundingRect(cnt1)
    coord1 = (x, y, x+w, y+h)
    centerCoord1 = np.array((coord1[0] + (coord1[2] / 2), coord1[1] + (coord1[3] / 2)))
    x, y, w, h = cv2.boundingRect(cnt2)
    coord2 = (x, y, x + w, y + h)
    centerCoord2 = np.array((coord2[0] + (coord2[2] / 2), coord2[1] + (coord2[3] / 2)))
    distance = np.linalg.norm(centerCoord1 - centerCoord2)
    if abs(distance) < d:
       return True
    else:
       return False

# Taking video feed
## EDIT THE LOCATION OF THE VIDEO
Video = cv2.VideoCapture("Side.mp4")

# Creating a Background Substractor kernel
fgbg = cv2.createBackgroundSubtractorKNN(128, cv2.THRESH_BINARY, 1)
w_list = []
h_list = []
framenum = 0;

while(1):
    framenum += 1
    # Obtain frame
    ret, frame = Video.read()
    # Convert the frame into Grey
    frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Blur the the grey frame
    frame_blur = cv2.GaussianBlur(frame_grey,(3,3),0)
    # Apply the Background Substraction mask
    fgmask = fgbg.apply(frame_blur)
    fgmask[fgmask == 127] = 0
    # Threshold the Background Substracted frame to remove grey values
    (threshold, frame_bw) = cv2.threshold(fgmask, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Dilate the frame
    frame_bw = cv2.dilate(frame_bw, None, iterations=2)
    # Find the contours
    im, contours, hierarchy = cv2.findContours(frame_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if(framenum > 50): ## CAN EDIT THE LIMIT
        # Develop a list of large contours
        contours_thresholded = []
        # Threshold the area for determining an contour is large enough or not
        threshold_area = 1
        v = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)

            if area > threshold_area:
                contours_thresholded.append(cnt)
                v += 1

        # Sort the largest contours
        largest_contours = sorted(contours_thresholded, key=cv2.contourArea)[-5:]
        # Determine the biggest contour
        contour_sizes = [(cv2.contourArea(contour), contour) for contour in contours]
        biggest_contour = max(contour_sizes, key=lambda x: x[0])[1]
        # Determine the co-ordinates of the bounding box for the biggest contour
        (xx, yy, ww, hh) = cv2.boundingRect(biggest_contour)

        # Determine the number of largest contours
        LENGTH = len(largest_contours)

        # Set a array that will store the nearest bounding boxes
        rect = np.zeros((LENGTH * LENGTH, 4))

        # Index for tracking the closest bounding boxes
        f = 0
        if LENGTH == 1:
            (x1, y1, w1, h1) = cv2.boundingRect(largest_contours[0])
            rect[f] = (x1, y1, x1 + w1, y1 + h1)
            f += 1

        else:
            # Compare pairwise bounding boxes for the proximity and combine them
            for i, cnt1 in enumerate(largest_contours):
                x = i
                if i != LENGTH - 1:
                    for j, cnt2 in enumerate(largest_contours[i + 1:]):
                        x = x + 1

                        # Call closest proximity check function
                        dist = find_if_close(cnt1, cnt2, 500)
                        if dist == True:
                            (x1, y1, w1, h1) = cv2.boundingRect(cnt1)
                            (x2, y2, w2, h2) = cv2.boundingRect(cnt2)
                            # Find the extreme values of the close bboxes
                            xl = min(x1, x2)
                            yl = min(y1, y2)
                            a = np.array((xl, yl))
                            xr = max(x1 + w1, x2 + w2)
                            yr = max(y1 + h1, y2 + h2)
                            b = np.array((xr, yr))
                            diag = np.linalg.norm(a - b)
                            # Store the diagonal points
                            rect[f] = (xl, yl, xr, yr)
                            f += 1

        # Find the extreme ends of the closest bounding boxes
        X = np.array(rect[(rect[:, 0] != 0), 0])
        Y = np.array(rect[(rect[:, 1] != 0), 1])
        X1 = int(min(X))
        Y1 = int(min(Y))
        X2 = int(max(rect[:, 2]))
        Y2 = int(max(rect[:, 3]))

        # list of difference between the two legs for all the frames
        w_list.append(ww)
        c = cv2.rectangle(fgmask, (X1, Y1),(X2, Y2), (255,0,0), 1)
        # Leg 1
        cv2.circle(frame, (xx + ww, Y2), 2, (0, 255, 0), -1)
        # Leg 2
        cv2.circle(frame, (xx, Y2), 2, (255, 0, 0), -1)

        # Beep Sound when the person is falling
        height = Y2-Y1
        h_list_length = len(h_list)
        if h_list_length > 0:
            height_thresh = (2/3)*(sum(h_list)/len(h_list))
            if height < height_thresh:
                # Set Frequency To 2500 Hertz
                frequency = 2500
                # Set Duration To 2000 ms == 2 second
                duration = 2000
                winsound.Beep(frequency, duration)
                print("beep")

        # List of height of the bounding box for all frames
        h_list.append(height)

        # The feed showing the bounding box
        cv2.imshow('Bounding box', c)
        # The feed showing the feet points
        cv2.imshow('Security feed', frame)

        # Plot of difference between both the feet
        plt.plot(w_list)
        ## CAN CHANGE THE PLOT CONDITIONS
        plt.xticks(np.arange(0,100,2))
        plt.axes(ylim=[0, 400], xlim=[0, 100])
        plt.pause(0.1)

    k = cv2.waitKey(1) & 0xff
    if k == 27:
        break

Video.release()
cv2.destroyAllWindows()