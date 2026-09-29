from io import BytesIO
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


def xlsx_text_values(content):
    """提取 XLSX 内全部文本值，用于验证导出内容。"""
    try:
        with ZipFile(BytesIO(content)) as workbook:
            values = []
            for name in workbook.namelist():
                if not name.startswith('xl/') or not name.endswith('.xml'):
                    continue
                root = ElementTree.fromstring(workbook.read(name))
                for node in root.iter():
                    if node.tag.endswith('}t') and node.text is not None:
                        values.append(node.text)
            return values
    except BadZipFile as exc:
        raise ValueError('响应内容不是有效的 XLSX 文件') from exc
