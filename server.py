import sys
from forum.server import *
from forum.common import *




def main():
    ip = "127.0.0.1"
    port = 1100
    #model = Model("127.0.0.1", 1100)
    Server(ip, port)
    


if __name__ == "__main__":
    main()
