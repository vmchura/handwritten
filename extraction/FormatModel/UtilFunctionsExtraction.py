#!/usr/bin/env python
# coding: utf-8

"""
    Extraction.UtilFunctions
    =============================

    Classes, .......

    _copyright_ = 'Copyright (c) 2017 Vm.C.', see AUTHORS for more details
    _license_ = GNU General Public License, see LICENSE for more details
"""
import statistics

import numpy as np
import cv2
from matplotlib import pyplot as plt
import math
import modeling

from extraction.FormatModel import UtilDebug

dx = [-1, 1, 0, 0]
dy = [0, 0, -1, 1]


def expandOnlyIntersections(BinaryOriginal, globalMask):
    V = np.zeros(BinaryOriginal.shape, dtype=bool)
    intersectionOfMask = cv2.bitwise_and(BinaryOriginal, globalMask)
    Q = [(1, 1)] * (BinaryOriginal.shape[0] * BinaryOriginal.shape[0])
    indxHead = 0
    indxTail = 0
    for i in range(BinaryOriginal.shape[0]):
        for j in range(BinaryOriginal.shape[1]):
            if intersectionOfMask[i, j] > 0:
                Q[indxTail] = (i, j)
                indxTail += 1
                V[i, j] = True
                # intersectionOfMask[i,j] = 0
    intersectionOfMask[intersectionOfMask >= 0] = 0  # OFF , 0 es ON
    while indxHead < indxTail:
        (i, j) = Q[indxHead]
        indxHead += 1
        intersectionOfMask[i, j] = 255
        for k in range(0, 4):
            ni = i + dx[k]
            nj = j + dy[k]
            if 0 <= ni < BinaryOriginal.shape[0] and 0 <= nj < BinaryOriginal.shape[1]:
                if BinaryOriginal[ni, nj] > 0 and not V[ni, nj]:
                    Q[indxTail] = (ni, nj)
                    indxTail += 1
                    V[ni, nj] = True
    return intersectionOfMask


def getPointProportion(A, B, a, b):
    px = (A[0] * b + B[0] * a) / (a + b)
    py = (A[1] * b + B[1] * a) / (a + b)
    return (int(px), int(py))


def closestNonZero(img, p, maxSize=21):
    if img[p[0], p[1]] > 0:
        return p
    if img[p[0], p[1]] > 0:
        return p
    dx_step = [-1, 0, 1, 0]
    dy_step = [0, 1, 0, -1]
    currentK = 0
    copyP = p
    for k in range(1, maxSize):
        for twice in range(0, 2):
            for times in range(0, k):
                p = (p[0] + dx_step[currentK]), (p[1] + dy_step[currentK])
                if p[0] >= 0 and p[1] >= 0 and p[0] < img.shape[0] and p[1] < img.shape[1] and img[p[0], p[1]] > 0:
                    # print('found: ', p)
                    return p
            currentK = (currentK + 1) % 4
    return copyP


def filterSingleCharacter_new(letter_original_and_mask):
    letter_original = letter_original_and_mask[0]
    mask = letter_original_and_mask[1][0]
    threshold_border = letter_original_and_mask[1][1]
    img = letter_original.copy()
    img[img > 230] = 255
    ret3, resaltado = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    rows, cols = resaltado.shape

    # creating border
    borde = resaltado.copy()
    borde[borde >= 0] = 255
    gb = 2  # grosor del borde
    borde[gb:borde.shape[0] - gb, gb:borde.shape[1] - gb] = 0
    borde[img < threshold_border] = 0
    pppb = cv2.bitwise_and(resaltado, borde)  # posible_pre_printed_borders
    wob = cv2.bitwise_and(resaltado, cv2.bitwise_not(borde))  # sin borders
    dilatado = cv2.dilate(wob, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=1)
    pdof = cv2.bitwise_and(dilatado, pppb)  # parte de la letra borrada
    result = cv2.bitwise_or(wob, pdof)

    onlyMatch = cv2.morphologyEx(result, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))
    # onlyMatch = expandOnlyIntersections(result, mask)
    onlyMatch = result

    stats = cv2.connectedComponentsWithStats(onlyMatch, connectivity=8)
    num_labels = stats[0]
    labels = stats[1]
    labelStats = stats[2]
    centroides = stats[3]
    # We expect the connected component of the numbers to be more or less with a constats ratio
    # So we find the medina ratio of all the comeonets because the majorty of connected compoent are numbers
    cosl = []
    edgesLength = []
    debugThisCharacter = False

    for label in range(num_labels):

        Width = labelStats[label, cv2.CC_STAT_WIDTH]
        Height = labelStats[label, cv2.CC_STAT_HEIGHT]
        area = labelStats[label, cv2.CC_STAT_AREA]
        # print(area, connectedCompoentHeight * connectedCompoentHeight, connectedCompoentHeight, connectedCompoentWidth)
        deleteGroup = False
        if centroides[label][0] < 0.1 * onlyMatch.shape[1] or \
                        centroides[label][1] < 0.1 * onlyMatch.shape[0] or \
                        centroides[label][0] > 0.9 * onlyMatch.shape[1] or \
                        centroides[label][1] > 0.9 * onlyMatch.shape[0]:
            if Width * Height * 0.5 < area:
                deleteGroup = True

        if area < 4:
            deleteGroup = True

        if deleteGroup:
            Left = labelStats[label, cv2.CC_STAT_LEFT]
            Top = labelStats[label, cv2.CC_STAT_TOP]
            Right = Left + Width
            Bottom = Top + Height
            onlyMatch[Top:Bottom, Left:Right] = 0
            debugThisCharacter = False
            print('centroide: ', centroides[label])

    img_copy = img.copy()

    img_copy[onlyMatch < 125] = 255  # lo que es negro en only match, ahora sera blanco en img_copy
    img_copy[onlyMatch >= 125] = 0  # to_do lo que no es absolutamente blanco, pasa a ser negro

    if cv2.countNonZero(onlyMatch) == 0:
        img_copy[mask >= 0] = 255

    try:

        # imgResult = GenerateData.myImResize_20x20_32x32(img_copy)
        imgResult = modeling.GenerateTrainDataAZ.myImResize_forDataTraining(img_copy, None)

        # for i in range(0,32):
        #     for j in range(0, 32):
        #         if shouldFill(imgResult, (i,j)):
        #             imgResult[i, j] = 0
        #         if shouldClear(imgResult, (i, j)):
        #             imgResult[i, j] = 255

        imgResult = (imgResult -
                     255.0 / 2) / 255.0

    except Exception as e:
        # print('error filtering: ', e)
        imgResult = None

    if debugThisCharacter and imgResult is not None:
        print('th ', threshold_border)
        plt.subplot(1, 7, 1), plt.imshow(img, 'gray'), plt.title('Original')
        plt.subplot(1, 7, 2), plt.imshow(resaltado, 'gray'), plt.title('Resaltado')
        plt.subplot(1, 7, 3), plt.imshow(borde, 'gray'), plt.title('Borde')
        plt.subplot(1, 7, 4), plt.imshow(result, 'gray'), plt.title('SinBordes')
        plt.subplot(1, 7, 5), plt.imshow(mask, 'gray'), plt.title('Mask')
        plt.subplot(1, 7, 6), plt.imshow(img_copy, 'gray'), plt.title('To myImResize')
        if imgResult is not None:
            plt.subplot(1, 7, 7), plt.imshow(imgResult, 'gray'), plt.title('imgResult resized to 32x32')
        plt.show()

    return imgResult


def filterSingleCharacter(letter_original_and_mask):
    # todavia puede tener los bordes
    letter_original = letter_original_and_mask[0]
    mask = letter_original_and_mask[1]
    img = letter_original.copy()
    # se va a crear una nueva mascara, pero mask, el parametro deberia ser util

    ret3, th3 = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    rows, cols = th3.shape

    # th3 tiene el character correcto, pero tambien tiene basura, solo se extendera los que hagan match
    #
    # SEh = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    # SEv = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
    # opHorizontal = cv2.morphologyEx(th3, cv2.MORPH_OPEN, SEh)
    # opVertical = cv2.morphologyEx(th3, cv2.MORPH_OPEN, SEv)

    # Ifp = cv2.bitwise_xor(th3, cv2.bitwise_or(opHorizontal, opVertical))

    # Dk = getDk()
    # Ifp_union = Ifp.copy()
    # Ifp_union[:,:]=0
    # for D in Dk:
    #     closeD = cv2.morphologyEx(Ifp, cv2.MORPH_CLOSE, D)
    #     Ifp_union = cv2.bitwise_or(Ifp_union, closeD)
    # L = cv2.bitwise_or(opHorizontal, opVertical)
    # for i in L.shape[0]:
    #    for j in L.shape[1]:
    #        if L[i,j]>0:
    #            Ifp[i,j] = Ifp_union[i,j]
    # Ifp[L>0]=Ifp_union[L>0]
    onlyMatch = expandOnlyIntersections(th3, mask)

    # newMask = th3.copy()
    # for i in range(0,rows):
    #    for j in range(0, cols):
    #        if shouldFill(th3, (i,j)):
    #            th3[i,j]=255
    #        if shouldClear(th3, (i, j)):
    #            th3[i, j] = 0

    # plt.subplot(1,2,1), plt.imshow(newMask,'gray'), plt.title('newMask (th original)')
    # plt.subplot(1, 2, 2), plt.imshow(th3,'gray'), plt.title('th3, modified')
    # plt.show()

    newMask = cv2.medianBlur(th3, 3)

    img_copy = img.copy()

    img_copy[onlyMatch < 125] = 255
    img_copy[img_copy < 255] = 0
    img_copy[img_copy >= 255] = 255

    if cv2.countNonZero(onlyMatch) == 0:
        img_copy[mask >= 0] = 255

    try:

        # imgResult = GenerateData.myImResize_20x20_32x32(img_copy)
        imgResult = modeling.GenerateTrainDataAZ.myImResize_20x20_32x32(img_copy)

        # for i in range(0,32):
        #     for j in range(0, 32):
        #         if shouldFill(imgResult, (i,j)):
        #             imgResult[i, j] = 0
        #         if shouldClear(imgResult, (i, j)):
        #             imgResult[i, j] = 255

        imgResult = (imgResult -
                     255.0 / 2) / 255.0
    except Exception as e:
        # print('error filtering: ', e)
        imgResult = None

    # plt.subplot(1, 5, 1), plt.imshow(img, 'gray'), plt.title('img original')
    # plt.subplot(1, 5, 2), plt.imshow(mask, 'gray'), plt.title('mask from input')
    # plt.subplot(1, 5, 3), plt.imshow(onlyMatch, 'gray'), plt.title('mask, mezclado')
    # plt.subplot(1, 5, 4), plt.imshow(img_copy, 'gray'), plt.title('to pass resize32x32')
    # if( imgResult is not None):
    #    plt.subplot(1, 5, 5), plt.imshow(imgResult, 'gray'), plt.title('imgResult resized to 32x32')
    # plt.show()

    return imgResult


def findApropiateTemplate(ratio):
    current_image = None
    bestRatio = 100
    for k in range(1, 5):
        img = cv2.imread('extraction/FormatModel/cuadro_template_' + str(k) + '.png', 0)
        current_ratio = img.shape[0] / img.shape[1]

        if abs(current_ratio - ratio) < abs(bestRatio - ratio):
            bestRatio = current_ratio
            current_image = img
            # print('best ratio: '+str(k))
    return current_image


def plotImagesWithPrediction(preditectArray, images):
    cols = len(images)
    for k in range(0, cols):
        if images[k] is not None:
            plt.subplot(1, cols, k + 1), plt.imshow(images[k], 'gray'), plt.title(preditectArray[k]), plt.axis('off')
    plt.show()


def findMaxElement(A):
    currentValue = -1.0
    currentI = 0
    currentJ = 0
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if A[i, j] > currentValue:
                currentValue = A[i, j]
                currentI = i
                currentJ = j
    return (currentI, currentJ)


def countNonZerosRows(sumRows, I, j1, j2):
    if j1 <= 0:
        return sumRows[I, j2]
    else:
        return sumRows[I, j2] - sumRows[I, (j1 - 1)]


def countNonZerosCols(sumCols, J, i1, i2):
    if i1 <= 0:
        return sumCols[i2, J]
    else:
        return sumCols[i2, J] - sumCols[(i1 - 1), J]


def countNonZeros(sumRows, sumCols, pi, pf):
    top = countNonZerosRows(sumRows, pi[0], pi[1], pf[1])
    bottom = countNonZerosRows(sumRows, pf[0], pi[1], pf[1])
    left = countNonZerosCols(sumCols, pi[1], pi[0] + 1, pf[0] - 1)
    right = countNonZerosCols(sumCols, pf[1], pi[0] + 1, pf[0] - 1)
    return top + bottom + left + right


def getFirstGroupLargerThan(a, L):
    b = np.zeros(a.shape)

    for i in range(1, len(b)):
        if a[i] > 0:
            b[i] = b[i - 1] + 1
        else:
            if b[i - 1] >= L:
                # print(b,' - ', i)
                return int(round(i - b[i - 1])), int(i)
    return -1, -1


def getBestRectangle_big(region, ratio_cols_over_rows):
    B = range(max(0, region.shape[1] - 30), region.shape[1])
    copia = region.copy()

    copia[copia >= 0] = 0
    rows, cols = region.shape
    print(region.shape)
    bestValue = -1.0
    bestA = 0
    bestB = 0
    bestPos = (-1, -1)

    sumCols = np.asarray(np.sum(region, 0) / 255.0)
    diffSumCols = np.ediff1d(sumCols)
    sortedCols = np.sort(sumCols)
    indexToCutCols = (cols - 2 * 22) // 2
    toCut = 2 * sortedCols[indexToCutCols] + 2
    sumCols[sumCols < toCut] = 0
    left, right = getFirstGroupLargerThan(sumCols, 15)
    if left + right < 0:
        return (0, 0), (20, 20)
    sumCols[:left] = 0
    sumCols[(right + 1):] = 0
    print(left, right)
    importanColum = region[:, left:right]
    sumRows = np.asarray(np.sum(importanColum, 1) / 255.0)
    diffSumRows = np.ediff1d(sumRows)
    sortedRows = np.sort(sumRows)
    indexToCutRows = (rows - 7 * 16) // 2
    valueToCut = 2 * sortedRows[indexToCutRows] + 2
    sumRows[sumRows < valueToCut] = 0

    for i in range(0, 7):
        left, right = getFirstGroupLargerThan(sumRows, 10)
        if right - left > 0:
            marca = sumRows[left:right]
            sortedMarca = np.sort(marca)
            print(i, ' : ', sortedMarca[len(sortedMarca) // 2])
            sumRows[left:right] = 0

    width = 1

    #
    #
    # max_indx_row, max_value_row = max(enumerate(sumRows), key=lambda p: p[1])
    # max_indx_col, max_value_col = max(enumerate(sumCols), key=lambda p: p[1])
    #
    # for b in B:
    #     minA = int(round(b/(ratio_cols_over_rows+0.1)))
    #     maxA = int(round(b/(ratio_cols_over_rows-0.1)))
    #     for a in range(minA,maxA):
    #         cum = np.zeros((rows, cols))
    #         for i in range(rows):
    #             if i + a >= rows:
    #                 break
    #             for j in range(cols):
    #                 if j + b >= cols:
    #                     break
    #                 #copia[copia >= 0] = 0
    #                 # pi = (j, i)
    #                 # pf = (j + b, i + a)
    #                 # cv2.rectangle(copia, pi, pf, 255, thickness=1)
    #                 # copia = cv2.bitwise_and(copia, region)
    #                 # cantMatch = cv2.countNonZero(copia)
    #                 # print('cant match: ', cantMatch)
    #                 myCantMatch = countNonZeros(sumRows, sumCols, (i, j), (i+a, j+b))
    #                 # print('cant mAtch: ', myCantMatch)
    #                 cum[i, j] = myCantMatch / (2 * (a + b))
    #                 # (I, J) = findMaxElement(cum)
    #                 # print(I,J)
    #                 # print('inicio', i, j)
    #                 # print('longitudes', a, b)
    #                 # print(cum)
    #                 # plt.subplot(1, 2, 1), plt.imshow(region, 'gray'), plt.title('region')
    #                 # plt.subplot(1, 2, 2), plt.imshow(copia, 'gray'), plt.title('copia con rect de 255')
    #                 # plt.show()
    #                 # cv2.rectangle(copia, pi, pf, 0, thickness=1)
    #
    #
    #         (I, J) = findMaxElement(cum)
    #         if cum[I, J] > bestValue:
    #             bestValue = cum[I, J]
    #             bestA = a
    #             bestB = b
    #             bestPos = (I, J)
    #
    # copia[copia >= 0] = 0
    # pi = (bestPos[1], bestPos[0])
    # pf = (bestPos[1] + bestB, bestPos[0] + bestA)
    # cv2.rectangle(copia, pi, pf, 255, thickness=1)
    # section = region[pi[1]:pf[1], pi[0]:pf[0]]
    # plt.subplot(1, 3, 1), plt.imshow(region, 'gray'), plt.title('region')
    # plt.subplot(1, 3, 2), plt.imshow(copia, 'gray'), plt.title('copia con rect de 255')
    # plt.subplot(1, 3, 3), plt.imshow(section, 'gray'), plt.title('best mark')
    plt.subplot(4, 2, 1), plt.imshow(region, 'gray')
    plt.subplot(4, 2, 2), plt.imshow(importanColum, 'gray')

    plt.subplot(4, 2, 3), plt.bar(range(len(sumRows)), sumRows, width, color="blue")
    plt.subplot(4, 2, 4), plt.bar(range(len(sumCols)), sumCols, width, color="blue")
    plt.subplot(4, 2, 5), plt.bar(range(len(diffSumRows)), diffSumRows, width, color="blue")
    plt.subplot(4, 2, 6), plt.bar(range(len(diffSumCols)), diffSumCols, width, color="blue")
    plt.subplot(4, 2, 7), plt.bar(range(len(sortedRows)), sortedRows, width, color="blue")
    plt.subplot(4, 2, 8), plt.bar(range(len(sortedCols)), sortedCols, width, color="blue")

    plt.show()
    return (0, 0), (20, 20)


def getBestRectangle(region, ratio_cols_over_rows):
    # B = range(max(0, region.shape[1] - 20), region.shape[1])
    # copia = region.copy()
    #
    # copia[copia >= 0] = 0
    # rows, cols = region.shape
    #
    # bestValue = -1.0
    # bestA = 0
    # bestB = 0
    # bestPos = (-1, -1)
    #
    # sumRows = np.zeros((rows, cols))
    # sumCols = np.zeros((rows, cols))
    # for i in range(rows):
    #     for j in range(cols):
    #         if j == 0:
    #             sumRows[i, j] = (1 if region[i, j] > 0 else 0)
    #         else:
    #             sumRows[i, j] = (1 if region[i, j] > 0 else 0) + sumRows[i, j - 1]
    #
    #         if i == 0:
    #             sumCols[i, j] = (1 if region[i, j] > 0 else 0)
    #         else:
    #             sumCols[i, j] = (1 if region[i, j] > 0 else 0) + sumCols[i - 1, j]
    # # print(region)
    # # print(sumRows)
    # # print(sumCols)
    #
    #
    # for b in B:
    #     minA = int(round(b / (ratio_cols_over_rows + 0.1)))
    #     maxA = int(round(b / (ratio_cols_over_rows - 0.1)))
    #     for a in range(minA, maxA):
    #         cum = np.zeros((rows, cols))
    #         for i in range(rows):
    #             if i + a >= rows:
    #                 break
    #             for j in range(cols):
    #                 if j + b >= cols:
    #                     break
    #                 # copia[copia >= 0] = 0
    #                 # pi = (j, i)
    #                 # pf = (j + b, i + a)
    #                 # cv2.rectangle(copia, pi, pf, 255, thickness=1)
    #                 # copia = cv2.bitwise_and(copia, region)
    #                 # cantMatch = cv2.countNonZero(copia)
    #                 # print('cant match: ', cantMatch)
    #                 myCantMatch = countNonZeros(sumRows, sumCols, (i, j), (i + a, j + b))
    #                 # print('cant mAtch: ', myCantMatch)
    #                 cum[i, j] = myCantMatch / (2 * (a + b))
    #                 # (I, J) = findMaxElement(cum)
    #                 # print(I,J)
    #                 # print('inicio', i, j)
    #                 # print('longitudes', a, b)
    #                 # print(cum)
    #                 # plt.subplot(1, 2, 1), plt.imshow(region, 'gray'), plt.title('region')
    #                 # plt.subplot(1, 2, 2), plt.imshow(copia, 'gray'), plt.title('copia con rect de 255')
    #                 # plt.show()
    #                 # cv2.rectangle(copia, pi, pf, 0, thickness=1)
    #
    #         (I, J) = findMaxElement(cum)
    #         if cum[I, J] > bestValue:
    #             bestValue = cum[I, J]
    #             bestA = a
    #             bestB = b
    #             bestPos = (I, J)
    #
    # copia[copia >= 0] = 0
    # pi = (bestPos[1], bestPos[0])
    # pf = (bestPos[1] + bestB, bestPos[0] + bestA)
    # # cv2.rectangle(copia, pi, pf, 255, thickness=1)
    # # section = region[pi[1]:pf[1], pi[0]:pf[0]]
    # # plt.subplot(1, 3, 1), plt.imshow(region, 'gray'), plt.title('region')
    # # plt.subplot(1, 3, 2), plt.imshow(copia, 'gray'), plt.title('copia con rect de 255')
    # # plt.subplot(1, 3, 3), plt.imshow(section, 'gray'), plt.title('best mark')
    # # plt.show()
    # ratioBuffer = UtilDebug.RatiosBuffer()
    # ratioBuffer.append((bestA, bestB))
    # retFirstAlgorithm = pi, pf

    copia = region.copy()

    copia = copia > 0
    rows, cols = region.shape

    bestValue = -1.0
    bestA = 0
    bestB = 0
    bestPos = (-1, -1)

    acumSumRows = np.cumsum(copia, 1)
    acumSumCols = np.cumsum(copia, 0)

    totSumRows = np.sum(copia, 1)
    totSumCols = np.sum(copia, 0)
    delta = 1

    maxCols = filter_and_getMaxElements(totSumCols, 0, 100, minPercent=0.5)
    maxRows = filter_and_getMaxElements(totSumRows, 0, 100, minPercent=0.5)
    print('SS:', len(maxCols), len(maxRows))
    bestValue = 0
    bestA = None
    bestB = None

    minB = region.shape[1] - 20
    for p in range(len(maxRows)-1):
        for q in range(p+1, len(maxRows)):
            for m in range(len(maxCols)-1):
                for n in range(m+1, len(maxCols)):
                    i = min(maxRows[p], maxRows[q])
                    a = max(maxRows[p], maxRows[q]) - i
                    j = min(maxCols[m], maxCols[n])
                    b = max(maxCols[m], maxCols[n]) - j

                    if 0.75 < b/a < 0.95 and b>=minB:
                        myCantMatch = countNonZeros(acumSumRows, acumSumCols, (i, j), (i + a, j + b))
                        # print('cant mAtch: ', myCantMatch)
                        cum = myCantMatch / (2 * (a + b))
                        if cum > bestValue:
                            bestValue = cum
                            bestA = a
                            bestB = b
                            bestPos = (i, j)

    pi = (bestPos[1], bestPos[0])
    pf = (bestPos[1] + bestB, bestPos[0] + bestA)
    retSecondtAlgorithm = (pi,pf)
    # print(retFirstAlgorithm, retSecondtAlgorithm)
    return retSecondtAlgorithm


def filter_and_getMaxElements(A, delta, cantMax, minPercent=0.5):
    filtered = np.zeros(len(A))
    for i in range(delta, len(A) - delta):
        k = max(A[i - delta:i + delta + 1])
        if k == A[i]:
            filtered[i] = k

    b = enumerate(filtered)
    c = sorted(b, key=lambda p: -p[1])

    ret = []
    count = 0
    for k in c:
        if count < cantMax and k[1] > minPercent*c[0][1]:
            ret.append(k[0])
            count += 1
    if 0 not in ret:
        ret.append(0)
    if len(A)-1 not in ret:
        ret.append(len(A)-1)

    # plt.bar(range(len(filtered)), filtered, 1)
    # print(ret)
    # plt.show()
    return ret

def predictCategoric_column_labels_inside(column, labels):
    sumRows = np.asarray(np.sum(column, 1) // 255)
    resp = extractLabelsBySquares(column, sumRows, labels)
    return resp


def predictCategoric_column_labels_sex(column, labels):
    # plt.imshow(column,'gray')
    # plt.show()
    sumRows = np.asarray(np.sum(column, 1) // 255)
    resp = extractLabelsBySquaresSex(column, sumRows, labels)
    return resp


def predictCategoric_column_labels_documento(column, labels):
    sumRows = np.asarray(np.sum(column, 1) // 255)
    resp = extractLabelsBySquaresDocument(column, sumRows, labels)
    return resp


def predictCategoric_column_labels_SingleButton(column, labels):
    sumRows = np.asarray(np.sum(column, 1) // 255)
    if len(labels) != 1:
        raise Exception("expected len(labels) = 1 on: " + str(labels))
    width = column.shape[1]
    button_height = column.shape[0]
    i = column.shape[0] // 2

    if isOn(i, img=None, width=width, buttonHeight=button_height, sumRows=sumRows):
        resp = labels[0]
    else:
        resp = '?'
    # print(resp)
    # plt.subplot(1,2,1),plt.bar(range(len(sumRows)),sumRows, 1)
    # plt.subplot(1, 2, 2), plt.imshow(column)
    # plt.show()
    return resp


def predictCategoric_column_labels_left(column, labels):
    onlyLeftMarks = column[:, :-24]
    sumRows = np.asarray(np.sum(onlyLeftMarks, 1) // 255)
    rows = len(sumRows)
    sumRows = sumRows - int(min(sumRows))
    acumBy7 = sumRows.copy()
    for i in range(len(acumBy7)):
        if i > 0:
            acumBy7[i] += acumBy7[i - 1]
        if i >= 7:
            acumBy7[i] -= sumRows[i - 7]

    acumBy7[0:7] = 0
    max_i_2 = 0
    max_val_i = 0
    cantLabels = len(labels)
    valid = False
    for i in range(len(acumBy7)):
        val = 0
        local_valid = True
        for k in range(cantLabels):
            j = i + k * 21
            if j < len(acumBy7):
                val += acumBy7[j]
            else:
                local_valid = False

        if val > max_val_i and local_valid:
            max_val_i = val
            valid = True
            max_i_2 = i

    if not valid:
        return '?'

    onlyGlobles = column[:, -24:-4]
    sumRowsGlobes = np.asarray(np.sum(onlyGlobles, 1) // 255)
    results = ''
    for k in range(cantLabels):
        j = max_i_2 - 3 + k * 21
        if isOn(j, width=20, buttonHeight=6, sumRows=sumRowsGlobes):
            if len(results) > 0:
                results = results + ';' + labels[k]
            else:
                results = labels[k]

    if results is None or len(results) == 0:
        results = '?'

    # print(max_i_2)
    # print(labels)
    # print(results)
    #
    # plt.subplot(1, 3, 1), plt.imshow(column)
    # plt.subplot(1, 3, 2), plt.imshow(onlyGlobles,'gray')
    # plt.subplot(1, 3, 3), plt.bar(range(len(sumRowsGlobes)), sumRowsGlobes, 1)
    # plt.show()
    # print(results)
    return results
    # return results


def predictValuesCategory(arrayOfImages, array_labels, func):
    if len(arrayOfImages) != len(array_labels):
        print('error: sz arrayOfImages != sz arrayLabels')
        return ['None'] * len(array_labels)

    result = []
    for indx, img in enumerate(arrayOfImages):
        if img is not None:
            labels = array_labels[indx]
            predictions = func(img, labels)
            if predictions is not None and result is not None:
                result.append(predictions)
            else:
                result = None
        else:
            print('wtf is none')

    if result is None:
        result = ['Unknow'] * len(arrayOfImages)
    print('Returning:', result)
    return result


def predictValuesCategory_labelsLeft(arrayOfImages, array_labels):
    return predictValuesCategory(arrayOfImages, array_labels, func=predictCategoric_column_labels_left)


def predictValuesCategory_labelsInside(arrayOfImages, array_labels):
    return predictValuesCategory(arrayOfImages, array_labels, func=predictCategoric_column_labels_inside)


def predictValuesCategory_labelsSex(arrayOfImages, array_labels):
    return predictValuesCategory(arrayOfImages, array_labels, func=predictCategoric_column_labels_sex)


def predictValuesCategory_labelsDocumento(arrayOfImages, array_labels):
    return predictValuesCategory(arrayOfImages, array_labels, func=predictCategoric_column_labels_documento)


def predictValuesCategory_labelsSingleButtons(arrayOfImages, array_labels):
    return predictValuesCategory(arrayOfImages, array_labels, func=predictCategoric_column_labels_SingleButton)


def countBlocks(a, sz):
    count = 0
    while True:
        left, right = getFirstGroupLargerThan(a, sz)
        if left + right < 0:
            return count
        count += 1
        print(left, right)
        a[left:right] = 0
        if left == right:
            a[left] = 0


def calcMeans(a, limit, iterations=1):
    n = len(a)
    medias = np.zeros(n)
    count_items = 0
    acum = []

    for i in range(n):
        acum.append(a[i])
        count_items += 1
        if count_items > limit:
            acum = acum[1:]
            count_items -= 1
        if count_items == limit:
            medias[i - limit // 2] = statistics.median(acum)
    if iterations > 1:
        return calcMeans(medias, limit, iterations - 1)
    return medias


def dropMinsTo0(a, limit):
    n = len(a)
    medias = np.zeros(n, dtype=np.int32)
    count_items = 0
    acum = []

    for i in range(n):
        acum.append(a[i])
        count_items += 1
        if count_items > limit:
            acum = acum[1:]
            count_items -= 1
        if count_items == limit:
            j = i - limit // 2
            val = a[j]
            if abs(val - min(acum)) < 2 and val * 3 < max(acum[0:2]) and val * 3 < max(acum[-2:]):
                medias[j] = 0
            else:
                medias[j] = val

    return medias


def isOn(row_i, img=None, width=None, buttonHeight=None, sumRows=None):
    if img is None:
        if width is None or sumRows is None or buttonHeight is None:
            raise Exception('img is None but widht or sumRows or buttonHeight are not defined')

        r = sum(sumRows[row_i - buttonHeight // 2:row_i + buttonHeight // 2])
        print(UtilDebug.bcolors.OKBLUE + "Recieving data w: " + str(width) + " buttonHeight:" + str(buttonHeight) +
              " r: " + str(r) + " " + str(r * 100.0 / (buttonHeight * width)) + "% " + UtilDebug.bcolors.ENDC)
        return 0.6 * buttonHeight * width < r
    else:
        width = img.shape[1]
        sumRows = np.asarray(np.sum(img, 1) / 255.0)
        print(UtilDebug.bcolors.OKBLUE + "Recieving data img.shape " + str(img.shape) + UtilDebug.bcolors.ENDC)
        return isOn(row_i, width=width, sumRows=sumRows, img=None, buttonHeight=buttonHeight)


def extractLabelsBySquares(column, sumRows, labels):
    cantRows = len(labels)

    sumRows = sumRows.copy()
    originalRows = sumRows.copy()
    sumRows[sumRows < int(max(sumRows))] = 0
    center = []
    sc = sumRows.copy()
    while True:
        left, right = getFirstGroupLargerThan(sumRows, 1)

        if left + right < 0:
            break
        sumRows[left:right] = 0
        if left == right:
            sumRows[left] = 0

        center.append((left + right) // 2)

    if len(center) < 2 or center[0] + 150 > center[-1]:
        return '?'
    i = center[0] + 17

    results = ''
    widthColumn = column.shape[1]
    for k in range(cantRows):
        j = i + 19 * k
        if isOn(j, img=None, width=widthColumn, sumRows=originalRows, buttonHeight=8):
            if len(results) > 0:
                results = results + ';' + labels[k]
            else:
                results = labels[k]

    if len(results) == 0:
        results = '?'
    return results
    # print(labels)
    # print(results)
    # plt.subplot(1,2,1), plt.imshow(column,'gray')
    # plt.subplot(1,2,2), plt.bar(range(len(originalRows)),originalRows, 1)
    # plt.show()


def extractLabelsBySquaresDocument(column, sumRows, labels):
    cantRows = len(labels)

    sumRows = sumRows.copy()
    originalRows = sumRows.copy()

    results = ''
    widthColumn = column.shape[1]
    for k, j in enumerate([4, 20]):

        if isOn(j, img=None, width=widthColumn, sumRows=originalRows, buttonHeight=6):
            if len(results) > 0:
                results = results + ';' + labels[k]
            else:
                results = labels[k]

    if len(results) == 0:
        results = '?'

    # print(labels)
    # print(results)
    # plt.subplot(1,2,1), plt.imshow(column,'gray')
    # plt.subplot(1,2,2), plt.bar(range(len(originalRows)),originalRows, 1)
    # plt.show()
    return results


def extractLabelsBySquaresSex(column, sumRows, labels):
    cantRows = len(labels)

    sumRows = sumRows.copy()
    originalRows = sumRows.copy()
    sumRows[sumRows < int(max(sumRows))] = 0
    center = []
    sc = sumRows.copy()
    while True:
        left, right = getFirstGroupLargerThan(sumRows, 1)

        if left + right < 0:
            break
        sumRows[left:right] = 0
        if left == right:
            sumRows[left] = 0

        center.append((left + right) // 2)

    if len(center) < 2 or center[0] + 150 > center[-1]:
        return '?'
    i = center[0]

    results = ''
    widthColumn = column.shape[1]
    for k, addJ in enumerate([18, 38, 116, 136]):
        j = i + addJ
        if isOn(j, img=None, width=widthColumn, sumRows=originalRows, buttonHeight=8):
            if len(results) > 0:
                results = results + ';' + labels[k]
            else:
                results = labels[k]

    if len(results) == 0:
        results = '?'
    return results
    # print(labels)
    # print(results)
    # plt.subplot(1,2,1), plt.imshow(column,'gray')
    # plt.subplot(1,2,2), plt.bar(range(len(originalRows)),originalRows, 1)
    # plt.show()


def extractColumnsBySquares(If, cantColumns):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    If = cv2.dilate(If, kernel)
    sumCols = np.asarray(np.sum(If, 0) // 255)
    sumCols = sumCols.copy()

    sumCols = sumCols - int(min(sumCols))
    sumCols = dropMinsTo0(sumCols, 3)
    left = 0
    right = max(sumCols)
    if cantColumns == 2:
        delta = 60
    else:
        delta = 45

    sumCols[sumCols < 125] = 0
    sc = sumCols.copy()
    blocks = countBlocks(sumCols, 1)
    arrayResult = []
    if blocks == 2:

        sumCols = sc.copy()
        returnNone = False

        center = []
        for k in range(0, 2):
            left, right = getFirstGroupLargerThan(sumCols, 1)
            print('LR', left, right)
            if left + right < 0:
                print('this shouldn be happening')
                returnNone = True
                continue
            sumCols[left:right] = 0
            if left == right:
                sumCols[left] = 0

            center.append((left + right) // 2)

            # importanColum = If[:, left:right]
            # arrayResult.append(importanColum)

        if returnNone or len(center) < 2:
            return [None] * cantColumns

        if cantColumns == 2:
            i = getPointProportion((center[0], 0), (center[1], 0), 20, 47)[0]
            j = getPointProportion((center[0], 0), (center[1], 0), 47, 20)[0]
            importanColum_I = If[:, (i - 11):(i + 11)]
            importanColum_J = If[:, (j - 11):(j + 11)]
            arrayResult.append(importanColum_I)
            arrayResult.append(importanColum_J)
            # plt.subplot(1, 3, 1), plt.imshow(If), plt.title('If')
            # plt.subplot(1, 3, 2), plt.bar(range(len(sumCols)), sumCols, 1),plt.title('SumCols')
            # plt.subplot(1, 3, 3), plt.imshow(importanColum_I), plt.title('FIrst Column')
            # plt.show()

        else:
            i = (center[0] + center[1]) // 2
            importanColum_I = If[:, (i - 11):(i + 11)]
            # plt.subplot(1, 3, 1), plt.imshow(If), plt.title('If')
            # plt.subplot(1, 3, 2), plt.imshow(importanColum_I), plt.title('Column')
            # plt.show()
            arrayResult.append(importanColum_I)

        return arrayResult

    else:
        return [None] * cantColumns


def extractSimpleButton(img):
    ret, If = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    If = cv2.bitwise_not(If)
    sumRows = np.asarray(np.sum(If, 1) // 255)
    sumCols = np.asarray(np.sum(If, 0) // 255)
    acumBy12 = sumRows.copy()
    for i in range(len(acumBy12)):
        if i > 0:
            acumBy12[i] += acumBy12[i - 1]
        if i >= 12:
            acumBy12[i] -= sumRows[i - 12]

    acumBy19 = sumCols.copy()
    for i in range(len(acumBy19)):
        if i > 0:
            acumBy19[i] += acumBy19[i - 1]
        if i >= 19:
            acumBy19[i] -= sumCols[i - 19]

    max_indx_12, max_value_12 = max(enumerate(acumBy12), key=lambda p: p[1])
    max_indx_19, max_value_19 = max(enumerate(acumBy19), key=lambda p: p[1])

    return If[max_indx_12 - 11:max_indx_12 + 1, max_indx_19 - 18:max_indx_19 + 1]


def extractCategory_extractColumnLabelsTipoSiNo(img, TL, BR, cantColumns):
    deltaAmpliacion = 5
    ROI_base = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    cols = ROI_base.shape[1]
    left = extractSimpleButton(ROI_base[:, :cols // 2])
    right = extractSimpleButton(ROI_base[:, cols // 2:])
    # plt.subplot(3, 1, 1), plt.imshow(ROI_base, 'gray'), plt.title('ROIS')
    # plt.subplot(3, 1, 2), plt.imshow(left, 'gray'), plt.title('left')
    # plt.subplot(3, 1, 3), plt.imshow(right, 'gray'), plt.title('right')

    # plt.show()
    arrayResult = []
    arrayResult.append(left)
    arrayResult.append(right)
    return arrayResult


def extractCategory_extractColumnLabelsDocumento(img, TL, BR, cantColumns):
    deltaAmpliacion = 5
    ROI_base = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    ROI = ROI_base.copy()
    #



    If = cv2.adaptiveThreshold(ROI, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 5, 2)
    If = cv2.bitwise_not(If)

    sumCols = np.asarray(np.sum(If, 0) // 255)
    left = sumCols[:(len(sumCols) // 2)]
    right = sumCols[(len(sumCols) // 2):]
    max_indx_left, max_value_row = max(enumerate(left), key=lambda p: p[1])
    max_indx_right, max_value_col = max(enumerate(right), key=lambda p: p[1])

    i = max_indx_left
    j = len(sumCols) // 2 + max_indx_right

    ROI = ROI_base[:, i:(j + 1)]

    ret, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    If = cv2.bitwise_not(If)
    sumRows = np.asarray(np.sum(If, 1) // 255)
    sumRows[sumRows > 0.9 * ROI.shape[1]] = 0
    acumBy5 = sumRows.copy()
    for i in range(len(acumBy5)):
        if i > 0:
            acumBy5[i] += acumBy5[i - 1]
        if i >= 5:
            acumBy5[i] -= sumRows[i - 5]

    print(sumRows)
    print(acumBy5)
    max_i_2 = 0
    max_val_i = 0
    for i in range(len(acumBy5)):
        if i + 16 >= len(acumBy5):
            break
        val = acumBy5[i] + acumBy5[i + 16]
        if val > max_val_i:
            max_val_i = val
            max_i_2 = i
    i_1 = max_i_2 - 7
    j_2 = max_i_2 + 18

    left = If[i_1:j_2, 4:22]
    right = If[i_1:j_2, 88:105]

    # plt.subplot(2,2,1),plt.imshow(ROI_base,'gray'), plt.title('img')
    # plt.subplot(2, 2, 2), plt.imshow(If, 'gray'), plt.title('Solo columna ancha importante')
    # plt.subplot(2, 2, 3), plt.imshow(left, 'gray'), plt.title('top')
    # plt.subplot(2, 2, 4), plt.imshow(right, 'gray'), plt.title('bot')
    # plt.show()
    arrayResult = []
    arrayResult.append(left)
    arrayResult.append(right)

    return arrayResult


def extractCategory_extractColumnLabelsTipoSuministro(img, TL, BR, cantColumns):
    deltaAmpliacion = 5
    ROI_base = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    ROI = ROI_base.copy()
    #



    ret, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    If = cv2.bitwise_not(If)
    # NO_TIENE = If[14:25, 222:277]
    # cv2.imwrite('NO_TIENE.png',NO_TIENE)

    sumRows = np.asarray(np.sum(If, 1) // 255)
    sumCols = np.asarray(np.sum(If, 0) // 255)
    NO_TIENE = cv2.imread('resources/NO_TIENE.png', 0)
    neg_NO_TIENE = cv2.bitwise_not(NO_TIENE)
    rows, cols = NO_TIENE.shape
    ROWS, COLS = If.shape
    I_J = None
    val = 0
    for i in range(ROWS):
        for j in range(COLS):
            i_2 = i + rows
            j_2 = j + cols
            if i_2 >= ROWS or j_2 >= COLS:
                break
            pos_no_tiene = If[i:i_2, j:j_2]

            c1 = cv2.countNonZero(cv2.bitwise_and(NO_TIENE, pos_no_tiene))
            c2 = cv2.countNonZero(cv2.bitwise_and(neg_NO_TIENE, pos_no_tiene))
            v = c1 - c2
            if v > val:
                val = v
                I_J = (i, j)

    if I_J is None or I_J[1] <= 199:
        return [None] * 3
    arrayResult = []
    d_j = 8
    d_i = 3
    for k in [-199, -105, -13]:
        j = I_J[1] + k
        i = I_J[0] + 5
        globe = If[(i - d_i):(i + d_i), (j - d_j):(j + d_j)]
        arrayResult.append(globe)

    # print(I_J)
    # plt.subplot(2, 2, 1), plt.imshow(ROI_base, 'gray'), plt.title('img')
    # plt.subplot(2, 2, 2), plt.imshow(If, 'gray'), plt.title('Solo columna ancha importante')
    # plt.subplot(2, 2, 3), plt.bar(range(len(sumRows)), sumRows, width=1), plt.title('sumRows')
    # plt.subplot(2, 2, 4), plt.bar(range(len(sumCols)), sumCols, width=1), plt.title('sumCols')
    # # plt.subplot(2, 2, 4), plt.imshow(right, 'gray'), plt.title('bot')
    # plt.show()

    return arrayResult


def extractCategory_extractColumnLabelsTipoVia(img, TL, BR, cantColumns):
    deltaAmpliacion = 5
    ROI_base = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    ROI = ROI_base.copy()
    #



    ret, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    If = cv2.bitwise_not(If)

    # CARRETERA = If[8:19, 523:589]
    # cv2.imwrite('CARRETERA.png',CARRETERA)
    #
    sumRows = np.asarray(np.sum(If, 1) // 255)
    sumCols = np.asarray(np.sum(If, 0) // 255)
    CARRETERA = cv2.imread('resources/CARRETERA.png', 0)
    neg_CARRETERA = cv2.bitwise_not(CARRETERA)
    rows, cols = CARRETERA.shape
    ROWS, COLS = If.shape
    I_J = None
    val = 0
    for i in range(ROWS):
        for j in range(COLS):
            i_2 = i + rows
            j_2 = j + cols
            if i_2 >= ROWS or j_2 >= COLS:
                break
            pos_no_tiene = If[i:i_2, j:j_2]

            c1 = cv2.countNonZero(cv2.bitwise_and(CARRETERA, pos_no_tiene))
            c2 = cv2.countNonZero(cv2.bitwise_and(neg_CARRETERA, pos_no_tiene))
            v = c1 - c2
            if v > val:
                val = v
                I_J = (i, j)

    if I_J is None or I_J[1] <= 500:
        return [None] * 6
    arrayResult = []
    d_j = 8
    d_i = 3
    for k in range(6):
        j = I_J[1] - 500 + 122 * k
        i = I_J[0] + 4
        globe = If[(i - d_i):(i + d_i), (j - d_j):(j + d_j)]
        arrayResult.append(globe)

    #
    # print(I_J)
    # plt.subplot(2, 2, 1), plt.imshow(ROI_base, 'gray'), plt.title('img')
    # plt.subplot(2, 2, 2), plt.imshow(If, 'gray'), plt.title('Solo columna ancha importante')
    # # plt.subplot(2, 2, 3), plt.bar(range(len(sumRows)), sumRows, width=1), plt.title('sumRows')
    # # plt.subplot(2, 2, 4), plt.bar(range(len(sumCols)), sumCols, width=1), plt.title('sumCols')
    # # plt.subplot(2, 2, 4), plt.imshow(right, 'gray'), plt.title('bot')
    # plt.show()
    return arrayResult


def extractCategory_extractColumnLabelsInside(img, TL, BR, cantColumns):
    deltaAmpliacion = 10
    ROI = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    # If = cv2.GaussianBlur(ROI, (3, 3), 0)
    ret, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    If = cv2.bitwise_not(If)
    rows, cols = If.shape

    resp = extractColumnsBySquares(If, cantColumns)
    #
    # sumCols = np.asarray(np.sum(If, 0) // 255)
    # sumCols = dropMinsTo0(sumCols, 11)
    #
    # left = 0
    # right = max(sumCols)
    #
    # toCut = -1
    # for i in range(left, right):
    #     sc = sumCols.copy()
    #     sc[sc < i] = 0
    #     print('testing with ', i)
    #     numBlocks = countBlocks(sc, 20)
    #
    #     if numBlocks == cantColumns:
    #         toCut = i
    #         break
    # #
    # # media_21 = calcMeans(sumCols, 3,3)
    # # with0 = dropMinsTo0(sumCols, 11)
    # # sum_medias = np.zeros(len(media_21))
    # # for i in range(len(sum_medias)):
    # #     sum_medias[i] = with0[i]+media_21[i]
    # # plt.subplot(2, 2, 1), plt.imshow(If, 'gray')
    # # plt.subplot(2, 2, 2), plt.bar(range(len(sumCols)), sumCols, 1, color="blue")
    # # plt.subplot(2, 2, 3), plt.bar(range(len(media_21)), media_21, 1, color="blue")
    # # plt.subplot(2, 2, 4), plt.bar(range(len(with0)), with0, 1, color="blue")
    # # plt.show()
    # sumCols[sumCols < toCut] = 0
    #
    # arrayResult = []
    # arResultOk = True
    # for k in range(0, cantColumns):
    #     left, right = getFirstGroupLargerThan(sumCols, 15)
    #     if left + right < 0:
    #         arrayResult.append(None)
    #         arResultOk = False
    #         continue
    #
    #     sumCols[left:right] = 0
    #     importanColum = If[:, left:right]
    #     arrayResult.append(importanColum)
    # print('Returning images A')
    # toPrint = False
    # for I in arrayResult:
    #     if I is None:
    #         toPrint = False
    # # if arResultOk == False:
    # #     arrayResult = resp
    # if toPrint:
    #
    #     sumCols = np.asarray(np.sum(If, 0) // 255)
    #     plt.subplot(3, 2, 1), plt.imshow(If, 'gray')
    #     plt.subplot(3, 2, 2), plt.bar(range(len(sumCols)), sumCols, 1, color="blue")
    #     if resp is not None and len(resp) > 0 and resp[0] is not None:
    #         plt.subplot(3, 2, 3), plt.imshow(resp[0], 'gray')
    #         sumRows = np.asarray(np.sum(resp[0], 1) // 255)
    #         plt.subplot(3, 2, 4), plt.bar(range(len(sumRows)), sumRows, 1, color="blue")
    #     if resp is not None and len(resp) > 1 and resp[1] is not None:
    #         plt.subplot(3, 2, 5), plt.imshow(resp[1], 'gray')
    #         sumRows = np.asarray(np.sum(resp[1], 1) // 255)
    #         plt.subplot(3, 2, 6), plt.bar(range(len(sumRows)), sumRows, 1, color="blue")
    #     plt.show()
    return resp


def extractCategory_extractColumnLabelsLeft(img, TL, BR, cantColumns):
    deltaAmpliacion = 10
    ROI = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    # If = cv2.GaussianBlur(ROI, (3, 3), 0)
    ret, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    If = cv2.bitwise_not(If)

    sumCols = np.asarray(np.sum(If, 0) // 255)
    compCols = (sumCols * (-1)) + If.shape[0]
    max_j = 0
    max_value_j = 0
    for j in range(0, len(sumCols) // 2):
        val = sumCols[j] + compCols[j + 4]
        if val > max_value_j:
            max_value_j = val
            max_j = j

    If2 = If[:, 0:max_j + 30]
    arrayResult = []
    arrayResult.append(If2)
    # plt.subplot(2,2,1), plt.imshow(If,'gray')
    # plt.subplot(2,2,2), plt.bar(range(len(sumCols)),sumCols,width=1)
    # plt.subplot(2, 2, 3), plt.imshow(If2,'gray')
    # plt.show()
    return arrayResult


def extractCategory_extractColumnLabelsSex(img, TL, BR, cantColumns):
    return extractCategory_extractColumnLabelsInside(img, TL, BR, cantColumns)

def getPixels(img, P, Q):
    minX = min(P[0],Q[0])-2
    maxX = max(P[0], Q[0])+2
    minY = min(P[1], Q[1])-2
    maxY = max(P[1], Q[1])+2

    roi = img[minX:maxX, minY:maxY]
    # print('getting:',P,Q)
    # plt.imshow(img,'gray')
    # plt.show()
    dx = Q[0] - P[0]
    dy = Q[1] - P[1]
    D = math.sqrt(dx*dx+dy*dy)
    res = []
    for d in np.arange(0, D, step=1.0):
        a = d
        b = D-a
        q = getPointProportion(P,Q,a,b)
        res.append(img[q])
    return res


def extractCharacters(img, onlyUserMarks, TL, BR, count):
    numRows = (BR[0] - TL[0]) / count
    numCols = BR[1] - TL[1]
    # print('finding ratio nr/nc : ' + str(numRows)+' / ' + str(numCols)+'  divided by '+ str(count))
    template = findApropiateTemplate(numRows / numCols)

    deltaAmpliacion = 5

    ROI = img[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion, TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]
    ROI_onlyUserMarks = onlyUserMarks[TL[1] - deltaAmpliacion:BR[1] + deltaAmpliacion,
                        TL[0] - deltaAmpliacion:BR[0] + deltaAmpliacion]

    If = cv2.GaussianBlur(ROI, (3, 3), 0)
    If = cv2.adaptiveThreshold(If, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 2)
    If = cv2.bitwise_not(If)

    leftPart = If[:, 0:(template.shape[1] + (deltaAmpliacion * 2 - 1))]
    rightPart = If[:, -(template.shape[1] + (deltaAmpliacion * 2 - 1)):]

    top_left_L, bottom_right_L = getBestRectangle(leftPart, 0.8)
    delta_L = (bottom_right_L[0] - top_left_L[0], bottom_right_L[1] - top_left_L[1])

    top_left_R, bottom_right_R = getBestRectangle(rightPart, 0.8)
    delta_R = (bottom_right_R[0] - top_left_R[0], bottom_right_R[1] - top_left_R[1])

    bestLeft = leftPart[top_left_L[1]:bottom_right_L[1], top_left_L[0]:bottom_right_L[0]]
    bestRight = rightPart[top_left_R[1]:bottom_right_R[1], top_left_R[0]:bottom_right_R[0]]

    # print('If shape: ', If.shape)
    # print('template shape: ', template.shape)
    # print('current top_left_R', top_left_R)
    top_left_R = (top_left_R[0] + If.shape[1] - (template.shape[1] + ((deltaAmpliacion * 2 - 1))), top_left_R[1])
    bottom_right_R = (top_left_R[0] + delta_R[0], top_left_R[1] + delta_R[1])
    # print('after top_left_R', top_left_R)
    possibleBestLeft = If[top_left_L[1]:bottom_right_L[1], top_left_L[0]:bottom_right_L[0]]
    possibleBestRight = If[top_left_R[1]:bottom_right_R[1], top_left_R[0]:bottom_right_R[0]]

    # plt.subplot(1,8,1), plt.imshow(If), plt.title('If')
    # plt.subplot(1, 8, 2), plt.imshow(template), plt.title('template')
    # plt.subplot(1, 8, 3), plt.imshow(leftPart), plt.title('leftPart')
    # plt.subplot(1, 8, 4), plt.imshow(rightPart), plt.title('rightPart')
    # plt.subplot(1, 8, 5), plt.imshow(bestLeft), plt.title('bestLeft')
    # plt.subplot(1, 8, 6), plt.imshow(possibleBestLeft), plt.title('possibleBestLeft')
    # plt.subplot(1, 8, 7), plt.imshow(bestRight), plt.title('bestRight')
    # plt.subplot(1, 8, 8), plt.imshow(possibleBestRight), plt.title('possbielBestRight')
    # plt.show()

    pointA = (top_left_L[1], top_left_L[0])
    pointY = (bottom_right_R[1], bottom_right_R[0])

    pointB = (pointY[0], pointA[1])
    pointX = (pointA[0], pointY[1])

    res = []
    TL = pointA
    BR = pointY
    BL = (bottom_right_L[1], top_left_L[0])
    TR = (top_left_R[1],bottom_right_R[0])
    res.extend(getPixels(ROI, TL, TR))
    res.extend(getPixels(ROI, BL, BR))
    for k in range(0, count):
        s = getPointProportion(TL,TR,k,count-k)
        t = getPointProportion(BL, BR, k, count - k)
        res.extend(getPixels(ROI, s, t))
    res.extend(getPixels(ROI, TR,BR))
    np_mean = int(np.mean(res))
    np_stdv = int(np.std(res))
    # print(pointA,pointB,pointX,pointY,ROI.shape)
    ROI_2 = ROI[pointA[0]:pointY[0], pointA[1]:pointY[1]]

    # plt.subplot(2,1,1), plt.imshow(ROI)
    # plt.subplot(2, 1, 2), plt.imshow(ROI_2)
    # plt.show()

    letters = []
    for k in range(0, count):
        upperLeft = getPointProportion(pointA, pointX, k, count - k)
        bottomLeft = getPointProportion(pointB, pointY, k, count - k)
        upperRight = getPointProportion(pointA, pointX, k + 1, count - (k + 1))
        bottomRight = getPointProportion(pointB, pointY, k + 1, count - (k + 1))

        minX = min(upperLeft[0], bottomLeft[0])
        maxX = max(upperRight[0], bottomRight[0])

        minY = min(bottomLeft[1], bottomRight[1])
        maxY = max(upperLeft[1], upperRight[1])

        singleCharacter = (ROI[minX:maxX, minY:maxY], (ROI_onlyUserMarks[minX:maxX, minY:maxY],np_mean-2*np_stdv))
        letters.append(singleCharacter)

    filteredLetters = []

    for letter in letters:
        singleLetterFiltered = filterSingleCharacter_new(letter)
        filteredLetters.append(singleLetterFiltered)

        # if singleLetterFiltered != None:
        #    plt.imshow(singleLetterFiltered)
        #    plt.show()

    return filteredLetters


def extractCharacters_old(img, onlyUserMarks, TL, BR, count):
    letters = []

    ROI = img[TL[1] - 3:BR[1] + 3, TL[0] - 3:BR[0] + 3]
    ROI_onlyUserMarks = onlyUserMarks[TL[1] - 3:BR[1] + 3, TL[0] - 3:BR[0] + 3]
    # ROI = cv2.medianBlur(ROI, 3)
    If = cv2.GaussianBlur(ROI, (3, 3), 0)
    # If = cv2.Canny(ROI,50,200)


    If = cv2.adaptiveThreshold(If, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 2)
    If = cv2.bitwise_not(If)

    dst = cv2.cornerHarris(If, 2, 3, 0.04)
    # dst = cv2.dilate(dst, None)

    ret, dst = cv2.threshold(dst, 0.01 * dst.max(), 255, 0)
    dst = np.uint8(dst)
    # find centroids
    ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)

    # define the criteria to stop and refine the corners
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    corners = cv2.cornerSubPix(If, np.float32(centroids), (5, 5), (-1, -1), criteria)

    # Now draw them
    res = np.hstack((centroids, corners))
    res = np.int0(res)
    If_copy = If.copy()
    If_copy[If_copy >= 125] = 125
    If[If >= 0] = 0

    list2 = res[:, 2]
    for indx, x in enumerate(res[:, 3]):
        y = list2[indx]
        if 0 <= x < If.shape[0] and 0 <= y < If.shape[1]:
            If[x, y] = 255
            If_copy[x, y] = 255
    # print('looking for A,B,X,Y')
    pointA = closestNonZero(If, (3, 3), 12)
    pointB = closestNonZero(If, (ROI.shape[0] - 3, 3), 12)
    pointX = closestNonZero(If, (3, ROI.shape[1] - 3), 12)
    pointY = closestNonZero(If, (ROI.shape[0] - 3, ROI.shape[1] - 3), 12)

    #
    # #ret3, If = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # #If = cv2.dilate(If, cv2.getStructuringElement(cv2.MORPH_RECT, (3,1)), iterations=1)
    # D9 = cv2.getStructuringElement(cv2.MORPH_CROSS, (15,15))
    # D9[1:,1:] = 0
    #
    # #D9[0:8, :] = 0
    # print(D9)
    # ROI_Open_D9 = cv2.morphologyEx(If, cv2.MORPH_ERODE, D9)

    # plt.subplot(3,1,1), plt.imshow(ROI), plt.title('ROI')
    # plt.subplot(3,1,2), plt.imshow(If), plt.title('If')
    # plt.subplot(3, 1, 3), plt.imshow(If_copy), plt.title('If_copy')
    # plt.show()

    for k in range(0, count):
        upperLeft = getPointProportion(pointA, pointX, k, count - k)

        # if k ==0:
        #    upperLeft = getCross(edges, 9, upperLeft)
        # else:
        #    upperLeft = getCross(edges, 13, upperLeft)

        bottomLeft = getPointProportion(pointB, pointY, k, count - k)

        # if k == 0:
        #    bottomLeft = getCross(edges, 3, bottomLeft)
        # else:
        #    bottomLeft = getCross(edges, 7, bottomLeft)

        upperRight = getPointProportion(pointA, pointX, k + 1, count - (k + 1))

        # if k == cant-1:
        #    upperRight = getCross(edges, 12, upperRight)
        # else:
        #    upperRight = getCross(edges, 13, upperRight)

        bottomRight = getPointProportion(pointB, pointY, k + 1, count - (k + 1))

        # if k == cant-1:
        #    bottomRight = getCross(edges, 6, bottomRight)
        # else:
        #    bottomRight = getCross(edges, 7, bottomRight)

        minX = min(upperLeft[0], bottomLeft[0]) + 2
        maxX = max(upperRight[0], bottomRight[0]) - 2

        minY = min(bottomLeft[1], bottomRight[1]) + 2
        maxY = max(upperLeft[1], upperRight[1]) - 2

        singleCharacter = (ROI[minX:maxX, minY:maxY], ROI_onlyUserMarks[minX:maxX, minY:maxY])
        letters.append(singleCharacter)

    filteredLetters = []

    for letter in letters:
        singleLetterFiltered = filterSingleCharacter(letter)
        filteredLetters.append(singleLetterFiltered)
    return filteredLetters
