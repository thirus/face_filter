from Cocoa import *
from Foundation import *
import objc


def handler(event):
    try:
        NSLog(u"%@", event)
    except KeyboardInterrupt:
        AppHelper.stopEventLoop()

class Delegate (NSObject):
    def applicationDidFinishLaunching_(self, aNotification):
        '''Called automatically when the application has launched'''
        # NSLog("Hello, World!")
        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, handler)
        pass

    def windowWillClose_(self, aNotification):
        '''Called automatically when the window is closed'''
        NSLog("Window has been closed")
        # Terminate the application
        NSApp().terminate_(self)

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        NSLog("Last Window has been closed")
        return YES
