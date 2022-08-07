import json
from datetime import date, datetime
import psycopg2
import pymssql
import cx_Oracle
import pymysql


class SqlExecutor:
    def __init__(self):
        self.conn = None
        self.error_msg = ''
        self.query_result = []
        self.query_field = []

    # 数据库连接方法
    def connect_database(self, database_type, host, port, username, password, database, sid=None):
        if database_type == 0:  # 连接类型为pg
            try:
                self.conn = psycopg2.connect(host=host, port=port,
                                             user=username, password=password, database=database)
                return True
            except Exception as e:
                self.error_msg = str(e)
                return False
        elif database_type == 1:  # 连接类型为sqlServer
            host = '%s:%s' % (host, port)
            try:
                self.conn = pymssql.connect(host=host, database=database, user=username, password=password,
                                            charset='utf8')
                return True
            except Exception as e:
                self.error_msg = str(e)
                return False
        elif database_type == 2:  # 连接类型为oracle
            host = '%s:%s/%s' % (host, port, sid)
            try:
                self.conn = cx_Oracle.connect(username, password, host, encoding="UTF-8")
                return True
            except Exception as e:
                self.error_msg = str(e)
                return False

        elif database_type == 3:  # 连接类型为mysql
            try:
                self.conn = pymysql.connect(host=host, port=port, user=username, passwd=password, db=database)
                return True
            except Exception as e:
                self.error_msg = str(e)
                return False

    def query_db(self, cur, query, one=False):
        try:
            cur.execute(query)
        except Exception as e:
            self.error_msg = str(e)
            return False
        self.query_field = [i[0] for i in cur.description]
        r = [dict((cur.description[i][0], value)
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        sql_result = (r[0] if r else None) if one else r
        json_output = json.dumps(sql_result, cls=ComplexEncoder)
        self.query_result = json_output
        return True

    def execute_db(self, cur, query):
        try:
            cur.execute(query)
            self.conn.commit()
        except Exception as e:
            self.error_msg = str(e)
            return False
        return True


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
    sql = SqlExecutor()
    connect = sql.connect_database(0, "192.168.6.146", 5432, "postgres", "postgres", "bdp_dev")
    # connect = sql.connect_database(3, "192.168.2.11", 3306, "testww", "testww", "test")
    cur = sql.conn.cursor()
    if not connect:
        print(sql.error_msg)
    else:
        sql_script = 'DELETE FROM dsm_tables \n WHERE table_id = 29230'
        result = sql.execute_db(sql_script)
        # result = sql.query_db(cur,sql_script)
        if result:
            print(sql.query_result)
        else:
            print(sql.error_msg)
    cur.connection.close()
