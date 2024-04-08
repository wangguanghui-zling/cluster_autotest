import xlrd
from logger.logger import logger

def read_excel(path,case):
    """
    获取excel数据
    parame: path: excel路径
    parame: case: 用例名称
    return: value: 返回case用例的测试数据
    """
    try:
        book = xlrd.open_workbook(path)
        sheet = book.sheet_by_index(0)
        header = sheet.row_values(0)
        testdata = []
        for row in range(1, sheet.nrows):
            row_data = {}
            for col in range(sheet.ncols):
                # 使用表头作为键，对应单元格的值作为值
                row_data[header[col]] = sheet.cell_value(row, col)
        # 将每行数据添加到列表中
            testdata.append(row_data)
        for value in testdata:
            if value["测试用例名称"] == case:
                return value
        logger.info("{}表格{}用例数据读取成功,读到的内容为{}".format(path,case,value))
    except Exception as e:
            logger.error(e)
            raise