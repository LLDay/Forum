import sys
from PyQt5.QtWidgets import QApplication
from forum.client import *
from forum.common import *


def main():
    app = QApplication([])
    model = Model("127.0.0.1", 1100)

    window = Authentication(model)
    window.show()
    window.exec()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
