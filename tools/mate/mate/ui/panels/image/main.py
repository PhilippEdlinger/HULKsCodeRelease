import os
import typing

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

import mate.net.utils as net_utils
import mate.ui.utils as ui_utils
from mate.net.nao import Nao
from mate.ui.panels._panel import _Panel
from mate.debug.colorlog import ColorLog

logger = ColorLog()


class Main(_Panel):
    name = "Image"
    shortcut = qtg.QKeySequence("Ctrl+I")
    fill_drop_down_signal = qtc.pyqtSignal()

    def __init__(self, main_window, nao: Nao, model: typing.Dict = None):
        super(Main, self).__init__(main_window, self.name, nao)
        ui_utils.loadUi(__file__, self)
        self.model = ui_utils.load_model(os.path.dirname(__file__) +
                                         "/model.json", model)
        self.dps_counter = 0
        self.dps_timer = qtc.QTimer()
        self.dps_timer.timeout.connect(self.update_dps)
        self.dps_timer.start(1000)

        self.timer = qtc.QTimer()
        self.timer.timeout.connect(self.update_image)
        self.spnFramerate.valueChanged.connect(self.set_timer)

        self.btnSnap.clicked.connect(self.snap)

        self.should_update = False
        self.data = None
        self.pixmap = qtg.QPixmap()

        self.cbxMount.completer().setFilterMode(qtc.Qt.MatchContains)
        self.cbxMount.completer().setCompletionMode(
            qtw.QCompleter.PopupCompletion)

        self.cbxMount.activated[str].connect(self.subscribe)
        self.cbxMount.setCurrentText(self.model["subscribe_key"])
        self.cbxMount.setFocus()

        self.fill_drop_down_signal.connect(self.fill_drop_down)

        if self.nao.is_connected():
            self.connect(self.nao)

    def update_dps(self):
        self.dpsLabel.setText(str(self.dps_counter))
        self.dps_counter = 0

    def set_timer(self, frame_rate: int):
        self.timer.stop()
        if frame_rate > 0 and self.nao.is_connected():
            self.timer.start(int(1000 / frame_rate))

    def subscribe(self, key, force=False):
        if self.nao.is_connected():
            if key != self.model["subscribe_key"] or force:
                self.nao.debug_protocol.unsubscribe(
                    self.model["subscribe_key"],
                    self.identifier)
                self.nao.debug_protocol.subscribe(
                    key,
                    self.identifier,
                    lambda d: self.data_received(d))
        self.model["subscribe_key"] = key

    def unsubscribe(self):
        if self.nao.is_connected():
            self.nao.debug_protocol.unsubscribe(self.model["subscribe_key"],
                                                self.identifier)

    def data_received(self, data: net_utils.Data):
        self.should_update = True
        self.dps_counter += 1
        self.data = data

    def connect(self, nao: Nao):
        self.nao = nao
        self.set_timer(self.spnFramerate.value())

        self.fill_drop_down()
        self.nao.debug_protocol.subscribe_msg_type(
            net_utils.DebugMsgType.list,
            self.identifier,
            self.fill_drop_down_signal.emit)

        if self.model["subscribe_key"]:
            self.subscribe(self.model["subscribe_key"], True)

    def fill_drop_down(self):
        self.cbxMount.clear()
        if self.model["subscribe_key"] not in self.nao.debug_data:
            self.cbxMount.addItem(self.model["subscribe_key"])
        for key, data in self.nao.debug_data.items():
            if data.isImage:
                self.cbxMount.addItem(key)
        self.cbxMount.setCurrentText(self.model["subscribe_key"])

    def update_image(self):
        if not self.should_update:
            return
        self.pixmap.loadFromData(self.data.data)

        w = self.label.width()
        h = self.label.height()

        self.label.setMinimumSize(1, 1)
        self.label.setPixmap(self.pixmap.scaled(
            w, h, qtc.Qt.KeepAspectRatio, transformMode=qtc.Qt.SmoothTransformation))

        self.should_update = False

    def snap(self):
        # Set filepath
        location_suggestion = os.path.join(os.getcwd(), os.getcwd(),
                                           "{}.png".format(
                                               self.model["subscribe_key"]))
        location, _ = qtw.QFileDialog. \
            getSaveFileName(self.widget(),
                            "Save snap",
                            location_suggestion,
                            options=qtw.QFileDialog.Options())
        if location == '':
            # If export is cancelled, exit gracefully
            logger.debug(__name__ + ": Saving Snapshot aborted.")
            return
        self.pixmap.save(location)

    def closeEvent(self, event):
        if self.nao.is_connected():
            self.unsubscribe()
            self.nao.debug_protocol.unsubscribe_msg_type(
                net_utils.DebugMsgType.list, self.identifier)
        self.timer.stop()
        self.deleteLater()
        super(Main, self).closeEvent(event)
