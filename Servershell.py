with open("./login.py",'r') as login:
    exec(login.read())
    print("login start!")
with open('hall.py','r') as hall:
    exec(hall.read())
    print("hall start!")
with open('game.py','r') as game:
    exec(game.read())
    print("game start!")