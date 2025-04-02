import atheris
from atheris.instrument_bytecode import instrument_func
import sys
import os

@instrument_func
def checkVerifyAgainst(hostname):
	os.system('vula verify against ' + str(hostname))

@instrument_func
def checkVulaAlone(data):
	os.system('vula ' + str(data))

atheris.Setup(sys.argv, checkVerifyAgainst) #change the function name to fuzz something else
atheris.Fuzz()