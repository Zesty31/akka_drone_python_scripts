#!/usr/bin/env python

###############################################################################
# Find_Target.py
# PAM;
#
#
# V0 ; 2018-09-09
#	Uses both the square detection from (PyImage) and a color based method
#	to identify the target
#	This version really heavy in computation an is intended to test
#	detection methods on laptop
#
# v1;2018-10-12
#	Use contour size to evaluate height
#
###############################################################################


# import the necessary packages
import argparse
import imutils
import cv2
import numpy as np
import math

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-n", "--noouput", help="does not display video, only give stdout ")
args = vars(ap.parse_args())

# load the video
camera = cv2.VideoCapture(args["video"])

# #################################################################################3
print("############################################################")

# physical sizes
White_rect_size = 410.0
Blue_diam = 240.0
Red_diam = 160.0
Yellow_diam = 80.0
White_diam = 80.0

# FOV = 90 Deg (bulked estimate)
# From pictue of the drone on table. Yellow radius =40mm=251 pix @ 170mm tan-1(40/170)~13deg
CamDegPerPix = np.arctan(40.0 / 170.0) / 251.0  # rad

# print ("Rad " + str(np.arctan(40.0/170.0)), " deg", str(np.rad2deg(np.arctan(40.0/170.0)))," CamDegPerPix", str(CamDegPerPix))
# reminder
#	if the real size of object is a [mm] and the b is the number of  pixel I see a
#	    hight = a/tan(b*CamDegPerPix)


# Altitude
White_rect_Alt = np.nan
Blue_Alt = np.nan
Red_Alt = np.nan
Yellow_Alt = np.nan
Consolidated_Alt = np.nan

# Selection filter for the colors
boundaries_HSV_Black = ([0, 0, 0], [180, 255, 150])  # Black
boundaries_HSV_Blue = ([60, 50, 120], [120, 255, 255])  # Blue
boundaries_HSV_Red_h = ([140, 50, 80], [180, 255, 255])  # Red
boundaries_HSV_Red_l = ([0, 50, 80], [10, 255, 255])  # Red lowerspectum
boundaries_HSV_Yellow = ([22, 50, 50], [30, 255, 255])  # Yellow
boundaries_HSV_White = ([0, 0, 220], [180, 50, 255])  # White

Framecounter = 0

# keep looping on all frame
while True:
    #
    Framecounter = Framecounter + 1

    # Altitude
    White_rect_Alt = np.nan
    Blue_Alt = np.nan
    Red_Alt = np.nan
    Yellow_Alt = np.nan
    Consolidated_Alt = np.nan

    # as the detection mechanism goes over detection filter, gather center and altitude
    White_rect_center = [np.nan, np.nan]
    Blue_center = [np.nan, np.nan]
    Red_center = [np.nan, np.nan]
    Yellow_center = [np.nan, np.nan]
    White_center = [np.nan, np.nan]
    status = ""

    ##################################################################################
    # grab the current frame and initialize the status text
    (grabbed, frame) = camera.read()
    image = frame

    # check to see if we have reached the end of the
    # video
    if not grabbed:
        break

    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    ###############################################################################
    ## here is the Square detection from "Find_square.py"
    ##https://www.pyimagesearch.com/2015/05/04/target-acquired-finding-targets-in-drone-and-quadcopter-video-streams-using-python-and-opencv/
    # convert the frame to grayscale, blur it, and detect edges
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edged = cv2.Canny(blurred, 50, 150)

    # prep the output
    output = image
    # output = blurred
    # output = gray

    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ##cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = cnts[1]
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)  ##modified Epsilon 0.01 to 0.1

        # ensure that the approximated contour is "roughly" rectangular
        if 3 <= len(approx) <= 8:

            Angles = np.zeros(len(approx))
            Length = np.zeros(len(approx))
            # print(approx)
            # cv2.drawContours(output, [approx], -1, (0,0, 255), 1)
            # print( "---------------")
            # print(approx)
            # print( "++")
            # print(approx.shape)
            # print( "++")
            ##print(np.array([approx[0]]).shape)
            # print(np.sqrt((approx[0][0][0]-approx[1][0][0])**2 + (approx[0][0][1]-approx[1][0][1])**2))
            # print(np.sqrt((approx[:-2][0][0]-approx[1:][0][0])**2 + (approx[:-2][0][1]-approx[1:][0][1])**2))
            # print( "++")
            ################################
            # to compute distances, I add the first element at the end
            approx_1 = np.append(approx, np.array([approx[0]]), axis=0)
            # print(approx_1)
            for toto in range(0, len(approx_1) - 1):  # all but one
                Length[toto] = (np.sqrt((approx_1[toto][0][0] - approx_1[toto + 1][0][0]) ** 2 + (
                        approx_1[toto][0][1] - approx_1[toto + 1][0][1]) ** 2))
            # print(Length)
            ###############################
            # to compute angles, I add the last element at the begin
            # not the current index can be
            n_approx_1 = np.append(np.array([approx_1[-2]]), approx_1, axis=0)
            # print(n_approx_1)
            for toto in range(0, len(n_approx_1) - 2):  # all but last 2
                ba = n_approx_1[toto][0][:] - n_approx_1[toto + 1][0][:]
                bc = n_approx_1[toto + 2][0][:] - n_approx_1[toto + 1][0][:]
                cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
                # print(cosine_angle)
                Angles[toto] = np.arccos(cosine_angle)
            # print(np.degrees(Angles))
            found_big_dist_or_square_angle = 0
            # display it all on the output image
            # for toto in range(0,len(approx)-1):
            #	if (Length[toto]>40) and (Length[toto] < 500) and (np.degrees(Angles[toto])>80) and (np.degrees(Angles[toto])< 100) and(np.degrees(Angles[toto+1])>80) and (np.degrees(Angles[toto+1])< 100):
            #
            #		cv2.putText(output,str(Length[toto]), ((approx_1[toto][0][0]+approx_1[toto+1][0][0])/2, (approx_1[toto][0][1]+approx_1[toto+1][0][1])/2), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(0, 0, 255), 2)
            #		cv2.rectangle(output, (approx[toto][0][0] - 5, approx[toto][0][1] - 5), (approx[toto][0][0] + 5, approx[toto][0][1] + 5), (255, 0, 0), -1)
            #		cv2.rectangle(output, (approx[toto+1][0][0] - 5, approx[toto+1][0][1] - 5), (approx[toto+1][0][0] + 5, approx[toto+1][0][1] + 5), (255, 0, 0), -1)

            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspectRatio = w / float(h)

            # compute the solidity of the original contour
            area = cv2.contourArea(c)
            hullArea = cv2.contourArea(cv2.convexHull(c))
            solidity = area / float(hullArea)

            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate bounds
            keepDims = w > 100 and h > 100  # modified from 25 t 100
            keepSolidity = solidity > 0.9
            keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2

            # ensure that the contour passes all our tests
            if keepDims and keepSolidity and keepAspectRatio:
                # print(len(approx))
                # draw an outline around the target and update the status
                # text
                # cv2.drawContours(output, [approx], -1, (200,200, 200), 2)
                # status = "Gray rectangle found "
                # print(approx)
                # compute here the size of the rectangle and compute altitude
                #
                # compute the center of the contour region and draw the
                # crosshairs
                M = cv2.moments(approx)
                (cX, cY) = (int(M["m10"] // M["m00"]), int(M["m01"] // M["m00"]))
                White_rect_center = (cX, cY)

        # Altitude
        # White_rect_Alt = White_rect_size/np.tan(b*CamDegPerPix)

    ## end of the Square detection from "Find_square.py"
    ###############################################################################

    ##############################################################################
    # just doing all masks

    # Black
    # (lower, upper) = boundaries_HSV_Black
    # lower = np.array(lower, dtype = "uint8")
    # upper = np.array(upper, dtype = "uint8")
    # mask_Black = cv2.inRange(hsv, lower, upper)
    # blue
    (lower, upper) = boundaries_HSV_Blue
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_Blue = cv2.inRange(hsv, lower, upper)
    # Red
    (lower, upper) = boundaries_HSV_Red_h
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_Red_h = cv2.inRange(hsv, lower, upper)

    (lower, upper) = boundaries_HSV_Red_l
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_Red_l = cv2.inRange(hsv, lower, upper)
    mask_Red = cv2.add(mask_Red_l, mask_Red_h)

    # yellow
    (lower, upper) = boundaries_HSV_Yellow
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_Yellow = cv2.inRange(hsv, lower, upper)
    # white
    (lower, upper) = boundaries_HSV_White
    lower = np.array(lower, dtype="uint8")
    upper = np.array(upper, dtype="uint8")
    mask_White = cv2.inRange(hsv, lower, upper)

    ##cv2.imshow("images",output )
    ##cv2.waitKey(0)

    # remove all the blobs in the mask by morpho close
    kernel_Black = np.ones((20, 20), np.uint8)  # definition of the Karnel that is used to close
    # karnel is big (50,50) because we have a big image to be reduced if we have a smaller image

    kernel = np.ones((5, 5), np.uint8)

    # morphed_mask_Black = cv2.morphologyEx(mask_Black, cv2.MORPH_CLOSE, kernel_Black)
    morphed_mask_Blue = cv2.morphologyEx(mask_Blue, cv2.MORPH_CLOSE, kernel)
    morphed_mask_Red = cv2.morphologyEx(mask_Red, cv2.MORPH_CLOSE, kernel)
    morphed_mask_Yellow = cv2.morphologyEx(mask_Yellow, cv2.MORPH_OPEN, kernel)
    morphed_mask_White = cv2.morphologyEx(mask_White, cv2.MORPH_OPEN, kernel)

    # cv2.imshow("images", mask_Black)
    # cv2.waitKey(0)
    # cv2.imshow("images", morphed_mask_Black)
    # cv2.waitKey(0)
    # cv2.imshow("images", mask_Blue)
    # cv2.waitKey(0)
    # cv2.imshow("images",morphed_mask_Blue)
    # cv2.waitKey(0)
    # cv2.imshow("images",mask_Red)
    # cv2.waitKey(0)
    # cv2.imshow("images", morphed_mask_Red)
    # cv2.waitKey(0)
    # cv2.imshow("images",mask_Yellow)
    # cv2.waitKey(0)
    # cv2.imshow("images", morphed_mask_Yellow)
    # cv2.waitKey(0)
    # cv2.imshow("images", mask_White)
    # cv2.waitKey(0)
    # cv2.imshow("images", morphed_mask_White)
    # cv2.waitKey(0)

    ##############################################################################
    # Detect blue circle (contour) in the picture
    cnts = []
    # find contours in the edge map
    cnts = cv2.findContours(morphed_mask_Blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ##cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = cnts[1]
    # print(len(cnts))
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)  ##modified Epsilon 0.01 to 0.1

        # ensure that the approximated contour is "roughly" rectangular
        if len(approx) >= 3 and len(approx) <= 8:

            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspectRatio = w / float(h)
            # compute the solidity of the original contour
            area = cv2.contourArea(c)
            hullArea = cv2.contourArea(cv2.convexHull(c))
            solidity = area / float(hullArea)
            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate  bounds
            keepDims = w > 25 and h > 25  # modified from 25 t 100
            keepSolidity = solidity > 0.9
            keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2

            # ensure that the contour passes all our tests
            if (keepDims and keepSolidity and keepAspectRatio):
                # print(len(approx))
                # draw an outline around the target and update the status
                # text
                # cv2.drawContours(output, [c], -1, (225,0, 0), 2)
                sizeofBlueContour = np.max(np.amax(c, axis=0) - np.min(c, axis=0))
                # status = status +" Blue contour found :" + str(sizeofBlueContour) + "pix. = "
                # status = status + str(Blue_diam/np.tan(sizeofBlueContour*CamDegPerPix))
                Blue_center = np.mean(c, axis=0)
                # compute here the size of the rectangle and compute altitude
                ## Altitude
                Blue_Alt = Blue_diam / np.tan((np.max(np.amax(c, axis=0) - np.min(c, axis=0))) * CamDegPerPix)

    #
    # compute the center of the contour region and draw the
    # crosshairs
    # M = cv2.moments(approx)
    # (cX, cY) = (int(M["m10"] // M["m00"]), int(M["m01"] // M["m00"]))
    # (startX, endX) = (int(cX - (w * 0.1)), int(cX + (w * 0.1)))
    # (startY, endY) = (int(cY - (h * 0.1)), int(cY + (h * 0.1)))
    # cv2.line(output, (startX, cY), (endX, cY), (200,200, 255), 2)
    # cv2.line(output, (cX, startY), (cX, endY), (200,200, 255), 2)

    # end of detect the circle in the Blue mask
    ###############################################################################

    ##############################################################################
    # Detect Red circle (contour) in the picture

    cnts = []
    # find contours in the edge map
    cnts = cv2.findContours(morphed_mask_Red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ##cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = cnts[1]
    # print(len(cnts))
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)  ##modified Epsilon 0.01 to 0.1

        # ensure that the approximated contour is "roughly" rectangular
        if len(approx) >= 3 and len(approx) <= 8:

            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspectRatio = w / float(h)
            # compute the solidity of the original contour
            area = cv2.contourArea(c)
            hullArea = cv2.contourArea(cv2.convexHull(c))
            solidity = area / float(hullArea)
            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate  bounds
            keepDims = w > 25 and h > 25  # modified from 25 t 100
            keepSolidity = solidity > 0.9
            keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2

            # ensure that the contour passes all our tests
            if (keepDims and keepSolidity and keepAspectRatio):
                # print(len(approx))
                # draw an outline around the target and update the status
                # text
                # cv2.drawContours(output, [c], -1, (0,0, 255), 2)
                SizeOfRedContour = np.max(np.amax(c, axis=0) - np.min(c, axis=0))
                # status = status +" Red contour found :" + str(SizeOfRedContour) + "pix. "
                # status = status + str( Red_diam/np.tan(SizeOfRedContour*CamDegPerPix))
                Red_center = np.mean(c, axis=0)
                # compute here the size of the rectangle and compute altitude
                ## Altitude
                Red_Alt = Red_diam / np.tan((np.max(np.amax(c, axis=0) - np.min(c, axis=0))) * CamDegPerPix)

    # end of detect the circle in the Red mask
    ###############################################################################

    ##############################################################################
    # Detect Yellow circle contour in the picture

    # detect circles in the image

    cnts = []
    # find contours in the edge map
    cnts = cv2.findContours(morphed_mask_Yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ##cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = cnts[1]
    # print(len(cnts))
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)  ##modified Epsilon 0.01 to 0.1

        # ensure that the approximated contour is "roughly" rectangular
        if len(approx) >= 3 and len(approx) <= 8:

            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspectRatio = w / float(h)
            # compute the solidity of the original contour
            area = cv2.contourArea(c)
            hullArea = cv2.contourArea(cv2.convexHull(c))
            solidity = area / float(hullArea)
            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate  bounds
            keepDims = w > 25 and h > 25  # modified from 25 t 100
            keepSolidity = solidity > 0.9
            keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2

            # ensure that the contour passes all our tests
            if (keepDims and keepSolidity and keepAspectRatio):
                # print(len(approx))
                # draw an outline around the target and update the status
                # text
                # cv2.drawContours(output, [c], -1, (0,255, 255), 2)
                # status = status +" Yellow contour found :" + str(np.max(np.amax(c, axis=0) - np.min(c, axis=0))) + "pix. "
                Yellow_center = np.mean(c, axis=0)
                ## Altitude
                Yellow_Alt = Yellow_diam / np.tan((np.max(np.amax(c, axis=0) - np.min(c, axis=0))) * CamDegPerPix)

    # end of detect the circle in the Yellow mask
    ###############################################################################

    ##############################################################################
    # Detect White circle(instead of the yellow) or square contour in the picture

    # detect circles in the image

    cnts = []
    # find contours in the edge map
    cnts = cv2.findContours(morphed_mask_White, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ##cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = cnts[1]
    # print(len(cnts))
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.1 * peri, True)  ##modified Epsilon 0.01 to 0.1

        # ensure that the approximated contour is "roughly" rectangular
        if len(approx) >= 3 and len(approx) <= 8:

            # compute the bounding box of the approximated contour and
            # use the bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspectRatio = w / float(h)
            # compute the solidity of the original contour
            area = cv2.contourArea(c)
            hullArea = cv2.contourArea(cv2.convexHull(c))
            solidity = area / float(hullArea)
            # compute whether or not the width and height, solidity, and
            # aspect ratio of the contour falls within appropriate  bounds
            keepDims = w > 25 and h > 25  # modified from 25 t 100
            keepSolidity = solidity > 0.9
            keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2

            # ensure that the contour passes all our tests
            if (keepDims and keepSolidity and keepAspectRatio):
                # print(len(approx))
                # draw an outline around the target and update the status
                # text
                # cv2.drawContours(output, [c], -1, (255,255, 255), 2)
                # status = status +" White contour found "
                White_center = np.mean(c, axis=0)
        # print(approx)
        # compute here the size of the rectangle and compute altitude

    # end of detect the circle in the Yellow mask
    ###############################################################################

    # compute the mean of the hight, for none - zero element
    alt = np.nanmean([White_rect_Alt, Blue_Alt, Red_Alt, Yellow_Alt])
    if np.isnan(alt):
        alt_str = "Alt: Unknown"
    else:
        alt_str = "Alt: " + '|' * int(alt / 100) + " " + str(alt)

    # compute the mean of the center, for none -zero element

    # print("  .....   ")
    # print(str([White_rect_center ,Blue_center, Red_center, Yellow_center]))

    ##center = np.nanmean([White_rect_center ,Blue_center, Red_center, Yellow_center],axis=0)
    # if not np.isnan(Red_center).any():
    #	print(str(center))

    # compute the sring output

    cv2.putText(output, alt_str, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # show the frame and record if a key is pressed
    # cv2.imshow("Frame", output)

    key = cv2.waitKey(1) & 0xFF

    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
