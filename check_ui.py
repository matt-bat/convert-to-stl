from pathlib import Path
import time
from PySide6.QtWidgets import QApplication
from app import Window, STYLE, app_icon
app=QApplication([]);app.setStyle('Fusion');app.setStyleSheet(STYLE)
w=Window();w.show();app.processEvents()
Path('artifacts').mkdir(exist_ok=True)
w.grab().save('artifacts/interface-empty.png')
app_icon().pixmap(256,256).save('artifacts/icon.png')
w.add_files([str(Path('samples',n).resolve()) for n in ['box-10x20x30.step','box-10x20x30.3mf','sphere-diameter-20.step']])
w.location.setCurrentIndex(1);w.destination.setText(str(Path('artifacts/ui-output').resolve()));w.refresh();app.processEvents()
w.grab().save('artifacts/interface-queued.png')
w.resize(860,520);app.processEvents();w.grab().save('artifacts/interface-small.png')
w.resize(1080,700);w.start()
deadline=time.monotonic()+90
while w.batch_running and time.monotonic()<deadline:
    app.processEvents();time.sleep(.02)
assert not w.batch_running and all(r['status']=='Done' for r in w.rows),w.rows
w.table.selectRow(0);app.processEvents();w.grab().save('artifacts/interface.png')
w.close()
