#! /usr/bin/env python



try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.excel.sheet import Sheet


class WorkBook:
    def __init__(self, wb):
        """
        initialize workbook
        @param:
            wb: an object of Excel workbook
        """
        self.__wb = wb
        self.__activeSheet = None

    @property
    def names(self):
        """
        return all sheet names as a list
        @return:
            list: name of all sheets
        """
        return [sht.name for sht in self.__wb.Worksheets]

    def new(self, name: str):
        """
        create a new sheet
        @param:
            name: name for new sheet
        """
        if name in self.names or name.lower() in [x.lower() for x in self.names]:
            logger.error(f"sheet: <{name}> already exists, creating failed.")
            return
        self.__wb.Worksheets.Add().Name = name

    def delete(self, nameOrNumber: (str, int)):
        """
        delete a specific sheet by sheet name or sheet index
        @param:
            nameOrNumber: name or index of sheet
        """
        if nameOrNumber in self.names or nameOrNumber.lower() in [x.lower() for x in self.names]:
            return self.__wb.Worksheets(nameOrNumber).Delete()
        else:
            logger.error(f"sheet: <{nameOrNumber}> not exists, deleting failed.")

    def activate(self, nameOrNumber: (str, int)):
        """
        activate and select a sheet by sheet name or sheet index and return an object of selected sheet, you could
        operate cells and ranges with this object
        @param:
            nameOrNumber: name or index of sheet
        @return:
            object of Sheet
        """
        if isinstance(nameOrNumber, str) and nameOrNumber not in self.names:
            logger.error(f"sheet: <{nameOrNumber}> not found in current opened excel file.")
            return
        self.__activeSheet = self.__wb.Worksheets(nameOrNumber)
        return Sheet(self.__activeSheet)


if __name__ == "__main__":
    pass
