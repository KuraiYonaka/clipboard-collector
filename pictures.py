"""Decode clipboard raster data and embed it in an Office document."""
from io import BytesIO
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from office_calls import retry_excel

MAX_PIXELS = 24_000_000
OFFICE_KINDS = ('excel', 'word')


def picture_signature(clipboard_picture):
    image_format, payload = clipboard_picture
    with Image.open(BytesIO(payload), formats=[image_format]) as image:
        if image.width * image.height > MAX_PIXELS:
            raise ValueError('The copied image exceeds 24 million pixels.')
        with image.convert('RGBA') as rgba:
            return rgba.size, sha256(rgba.tobytes()).digest()


def insert_picture(target, clipboard_picture):
    image_format, payload = clipboard_picture
    with TemporaryDirectory(prefix='ClipboardCollector-') as folder:
        path = str(Path(folder) / 'clipboard.png')
        with Image.open(BytesIO(payload), formats=[image_format]) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ValueError('The copied image exceeds 24 million pixels.')
            dpi = image.info.get('dpi', (96, 96))
            if any(not 10 <= value <= 2400 for value in dpi):
                dpi = (96, 96)
            with image.convert('RGBA') as rgba:
                rgba.save(path, dpi=dpi, compress_level=1)
        if target['kind'] == 'excel':
            insert_excel_picture(target, path)
        else:
            insert_word_picture(target, path)


def insert_excel_picture(target, path):
    book, sheet = target['book'], target['sheet']
    row, column = target['next_row'], target['col']

    def add_picture():
        if str(book.FullName) != target['book_name'] or str(sheet.Name) != target['sheet_name']:
            raise RuntimeError('The target Excel workbook changed.')
        if sheet.ProtectContents or book.ReadOnly:
            raise RuntimeError('The Excel worksheet is protected or read-only.')
        if row > int(sheet.Rows.Count):
            raise RuntimeError('The Excel row limit was exceeded.')
        cell = sheet.Cells(row, column)
        if cell.Value2 is not None:
            raise RuntimeError(f'Excel cell {cell.Address} already contains data. Collection stopped to avoid overwriting it.')
        return sheet.Shapes.AddPicture(path, 0, -1, float(cell.Left), float(cell.Top), -1, -1)

    picture = retry_excel(add_picture)

    def next_row():
        bottom = float(picture.Top) + float(picture.Height)
        # Find the first row below the picture, including across hidden rows.
        low, high = row + 1, int(sheet.Rows.Count) + 1
        while low < high:
            mid = (low + high) // 2
            if float(sheet.Cells(mid, column).Top) < bottom:
                low = mid + 1
            else:
                high = mid
        return low

    try:
        target['next_row'] = retry_excel(next_row)
    except Exception:
        try:
            retry_excel(lambda: picture.Delete())
        except Exception as exc:
            raise RuntimeError('The picture was inserted, but its position could not be verified. Check the worksheet before restarting.') from exc
        raise


def insert_word_picture(target, path):
    doc = target['doc']
    if str(doc.FullName) != target['path'] or doc.ReadOnly or doc.ProtectionType != -1:
        raise RuntimeError('The target Word document changed or is no longer editable.')
    start = int(doc.Content.End) - 1
    position = start
    if start:
        doc.Range(start, start).InsertAfter('\r')
        position += 1
    picture = None
    try:
        picture = doc.InlineShapes.AddPicture(path, False, True, doc.Range(position, position))
        # Word may initially scale to the available width.
        picture.ScaleWidth = 100
        picture.ScaleHeight = 100
    except Exception:
        if picture is not None:
            picture.Delete()
        if position != start:
            doc.Range(start, position).Delete()
        raise
