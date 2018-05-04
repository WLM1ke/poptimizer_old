"""Основные стили pdf-файла"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

BLOCK_HEADER_STYLE = ParagraphStyle('Block_Header', fontName='Helvetica-Bold', spaceAfter=10)
TABLE_LINE_COLOR = colors.black
TABLE_LINE_WIDTH = 0.5
BOLD_FONT = 'Helvetica-Bold'
