import os

PORT = 20050
TOP_DIR = os.path.dirname(os.path.realpath( __file__ ) )
TPY_DIR = os.path.join(os.path.dirname(TOP_DIR),"Tpy")
LOG_DIR = os.path.join(os.path.dirname(TOP_DIR),"Log")
TOP_TPY_DIR = os.path.join(os.path.dirname(TOP_DIR),"..","Tpy") 
DATA_DIR = os.path.join(os.path.dirname(TOP_DIR),"Data")

RESTART_FILENAME = os.path.join(LOG_DIR,"restart.flag")
LOG_FILENAME = os.path.join(LOG_DIR,"server.out")
ERROR_FILENAME = os.path.join(LOG_DIR,"error.out")
