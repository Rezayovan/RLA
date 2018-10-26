import os
import contextlib

'''
Delete file at the specified path if it exists
'''
def delete_file(path):
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)