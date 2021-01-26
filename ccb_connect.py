import threading
from os import getenv
from logging import basicConfig, FileHandler, DEBUG, error

import cx_Oracle
from dotenv import load_dotenv


class TABLE_NAME:
    SUBSCRIBER_OPTION = "ccb.ccb_subscriber_option"
    WS_LOG = "ccb.ccb_ws_log"

class CCB:
    def __init__(self):
        load_dotenv('ccb.env')
        cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_9")
        self.connection = self.connect_db(getenv("ccb_host"), getenv("ccb_port"), getenv("ccb_service_name"))
        basicConfig(handlers=[FileHandler(encoding='utf-8', filename='ccb.log')],
                    level=DEBUG,
                    format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
        if not self.check_connection():
            raise Exception("Couldn't connect to CCB DB.")

    def connect_db(self, ip, port, SID):
        dsnStr = cx_Oracle.makedsn(ip, port, service_name=SID)
        return cx_Oracle.connect(getenv("ccb_username"), getenv("ccb_password"), dsn=dsnStr)

    def check_connection(self):
        t = threading.Timer(10, self.connection.cancel)
        t.start()
        try:
            cursor = self.connection.cursor()
            cursor.execute("""SELECT 1 FROM DUAL""")
            t.cancel()
            print("CCB OK")
            del cursor
            return True
        except:
            error("Error:", exc_info=True)
            print("CCB DOWN")
            return False

    def get_data(self, query):
        t = threading.Timer(30, self.connection.cancel)
        t.start()
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            output = []
            print("Results:\n")
            for fname in cursor:
                output.append(fname)
            t.cancel()
            return output
        except:
            error("Error:", exc_info=True)
            return None

    def check_ccb(self, gsm_no, table_name=TABLE_NAME.SUBSCRIBER_OPTION):
        try:
            response = {}
            query = f"""select * from {table_name} where gsm_no='{gsm_no}' order by cr_date desc """
            result = self.get_data(query)
            print(result)
            if table_name == TABLE_NAME.SUBSCRIBER_OPTION:
                response.update({"cr_user": result[0][6],
                                 "sw_date": result[0][4],
                                 "exp_date": result[0][12],
                                 "option_status": result[0][-1]
                                 })
            elif table_name == TABLE_NAME.WS_LOG:
                response.update({"channel": result[0][3],
                                 "cr_date": result[0][4],
                                 })
            print("### END QUERY ###")
            return response
        except:
            error("Error:", exc_info=True)
            return None