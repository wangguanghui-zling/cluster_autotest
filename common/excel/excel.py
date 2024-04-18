#! /usr/bin/env python



"""
read and write Excel file(including encrypted Excel), only basic function for retrieving and writing data, more APIs
might be added later depending on requirement

usage:
    1.from common import Excel
    or
    2.from excel import Excel

    excel_file_name = "aaa/bbb/ccc.xlsx"

    1.
    excelApp = Excel(excel_file_name)
    # call APIs or do some other operation
    excelApp.close()

    or
    2.
    with Excel(excel_file_name) as excelApp:
        # call APIs or do some other operation

    APIs:
        # read names of all sheets
        d = app.sheets.names

        # create a new sheet named "sheet19"
        d = app.sheets.new("sheet19")

        # delete a sheet by name or index
        app.sheets.delete("sheet19")

        # activate sheet
        sht = app.sheets.activate("test")

        # get all data from excel's used cells
        d = sht.used_range

        # get all data as lines
        d = sht.rows

        # get all data as columns
        d = sht.columns

        # get the max number of used columns
        d = sht.max_column

        # get the max number of used rows
        d = sht.max_row

        # read data from one cell: row=3, column=2
        d = sht.read_cell(3, 2)

        # write data to one cell: row=4, column=5, data="hahaha"
        sht.write_cell(4, 5, "hahaha")

        # read a serial of data from a range of excel: from A5 to B10
        d = sht.read_range("A5", "B10")
        or
        d = sht.read_range([5, 1], [10, 2])

        # write a serial of data to excel
        val = [["10", 2, 5], [5, 5, 5], ["dd", "vvv", "eee"]]
        sht.write_range("C3", "E5", val)
        or
        sht.write_range([3, 3], [5, 5], val)

        # delete row 3
        sht.delete_row(3)

        # delete column 4
        sht.delete_column(4)

        # insert row 5
        sht.insert_row(5)

        # insert column 6
        sht.insert_column(6)
"""

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
import win32com.client
import os
import numpy
from common.excel.workbook import WorkBook


class Excel:
    def __init__(self, file: str, openCopy: bool = False, visible: bool = False, autoSave: bool = True):
        """
        initialize and open excel file
        @param:
            file: absolute path of Excel file
            openCopy(optional): True: open a read only copy when Excel file has already opened, False: operate the opened Excel file directly
            visible(optional): True: show interface of Excel, False: do not show interface of Excel
            autoSave(optional): True: save changes before closing, False: do not save changes
        """
        self.__filename = file
        self.__openCopy = openCopy
        self.__visible = visible
        self.__autoSaveExcel = autoSave
        self.__open_excel()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        logger.info(f"closing excel: <{self.__filename}>, error message: <exc_type={exc_type}, exc_val={exc_val}, exc_tb={exc_tb}>")

    def __open_excel(self):
        if not self.__filename.endswith(".xlsx") and not self.__filename.endswith(".xlsm"):
            logger.error(f"can not find excel file: {self.__filename}")
            raise FileNotFoundError(f"can not find excel file: {self.__filename}")
        if not os.path.exists(os.path.split(self.__filename)[0]):
            logger.error(f"can not locate dir <{os.path.split(self.__filename)[0]}> for excel file.")
            raise FileNotFoundError(f"can not locate dir <{os.path.split(self.__filename)[0]}> for excel file.")
        if os.path.exists(self.__filename):
            if self.__openCopy:
                self.__excelApp = win32com.client.DispatchEx('Excel.Application')
            else:
                self.__excelApp = win32com.client.Dispatch('Excel.Application')
            logger.info(f"opening excel file: <{self.__filename}>")
            self.__excelApp.Visible = self.__visible
            self.__workbook = self.__excelApp.Workbooks.Open(self.__filename)
        else:
            self.__excelApp = win32com.client.Dispatch('Excel.Application')
            logger.info(f"creating a new excel file: <{self.__filename}>")
            self.__excelApp.Visible = self.__visible
            self.__workbook = self.__excelApp.Workbooks.Add()

    def save(self):
        """
        save changes of workbook
        """
        if os.path.exists(self.__filename):
            self.__workbook.Save()
        else:
            self.__workbook.SaveAs(self.__filename)

    def close(self):
        """
        close workbook and quit excel application
        """
        if self.__autoSaveExcel:
            self.save()
        self.__workbook.Close()
        self.__excelApp.Quit()

    @property
    def sheets(self):
        """
        return an object of workbook, you can operate sheets with this object
        @return:
            object of WorkBook
        """
        return WorkBook(self.__workbook)


if __name__ == "__main__":
    fn = r"D:\Bruce\003_GIT\cluster\ACT\common\excel\测试用例.xlsx"
    app = Excel(fn)
    # read names of all sheets
    d = app.sheets.names
    print(d)
    # create a new sheet named "sheet19"
    d = app.sheets.new("sheet19")
    print(d)
    # read names of all sheets
    d = app.sheets.names
    print(d)
    # get all data from excel's used cells
    d = app.sheets.activate("test").used_range
    print(d)
    # get all data as lines
    d = app.sheets.activate("test").rows
    print(d)
    # get all data as columns
    d = app.sheets.activate("test").columns
    print(d)
    # get the max number of used columns
    d = app.sheets.activate("test").max_column
    print(d)
    # get the max number of used rows
    d = app.sheets.activate("test").max_row
    print(d)
    # read data from one cell: row=3, column=2
    d = app.sheets.activate("test").read_cell(3, 2)
    print(d)
    # write data to one cell: row=4, column=5, data="hahaha"
    app.sheets.activate("test").write_cell(4, 5, "hahaha")
    # read a serial of data from a range of excel: from A5 to B10
    d = app.sheets.activate("test").read_range("A5", "B10")
    print(d)
    # write a serial of data to excel
    val = [["10", 2, 5], [5, 5, 5], ["dd", "vvv", "eee"]]
    app.sheets.activate("test").write_range("C3", "E5", val)
    app.close()
