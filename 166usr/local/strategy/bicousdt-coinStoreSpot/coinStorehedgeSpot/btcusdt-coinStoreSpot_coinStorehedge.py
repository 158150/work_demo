
import os


path = os.path.abspath(os.path.dirname(__file__))
# import m111 as task
import sys
sys.path.append('/usr/local/strategy/public/coinStorehedge')
sys.path.append('../..')
import coinStorehedge as task

task.main('config_hedge.py')
# task._stop('config_hedge.py')





