# SPDX-FileCopyrightText: 2022 Renaissance Computing Institute. All rights reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-License-Identifier: LicenseRef-RENCI
# SPDX-License-Identifier: MIT

"""APSVIZ UI Data server."""
import json
import logging
import os

from enum import Enum
from typing import Union

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from common.logger import LoggingUtil
from src.pg_utils import PGUtils

# set the app version
APP_VERSION = 'v0.0.3'

# get the log level and directory from the environment.
# level comes from the container dockerfile, path comes from the k8s secrets
log_level: int = int(os.getenv('LOG_LEVEL', logging.INFO))
log_path: str = os.getenv('LOG_PATH', os.path.dirname(__file__))

# get the DB connection details for the asgs DB
asgs_dbname = os.environ.get('ASGS_DB_DATABASE')
asgs_username = os.environ.get('ASGS_DB_USERNAME')
asgs_password = os.environ.get('ASGS_DB_PASSWORD')

# get the DB connection details for the apsviz DB
apsviz_dbname = os.environ.get('APSVIZ_DB_DATABASE')
apsviz_username = os.environ.get('APSVIZ_DB_USERNAME')
apsviz_password = os.environ.get('APSVIZ_DB_PASSWORD')

# create the dir if it does not exist
if not os.path.exists(log_path):
    os.mkdir(log_path)

# create a logger
logger = LoggingUtil.init_logging("APSVIZ.ui-data.ui", level=log_level, line_format='medium', log_file_path=log_path)

# declare the FastAPI details
APP = FastAPI(
    title='APSVIZ UI Data',
    version=APP_VERSION
)

# declare app access details
APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@APP.get('/get_ui_data', status_code=200)
async def get_terria_map_catalog_data(grid_type: Union[str, None] = Query(default=None),
                                      event_type: Union[str, None] = Query(default=None),
                                      instance_name: Union[str, None] = Query(default=None),
                                      run_date: Union[str, None] = Query(default=None),
                                      end_date: Union[str, None] = Query(default=None),
                                      limit: Union[int, None] = Query(default=4)) -> json:
    """
    Gets the json formatted terria map UI catalog data.
    <br/>Note: Leave filtering params empty if not desired.
    <br/>&nbsp;&nbsp;&nbsp;grid_type: Filter by the name of the ASGS grid
    <br/>&nbsp;&nbsp;&nbsp;event_type: Filter by the event type
    <br/>&nbsp;&nbsp;&nbsp;instance_name: Filter by the name of the ASGS instance
    <br/>&nbsp;&nbsp;&nbsp;run_date: Filter by the run date in the form of yyyy-mm-dd
    <br/>&nbsp;&nbsp;&nbsp;end_date: Filter by the data between the run date and end date
    <br/>&nbsp;&nbsp;&nbsp;limit: Limit the number of catalog records returned (default is 4)
    """

    # init the returned html status code
    status_code = 200

    try:
        # create the postgres access object
        pg_db = PGUtils(apsviz_dbname, apsviz_username, apsviz_password)

        # prep the data for the DB SP
        grid_type = 'null' if not grid_type else f"'{grid_type}'"
        event_type = 'null' if not event_type else f"'{event_type}'"
        instance_name = 'null' if not instance_name else f"'{instance_name}'"
        run_date = 'null' if not run_date else f"'{run_date}'"
        end_date = 'null' if not end_date else f"'{end_date}'"

        # try to make the call for records
        ret_val = pg_db.get_terria_map_catalog_data(grid_type, event_type, instance_name, run_date, end_date, limit)
    except Exception as e:
        # return a failure message
        ret_val = f'Exception detected trying to get the terria map catalog data.'

        # log the exception
        logger.exception(ret_val)

        # set the status to a server error
        status_code = 500

    # return to the caller
    return JSONResponse(content=ret_val, status_code=status_code, media_type="application/json")


@APP.get('/get_ui_data_file', status_code=200)
async def get_terria_map_catalog_data_file(file_name: Union[str, None] = Query(default='apsviz.json'),
                                           grid_type: Union[str, None] = Query(default=None),
                                           event_type: Union[str, None] = Query(default=None),
                                           instance_name: Union[str, None] = Query(default=None),
                                           run_date: Union[str, None] = Query(default=None),
                                           end_date: Union[str, None] = Query(default=None),
                                           limit: Union[int, None] = Query(default=4)) -> FileResponse:
    """
    Returns the json formatted terria map UI catalog data in a file specified.
    <br/>Note: Leave filtering params empty if not desired.
    <br/>&nbsp;&nbsp;&nbsp;file_name: The name of the output file (default is apsviz.json)
    <br/>&nbsp;&nbsp;&nbsp;grid_type: Filter by the name of the ASGS grid
    <br/>&nbsp;&nbsp;&nbsp;event_type: Filter by the event type
    <br/>&nbsp;&nbsp;&nbsp;instance_name: Filter by the name of the ASGS instance
    <br/>&nbsp;&nbsp;&nbsp;run_date: Filter by the run date in the form of yyyy-mm-dd
    <br/>&nbsp;&nbsp;&nbsp;end_date: Filter by the data between the run date and end date
    <br/>&nbsp;&nbsp;&nbsp;limit: Limit the number of catalog records returned (default is 4)
    """
    # init the returned html status code
    status_code = 200

    # get the full file path to the dummy file
    file_path = os.path.join(os.path.dirname(__file__), file_name)

    # prep the data for the DB SP
    grid_type = 'null' if not grid_type else f"'{grid_type}'"
    event_type = 'null' if not event_type else f"'{event_type}'"
    instance_name = 'null' if not instance_name else f"'{instance_name}'"
    run_date = 'null' if not run_date else f"'{run_date}'"
    end_date = 'null' if not end_date else f"'{end_date}'"

    try:
        # create the postgres access object
        pg_db = PGUtils(apsviz_dbname, apsviz_username, apsviz_password)

        # try to make the call for records
        ret_val = pg_db.get_terria_map_catalog_data(grid_type, event_type, instance_name, run_date, end_date, limit)

        # write out the data to a file
        with open(file_path, 'w') as fp:
            json.dump(ret_val, fp)

    except Exception as e:
        # log the exception
        logger.exception(e)

        # set the status to a server error
        status_code = 500

    # return to the caller
    return FileResponse(path=file_path, filename=file_name, media_type='text/json')
