import sys
from PyQt5.QtWidgets import QApplication
from forum.client import Model
from socket import *
import argparse


def parse_arguments():
    default_ip = '25.42.9.199'
    default_port = 1200
    parser = argparse.ArgumentParser(description="Forum client")
    parser.add_argument('-i', '--ip', type=str, metavar='address',
                        nargs=1, default=default_ip, help=f'specify ip address (default: {default_ip})')
    parser.add_argument('-p', '--port', type=int, metavar='port',
                        nargs=1, default=default_port, help=f'specify port number (default: {default_port})')
    return parser.parse_args()


def main():
    args = parse_arguments()
    app = QApplication([])
    model = Model(args.ip, args.port)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
