from Cocoa import *
from Foundation import NSObject
import objc

class Delegate (NSObject):
    def applicationDidFinishLaunching_(self, aNotification):
        '''Called automatically when the application has launched'''
        # NSLog("Hello, World!")
        pass

    def windowWillClose_(self, aNotification):
        '''Called automatically when the window is closed'''
        NSLog("Window has been closed")
        # Terminate the application
        NSApp().terminate_(self)

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        NSLog("Last Window has been closed")
        return YES
