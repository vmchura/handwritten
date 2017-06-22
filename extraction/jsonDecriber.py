import json

from extraction.FormatModel.UtilFunctionsLoadTemplates import loadCategory


if __name__ == '__main__':
    str_number = '2'

    with open('extraction/FormatModel/pagina' + str_number + '.json', 'r') as input:
        dict_Page1 = json.load(input)
        Page = loadCategory(dict_Page1)
        print(Page)

    Page.describeAsTable()