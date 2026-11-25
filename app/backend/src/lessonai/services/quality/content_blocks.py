"""Runtime checks for callers accepting legacy dictionaries."""
from pydantic import ValidationError
from lessonai.schemas.content_blocks import BLOCK, TextBlock, FormulaBlock, table_rows


def block_errors(slide):
    for index, block in enumerate(slide.get('blocks') or []):
        try:
            parsed = BLOCK.validate_python(block)
            if isinstance(parsed, (TextBlock, FormulaBlock)) and not (block.get('text') or block.get('latex') or '').strip():
                raise ValueError('Nội dung khối rỗng')
        except (ValidationError, ValueError) as error:
            yield f'blocks[{index}]', f'Khối nội dung không hợp lệ: {error}'
    if slide.get('table_data') is not None:
        try:
            table_rows(slide['table_data'])
        except ValueError as error:
            yield 'table_data', str(error)
