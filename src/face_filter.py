from Cocoa import *
from Foundation import NSObject
import objc
import os
import subprocess
import shlex

from app_delegate import Delegate
from worker_thread import WorkerThread

class FaceFilterXibController(NSWindowController):
    filetypes = ('avi', 'mkv', 'mp4')
    destTextField = objc.IBOutlet()
    arrayController = objc.IBOutlet()
    results = []
    _workerThread = None
    dest_dir = ""
    src_dir = ""
    queue = []
    _windowIsClosing = 0
    _workerThread = None

    def init(self):
        self.src_dir = ""
        self.dest_dir = "/Users/thiruvarasans/Desktop"
        self.queue = []
        self._windowIsClosing = 0
        self._workerThread = WorkerThread()
        self._workerThread.start()
        return self

    def windowDidLoad(self):
        NSWindowController.windowDidLoad(self)
        # res = self.performSelectorOnMainThread_withObject_waitUntilDone_("updateDisplay:", 1, 0)
        self.init()
        self.updateDisplay_()

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
        panel.setAllowsMultipleSelection_(YES)

        ret_value = panel.runModalForTypes_(self.filetypes)

        if ret_value:
            NSLog("Selected files %s" % ",".join(panel.filenames()))
            self.queue = [{'name': x, 'status': 'Queued'} for x in panel.filenames()]
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
        self.destTextField.setStringValue_(self.dest_dir)
        self.results = [NSDictionary.dictionaryWithDictionary_({'name': os.path.basename(x['name']),  'status': x['status']}) for x in self.queue]
        self.arrayController.rearrangeObjects()
        return a

    @objc.IBAction
    def startConvert_(self, sender):
        if len(self.queue) == 0 or len(self.dest_dir) == 0 or not os.path.exists(self.dest_dir):
            NSLog("Invalid data for conversion!")
            return

        for item in self.queue:
            inputfile = item['name']
            basename, _ = os.path.splitext(os.path.basename(inputfile))
            outfile = os.path.join(self.dest_dir, basename + ".mp3")

            if os.path.exists(outfile):
                item['status'] = 'Skipped'
                continue

            item['status'] = 'Converting...'
            # t = threading.Thread(target=self.doConvert, args=(inputfile, outfile, item))
            # t.start()
            # self.doConvert(inputfile, outfile, item)
            if self._windowIsClosing:
                return
            self._workerThread.scheduleWork(self.doConvert, inputfile, outfile, item)

        self.updateDisplay_()

    def doConvert(self, inputfile, outfile, item):
        if self._windowIsClosing:
            return
        args = "ffmpeg -i \"%s\" -f mp3 -ab 192000 -vn \"%s\"" % (inputfile, outfile)
        with open(os.devnull, 'w') as FNULL:
            NSLog("EXEC: " + args)
            ret = subprocess.call(shlex.split(args), stdout=FNULL, stderr=FNULL, shell=False)
            if not ret:
                item['status'] = 'Done'
            else:
                item['status'] = 'Error'
            res = self.performSelectorOnMainThread_withObject_waitUntilDone_("updateDisplay:", 1, 0)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()

    delegate = Delegate.alloc().init()
    app.setDelegate_(delegate)

    # Initiate the contrller with a XIB
    viewController = FaceFilterXibController.alloc().initWithWindowNibName_("face_filter_main_window")

    # Show the window
    viewController.showWindow_(viewController)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)

    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()
