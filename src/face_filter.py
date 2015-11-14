from Cocoa import *
from Foundation import NSObject
import objc
import os
import subprocess
import shlex

from app_delegate import Delegate
from worker_thread import WorkerThread

from face_rec import FaceRec

class FaceFilterXibController(NSWindowController):
    filetypes = ('avi', 'mkv', 'mp4')
    srcTextField = objc.IBOutlet()
    destTextField = objc.IBOutlet()
    arrayController = objc.IBOutlet()
    imageView = objc.IBOutlet()
    tableView = objc.IBOutlet()
    results = []
    _workerThread = None
    dest_dir = ""
    src_dir = ""
    queue = []
    _windowIsClosing = 0
    _workerThread = None
    testImg = None

    def init(self):
        self.src_dir = "/Users/thiruvarasans/Projects/OpenCV/face_filter/src/test/src_images"
        self.training_images_path = "/Users/thiruvarasans/Projects/OpenCV/face_filter/src/test/training_images"
        self.dest_dir = "/Users/thiruvarasans/Desktop"
        self.queue = []
        self.testImg = None
        self._windowIsClosing = 0
        self._workerThread = WorkerThread()
        self._workerThread.start()
        return self

    def windowDidLoad(self):
        NSWindowController.windowDidLoad(self)
        # res = self.performSelectorOnMainThread_withObject_waitUntilDone_("updateDisplay:", 1, 0)
        self.init()
        self.updateDisplay_()

    def awakeFromNib(self):
        if self.tableView:
            self.tableView.setTarget_(self)
            self.tableView.setDoubleAction_("showImage:")
        pass

    def windowWillClose_(self, aNotification):
        """
        Clean up when the document window is closed.
        """
        # We must stop the worker thread and wait until it actually finishes before
        # we can allow the window to close. Weird stuff happens if we simply let the
        # thread run. When this thread is idle (blocking in queue.get()) there is
        # no problem and we can almost instantly close the window. If it's actually
        # in the middle of working it may take a couple of seconds, as we can't
        # _force_ the thread to stop: we have to ask it to to stop itself.
        self._windowIsClosing = 1  # try to stop the thread a.s.a.p.
        self._workerThread.stop()  # signal the thread that there is no more work to do
        self._workerThread.join()  # wait until it finishes
        self.autorelease()

    @objc.IBAction
    def openSrcDirectory_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(YES)
        panel.setAllowsMultipleSelection_(NO)

        ret_value = panel.runModalForTypes_(self.filetypes)

        if ret_value and len(panel.filenames()) > 0:
            self.src_dir = panel.filenames()[0]
            NSLog("Selected source directory %s" % self.src_dir)
            self.updateDisplay_()

    @objc.IBAction
    def openDestDirectory_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseDirectories_(YES)
        panel.setAllowsMultipleSelection_(NO)

        ret_value = panel.runModalForTypes_(self.filetypes)

        if ret_value and len(panel.filenames()) > 0:
            self.dest_dir = panel.filenames()[0]
            NSLog("Selected ouput directory %s" % self.dest_dir)
            self.updateDisplay()

    def updateDisplay_(self, a=None):
        self.srcTextField.setStringValue_(self.src_dir)
        self.destTextField.setStringValue_(self.dest_dir)
        self.results = [NSDictionary.dictionaryWithDictionary_({'img_path': x['img_path'], 'name': os.path.basename(x['img_path']), 'label': x['label'], 'confidence': x['confidence']}) for x in self.queue]
        self.arrayController.rearrangeObjects()
        if self.testImg != None:
            self.imageView.setImage_(self.testImg)
        else:
            self.imageView.setImage_(None)
        return a

    @objc.IBAction
    def startScan_(self, sender):
        self.training_images_path = os.path.normpath(os.path.join(self.src_dir, "../training_images"))
        if not self.is_valid():
            return

        self._workerThread.scheduleWork(self.doScan)

    def doScan(self):
        if self._windowIsClosing:
            return
        self.testImg = None
        self.updateDisplay_()

        rec = FaceRec(self.training_images_path, self.src_dir)
        filtered_images = rec.filter()
        self.queue = [{'img_path': img_path, 'label': label, 'confidence': confidence} for img_path,label,confidence in filtered_images]
        self.performSelectorOnMainThread_withObject_waitUntilDone_("updateDisplay:", 1, 0)

    def is_valid(self):
        if len(self.src_dir) == 0 \
                or len(self.dest_dir) == 0 \
                or len(self.training_images_path) == 0 \
                or not os.path.exists(self.training_images_path) \
                or not os.path.exists(self.src_dir) \
                or not os.path.exists(self.dest_dir):
            NSLog("Invalid folder selection!")
            return False
        return True

    def showImage_(self,sender):
        # NSLog("doubleClick! %d, %d", sender.clickedColumn(), sender.clickedRow())
        rowIndex = sender.clickedRow()
        if rowIndex == -1:
            return

        row = self.arrayController.arrangedObjects()[rowIndex]
        source_image = row['img_path']
        self.testImg = NSImage.alloc().initWithContentsOfFile_(source_image)
        self.updateDisplay_()


if __name__ == "__main__":
    app = NSApplication.sharedApplication()

    delegate = Delegate.alloc().init()
    app.setDelegate_(delegate)
    NSApp().setDelegate_(delegate)

    # Initiate the contrller with a XIB
    viewController = FaceFilterXibController.alloc().initWithWindowNibName_("face_filter_main_window")

    # Show the window
    viewController.showWindow_(viewController)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)

    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()
