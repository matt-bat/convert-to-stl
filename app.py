"""Convert to STL — native Windows desktop application."""
import json
import os
from pathlib import Path
import sys
import tempfile


def worker():
    from converter import convert
    result_path = Path(sys.argv[6])
    try:
        result = convert(sys.argv[2], sys.argv[3] or None, sys.argv[4], sys.argv[5])
        result['ok'] = True
    except Exception as exc:
        result = {'ok': False, 'error': str(exc) or type(exc).__name__}
    result_path.write_text(json.dumps(result), encoding='utf-8')
    return 0 if result['ok'] else 1


if '--worker' in sys.argv:
    sys.exit(worker())

from PySide6.QtCore import Qt, QProcess, QTimer, QUrl, QSettings, QPointF, QItemSelectionModel
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPen, QPixmap, QPolygonF, QLinearGradient, QShortcut, QKeySequence, QPalette
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QLineEdit, QProgressBar, QMessageBox, QStackedWidget,
    QScrollArea, QSizePolicy)

FORMATS = '.3mf .step .stp .iges .igs .obj .ply .off .glb .gltf .amf .stl'.split()
FILTER = '3D models (' + ' '.join('*' + x for x in FORMATS) + ')'
STYLE = '''
QWidget { font-family: "Segoe UI"; font-size: 10pt; color: #202724; }
QMainWindow { background: #edf0e9; }
QWidget#root { background: transparent; }
QLabel { background: transparent; }
QLabel#title { font-size: 20pt; font-weight: 600; }
QLabel#section { font-size: 11pt; font-weight: 650; }
QLabel#muted { color: #59625d; }
QLabel#emptyTitle { font-size: 17pt; font-weight: 600; }
QLabel#field { font-weight: 600; }
QFrame#workspace { background: rgba(255, 255, 255, 190); border: 1px solid rgba(255, 255, 255, 235); border-radius: 18px; }
QFrame#settings { background: rgba(224, 232, 216, 150); border-left: 1px solid rgba(255,255,255,180); border-top-right-radius: 18px; border-bottom-right-radius: 18px; }
QFrame#separator { background: #cdd3ce; max-height: 1px; }
QPushButton { background: rgba(255,255,255,185); border: 1px solid #a8b2aa; border-radius: 11px; padding: 8px 14px; font-weight: 600; min-height: 20px; }
QPushButton:hover { background: #e8eee9; border-color: #4c6858; }
QPushButton:pressed { background: #d7e4da; }
QPushButton:focus { outline: none; border: 2px solid #245b40; }
QPushButton:disabled { color: #707a73; background: #e7eae5; border-color: #cbd1cb; }
QPushButton#primary { background: #245b40; color: #ffffff; border-color: #245b40; padding: 10px 23px; }
QPushButton#primary:hover { background: #18462f; }
QPushButton#primary:focus { border: 2px solid #162a1d; background: #316d4d; }
QPushButton#primary:disabled { background: #d2dbd4; color: #58675c; border-color: #b4bfb6; }
QPushButton#quiet { background: transparent; border: 1px solid transparent; padding: 6px 9px; }
QPushButton#quiet:disabled { color: #818a83; background: transparent; border-color: transparent; }
QPushButton#quiet:hover { background: #dce5dd; border-color: #b6c3b9; }
QPushButton#quiet:focus { border: 2px solid #245b40; }
QLineEdit, QComboBox { background: rgba(255,255,255,195); border: 1px solid #a8b2aa; border-radius: 10px; padding: 8px; min-height: 22px; }
QLineEdit:focus, QComboBox:focus { border: 2px solid #245b40; }
QComboBox::drop-down { border: none; width: 23px; }
QComboBox::down-arrow { image: url("__CHEVRON__"); width: 10px; height: 6px; }
QScrollBar:vertical { background: #eef1ec; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #a4b0a6; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QComboBox:disabled, QLineEdit:disabled { background: #e7eae5; color: #667269; }
QTableWidget { background: transparent; border: none; selection-background-color: #d9e8dd; selection-color: #162d20; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid #edf0ed; }
QHeaderView::section { background: #eae6ec; color: #4d5750; border: none; border-bottom: 1px solid #d6dcd6; padding: 9px; font-weight: 600; }
QProgressBar { background: #d9dfd8; border: none; max-height: 4px; min-height: 4px; }
QProgressBar::chunk { background: #245b40; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip { background: #202e25; color: #ffffff; border: none; padding: 6px; }
'''
STYLE = STYLE.replace('__CHEVRON__', (Path(__file__).resolve().parent / 'assets/chevron.png').as_posix())


def label(text, name=None, wrap=True):
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    w.setWordWrap(wrap)
    return w


def button(text, callback, primary=False, quiet=False):
    b = QPushButton(text)
    if primary:
        b.setObjectName('primary')
    elif quiet:
        b.setObjectName('quiet')
    b.clicked.connect(callback)
    b.setCursor(Qt.PointingHandCursor)
    return b


def app_icon():
    pix = QPixmap(128, 128)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('#245b40'))
    p.drawRoundedRect(4, 4, 120, 120, 14, 14)
    p.setPen(QPen(QColor('#ffffff'), 5))
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(QPolygonF([QPointF(64, 26), QPointF(98, 45), QPointF(98, 83), QPointF(64, 103), QPointF(30, 83), QPointF(30, 45)]))
    p.drawLine(30, 45, 64, 65)
    p.drawLine(98, 45, 64, 65)
    p.drawLine(64, 65, 64, 103)
    p.end()
    return QIcon(pix)


class StudioCanvas(QWidget):
    """Soft translucent colour fields; no OS compositor dependency."""
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor('#e5ebdf'))
        gradient.setColorAt(.52, QColor('#f2eee7'))
        gradient.setColorAt(1, QColor('#e3e3ec'))
        p.fillRect(self.rect(), gradient)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(207, 163, 142, 38))
        p.drawEllipse(QPointF(self.width() * .84, self.height() * .22), 245, 245)
        p.setBrush(QColor(142, 172, 149, 26))
        p.drawEllipse(QPointF(self.width() * .12, self.height() * .82), 240, 180)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 90), 1.2))
        for offset in range(0, 80, 16):
            x, y = self.width() - 180 + offset, 42 + offset
            p.drawRoundedRect(x, y, 125, 125, 28, 28)
        p.end()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Convert to STL')
        self.setWindowIcon(app_icon())
        self.resize(1080, 700)
        self.setMinimumSize(860, 520)
        self.setAcceptDrops(True)
        self.rows = []
        self.proc = None
        self.active = None
        self.stopping = False
        self.batch = []
        self.batch_running = False
        self.batch_total = 0
        self.batch_done = 0
        self.temp = tempfile.TemporaryDirectory(prefix='convert_stl_')
        self.settings = QSettings('MattBat', 'ConvertToSTL')
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timeout)
        root = StudioCanvas()
        root.setObjectName('root')
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)
        icon = QLabel()
        icon.setPixmap(app_icon().pixmap(36, 36))
        header.addWidget(icon)
        header.addWidget(label('Convert to STL', 'title'))
        header.addStretch()
        header.addWidget(label('Your files. Your computer.', 'muted', False))
        layout.addLayout(header)

        workspace = QFrame()
        workspace.setObjectName('workspace')
        wl = QHBoxLayout(workspace)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        queue = QWidget()
        ql = QVBoxLayout(queue)
        ql.setContentsMargins(18, 16, 18, 14)
        ql.setSpacing(10)
        toolbar = QHBoxLayout()
        self.count = label('Files', 'section', False)
        toolbar.addWidget(self.count)
        toolbar.addStretch()
        self.addbtn = button('&Add files…', self.browse)
        self.addbtn.setToolTip('Add models to the queue (Ctrl+O). Nothing converts until you choose Convert.')
        toolbar.addWidget(self.addbtn)
        ql.addLayout(toolbar)
        self.stack = QStackedWidget()
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setContentsMargins(30, 25, 30, 25)
        el.addStretch()
        for text, style in [('Your next print starts here', 'emptyTitle'),
                            ('Drop your 3D files anywhere in this window.', 'muted'),
                            ('Add files, choose where to save, then Convert.', 'muted')]:
            item = label(text, style)
            item.setAlignment(Qt.AlignCenter)
            el.addWidget(item)
        el.addSpacing(18)
        empty_add = button('Add files…', self.browse)
        el.addWidget(empty_add, 0, Qt.AlignHCenter)
        el.addSpacing(14)
        formats = label('3MF · STEP · IGES · OBJ · PLY\nOFF · GLB / GLTF · AMF · STL', 'muted')
        formats.setAlignment(Qt.AlignCenter)
        el.addWidget(formats)
        el.addStretch()
        self.stack.addWidget(empty)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['File', 'Type', 'Status'])
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAccessibleName('Files awaiting conversion and their status')
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.table.cellDoubleClicked.connect(lambda row, col: self.details(row))
        self.stack.addWidget(self.table)
        ql.addWidget(self.stack, 1)
        actions = QHBoxLayout()
        self.removebtn = button('Remove', self.remove_selected, quiet=True)
        self.clearbtn = button('Clear finished', self.clear_finished, quiet=True)
        self.retrybtn = button('Requeue failed', self.retry_failed, quiet=True)
        self.detailsbtn = button('Details', self.selected_details, quiet=True)
        for b in (self.removebtn, self.clearbtn, self.retrybtn): actions.addWidget(b)
        actions.addStretch()
        actions.addWidget(self.detailsbtn)
        ql.addLayout(actions)
        separator = QFrame()
        separator.setObjectName('separator')
        ql.addWidget(separator)
        self.selection_info = label('Original files stay untouched. Existing STL files are never overwritten.', 'muted')
        self.selection_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.selection_info.setMinimumHeight(50)
        ql.addWidget(self.selection_info)
        wl.addWidget(queue, 1)

        rail = QFrame()
        rail.setObjectName('settings')
        rail.setFixedWidth(280)
        rl = QVBoxLayout(rail)
        rl.setContentsMargins(18, 18, 18, 18)
        rl.setSpacing(10)
        rl.addWidget(label('STL settings', 'section'))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_content = QWidget()
        sl = QVBoxLayout(settings_content)
        sl.setContentsMargins(0, 0, 3, 0)
        sl.setSpacing(7)
        destination_label = label('&Save location', 'field')
        self.location = QComboBox()
        self.location.addItems(['Beside original files', 'Selected folder'])
        destination_label.setBuddy(self.location)
        self.location.currentIndexChanged.connect(self.destination_mode)
        sl.addWidget(destination_label)
        sl.addWidget(self.location)
        self.destination = QLineEdit(self.settings.value('destination', ''))
        self.destination.setReadOnly(True)
        self.destination.setPlaceholderText('No folder selected')
        self.destination.setAccessibleName('Selected output folder')
        self.pickdest = button('Choose &folder…', self.choose_folder)
        sl.addWidget(self.destination)
        sl.addWidget(self.pickdest)
        self.location_hint = label('Each STL is saved beside its source file.', 'muted')
        sl.addWidget(self.location_hint)
        sl.addSpacing(6)
        qlabel = label('CAD surface &detail', 'field')
        self.quality = QComboBox()
        self.quality.addItems(['Fast', 'Balanced', 'Fine'])
        self.quality.setCurrentText('Balanced')
        qlabel.setBuddy(self.quality)
        sl.addWidget(qlabel)
        sl.addWidget(self.quality)
        self.quality_hint = label('STEP / IGES only', 'muted')
        sl.addWidget(self.quality_hint)
        self.cad_controls = (qlabel, self.quality, self.quality_hint)
        self.quality.setToolTip('Finer surface detail creates smoother curves and larger STL files. Existing mesh triangles are preserved.')
        sl.addSpacing(6)
        ulabel = label('Source &units', 'field')
        self.units = QComboBox()
        for title, value in [('Millimetres', 'millimeter'), ('Centimetres', 'centimeter'), ('Inches', 'inch'), ('Metres', 'meter')]:
            self.units.addItem(title, value)
        ulabel.setBuddy(self.units)
        sl.addWidget(ulabel)
        sl.addWidget(self.units)
        self.units_hint = label('OBJ / PLY / OFF / STL only', 'muted')
        sl.addWidget(self.units_hint)
        self.mesh_controls = (ulabel, self.units, self.units_hint)
        self.auto_hint = label('This format carries its own units and mesh detail. You’re ready to convert.', 'muted')
        sl.addWidget(self.auto_hint)
        self.units.setToolTip('Choose the units used in the source mesh. Other file formats use their embedded units automatically.')
        sl.addStretch()
        scroll.setWidget(settings_content)
        rl.addWidget(scroll, 1)
        rl.addWidget(label('Binary STL · millimetres', 'field'))
        rl.addWidget(label('Shape only. No colour or print settings.', 'muted'))
        wl.addWidget(rail)
        layout.addWidget(workspace, 1)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        footer = QHBoxLayout()
        text = QVBoxLayout()
        self.status = label('Ready when you are.', 'section')
        self.status_hint = label('Add one file or a whole batch. Nothing starts automatically.', 'muted')
        text.addWidget(self.status)
        text.addWidget(self.status_hint)
        footer.addLayout(text, 1)
        self.openbtn = button('Open output', self.open_output)
        self.cancelbtn = button('Stop', self.stop)
        self.startbtn = button('Convert to STL', self.start, primary=True)
        footer.addWidget(self.openbtn)
        footer.addWidget(self.cancelbtn)
        footer.addWidget(self.startbtn)
        layout.addLayout(footer)
        self.shortcuts = []
        for key, action in [('Ctrl+O', self.browse), ('Ctrl+Return', self.start)]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(action)
            self.shortcuts.append(shortcut)
        remove_shortcut = QShortcut(QKeySequence('Delete'), self.table)
        remove_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        remove_shortcut.activated.connect(self.remove_selected)
        self.shortcuts.append(remove_shortcut)
        order = [self.addbtn, self.table, self.removebtn, self.clearbtn, self.retrybtn,
                 self.detailsbtn, self.location, self.destination, self.pickdest,
                 self.quality, self.units, self.openbtn, self.cancelbtn, self.startbtn]
        for a, b in zip(order, order[1:]): self.setTabOrder(a, b)
        self.destination_mode()
        self.refresh()

    def destination_mode(self, *args):
        selected = self.location.currentIndex() == 1
        self.destination.setVisible(selected)
        self.pickdest.setVisible(selected)
        self.location_hint.setText('Every STL in this batch goes into the selected folder.' if selected else 'Each STL is saved beside its source file.')
        if hasattr(self, 'startbtn'): self.refresh()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Save STL files to', self.destination.text())
        if folder:
            self.destination.setText(folder)
            self.destination.setCursorPosition(0)
            self.destination.setToolTip(folder)
            self.settings.setValue('destination', folder)
            self.refresh()

    def browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose 3D models', '', FILTER)
        self.add_files(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_files([u.toLocalFile() for u in event.mimeData().urls()])
        event.acceptProposedAction()

    def add_files(self, files):
        known = {os.path.normcase(r['path']) for r in self.rows}
        rejected = []
        for f in files:
            p = Path(f).resolve()
            if not p.is_file() or p.suffix.lower() not in FORMATS:
                rejected.append(p.name)
                continue
            if os.path.normcase(str(p)) not in known:
                self.rows.append({'path': str(p), 'status': 'Queued', 'message': 'Waiting for you to click Convert.', 'output': None})
                known.add(os.path.normcase(str(p)))
        self.refresh()
        if rejected:
            QMessageBox.information(self, 'Some items were not added', 'Unsupported files or folders:\n' + '\n'.join(rejected[:12]) + '\n\nAdd individual 3MF, STEP, IGES, OBJ, PLY, OFF, GLB, GLTF, AMF or STL files. G-code cannot restore the original model.')

    def refresh(self):
        selected = {i.row() for i in self.table.selectionModel().selectedRows()}
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            display = {'Queued': 'Ready', 'Done': 'Saved', 'Warning': 'Check mesh'}.get(r['status'], r['status'])
            for j, value in enumerate((Path(r['path']).name, Path(r['path']).suffix[1:].upper(), display)):
                item = QTableWidgetItem(value)
                item.setToolTip(r['path'] if j == 0 else r['message'])
                if j == 2:
                    item.setForeground(QColor({'Done': '#245b40', 'Warning': '#805300', 'Error': '#ac2935', 'Converting': '#245b40'}.get(r['status'], '#59625d')))
                self.table.setItem(i, j, item)
        for i in selected:
            if i < len(self.rows):
                self.table.selectionModel().select(self.table.model().index(i, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.table.blockSignals(False)
        self.stack.setCurrentIndex(1 if self.rows else 0)
        self.count.setText(f'Files · {len(self.rows)}' if self.rows else 'Files')
        queued = sum(r['status'] == 'Queued' for r in self.rows)
        busy = self.batch_running
        self.startbtn.setText(f'Convert {queued} file' + ('' if queued == 1 else 's') if queued else 'Convert to STL')
        if busy: self.startbtn.setText('Converting…')
        self.startbtn.setToolTip('Start the queued files (Ctrl+Enter)')
        self.startbtn.setEnabled(bool(queued) and not busy and (self.location.currentIndex() == 0 or bool(self.destination.text())))
        self.retrybtn.setVisible(any(r['status'] in ('Error', 'Stopped') for r in self.rows))
        self.retrybtn.setEnabled(not busy)
        self.clearbtn.setEnabled(not busy and any(r['status'] != 'Queued' for r in self.rows))
        self.cancelbtn.setVisible(busy)
        for control in (self.location, self.pickdest, self.quality, self.units): control.setEnabled(not busy)
        self.openbtn.setVisible(any(r.get('output') for r in self.rows))
        self.progress.setVisible(busy or bool(self.batch_done))
        pending_formats = {Path(r['path']).suffix.lower() for r in self.rows if r['status'] in ('Queued', 'Converting')}
        show_cad = not self.rows or bool(pending_formats & {'.step', '.stp', '.iges', '.igs'})
        show_mesh = not self.rows or bool(pending_formats & {'.obj', '.ply', '.off', '.stl'})
        for control in self.cad_controls: control.setVisible(show_cad)
        for control in self.mesh_controls: control.setVisible(show_mesh)
        self.auto_hint.setVisible(bool(pending_formats) and not show_cad and not show_mesh)
        self.clearbtn.setVisible(any(r['status'] not in ('Queued', 'Converting') for r in self.rows))
        self.removebtn.setVisible(bool(self.rows))
        self.detailsbtn.setVisible(bool(self.rows))
        self.progress.setRange(0, max(1, self.batch_total))
        self.progress.setValue(self.batch_done)
        if not busy:
            if queued:
                self.status.setText(f'{queued} file' + ('' if queued == 1 else 's') + ' ready to convert')
                self.status_hint.setText('Choose an output folder to continue.' if self.location.currentIndex() and not self.destination.text() else 'Check your settings, then click Convert. Originals stay untouched.')
            elif self.rows:
                good = sum(r['status'] in ('Done', 'Warning') for r in self.rows)
                failed = sum(r['status'] == 'Error' for r in self.rows)
                warnings = sum(r['status'] == 'Warning' for r in self.rows)
                self.status.setText(f'{good} saved' + (f' · {warnings} to check' if warnings else '') + (f' · {failed} failed' if failed else ''))
                self.status_hint.setText('Select a file for its result. Requeue failed files to try again.' if failed else 'Select a file for details, or open the output folder.')
            else:
                self.status.setText('Ready when you are.')
                self.status_hint.setText('Add one file or a whole batch. Nothing starts automatically.')
        self.selection_changed()

    def selection_changed(self):
        selection = self.table.selectionModel().selectedRows()
        self.removebtn.setEnabled(bool(selection) and not self.batch_running)
        self.detailsbtn.setEnabled(len(selection) == 1)
        if len(selection) == 1:
            r = self.rows[selection[0].row()]
            self.selection_info.setText(r.get('warning') or r['message'])
            self.selection_info.setToolTip(r.get('output') or r['path'])
        elif selection:
            self.selection_info.setText(f'{len(selection)} files selected. Remove takes them out of this queue; it does not delete them.')
        else:
            self.selection_info.setText('Original files stay untouched. Existing STL files are never overwritten.')
            self.selection_info.setToolTip('')

    def start(self):
        if self.batch_running:
            return
        if self.location.currentIndex() and not self.destination.text():
            self.refresh()
            return
        self.batch = [r for r in self.rows if r['status'] == 'Queued']
        if not self.batch:
            return
        self.batch_options = (self.destination.text() if self.location.currentIndex() else '', self.quality.currentText(), self.units.currentData())
        self.batch_total = len(self.batch)
        self.batch_done = 0
        self.stopping = False
        self.batch_running = True
        self._next()

    def _next(self):
        if self.stopping or not self.batch:
            self.batch_running = False
            self.refresh()
            if self.stopping:
                self.status.setText('Conversion stopped')
                self.status_hint.setText('Completed files were kept. Requeue stopped files or convert the remaining queue.')
            return
        pending = self.batch.pop(0)
        self.active = pending
        pending.update(status='Converting', message='Reading and converting geometry…')
        self.result_path = Path(self.temp.name) / 'result.json'
        self.result_path.unlink(missing_ok=True)
        self.proc = QProcess(self)
        process = self.proc
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.finished.connect(self.finished)
        process.errorOccurred.connect(self.process_error)
        process.readyReadStandardOutput.connect(lambda: process.readAllStandardOutput())
        output_dir, quality, units = self.batch_options
        args = ['--worker', pending['path'], output_dir, quality, units, str(self.result_path)]
        if not getattr(sys, 'frozen', False): args.insert(0, str(Path(__file__).resolve()))
        process.start(sys.executable, args)
        self.timer.start(20 * 60 * 1000)
        self.refresh()
        self.status.setText(f'Converting {self.batch_done + 1} of {self.batch_total}')
        self.status_hint.setText(Path(pending['path']).name)

    def process_error(self, error):
        if error == QProcess.FailedToStart: self.finished(-1, QProcess.CrashExit)

    def finished(self, code, exit_status):
        if self.proc is None:
            return
        self.timer.stop()
        process = self.proc
        self.proc = None
        process.deleteLater()
        try:
            result = json.loads(self.result_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            result = {'ok': False, 'error': 'Stopped by you.' if self.stopping else 'Conversion process ended unexpectedly. Try a smaller file or export a mesh from your CAD app.'}
        if result.get('ok'):
            dimensions = ' × '.join(str(x) for x in result['size_mm']) + ' mm'
            self.active.update(status='Warning' if result['warning'] else 'Done', output=result['output'], warning=result['warning'], message=f"{result['triangles']:,} triangles · {dimensions}")
            self.active['details'] = self.active['message'] + '\n\nSaved to:\n' + result['output'] + ('\n\n' + result['warning'] if result['warning'] else '')
        else:
            self.active.update(status='Stopped' if self.stopping else 'Error', message=result.get('error', 'Unknown conversion error.'))
        self.active = None
        self.batch_done += 1
        self.refresh()
        QTimer.singleShot(0, self._next)

    def stop(self):
        self.stopping = True
        self.batch = []
        if self.proc: self.proc.kill()
        else: self._next()

    def timeout(self):
        if self.proc:
            self.result_path.write_text(json.dumps({'ok': False, 'error': 'Conversion exceeded 20 minutes. Try Fast CAD detail or split the model.'}), encoding='utf-8')
            self.proc.kill()

    def retry_failed(self):
        if self.batch_running: return
        for row in self.rows:
            if row['status'] in ('Error', 'Stopped'):
                row.update(status='Queued', message='Waiting for you to click Convert.')
        self.refresh()

    def remove_selected(self):
        if self.batch_running:
            return
        selected = {i.row() for i in self.table.selectionModel().selectedRows()}
        self.rows = [r for i, r in enumerate(self.rows) if i not in selected]
        self.table.clearSelection()
        self.refresh()

    def clear_finished(self):
        if self.batch_running: return
        self.rows = [r for r in self.rows if r['status'] == 'Queued']
        self.table.clearSelection()
        self.refresh()

    def selected_details(self):
        selected = self.table.selectionModel().selectedRows()
        if len(selected) == 1: self.details(selected[0].row())

    def details(self, row):
        r = self.rows[row]
        QMessageBox.information(self, Path(r['path']).name, r.get('details', r['message']) + '\n\nSource:\n' + r['path'])

    def open_output(self):
        selection = self.table.currentRow()
        r = self.rows[selection] if 0 <= selection < len(self.rows) and self.rows[selection].get('output') else next((r for r in reversed(self.rows) if r.get('output')), None)
        if r: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(r['output']).parent)))

    def closeEvent(self, event):
        if self.batch_running:
            if QMessageBox.question(self, 'Conversion in progress', 'Stop this batch and close?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                event.ignore()
                return
            self.stopping = True
            self.batch = []
            if self.proc:
                process = self.proc
                process.kill()
                process.waitForFinished(3000)
        self.temp.cleanup()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    win = Window()
    win.show()
    if len(sys.argv) > 2 and sys.argv[1] == '--ui-check':
        def capture():
            win.grab().save(sys.argv[2])
            win.close()
        QTimer.singleShot(500, capture)
    elif len(sys.argv) > 1:
        QTimer.singleShot(0, lambda: win.add_files(sys.argv[1:]))
    sys.exit(app.exec())

