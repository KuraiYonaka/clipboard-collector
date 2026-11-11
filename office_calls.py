import time


def retry_excel(operation, timeout=5.0):
    """Retry calls rejected before execution, never an ambiguous COM failure."""
    from pywintypes import com_error

    rejected = (0x80010001, 0x8001010A, 0x8001010B)
    deadline = time.monotonic() + timeout
    while True:
        try:
            return operation()
        except com_error as exc:
            if (exc.hresult & 0xFFFFFFFF) not in rejected:
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError('Excel is still busy. Finish editing the cell or close the Excel dialog, then start collection again.') from exc
            time.sleep(min(0.15, remaining))
