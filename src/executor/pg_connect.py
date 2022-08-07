import json
from datetime import date, datetime
import psycopg2
import pymssql
import cx_Oracle

conn = psycopg2.connect(database="opmgmt_test", user="postgres", password="postgres", host="192.168.6.146", port="5432")

try:
    conn = pymssql.connect(host='192.168.2.11:49221', database='comm', user='sa', password='cecdata88', charset='utf8')
except Exception as e:
    print(e)
# conn = cx_Oracle.connect(dsn='192.168.5.117:49161/XE', user='system', password='oracle',
#                          encoding="UTF-8")
# conn = cx_Oracle.connect('system', 'oracle', '192.168.5.117:49161/XE', encoding="UTF-8")


# cur = conn.cursor()

# cur.execute("select * from data_modeling.model_base_dict LIMIT 20;")
# cur.execute("select frequency_no from opmgmt.sc_frequency LIMIT 20;")
# cur.execute("delete from opmgmt.sys_log where user_name = 'qatestuser' and id='44737';")

# rows = cur.fetchall()
#
# frequency_list = [row[0] for row in rows]
# print(frequency_list)
# 事务提交
# conn.commit()
# 关闭数据库连接
# conn.close()
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def query_db(query, one=False):
    cur = conn.cursor()
    cur.execute(query)
    r = [dict((cur.description[i][0], value)
              for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r


# my_query = query_db("select count(1) from opmgmt.sc_frequency;")
# my_query = query_db("select * from dbo.aaa;")
my_query = query_db("select * from HR.JOBS;")

json_output = json.dumps(my_query, cls=ComplexEncoder)

print(json_output)
