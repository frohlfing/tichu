# Befehl, um die Codeabdeckung zu starten:
# coverage run -m unittest discover -s tests
#
# Beispiel-Befehl, um einen bestimmten Unittest auszuführen:
# coverage run -m unittest tests.test_myclass.TestMyClass.test_myfunc
#
# Befehl, um den Bericht anzuzeigen:
# coverage report -m

@echo off
coverage run -m unittest discover -s tests
coverage report -m
