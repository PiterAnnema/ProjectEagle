import sqlite3
import datetime
import os
import shutil

import config

class DBConnection:
    name = config.DB_NAME


    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DBConnection, cls).__new__(cls)
        return cls.instance


    def __init__(self):
        self.cur = None
        self.conn = None
        self.open()

    
    def open(self):
        try:
            conn = sqlite3.connect(self.name)
            cur = conn.cursor()
        except sqlite3.Error as e:
            print("Error connecting to database!", e)
        else:
            self.conn = conn
            self.cur = cur
    
    def close(self):
        if self.conn:
            self.conn.commit()
            self.cur.close()
            self.conn.close()


    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        self.close()


    def execute_query(self, query, params = ()):
        return self.cur.execute(query, params)


    @staticmethod
    def backup():
        dt = datetime.datetime.now()
        dt_str = dt.strftime("%d_%m_%Y_%H_%M_%S")
        dst = os.path.join(config.DB_BACKUP_DIR, dt_str + config.DB_NAME + '.bak')
        shutil.copyfile(config.DB_NAME, dst)