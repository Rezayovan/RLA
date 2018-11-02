'''
Run the server with this command:
gunicorn --config=python:gunicorn_config app:app
'''

from multiprocessing import cpu_count

bind = '127.0.0.1:5000'

workers = cpu_count() * 2 + 1
worker_class = 'gthread'
threads = cpu_count() * 2 + 1

reload = True
