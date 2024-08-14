# coding: utf8
# !/usr/bin/env python

""" repo.py: Easy UCS Deployment Tool """

import os

from flask import Flask, Response, request
from flask_cors import CORS

from __init__ import EASYUCS_ROOT
from api.api_server import response_handle

app = Flask(__name__)
cors = CORS(app)
easyucs = None


@app.route('/<path:file_path>', methods=['GET', 'HEAD'])
def repository(file_path=None):
    file_hosting_path = os.path.abspath(os.path.join(
        EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
        easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME)
    )

    if not file_path:
        response = response_handle(code=400, response="Please provide a valid file path")
        return response

    absolute_file_path = os.path.abspath(os.path.join(file_hosting_path, file_path))

    if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                      absolute_file_path]):
        easyucs.logger(level="warning",
                       message=f"User is trying to access restricted path {absolute_file_path}")
        return response_handle(code=400, response=f"Please provide a valid file path")

    if not os.path.exists(absolute_file_path):
        response = response_handle(f"File {file_path} not found", 404)
        return response

    if not os.path.isfile(absolute_file_path):
        response = response_handle(code=400, response="Please provide a valid file path")
        return response

    file_name = os.path.basename(absolute_file_path)
    file_size = content_length = os.path.getsize(absolute_file_path)

    if request.method == 'HEAD':
        try:
            response = Response()
            response.headers["Content-Disposition"] = "attachment; filename=%s" % file_name
            response.headers["Content-Type"] = "application/octet-stream"
            response.headers["Content-Length"] = file_size
            response.headers["Accept-Ranges"] = "bytes"
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'GET':
        # This API endpoint downloads the file
        try:
            def stream_file(start=0, end=file_size - 1):
                """
                Streams a portion of a file between 'start' and 'end' positions, yielding data in chunks.

                Notice the use of 'yield':
                -> In this context, the stream_file function is a generator function that yields data chunks while
                reading a file in specified ranges.
                -> When the generator is iterated (e.g., in a loop or using next()), it executes until it encounters
                a yield statement. At that point, it produces the yielded value, and the function's state is saved.
                -> The next time the generator is iterated, it resumes execution from where it was paused,
                continuing until the next yield or until the function exits.
                -> This allows for efficient streaming of data in chunks, providing a memory-efficient way to handle
                large datasets or files.

                Args:
                    start (int): The starting position in the file (default is 0).
                    end (int): The ending position in the file (default is file_size - 1).

                Yields:
                    bytes: Data chunks of maximum 'chunk_size'.
                """

                chunk_size = 10 ** 6  # 10 MB
                with open(absolute_file_path, "rb") as f_read:
                    f_read.seek(start)
                    if end - start + 1 > chunk_size:
                        while f_read.tell() <= end:
                            if f_read.tell() + chunk_size > end + 1:
                                data = f_read.read(end - f_read.tell() + 1)
                            else:
                                data = f_read.read(chunk_size)
                            if not data:
                                return
                            yield data
                    else:
                        data = f_read.read(end - start + 1)
                        if not data:
                            return
                        yield data

            # Set default values of start and end pointers
            start, end = 0, file_size - 1

            # Get the range header, and assign the values to start and end pointers
            range_header = request.headers.get('Range')
            if range_header:
                start, end = map(int, range_header.replace('bytes=', '').split('-'))
                if end == 0:
                    end = file_size - 1
                if start < 0 or end >= file_size or start > end:
                    # Range Not Satisfiable
                    return response_handle(code=416, response=f"Invalid Range Header {range_header}")
                content_length = end - start + 1

            response = Response(stream_file(start=start, end=end), mimetype="application/octet-stream",
                                status=200 if not range_header else 206)
            response.headers["Content-Disposition"] = "attachment; filename=%s" % file_name
            response.headers["Content-Length"] = content_length
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers["Accept-Ranges"] = "bytes"
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response


def start(easyucs_object=None):
    global easyucs
    easyucs = easyucs_object
