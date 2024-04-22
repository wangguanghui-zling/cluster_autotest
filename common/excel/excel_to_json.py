import json
from common.excel.excel import Excel
import os
from common.logger.logger import logger
import codecs

class Excel_To_JSON:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.app = Excel(self.file_path)

    def close_excel(self):
        """
        关闭已经打开的excel
        """
        self.app.close()

    def excel2json(self):
        """
        将测试用例excel转换成json格式
        """
        n = self.app.sheets.names
        logger.info("获取所有sheet页")
        for i in n:
            sht = self.app.sheets.activate(i)            
            max_colum = sht.max_column
            logger.info(f"sheet页_{i}有{max_colum}列")
            max_row = sht.max_row
            logger.info(f"sheet页_{i}有{max_row}行")
            result = []
            heads = []
            for col in range(max_colum):
                heads.append(sht.read_cell(1, col+1))
            for row in range(max_row-1):
                if row == 0:
                    continue
                one_line = {}
                for col in range(max_colum-2):
                    k = heads[col]
                    cell = sht.read_cell(row + 1, col + 1)
                    one_line[k] = cell
                    logger.info(f"one_line={one_line}")
                result.append(one_line)
            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            with codecs.open(os.path.join(os.path.dirname(self.file_path), "test"+i+".json"), "w", "utf-8") as json_file:
                json_file.write(json_str)



if __name__ == "__main__":
    f = r"E:\lulei\test.xlsx"
    es = Excel_To_JSON(f)
    es.excel2json()
    es.close_excel()




