"""
test example for the ui
"""


from event.engine import EventEngine

from engine import MainEngine
from ui import MainWindow, create_qapp, QtGui


def main():
    """"""

    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    # font_families = QtGui.QFontDatabase.families()
    # print(f"all font families supported are {'***' * 10} \n {font_families}")

    cn_families = QtGui.QFontDatabase.families(QtGui.QFontDatabase.WritingSystem.SimplifiedChinese)
    print(f"chinese supported font families supported are {'***' * 10} \n {cn_families}")

    # main_engine.add_gateway(CtpGateway)
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
