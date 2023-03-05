import sys
import traceback
from typing import TextIO


class Tee(object):
    def __init__(self, file=TextIO | str):
        if isinstance(file, str):
            self.should_close = True
            file = open(file, "w")
        else:
            self.should_close = False  # The caller is responsible for closing the file
        self.file = file
        self.stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self

    def __exit__(self, exc_type, exc_value, tb):
        sys.stdout = self.stdout
        if exc_type is not None:
            self.file.write(traceback.format_exc())
        if self.should_close:
            self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()
