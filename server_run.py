import sys
import argparse
from forum.server import *
from forum.common import *




def main():
    parser = argparse.ArgumentParser(description='input ip and port')
    parser.add_argument('-i', '--ip', metavar='ip', type=str, default="25.42.9.199", help='ip adress for connection')
    parser.add_argument('-p', '--port', metavar='port', type=int, default=1200, help='port adress for connection')
    args = parser.parse_args()
    
    print(args.ip, args.port)
    Server(args.ip, args.port)



if __name__ == "__main__":
    main()
