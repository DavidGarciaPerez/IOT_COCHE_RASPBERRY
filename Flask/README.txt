pi@pi-g05:~ $ ls
Desktop    ImageMagick-7.0.8-14  MagPi     Proyecto      Templates
Documents  ImageMagick.tar.gz    Music     Public        testhttp
Downloads  labs                  Pictures  python_games  Videos
pi@pi-g05:~ $ cd Proyecto/
pi@pi-g05:~/Proyecto $ ls
ScriptsDefinitivos  ScriptsPruebas
pi@pi-g05:~/Proyecto $ cd ScriptsPruebas/
pi@pi-g05:~/Proyecto/ScriptsPruebas $ ls
ControlBaseDatos  ControlSensores  ControlServos  Flask
pi@pi-g05:~/Proyecto/ScriptsPruebas $ cd Flask/
pi@pi-g05:~/Proyecto/ScriptsPruebas/Flask $ ls
Prueba_Conexion.py  __pycache__
pi@pi-g05:~/Proyecto/ScriptsPruebas/Flask $ FLASK_APP=Prueba_Conexion.py flask run
 * Serving Flask app "Prueba_Conexion"
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
127.0.0.1 - - [19/Dec/2018 16:35:47] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [19/Dec/2018 16:35:48] "GET /favicon.ico HTTP/1.1" 404 -

###################### CONECTARSE DESDE IP PUBLICA #########################

FLASK_APP=Prueba_Completa.py flask run --host=0.0.0.0

############################################################################
