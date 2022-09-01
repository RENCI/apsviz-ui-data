# SPDX-FileCopyrightText: 2022 Renaissance Computing Institute. All rights reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-License-Identifier: LicenseRef-RENCI
# SPDX-License-Identifier: MIT

import os
import psycopg2
import logging
import time
from common.logger import LoggingUtil


class PGUtils:
    def __init__(self, dbname, username, password, auto_commit=True):
        # get the log level and directory from the environment.
        # level comes from the container dockerfile, path comes from the k8s secrets
        log_level: int = int(os.getenv('LOG_LEVEL', logging.INFO))
        log_path: str = os.getenv('LOG_PATH', os.path.dirname(__file__))

        # create the dir if it does not exist
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        # create a logger
        self.logger = LoggingUtil.init_logging("APSVIZ.ui-data.pg_utils", level=log_level, line_format='medium', log_file_path=log_path)

        # get configuration params from the pods secrets
        host = os.environ.get('ASGS_DB_HOST')
        port = os.environ.get('ASGS_DB_PORT')

        # create a connection string
        self.conn_str = f"host={host} port={port} dbname={dbname} user={username} password={password}"

        # init the DB connection objects
        self.conn = None
        self.cursor = None
        self.auto_commit = auto_commit

        # get a db connection and cursor
        self.get_db_connection()

    def get_db_connection(self):
        """
        Gets a connection to the DB. performs a check to continue trying until
        a connection is made

        :return:
        """
        # init the connection status indicator
        good_conn = False

        # until forever
        while not good_conn:
            # check the DB connection
            good_conn = self.check_db_connection()

            try:
                # do we have a good connection
                if not good_conn:
                    # connect to the DB
                    self.conn = psycopg2.connect(self.conn_str)

                    # set the manner of commit
                    self.conn.autocommit = self.auto_commit

                    # create the connection cursor
                    self.cursor = self.conn.cursor()

                    # check the DB connection
                    good_conn = self.check_db_connection()

                    # is the connection ok now?
                    if good_conn:
                        # ok to continue
                        return
                else:
                    # ok to continue
                    return
            except (Exception, psycopg2.DatabaseError):
                good_conn = False

            self.logger.error(f'DB Connection failed. Retrying...')
            time.sleep(5)

    def check_db_connection(self) -> bool:
        """
        checks to see if there is a good connection to the DB

        :return: boolean
        """
        # init the return value
        ret_val = None

        try:
            # is there a connection
            if not self.conn or not self.cursor:
                ret_val = False
            else:
                # get the DB version
                self.cursor.execute("SELECT version()")

                # get the value
                db_version = self.cursor.fetchone()

                # did we get a value
                if db_version:
                    # update the return flag
                    ret_val = True

        except (Exception, psycopg2.DatabaseError):
            # connect failed
            ret_val = False

        # return to the caller
        return ret_val

    def __del__(self):
        """
        close up the DB

        :return:
        """

        # check/terminate the DB connection and cursor
        try:
            if self.cursor is not None:
                self.cursor.close()

            if self.conn is not None:
                self.conn.close()
        except Exception as e:
            self.logger.error(f'Error detected closing cursor or connection. {e}')

    def exec_sql(self, sql_stmt, is_select=True):
        """
        executes a sql statement

        :param sql_stmt:
        :param is_select:
        :return:
        """
        # init the return
        ret_val = None

        # insure we have a valid DB connection
        self.get_db_connection()

        try:
            # execute the sql
            ret_val = self.cursor.execute(sql_stmt)

            # get the data
            if is_select:
                # get the returned value
                ret_val = self.cursor.fetchall()

                # trap the return
                if len(ret_val) == 0:
                    # specify a return code on an empty result
                    ret_val = -1

        except Exception as e:
            self.logger.error(f'Error detected executing SQL: {sql_stmt}. {e}')
            ret_val = -2

        # return to the caller
        return ret_val

    def get_terria_map_catalog_data(self, grid_type, event_type, instance_name, run_date, end_date, limit):
        """
        gets the catalog data for the terria map UI

        :return:
        """

        # create the sql
        sql: str = f'SELECT public.get_terria_data_json(_grid_type:={grid_type}, _event_type:={event_type}, _instance_name:={instance_name}, _run_date:={run_date}, _end_date:={end_date}, _limit:={limit})'

        # get the data
        return self.exec_sql(sql)[0][0]
