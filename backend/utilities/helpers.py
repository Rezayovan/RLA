import os
import contextlib

'''
Delete file at the specified path if it exists
'''
def delete_file(path):
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)

'''
Checks to see if all specified keys in keys_to_check are in dict_in
'''
def all_keys_present_in_dict(keys_to_check, dict_in):
    return all (key in dict_in for key in keys_to_check)
