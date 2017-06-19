#!/usr/bin/env python
# coding: utf-8

"""
    mindisApp
    ============================

    Handwritten characters and digits recognition application
    Structure/
        Extraction
        Model design - Prediction
        Integration (API)

    _copyright_ = 'Copyright (c) 2017 J.W. & Vm.C.', see AUTHORS for more details
    _license_ = GNU General Public License, see LICENSE for more details
"""

import numpy as np
import cv2
from matplotlib import pyplot as plt
import sys
import os
import time

from wand.image import Image
from wand.color import Color
from PyPDF2 import PdfFileWriter, PdfFileReader

from extraction import FeatureExtractor
from extraction import PageDetector
from extraction.FormatModel import UtilDebug


# Input  settings ####
# img = cv2.imread('input/pagina3_1.png', 0) # Doesnt work either
# img = cv2.imread('input/pagina3_2.jpeg', 0)
# img = cv2.imread('input/pagina3_3.jpg', 0)
# img = cv2.imread('input/pagina3_4.png', 0)
# img = cv2.imread('input/pagina3_5.png', 0)
# img = cv2.imread('input/pagina3_6.png', 0)
# img = cv2.imread('input/pagina1_1.png', 0) # para Debugear
# img = cv2.imread('input/pagina1_2.png', 0) # Otra mas
# img = cv2.imread('input/pagina1_3.png', 0)
# img = cv2.imread('input/pagina1_4.png', 0)
# img = cv2.imread('input/pagina2_1.png', 0)
# img = cv2.imread('input/pagina2_2.png', 0)
# img = cv2.imread('input/pagina4_1.png', 0)
# img = cv2.imread('input/pagina4_2.png', 0)

def processPdf(originalPdf):
    inputPdf = PdfFileReader(open(originalPdf, 'rb'))

    pdfname = os.path.basename(originalPdf)
    pdfname = pdfname.split('.')
    pdfname = pdfname[len(pdfname) - 2]

    """
    if len(originalPdf.split('\\')) == 1:
        if len(originalPdf.split('/')) == 1:
            pdfname = originalPdf.split('.')
            pdfname = pdfname[len(pdfname) - 2]
        else:
            pdfname = originalPdf.split('/')
            pdfname = pdfname[len(pdfname) - 1]
            pdfname = pdfname.split('.')
            pdfname = pdfname[len(pdfname) - 2]
    else:
        pdfname = originalPdf.split('\\')
        pdfname = pdfname[len(pdfname) - 1]
        pdfname = pdfname.split('.')
        pdfname = pdfname[len(pdfname) - 2]
    """

    if not os.path.exists('input/tmp/'):
        os.makedirs('input/tmp/')

    outputPath = []
    for i in range(inputPdf.getNumPages()):
        p = inputPdf.getPage(i)
        outputPdf = PdfFileWriter()
        outputPdf.addPage(p)

        with open('input/tmp/' + pdfname + '_%1d.pdf' % (i + 1), 'wb') as f:
            outputPdf.write(f)
            outputPath.append(f.name)

    outputPath = np.array(outputPath)
    # print('outputPdf', type(outputPath), outputPath)
    return outputPath, inputPdf.getNumPages()


def convert_pdf_png(filePath, numPages):
    imagePath = []
    for i in range(numPages):
        path = filePath[i]
        pathName = path.split('.')

        print('Converting page %d' % (i + 1))
        try:
            with Image(filename=path, resolution=300) as img:
                with Image(width=img.width, height=img.height, background=Color('white')) as bg:
                    bg.composite(img, 0, 0)
                    bg.save(filename=pathName[0] + '.png')
        except Exception as e:
            print('Unable to convert pdf file', e)
            raise

        imagePath.append(pathName[0] + '.png')
    
    imagePath = np.array(imagePath)
    return imagePath


# Main function ####
if __name__ == '__main__':
    """ .........
    To run the app, execute the following in terminal:

    [terminal_prompt]$ python App.py path/to/image.pdf

    Currently the app supports images in the following formats: 
        .png
        .jpeg
        .jpg
        .pdf
    """
    print("Hi there, its mindisApp I'll try to be helpful :) \nBut I'm still just a robot. Sorry!")

    arg = sys.argv[1]
    print('arg', arg)
    splitArg = arg.split('.')


    if splitArg[1] == 'png' or splitArg[1] == 'jpeg' or splitArg[1] == 'jpg':
        print("File is a picture!")
        imgPath = np.array([arg])
    else:
        if splitArg[1] == 'pdf' or splitArg[1] == 'PDF':
            print('File is a pdf!')
            pdfPath, numPag = processPdf(arg)
            imgPath = convert_pdf_png(pdfPath, numPag)

            # print('imgPath__', type(imgPath), imgPath)
        else:
            raise ValueError(splitArg[1] + ' File format cannot be processed :(!')

    # print('imgPath for cv2', type(imgPath), len(imgPath))
    for i in range(len(imgPath)):
        print('***** IMAGE ' + str(i + 1) + ' PROCESSING *****')
        start_time = time.time()

        timer_detector = UtilDebug.PageDetectorTimer()
        timer_detector.startTimer(1)

        img = cv2.imread(imgPath[i], 0)
        rows, cols = img.shape

        if rows < cols:
            image = cv2.transpose(img)

        img = cv2.resize(img, (1240, 1754))

        img = PageDetector.enderezarImagen(img)
        page = PageDetector.detectPage(img)

        timer_detector.endTimer()

        if page is not None:
            # plt.imshow(page[0],'gray')
            # plt.title(' Es la página: '+str(page[1][0]))
            # plt.show()
            print(' This image can be processed')
            if page[1][1] == 0:  # esta orientado de manera normal
                FeatureExtractor.extractPageData(page[0], page[1][0], None, os.path.basename(imgPath[i]))
                print('Total time: {0} seconds'.format(time.time() - start_time))
            else:
                if page[1][1] == 1:  # esta al revez
                    flipped = cv2.flip(page[0], 0)
                    flipped = cv2.flip(flipped, 1)
                    FeatureExtractor.extractPageData(flipped, page[1][0], None, os.path.basename(imgPath[i]))
                    print('Total time: {0} seconds'.format(time.time() - start_time))
                else:
                    raise ValueError(
                        'Image cannot be processed, Check its quality\nUse a different scanner and try again')


    timers = [UtilDebug.PageDetectorTimer(), UtilDebug.CategoryTimer(), UtilDebug.ArrayLetterTimer(),
              UtilDebug.ArrayDigitTimer(), UtilDebug.PredictorTimer()]
    totalTime_controlled = 0

    for timer in timers:
        totalTime_controlled += timer.secs

    print(UtilDebug.bcolors.BOLD + 'Total time controlled: ' + str(totalTime_controlled) + ' secs' + UtilDebug.bcolors.ENDC)

    total_length = 100
    barra_length = []

    colors = [UtilDebug.bcolors.HEADER, UtilDebug.bcolors.OKGREEN, UtilDebug.bcolors.WARNING, UtilDebug.bcolors.FAIL,
              UtilDebug.bcolors.OKBLUE]
    for indx, timer in enumerate(timers):
        barra_length.append(int(round(timer.secs * total_length / totalTime_controlled)))
        print(colors[indx] + str(timer) + UtilDebug.bcolors.ENDC)

    for indx, portion in enumerate(barra_length):
        sys.stdout.write(colors[indx])
        for k in range(portion):
            sys.stdout.write('#')
        sys.stdout.write(UtilDebug.bcolors.ENDC)
    sys.stdout.flush()
    print('')



