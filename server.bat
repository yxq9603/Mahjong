@ECHO OFF
start cmd /k python .server/login.py
start cmd /k python .server/hall.py
cmd /k python .server/game.py