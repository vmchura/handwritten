from pip._vendor.distlib.compat import raw_input

from extraction.FormatModel import CreatePage1Variable
from extraction.FormatModel.RawVariableDefinitions import *
from extraction.FormatModel.UtilFunctionsLoadTemplates import loadCategory
import pickle
import cv2
import json

pagina = '1'
fileToEdit = 'paginaNew' + pagina + '.json'
image = cv2.imread('../../resources/pag' + pagina + '_Template_to_positions.png')


def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global refPt, cropping

    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append((x, y))
        cropping = False

        # draw a rectangle around the region of interest
        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("image", image)


def updateValues(catBase, catT, posBase, posT):
    if catBase.hasValue:
        dx_0 = catBase.value.position[0][0] - posBase[0]
        dy_0 = catBase.value.position[0][1] - posBase[1]

        dx_1 = catBase.value.position[1][0] - posBase[0]
        dy_1 = catBase.value.position[1][1] - posBase[1]

        new_position = []
        new_position.append((posT[0] + dx_0, posT[1] + dy_0))
        new_position.append((posT[0] + dx_1, posT[1] + dy_1))
        val = None
        if catBase.value.nameParser == 'parserImage2ArrayChar':
            if catBase.value.nameSingleParser == 'letterPredictor':
                val = ArrayImageChar(new_position, catBase.value.countItems)
            if catBase.value.nameSingleParser == 'digitPredictor':
                val = ArrayImageNumber(new_position, catBase.value.countItems)
        elif catBase.value.nameParser == 'parserImage2Categoric':
            val = ImageCategoric(new_position, catBase.value.countItems)

        if val is None:
            print('wtf')
        else:
            catT.value = val

    else:
        for subtype in catBase.subTypes:
            name = subtype.name
            subType_T = catT[name]
            if (subType_T is None):
                print('not Found: ', name, ' on ', catT)
            else:
                updateValues(subtype, subType_T, posBase, posT)


if __name__ == '__main__':

    if (image is None):
        print('image not foound')
    img_clone = image.copy()
    with open(fileToEdit, 'r') as input:
        print(input)
        dict_Page1 = json.load(input)
        Page = loadCategory(dict_Page1)
        print(Page)

    Page.describe(True)

    P01 = Page['P01']
    print('P01:')
    print(P01.describe(True))
    print('tipo_documento')
    tipo = P01['tipo_documento']
    print(tipo.describe(True))
    pos = tipo['pos_TL_BR']
    val = pos.value
    print(pos.describe(True), 'value: ', val.position)
    delta_rows = val.position[1][1] - val.position[0][1]

    P02 = Page['P02']

    # P02 = Page['P02']
    # T = UtilFunctionsExtraction.getPointProportion(A, B, 1, 3)
    # updateValues(P01, P02, A, T)
    #
    # P03 = Page['P03']
    # T = UtilFunctionsExtraction.getPointProportion(A, B, 1, 1)
    # updateValues(P01, P03, A, T)
    #
    # P04 = Page['P04']
    # T = UtilFunctionsExtraction.getPointProportion(A, B, 3, 1)
    # updateValues(P01, P04, A, T)
    #
    # P05 = Page['P05']
    # T = UtilFunctionsExtraction.getPointProportion(A, B, 4, 0)
    # updateValues(P01, P05, A, T)


    for p in range(2, 13):
        str_p = 'P' + ('0' if p < 10 else '') + str(p)
        P = Page[str_p]
        updateValues(P01, P, (0, 0), (0, delta_rows* (p - 1) + (int(round(p*1.7)))//p ))

    with open(fileToEdit, 'w') as output:
        json.dump(Page, output, default=CreatePage1Variable.jsonDefault, indent=4)
