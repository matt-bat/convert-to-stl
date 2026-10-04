"""Native GUI regression checks for explicit batch control."""
import time
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings
from PySide6.QtTest import QTest
from app import Window, STYLE

@pytest.fixture(scope='module')
def qtapp():
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion');app.setStyleSheet(STYLE)
    return app

@pytest.fixture
def window(qtapp,tmp_path):
    w=Window();w.settings=QSettings(str(tmp_path/'settings.ini'),QSettings.IniFormat)
    w.location.setCurrentIndex(1);w.destination.setText(str(tmp_path/'output'));w.show();w.activateWindow();w.refresh();QTest.qWait(150)
    yield w
    if w.batch_running:
        w.stop()
        wait(qtapp,lambda:not w.batch_running)
    w.close();qtapp.processEvents()

def sample(name): return str(Path('samples',name).resolve())

def wait(app,condition,limit=45):
    deadline=time.monotonic()+limit
    while time.monotonic()<deadline:
        app.processEvents()
        if condition():return
        time.sleep(.015)
    raise AssertionError('GUI did not reach the expected state')

def test_one_file_waits_for_explicit_convert(qtapp,window):
    window.add_files([sample('box-10x20x30.obj')])
    QTest.qWait(400)
    assert window.proc is None
    assert window.rows[0]['status']=='Queued'
    assert not Path(window.destination.text()).exists()
    assert window.startbtn.isEnabled()
    assert window.startbtn.text()=='Convert 1 file'

def test_manual_batch_excludes_later_additions(qtapp,window):
    window.add_files([sample('box-10x20x30.step'),sample('box-10x20x30.3mf')])
    QTest.mouseClick(window.startbtn,Qt.LeftButton)
    window.add_files([sample('box-10x20x30.obj')])
    wait(qtapp,lambda:not window.batch_running)
    assert [r['status'] for r in window.rows]==['Done','Done','Queued']
    assert not (Path(window.destination.text())/'box-10x20x30 (2).stl').exists()
    assert window.startbtn.isEnabled()
    assert window.batch_done==2

def test_retry_only_requeues(qtapp,window,tmp_path):
    broken=tmp_path/'broken.3mf';broken.write_bytes(b'not a zip')
    window.add_files([str(broken)]);window.start()
    wait(qtapp,lambda:not window.batch_running)
    assert window.rows[0]['status']=='Error'
    QTest.mouseClick(window.retrybtn,Qt.LeftButton);QTest.qWait(250)
    assert window.rows[0]['status']=='Queued' and window.proc is None

def test_stop_keeps_remaining_files_pending(qtapp,window):
    window.add_files([sample('sphere-diameter-20.step'),sample('box-10x20x30.3mf')])
    window.start();window.stop()
    wait(qtapp,lambda:not window.batch_running)
    assert window.rows[0]['status']=='Stopped'
    assert window.rows[1]['status']=='Queued'
    assert window.startbtn.isEnabled()

def test_output_folder_is_required_without_auto_start(qtapp,window):
    window.destination.clear();window.add_files([sample('box-10x20x30.obj')])
    assert not window.startbtn.isEnabled()
    window.start();assert window.proc is None
    window.destination.setText(str(Path(window.temp.name)/'output'));window.refresh()
    assert window.startbtn.isEnabled() and window.proc is None

def test_keyboard_selection_and_resize(qtapp,window):
    window.add_files([sample('box-10x20x30.obj'),sample('box-10x20x30.3mf')])
    window.table.selectRow(0);window.refresh()
    assert len(window.table.selectionModel().selectedRows())==1
    assert window.removebtn.isEnabled() and window.detailsbtn.isEnabled()
    window.activateWindow();window.table.setFocus();QTest.qWait(150);QTest.keyClick(window.table,Qt.Key_Delete)
    assert len(window.rows)==1
    window.resize(900,580);qtapp.processEvents()
    assert window.startbtn.isVisible() and window.location.isVisible()
    assert not window.units.isVisible()
    assert window.auto_hint.isVisible()
    window.startbtn.setFocus();QTest.keyClick(window.startbtn,Qt.Key_Space)
    wait(qtapp,lambda:not window.batch_running)
    assert window.rows[0]['status']=='Done'


def test_settings_follow_pending_file_types(qtapp,window):
    window.add_files([sample('box-10x20x30.3mf')])
    assert window.auto_hint.isVisible()
    assert not window.quality.isVisible() and not window.units.isVisible()
    window.add_files([sample('box-10x20x30.step')])
    assert window.quality.isVisible() and not window.units.isVisible()
    window.add_files([sample('box-10x20x30.obj')])
    assert window.units.isVisible()
    window.units.setCurrentIndex(2)
    assert window.units.currentData()=='inch'
