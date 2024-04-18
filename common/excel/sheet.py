#! /usr/bin/env python



try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger


class Sheet:
    def __init__(self, sheet):
        """
        initialize worksheet
        @param:
            sheet: an object of Excel worksheet
        """
        self.__sheet = sheet

    @property
    def used_range(self):
        """
        return all data of used range in current worksheet
        @return:
            range
        """
        return self.__sheet.UsedRange

    @property
    def rows(self):
        """
        return all data of used range in current worksheet by rows
        @return:
            rows
        """
        return self.__sheet.UsedRange.Rows()

    @property
    def columns(self):
        """
        return all data of used range in current worksheet by columns
        @return:
            columns
        """
        return self.__sheet.UsedRange.Columns()

    def delete_row(self, row: int):
        """
        delete specific row by index
        @param:
            row: index of row
        """
        if row <= 0:
            logger.error(f"an integer larger than 0 expected: row={row}")
            return
        return self.__sheet.Rows(row).Delete()

    def delete_column(self, col: int):
        """
        delete specific column by index
        @param:
            col: index of column
        """
        if col <= 0:
            logger.error(f"an integer larger than 0 expected: col={col}")
            return
        return self.__sheet.Column(col).Delete()

    def insert_row(self, row: int):
        """
        insert a new row before specific row
        @param:
            row: index of row
        """
        if row <= 0:
            logger.error(f"an integer larger than 0 expected: row={row}")
            return
        return self.__sheet.Rows(row).Insert()

    def insert_column(self, col: int):
        """
        insert a new column before specific column
        @param:
            col: index of column
        """
        if col <= 0:
            logger.error(f"an integer larger than 0 expected: col={col}")
            return
        return self.__sheet.Columns(col).Insert()

    @property
    def max_row(self):
        """
        return index of max used row
        @return:
            int
        """
        return self.__sheet.UsedRange.Rows.Count

    @property
    def max_column(self):
        """
        return index of max used column
        @return:
            int
        """
        return self.__sheet.UsedRange.Columns.Count

    def read_cell(self, row: int, column: int):
        """
        get data from specific cell: (row, column)
        @param:
            row: index of row
            column: index of column
        @return:
            str or int or float ...: data value of specific cell
        """
        return self.__sheet.Cells(row, column).Value

    def write_cell(self, row: int, column: int, value):
        """
        write data to specific cell: (row, column)
        @param:
            row: index of row
            column: index of column
            value: value to be wrote to cell
        """
        self.__sheet.Cells(row, column).Value = value

    def read_range(self, start: (str, tuple, list), end: (str, tuple, list)):
        """
        get data values from specific table range
        @param:
            start: position of start cell, "A1" or [1, 1]
            end: position of end cell, "D50" or [50, 4]
        @return:
            list, tuple: values of table range
        """
        if isinstance(start, str) and isinstance(end, str):
            return self.__sheet.Range(f"{start}:{end}").Value
        else:
            if len(start) != 2 or len(end) != 2:
                logger.error(f"range: <start={start}, end={end}> not support, example: start=(1, 1), end=(5, 5)")
                return
            all_int = [True for x in list(start) + list(end) if not isinstance(x, int)]
            if len(all_int) != 0:
                logger.error(f"range: <start={start}, end={end}> not support, start and end must be integers")
                return
            if (start[0] <= 0 or start[0] > end[0]) or (start[1] <= 0 or start[1] > end[1]):
                logger.error(f"range: <start={start}, end={end}> not support, start must be a location of top-left and "
                             f"end must be a location of bottom-right")
                return
            return self.__sheet.Range(self.__sheet.Cells(*start), self.__sheet.Cells(*end)).Value

    def write_range(self, start: (str, tuple, list), end: (str, tuple, list), values):
        """
        write data values to specific table range
        @param:
            start: position of start cell, "A1" or [1, 1]
            end: position of end cell, "D50" or [50, 4]
            values: a list or tuple stored values to be wrote
        """
        if isinstance(start, str) and isinstance(end, str):
            self.__sheet.Range(f"{start}:{end}").Value = values
        else:
            if len(start) != 2 or len(end) != 2:
                logger.error(f"range: <start={start}, end={end}> not support, example: start=(1, 1), end=(5, 5)")
                return
            all_int = [True for x in list(start) + list(end) if not isinstance(x, int)]
            if len(all_int) != 0:
                logger.error(f"range: <start={start}, end={end}> not support, start and end must be integers")
                return
            if (start[0] <= 0 or start[0] > end[0]) or (start[1] <= 0 or start[1] > end[1]):
                logger.error(f"range: <start={start}, end={end}> not support, start must be a location of top-left and "
                             f"end must be a location of bottom-right")
                return
            self.__sheet.Range(self.__sheet.Cells(*start), self.__sheet.Cells(*end)).Value = values


if __name__ == "__main__":
    pass
