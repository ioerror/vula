import atheris
import sys
import os

@atheris.instrument_func
def checkVerifyAgainst(hostname):
	os.system('vula verify against ' + str(hostname))

@atheris.instrument_func
def checkVulaAlone(data):
	os.system('vula ' + str(data))

atheris.Setup(sys.argv, checkVerifyAgainst) #change the function name to fuzz something else
atheris.Fuzz()