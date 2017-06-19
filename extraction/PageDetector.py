#!/usr/bin/env python
# coding: utf-8

"""
    Extraction.PageDetector
    ============================
    Detect page number and oritentation to extract features
    properly.

    _copyright_ = 'Copyright (c) 2017 Vm.C.', see AUTHORS for more details
    _license_ = GNU General Public License, see LICENSE for more details
"""

import numpy as np
import cv2
from matplotlib import pyplot as plt
import math
from os import listdir
from os.path import isfile, join

# Global settings ####
dx = [-1, 1, 0, 0]
dy = [0, 0, -1, 1]


# Function definition ####
def sortSquareCenters(L):
    if len(L) != 4:
        print('wtf, there are not 4 centers: ', len(L))
    L = sorted(L, key=lambda x: x[0] + x[1])
    return L


class ShapeDetector:
    def __init__(self):
        pass

    def detect(self, c):
        # initialize the shape name and approximate the contour
        shape = "unidentified"
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)

        # if the shape is a triangle, it will have 3 vertices
        if len(approx) == 3:
            shape = "triangle"

        # if the shape has 4 vertices, it is either a square or
        # a rectangle
        elif len(approx) == 4:
            # compute the bounding box of the contour and use the
            # bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            ar = w / float(h)

            # a square will have an aspect ratio that is approximately
            # equal to one, otherwise, the shape is a rectangle
            shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

        # if the shape is a pentagon, it will have 5 vertices
        elif len(approx) == 5:
            shape = "pentagon"

        # otherwise, we assume the shape is a circle
        else:
            shape = "circle"

        # return the name of the shape
        return shape


def getSingleSquare(image_original, corner, iterations=1):
    ret3, th3 = cv2.threshold(image_original, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thIMor = cv2.morphologyEx(th3, cv2.MORPH_CLOSE, se)
    maxShape = max(image_original.shape)

    k_left = int(25)  # componentes >= 4
    k_right = int(25)  # componentes < 4

    while k_left + +1 < k_right:
        k = (k_left + k_right) // 2
        onlySquares = cv2.erode(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)), iterations=1)
        onlySquares = cv2.dilate(onlySquares, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)), iterations=1)
        # Connected compoent labling
        stats = cv2.connectedComponentsWithStats(onlySquares, connectivity=4)
        print('with ', k, ' we got: ', stats[0])
        print('with ',k,' got: ', stats[0])
        if stats[0] >= 2:
            k_left = k
        else:
            k_right = k


        # plt.subplot(1, 2, 1), plt.imshow(onlySquares, 'gray'), plt.title(str(k) + '::' + str(stats[0]))
        # plt.subplot(1, 2, 2), plt.imshow(thIMor, 'gray'), plt.title('th3')
        # plt.show()

    print('FInally: ', k_left, k_right)
    print('k_left final: ', k_left)
    thIMor = cv2.erode(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k_left, k_left)), iterations=1)
    thIMor = cv2.dilate(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k_left, k_left)), iterations=1)
    backtorgb = cv2.cvtColor(image_original, cv2.COLOR_GRAY2RGB)
    cnts = cv2.findContours(thIMor.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[1] #if imutils.is_cv2() else cnts[1]
    sd = ShapeDetector()
    ratio = 1.0
    squares_found = []
    for c in cnts:
        # compute the center of the contour, then detect the name of the
        # shape using only the contour
        M = cv2.moments(c)
        cX = int((M["m10"] / M["m00"]) * ratio)
        cY = int((M["m01"] / M["m00"]) * ratio)
        # shape = sd.detect(c)
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        (x, y, w, h) = cv2.boundingRect(approx)
        ar = w / float(h)
        if 26 < h < 33 and 26 < w < 33:
            squares_found.append(c)
        print('wxh = squares: ',w,h)

        # multiply the contour (x, y)-coordinates by the resize ratio,
        # then draw the contours and the name of the shape on the image


    if len(squares_found) != 1:
        return None
    c = squares_found[0]
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    (x, y, w, h) = cv2.boundingRect(approx)
    c = c.astype("float")
    c *= ratio
    c = c.astype("int")
    cv2.drawContours(backtorgb, [c], -1, (0, 255, 0), 2)

    W = w
    H = h
    Top = y
    Left = x
    corners = []
    corners.append([Top + H, Left + W])
    corners.append([Top, Left + W])
    corners.append([Top + H, Left])
    corners.append([Top, Left])
    print('corners: ',corners)
    # plt.subplot(2, 1, 1), plt.imshow(backtorgb,'gray'), plt.title('backtorgb')
    # plt.subplot(2, 1, 2), plt.imshow(image_original, 'gray'), plt.title('image_original')
    # plt.show()

    # if iterations <= 1:
    #     print('it will return ', k_left)
    #     return k_left, [corners[corner][1],corners[corner][0]]
    # print('it will return ', k_left)
    return (w+h)//2, [corners[corner][0], corners[corner][1]]
    # rows,cols = image_original.shape
    # L = (k_left+9)//2
    # i_1 = max(0,c[0]-L)
    # i_2 = min(c[0]+L, rows)
    # j_1 = max(0,c[1]-L)
    # j_2 = min(c[1]+L, cols)
    # ROI = image_original[i_1:i_2, j_1:j_2]
    #
    # new_k_left, corner = getSingleSquare(ROI, corner, iterations=1)
    # return new_k_left, [corner[0]+i_1,corner[1]+j_1]


def getSquares_newAlgorithm(image_original):
    rows, cols = image_original.shape


    percent_top = 0.1
    percent_bot = 0.1

    delta_bottom = int(rows *(1- percent_bot))
    top = image_original[0:int(rows*percent_top),:]
    bottom = image_original[delta_bottom:, :]

    A = getSingleSquare(top[:, : cols // 2], 0, iterations=2)
    B = getSingleSquare(bottom[:, : cols // 2], 1, iterations=2)
    X = getSingleSquare(top[:, cols // 2:], 2, iterations=2)
    Y = getSingleSquare(bottom[:, cols // 2:], 3, iterations=2)

    if A is None or B is None or X is None or Y is None:
        return None
    P = [A[0], B[0], X[0], Y[0]]
    # print('P: ', P)
    k = max(P)
    L = k
    A = A[1]
    B = B[1][0] + delta_bottom, B[1][1]
    X = X[1][0], X[1][1] + cols // 2
    Y = Y[1][0] + delta_bottom, Y[1][1] + cols // 2

    cA = A[0] - L, A[1] - L
    cB = B[0] + L, B[1] - L
    cX = X[0] - L, X[1] + L
    cY = Y[0] + L, Y[1] + L

    cA = cA[1], cA[0]
    cB = cB[1], cB[0]
    cX = cX[1], cX[0]
    cY = cY[1], cY[0]
    centers = [cA, cB, cX, cY]
    centers = sortSquareCenters(centers)
    print(centers)
    plt.imshow(image_original, 'gray')
    plt.show()
    return centers,k


def getSquares(image_original):
    """Detecta la orientación de la imagen y la orienta.
    Args:
        image_original: Original image.
    Returns:
        cosl: ....
    """
    #
    # ret3, th3 = cv2.threshold(image_original, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    #
    # se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
    # thIMor = cv2.morphologyEx(th3, cv2.MORPH_CLOSE, se)
    #
    # maxShape = max(image_original.shape)
    # toleranciaCuadrado = int(round(20 * maxShape / 1750))
    #
    # print('ToleranciaCuadrado: ', toleranciaCuadrado)
    # k_left = int(round(5 * maxShape / 1750))  # componentes >= 4
    # k_right = int(round(80 * maxShape / 1750))  # componentes < 4
    #
    # while k_left + +1 < k_right:
    #     k = (k_left + k_right) // 2
    #     onlySquares = cv2.erode(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)), iterations=1)
    #     onlySquares = cv2.dilate(onlySquares, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)), iterations=1)
    #     # Connected compoent labling
    #     stats = cv2.connectedComponentsWithStats(onlySquares, connectivity=8)
    #     print('with ', k, ' we got: ', stats[0])
    #     if stats[0] >= 5:
    #         k_left = k
    #     else:
    #         k_right = k
    #         # plt.imshow(onlySquares), plt.title(str(k)+'::'+str(stats[0]))
    #         # plt.show()
    #
    # print('k_left final: ', k_left)
    # thIMor = cv2.erode(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k_left, k_left)), iterations=1)
    # thIMor = cv2.dilate(thIMor, cv2.getStructuringElement(cv2.MORPH_RECT, (k_left, k_left)), iterations=1)
    # # Connected component labling
    # stats = cv2.connectedComponentsWithStats(thIMor, connectivity=8)
    # num_labels = stats[0]
    # print('num labels:', num_labels)
    # labels = stats[1]
    # labelStats = stats[2]
    # centroides = stats[3]
    # # We expect the connected component of the numbers to be more or less with a constats ratio
    # # So we find the medina ratio of all the comeonets because the majorty of connected compoent are numbers
    # cosl = []
    # edgesLength = []
    # for label in range(num_labels):
    #     connectedCompoentWidth = labelStats[label, cv2.CC_STAT_WIDTH]
    #     connectedCompoentHeight = labelStats[label, cv2.CC_STAT_HEIGHT]
    #     area = labelStats[label, cv2.CC_STAT_AREA]
    #     print(area, connectedCompoentHeight * connectedCompoentHeight, connectedCompoentHeight, connectedCompoentWidth)
    #     if abs(connectedCompoentHeight - connectedCompoentWidth) < toleranciaCuadrado \
    #             and connectedCompoentWidth * connectedCompoentHeight * 0.6 < area:
    #         cosl.append((int(round(centroides[label][0])), int(round(centroides[label][1])),  # ,
    #                      connectedCompoentWidth, connectedCompoentHeight))
    #         # min(connectedCompoentHeight , connectedCompoentWidth)])
    #         edgesLength.append(min(connectedCompoentHeight, connectedCompoentWidth) // 2)
    #
    # delta = sum(edgesLength) // 4
    # cosl = sortSquareCenters(cosl)
    # cosl[0] = (cosl[0][0] - cosl[0][2] // 2, cosl[0][1] - cosl[0][3] // 2)
    # if cosl[1][0] < cosl[1][1]:
    #     cosl[1] = (cosl[1][0] - cosl[1][2] // 2, cosl[1][1] + cosl[1][3] // 2)
    #     cosl[2] = (cosl[2][0] + cosl[2][2] // 2, cosl[2][1] - cosl[2][3] // 2)
    # else:
    #     cosl[1] = (cosl[1][0] + cosl[1][2] // 2, cosl[1][1] - cosl[1][3] // 2)
    #     cosl[2] = (cosl[2][0] - cosl[2][2] // 2, cosl[2][1] + cosl[2][3] // 2)
    #
    # cosl[3] = (cosl[3][0] + cosl[3][2] // 2, cosl[3][1] + cosl[3][3] // 2)
    # print('cosl', cosl)

    center_of_squares,var = getSquares_newAlgorithm(image_original)
    # print('new algorithm: ', center_of_squares)
    # print('old algorithm: ', cosl)
    # plt.subplot(1, 3, 1), plt.imshow(image_original, 'gray')
    # plt.subplot(1, 3, 2), plt.imshow(th3, 'gray')
    # plt.subplot(1, 3, 3), plt.imshow(thIMor, 'gray')
    #
    # plt.show()
    # return cosl
    return center_of_squares,var


def enderezarImagen(image):
    """Detecta la orientación de la imagen y la orienta.
    Args:
        image: Original image.
    Returns:
        rotatedImg: Rotated image.
    """
    rows,cols = image.shape
    if rows < cols:
        image = cv2.transpose(image)

    # rows, cols = image.shape
    #
    # percent_top = 0.1
    # percent_bot = 0.1
    # top = image[0:int(rows*percent_top),:]
    # bottom = image[int(rows *(1- percent_bot)):, :]
    #
    #
    # plt.subplot(2,1,1), plt.imshow(top, 'gray'), plt.title('top')
    # plt.subplot(2, 1, 2), plt.imshow(bottom, 'gray'), plt.title('bottom')
    # plt.show()


    squaresCenters, _ = getSquares(image)
    if len(squaresCenters) != 4:
        raise Exception('There is no 4 centers')
    print('First squares: ', squaresCenters)
    dI = squaresCenters[1][0] - squaresCenters[0][0]
    dJ = squaresCenters[1][1] - squaresCenters[0][1]
    theta = np.arctan2(dJ, dI)
    thetaDegrees = theta * 180 / np.pi
    (oldY, oldX) = image.shape
    M = cv2.getRotationMatrix2D(center=(oldX / 2, oldY / 2), angle=thetaDegrees,
                                scale=1)  # rotate about center of image.
    newX, newY = oldX * 1, oldY * 1
    r = np.deg2rad(thetaDegrees)
    newX, newY = (abs(np.sin(r) * newY) + abs(np.cos(r) * newX), abs(np.sin(r) * newX) + abs(np.cos(r) * newY))

    # the warpAffine function call, below, basically works like this:
    # 1. apply the M transformation on each pixel of the original image
    # 2. save everything that falls within the upper-left "dsize" portion of the resulting image.

    # Find the translation that moves the result to the center of that region.
    (tx, ty) = ((newX - oldX) / 2, (newY - oldY) / 2)
    M[0, 2] += tx  # third column of matrix holds translation, which takes effect after rotation.
    M[1, 2] += ty

    rotatedImg = cv2.warpAffine(image, M, dsize=(int(newX), int(newY)))
    return rotatedImg


def getCenterZone(img, center, delta):
    """ .........
    Args:
        img: Original image.
        center: Center of ....
        delta: .....
    Returns:
        centerZone: .........
    """
    K = img[center[1] - delta:center[1] + delta, center[0] - delta:center[0] + delta].copy()
    # K = img[squaresCenters[0][1]:squaresCenters[3][1],squaresCenters[0][0]:squaresCenters[3][0]].copy()
    ret3, th3 = cv2.threshold(K, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)


    # ret3, th3 = cv2.threshold(K, 240, 255, cv2.THRESH_BINARY_INV)
    K = cv2.dilate(th3, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=1)

    centerZone = cv2.resize(K, (750, 750))
    centerZone[centerZone > 125] = 255
    centerZone[centerZone <= 125] = 0
    # cv2.imwrite('resources/s100_center_inversa_2.png',centerZone)
    return centerZone


def getPercentMatched(baseImage, testImage):
    if baseImage.shape != testImage.shape:
        print('shapeBase ', baseImage.shape)
        print('testBase ', testImage.shape)
        return 0
    onlyMatched = cv2.bitwise_and(baseImage, testImage)
    nonZeroDB = cv2.countNonZero(baseImage)
    nonZeroAND = cv2.countNonZero(onlyMatched)
    return nonZeroAND / nonZeroDB


def percentPage1Normal(centerZone):
    centerZone_Base = cv2.imread('resources/s100_center_normal_1.png', 0)
    return getPercentMatched(centerZone_Base, centerZone)


def percentPage2Normal(centerZone):
    centerZone_Base = cv2.imread('resources/s100_center_normal_2.png', 0)
    return getPercentMatched(centerZone_Base, centerZone)


def percentPage1Inversa(centerZone):
    centerZone_Base = cv2.imread('resources/s100_center_inversa_1.png', 0)
    return getPercentMatched(centerZone_Base, centerZone)


def percentPage2Inversa(centerZone):
    centerZone_Base = cv2.imread('resources/s100_center_inversa_2.png', 0)
    return getPercentMatched(centerZone_Base, centerZone)


def detectPage(img):
    """Detecta el número de la página.
    Args:
        img: Imagen orientada.
    Returns:
        _: Rotated image.
    """
    squaresCenters, L_edge_square = getSquares(img)
    print('Second squares: ', squaresCenters)
    if len(squaresCenters) != 4:
        raise Exception('There is no 4 centers')
    TL_0 = squaresCenters[0]
    BR_0 = squaresCenters[0][0] + L_edge_square, squaresCenters[0][1] + L_edge_square

    TL_3 = squaresCenters[3][0] - L_edge_square, squaresCenters[3][1] - L_edge_square
    BR_3 = squaresCenters[3]

    colsToAddLeft = max(0, -TL_0[0])
    colsToAddRight = max(0, BR_3[0] - img.shape[1])

    rowsToAddTop = max(0, -TL_0[1])
    rowsToAddBottom = max(0, BR_3[1] - img.shape[0])

    completeImage = np.append(np.full((img.shape[0], colsToAddLeft), 255, dtype=img.dtype), img, axis=1)
    #print('shape after adding: ', colsToAddLeft, ' cols to left ', completeImage.shape)
    completeImage = np.append(completeImage, np.full((img.shape[0], colsToAddRight), 255, dtype=img.dtype), axis=1)
    #print('shape after adding: ', colsToAddRight, ' cols to right  ', completeImage.shape)

    completeImage = np.append(np.full((rowsToAddTop, completeImage.shape[1]), 255, dtype=img.dtype), completeImage,
                              axis=0)
    #print('shape after adding: ', rowsToAddTop, ' rows to top  ', completeImage.shape)

    completeImage = np.append(completeImage, np.full((rowsToAddBottom, completeImage.shape[1]), 255, dtype=img.dtype),
                              axis=0)

    img = completeImage.copy()

    sq0 = squaresCenters[0][0] + colsToAddLeft, squaresCenters[0][1] + rowsToAddTop
    sq1 = squaresCenters[1][0] + colsToAddLeft, squaresCenters[1][1] + rowsToAddTop
    sq2 = squaresCenters[2][0] + colsToAddLeft, squaresCenters[2][1] + rowsToAddTop
    sq3 = squaresCenters[3][0] + colsToAddLeft, squaresCenters[3][1] + rowsToAddTop

    squaresCenters = [sq0, sq1, sq2, sq3]
    print('shape after adding: ', rowsToAddBottom, ' rows to bottom  ', completeImage.shape)
    # supuestamente esta horizontal
    distCols = squaresCenters[3][1] - squaresCenters[0][1]
    distRows = squaresCenters[3][0] - squaresCenters[0][0]

    print('Ratio: ', (distRows / distCols))
    sumX = 0
    sumY = 0
    for sqCenters in squaresCenters:
        sumX += sqCenters[0]
        sumY += sqCenters[1]

    delta = distCols // 4
    center = (sumX // 4-delta//4, sumY // 4-delta//2)

    centerZone = getCenterZone(img, center, delta)
    newImage = img[squaresCenters[0][1]:squaresCenters[3][1], squaresCenters[0][0]:squaresCenters[3][0]]
    # plt.subplot(1,2,1), plt.imshow(centerZone,'gray'), plt.title('centerZone')
    # plt.subplot(1, 2, 2), plt.imshow(newImage, 'gray'), plt.title('newImage')
    # plt.show()
    detectors = []
    percent = []
    page = []
    detectors.append(percentPage1Normal)
    page.append((1, 0))
    detectors.append(percentPage2Normal)
    page.append((2, 0))
    detectors.append(percentPage1Inversa)
    page.append((1, 1))
    detectors.append(percentPage2Inversa)
    page.append((2, 1))

    for detector in detectors:
        percent.append(detector(centerZone))
    print('Percents: ', percent)
    max_indx, max_value = max(enumerate(percent), key=lambda p: p[1])
    newImage = img[squaresCenters[0][1]:squaresCenters[3][1], squaresCenters[0][0]:squaresCenters[3][0]]
    return (newImage, page[max_indx])

if __name__ == '__main__':
    imagen_test = cv2.imread('/home/vmchura/Documents/s100/handwritten/input/pag1.png',0)
    imagen_test = cv2.resize(imagen_test, (1240,1754))

    rotatedImg = enderezarImagen(imagen_test)


    newImage, page = detectPage(rotatedImg)
    print('La pagina es: ',page)
    plt.subplot(1, 2, 1), plt.imshow(imagen_test, 'gray'), plt.title('original')
    plt.subplot(1, 2, 2), plt.imshow(newImage, 'gray'), plt.title('detected')
    plt.show()
    # onlyfiles = [f for f in listdir('../input/tmp') if isfile(join('../input/tmp', f))]
    # for filename in onlyfiles:
    #     if 'im1_1.png' in filename:
    #         img = cv2.imread(join('../input/tmp',filename), 0)
    #         print('Processing: ',filename)
    #         img = enderezarImagen(img)
    #         squaresCenters,k = getSquares(img)
    #         TL_0 = squaresCenters[0]
    #         BR_0 = squaresCenters[0][0] + k, squaresCenters[0][1] + k
    #
    #         TL_3 = squaresCenters[3][0] - k, squaresCenters[3][1] - k
    #         BR_3 = squaresCenters[3]
    #
    #         print('BR_3: ',BR_3)
    #         print('img.shape: ', img.shape)
    #         colsToAddLeft = max(0, -TL_0[0])
    #         colsToAddRight = max(0, BR_3[0] - img.shape[1])
    #
    #         rowsToAddTop = max(0, -TL_0[1])
    #         rowsToAddBottom = max(0, BR_3[1] - img.shape[0])
    #         print('shape of image', img.shape)
    #         completeImage = np.append(np.full((img.shape[0],colsToAddLeft),255,dtype=img.dtype),img, axis=1)
    #         print('shape after adding: ',colsToAddLeft,' cols to left ', completeImage.shape)
    #         completeImage = np.append(completeImage,np.full((img.shape[0],colsToAddRight),255, dtype=img.dtype), axis=1)
    #         print('shape after adding: ', colsToAddRight, ' cols to right  ', completeImage.shape)
    #
    #         completeImage = np.append(np.full((rowsToAddTop, completeImage.shape[1]), 255,dtype=img.dtype), completeImage, axis=0)
    #         print('shape after adding: ', rowsToAddTop, ' rows to top  ', completeImage.shape)
    #
    #         completeImage = np.append(completeImage,np.full((rowsToAddBottom, completeImage.shape[1]),255, dtype=img.dtype),  axis=0)
    #         print('shape after adding: ', rowsToAddBottom, ' rows to bottom  ', completeImage.shape)
    #
    #
    #         print('To Add cols: ', colsToAddLeft,colsToAddRight)
    #         print('To Add rows: ', rowsToAddTop, rowsToAddTop)
    #
    #         TL_0 = TL_0[0] + colsToAddLeft, TL_0[1] + rowsToAddTop
    #         BR_0 = BR_0[0] + colsToAddLeft, BR_0[1] + rowsToAddTop
    #
    #         TL_3 = TL_3[0] + colsToAddLeft, TL_3[1] + rowsToAddTop
    #         BR_3 = BR_3[0] + colsToAddLeft, BR_3[1] + rowsToAddTop
    #
    #
    #
    #         backtorgb = cv2.cvtColor(completeImage, cv2.COLOR_GRAY2RGB)
    #
    #         cv2.rectangle(backtorgb, TL_0, BR_0, (0, 255, 0), 2)
    #         cv2.rectangle(backtorgb, TL_3, BR_3, (0, 255, 0), 2)
		#
    #
    #         cv2.imwrite(join('../output',filename),backtorgb)
