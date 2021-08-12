import os

PORT = 20110
 
SOURCE_DIR =  os.path.dirname(os.path.realpath( __file__ ) )
TOP_DIR =  os.path.dirname(os.path.realpath( SOURCE_DIR ) )
TPY_DIR = os.path.join(TOP_DIR,"Tpy")
TOP_TPY_DIR = os.path.join(TOP_DIR,"..","Tpy") 
LOG_DIR = os.path.join(TOP_DIR,"Log")
DATA_SOURCE_DIR = os.path.join(TOP_DIR,"Data","Source")
DATA_DIR = os.path.join(TOP_DIR,"Data")

RESTART_FILENAME = os.path.join(LOG_DIR,"restart.flag")
LOG_FILENAME = os.path.join(LOG_DIR,"server.out")
ERROR_FILENAME = os.path.join(LOG_DIR,"error.out")
