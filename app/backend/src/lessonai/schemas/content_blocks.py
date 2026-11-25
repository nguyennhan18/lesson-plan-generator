"""Public discriminated block contract; retain unrecognized extension fields."""
import base64
import io
from typing import Annotated, Literal
from PIL import Image
from pydantic import model_serializer, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator


class Block(BaseModel):
    model_config = ConfigDict(extra='allow', strict=True, str_strip_whitespace=False)


class TextBlock(Block):
    type: Literal['text']
    text: str = Field(min_length=1, pattern=r'\S')


class FormulaBlock(Block):
    type: Literal['formula']
    latex: str = Field(min_length=1, pattern=r'\S')


class ImageBlock(Block):
    type: Literal['image']
    data_url: str
    alt: str = Field(min_length=1, pattern=r'\S')

    @model_validator(mode='after')
    def valid_image(self):
        if not self.data_url.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,')):
            raise ValueError('Hình cần dữ liệu PNG/JPEG được nhúng')
        try:
            data = base64.b64decode(self.data_url.split(',', 1)[1], validate=True)
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
        except Exception as error:
            raise ValueError('Dữ liệu hình không đọc được') from error
        return self


def table_rows(value):
    rows = value.get('rows') if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows or not all(isinstance(row, list) and row for row in rows):
        raise ValueError('Bảng cần các hàng ô không rỗng')
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError('Số cột của bảng không thống nhất')
    if any(type(cell) not in (str, int, float) for row in rows for cell in row):
        raise ValueError('Ô bảng cần văn bản hoặc số')
    return rows


class TableBlock(Block):
    type: Literal['table']
    rows: list | dict | None = None
    data: list | dict | None = None

    @model_serializer(mode='wrap')
    def serialize_table(self, handler):
        data = handler(self)
        return {key: value for key, value in data.items() if key not in {'rows', 'data'} or value is not None}

    @model_validator(mode='after')
    def valid_table(self):
        table_rows(self.rows if self.rows is not None else self.data)
        return self


ContentBlock = Annotated[TextBlock | FormulaBlock | ImageBlock | TableBlock, Field(discriminator='type')]
BLOCK = TypeAdapter(ContentBlock)


