import json

from extraction.FormatModel.UtilFunctionsLoadTemplates import loadCategory


if __name__ == '__main__':
    str_number = '1'

    with open('extraction/FormatModel/paginaNew' + str_number + '.json', 'r') as input:
        dict_Page1 = json.load(input)
        Page = loadCategory(dict_Page1)
        print(Page)

    Page.describeAsTable()