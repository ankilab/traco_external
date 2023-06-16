import PyQt6
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, \
    QGridLayout, QWidget, QMessageBox, QLabel, QCheckBox, \
        QSizePolicy, QComboBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtCore import pyqtRemoveInputHook
import pandas as pd
import pyqtgraph as pg
import imageio as io
import numpy as np
import json
import os
import matplotlib.pyplot as plt

from pdb import set_trace


def trace():
    pyqtRemoveInputHook()
    set_trace()


#### ROI helper class
class ROI:
    def __init__(self, pos=[100, 100], shown=True):
        """
        ROI class that keeps ROI position and if it is active.
        :param pos: list, tuple or pyqtgraph Point
        :param shown: boolean
        """
        self.pos = pos
        self.shown = shown

    def serialize(self):
        """
        Serializes object to dictionary
        :return: dict
        """
        return {'pos': tuple(self.pos), 'shown': self.shown}

## Custom ImageView
class ImageView(pg.ImageView):
    keysignal = pyqtSignal(int)
    mousesignal = pyqtSignal(int)

    def __init__(self, im, parent=None):
        """
        Custom ImageView class to handle ROIs dynamically
        :param im: The image to be shown
        :param rois: The rois for this image
        :param parent: The parent widget where the window is embedded
        """
        # Set Widget as parent to show ImageView in Widget
        super().__init__(parent=parent)

        # Set 2D image
        self.setImage(im)
        self.colors = ['#1a87f4', '#ebf441', '#9b1a9b', '#42f489']
        
        self.realRois = []

        for i in range(4):
            t = pg.CrosshairROI([-1, -1])
            t.setPen(pg.mkPen(self.colors[i]))
            t.aspectLocked = True
            t.rotateAllowed = False
            ### Storing, not actually saving! ###
            # t.sigRegionChanged.connect(self.saveROIs)
            self.realRois.append(t)
            self.getView().addItem(self.realRois[-1])
        
        self.getView().setMenuEnabled(False)

        # Set reference to stack
        self.stack = parent

    def mousePressEvent(self, e):
        # Important, map xy coordinates to scene!
        pos = e.pos()
        xy = self.getImageItem().mapFromScene(pos.x(), pos.y())
        modifiers = QApplication.keyboardModifiers()

        # Set posterior point
        if e.button() == Qt.MouseButton.LeftButton:
        #if e.button() == Qt.MouseButton.LeftButton and modifiers == Qt.KeyboardModifier.ControlModifier:
            self.realRois[self.stack.annotating].setPos(xy)
            self.realRois[self.stack.annotating].show() 

            # Check checkbox
            self.mousesignal.emit(self.stack.annotating)

    def setROIs(self, rois):
        """Set ROIs from a list of ROI instances

        Args:
            rois (list[ROI]): The ROIs of the current frame
        """
        for i, r in enumerate(rois):
            self.realRois[i].setPos(r.pos)
            
            if r.shown:
                self.realRois[i].show()
            else:
                self.realRois[i].hide()

    def getROIs(self):
        """Saves and returns the current ROIs"""
        
        return [ROI(r.pos(), r.isVisible()) for r in self.realRois]

    def keyPressEvent(self, ev):
        """Pass keyPressEvent to parent classes
        
        Parameters
        ----------
        ev : event
            key event
        """
        self.keysignal.emit(ev.key())


##################
### STACK
##################
class Stack(QWidget):
    def __init__(self, fn, rois=None):
        """
        Main Widget to keep track of the stack (or movie) and the ROIs.
        :param stack: ndarray
        :param rois: None or list of saved ROIs (json)
        """
        super().__init__()

        self.fn = fn
        self.colors = ['#1a87f4', '#c17511', '#9b1a9b', '#0c7232']
        
        self.curId = 0
        self.freeze = False

        self.im = np.asarray(io.mimread(self.fn, memtest=False))
        self.dim = self.im.shape        

        self.rois = self.createROIs(rois)
        
        self.w = ImageView(self.im.transpose(0, 2, 1, 3), parent=self)

        ### Create Grid Layout and add the main image window to layout ###
        self.l = QGridLayout()
        self.l.addWidget(self.w, 0, 0, 12, 1)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.w.setSizePolicy(sizePolicy)
        self.w.show()

        self.w.sigTimeChanged.connect(self.changeZ)

        self.w.keysignal.connect(self.keyPress)
        self.w.mousesignal.connect(self.mousePress)

        ### Checkboxes for point selection ###
        self.annotate = QComboBox()
        self.annotate.addItems([
            f"Hexbug {i}" for i in range(1,5)
        ])
        self.annotate.currentIndexChanged.connect(self.changeAnnotating)
        self.annotating = 0

        ### FCK don't repeat yourself
        self.p1 = QCheckBox("show/select")
        self.p1.setStyleSheet("color: #{}".format(self.colors[0]))
        self.p1.stateChanged.connect(self.checkROIs)
        self.p2 = QCheckBox("show/select")
        self.p2.setStyleSheet("color: #{}".format(self.colors[1]))
        self.p2.stateChanged.connect(self.checkROIs)
        self.p3 = QCheckBox("show/select")
        self.p3.setStyleSheet("color: #{}".format(self.colors[2]))
        self.p3.stateChanged.connect(self.checkROIs)
        self.p4 = QCheckBox("show/select")
        self.p4.setStyleSheet("color: #{}".format(self.colors[3]))
        self.p4.stateChanged.connect(self.checkROIs)

        ### Add checkboxes and labels to GUI ###
        self.l.addWidget(QLabel("Hexbug 1"), 0, 1)
        self.l.addWidget(self.p1, 1, 1)
        self.l.addWidget(QLabel("Hexbug 2"), 2, 1)
        self.l.addWidget(self.p2, 3, 1)
        self.l.addWidget(QLabel("Hexbug 3"), 4, 1)
        self.l.addWidget(self.p3, 5, 1)
        self.l.addWidget(QLabel("Hexbug 4"), 6, 1)
        self.l.addWidget(self.p4, 7, 1)

        self.l.addWidget(QLabel("Currently annotating:"), 8, 1)
        self.l.addWidget(self.annotate, 9, 1)

        self.autoMove = QCheckBox("Automatically change frame")
        self.autoMove.setChecked(True)
        self.l.addWidget(self.autoMove, 10, 1)

        ### Add another empty label to ensure nice GUI formatting ###
        self.ll = QLabel()
        self.ll.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding))
        self.l.addWidget(self.ll, 11, 1)

    
        self.setLayout(self.l)

        ### Update once the checkboxes and the ROIs ###
        self.updateCheckboxes()
        self.checkROIs()
        self.w.setROIs(self.rois[0])

    def changeAnnotating(self):
        self.annotating = self.annotate.currentIndex()

    def createROIs(self, rois=None):
        tmp_rois = [[ROI([100 + i * 25, 100 + i * 25], False) for i in range(4)]
                for _ in range(self.dim[0])]

        # Loads saved ROIs
        if type(rois) == list:
            for r in rois:
                tmp_rois[r['z']][r['id']].pos = r['pos']
                tmp_rois[r['z']][r['id']].shown = True

        return tmp_rois

    def updateCheckboxes(self):
        self.freeze = True
        self.p1.setChecked(self.rois[self.curId][0].shown)
        self.p2.setChecked(self.rois[self.curId][1].shown)
        self.p3.setChecked(self.rois[self.curId][2].shown)
        self.p4.setChecked(self.rois[self.curId][3].shown)

        self.freeze = False

    def checkROIs(self):
        # Save only when in "non-freeze" mode,
        #  meaning if I change z, and thus the checkboxes,
        #  do NOT save the current checkboxes, as it makes no sense.
        if not self.freeze:
            if self.p1.isChecked():
                self.w.realRois[0].show()
            else:
                self.w.realRois[0].hide()

            if self.p2.isChecked():
                self.w.realRois[1].show()
            else:
                self.w.realRois[1].hide()

            if self.p3.isChecked():
                self.w.realRois[2].show()
            else:
                self.w.realRois[2].hide()

            if self.p4.isChecked():
                self.w.realRois[3].show()
            else:
                self.w.realRois[3].hide()

    def mousePress(self, roi_id):
        if roi_id == 0:
         
            self.p1.setChecked(True)

        elif roi_id == 1:
  
            self.p2.setChecked(True)

        elif roi_id == 2:
  
            self.p3.setChecked(True)

        elif roi_id == 3:
            
            self.p4.setChecked(True)

        if self.autoMove.isChecked():
            self.forceStep(1)

    def forceStep(self, direction=1):
        self.w.setCurrentIndex(self.curId+direction)

    def changeZ(self, *args, force_step=0):
        # Save ROIs
        self.rois[self.curId] = self.w.getROIs()
            

        # New image position
        self.curId = self.w.currentIndex
        self.updateCheckboxes()

        # Set current image and current ROI data
        self.w.setROIs(self.rois[self.curId])


    def keyPress(self, key):
        # AD for -1 +1
        if key == Qt.Key.Key_D:
             self.forceStep(1)

        elif key == Qt.Key.Key_A:
            self.forceStep(-1)

        elif key == Qt.Key.Key_1:
            self.p1.setChecked(not self.p1.isChecked())

        elif key == Qt.Key.Key_2:
            self.p2.setChecked(not self.p2.isChecked())

        elif key == Qt.Key.Key_3:
            self.p3.setChecked(not self.p3.isChecked())

        elif key == Qt.Key.Key_4:
            self.p4.setChecked(not self.p4.isChecked())

        elif key == Qt.Key.Key_Q:
            self.p1.setChecked(True)
            self.p2.setChecked(True)
            self.p3.setChecked(True)
            self.p4.setChecked(True)

    def keyPressEvent(self, e):
        # Emit Save command to parent class
        if e.key() == Qt.Key.Key_S:
            self.w.keysignal.emit(e.key())

######################
######################
##     MAIN WINDOW  ##
######################
######################
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_fn = None
        self.status = self.statusBar()
        self.menu = self.menuBar()

        self.file = self.menu.addMenu("&File")
        self.file.addAction("Open", self.open)
        self.file.addAction("Save", self.save)
        self.file.addAction("Exit", self.close)

        self.features = self.menu.addMenu("&Features")
        self.features.addAction("Plot trajectories", self.plotTrajectories)
        self.features.addAction("Export trajectories to CSV", self.export)

        self.fn = None
        self.history = []

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("TRACO Annotator")

    def plotTrajectories(self):
        if not self.fn:
            return

        plt.figure()
        plt.imshow(self.stack.im[0])

        ts = [[] for i in range(4)]
        xys = [[] for i in range(4)]

        for i in range(self.stack.dim[0]):
            for j in range(4):
                r = self.stack.rois[i][j]

                if r.shown:
                    ts[j].append(i)
                    xys[j].append(r.pos)

        for i, xy in enumerate(xys):
            for j in xy:
                plt.scatter(*j, color="#"+self.stack.colors[i])

        
        plt.xlim([0, self.stack.dim[2]])
        plt.ylim([self.stack.dim[1], 0])
        plt.show()

    def export(self):
        with open('settings.json', 'r') as file:
            keys_2_settings = json.load(file)

        fn = QFileDialog.getSaveFileName(directory=keys_2_settings["default_directory"], filter="*.csv")[0]

        if fn:
            tmp = []

            for j in range(4):
                for i in range(len(self.stack.rois)):
                    r = self.stack.rois[i][j]

                    e = {
                        't': i,
                        'hexbug': j,
                        'x': r.pos[1],
                        'y': r.pos[0]
                    }

                    if r.shown:
                        tmp.append(e)

            pd.DataFrame(tmp).to_csv(fn)
            
            QMessageBox.information(self, "Data exported.", f"Data saved at\n{fn}")


    def close(self):
        ok = QMessageBox.question(self, "Exiting?",
            "Do you really want to exit the annotation program? Ensure you save for progress.")

        if ok == QMessageBox.Yes:
            super().close()

    def connectROIs(self):
        for i in range(len(self.stack.w.realRois)):
            self.stack.w.realRois[i].sigRegionChanged.connect(self.p)

    def updateStatus(self):
        """Shows the current "z-value", i.e. the image ID, and its dimensions
        """
        self.status.showMessage('z: {} x: {} y: {}'.format(self.stack.w.currentIndex,
                                                           self.stack.dim[0],
                                                           self.stack.dim[1]))

    def open(self):
        # Load some settings, currently only the default directory
        with open('settings.json', 'r') as file:
            keys_2_settings = json.load(file)

        # Select a file
        fn = QFileDialog.getOpenFileName(directory=keys_2_settings["default_directory"])[0]
        print(fn)

        self.status.showMessage(fn)

        # Was a file selected? Go for it!
        if fn:
            self.fn = fn # assuming these are mp4 files...
            self.fn_rois = fn.replace("mp4", "traco")

            # If ROI file is existing, read and decode
            if os.path.isfile(self.fn_rois):
                with open(self.fn_rois, 'r') as fp:
                    rois = json.load(fp)['rois']

            else:
                rois = None

            # Create new Image pane and show first image,
            # connect slider and save function
            self.stack = Stack(self.fn, rois=rois)
            self.setCentralWidget(self.stack)

            self.stack.w.sigTimeChanged.connect(self.updateStatus)
            self.stack.w.keysignal.connect(self.savekeyboard)

            self.connectROIs()

            self.setWindowTitle("TRACO Annotator | Working on file {}".format(self.fn))

    def p(self, e):
        """Shows current position
        
        Parameters
        ----------
        e : event
            Mouse event carrying the position
        """
        self.status.showMessage("{}".format(e.pos()))

    def save(self):
        """Saves all ROIs to file
        """
        if self.fn_rois:
            with open(self.fn_rois, "w") as fp:
                json.dump({
                    "rois": [{'z': i,
                              'id': j,
                              'pos': self.stack.rois[i][j].serialize()['pos']}
                             for i in range(len(self.stack.rois))
                             for j in range(len(self.stack.rois[i]))
                             if self.stack.rois[i][j].shown]
                }, fp, indent=4)

            self.status.showMessage("ROIs saved to {}".format(self.fn_rois), 1000)

    def savekeyboard(self, key):
        """Saves the annotation

        Args:
            key (Qt.Key): the pressed key
        """
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key.Key_S and modifiers == Qt.KeyboardModifier.ControlModifier:
            self.save()



if __name__ == '__main__':
    if not os.path.exists("settings.json"):
        with open('settings.json','w') as fp:
            json.dump(dict(default_directory=os.getcwd()), fp)
        
    import sys
    app = QApplication(sys.argv)

    m = Main()
    m.show()

    sys.exit(app.exec())