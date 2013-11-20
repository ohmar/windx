#!/usr/bin/env/ python2

"""
windx by Omar Sandoval.
References:

http://incise.org/tinywm.html

http://plwm.sourceforge.net/

http://qtile.org/


This program is an extremely simple window manager for X.
Emphasis on EXTREMELY. It does not handle any errors and
assumes the user is sending correct events.
So far, it has trouble resizing windows and bringing windows
to the front. 

It requires an installation of urxvt. If you'd prefer not to install it
then change "/usr/bin/urxvt" to /usr/bin/xterm"

Keybindings for windx are as follows:

Shift-Enter opens a urxvt.
RightClick-Drag will move a window.

"""

import os
import sys
import Xlib.rdb
import Xlib.X
import Xlib.XK

# Command to be called when Shift-Enter is read
urxvtCommand = ["/usr/bin/urxvt"]


class WindowManager(object):
    def __init__(self, display):
        self.display = display
        self.dragWindow = None
        self.dragOffset = (0, 0)
        os.environ["DISPLAY"] = display.get_display_name()
        self.enterCodes = set(code for code, index in self.display.keysym_to_keycodes(Xlib.XK.XK_Return))

        self.screens = []
        for screenID in xrange(0, display.screen_count()):
            if self.screenEvent(screenID):
                self.screens.append(screenID)


        self.requestedEvent = {
            Xlib.X.MapRequest: self.mapRequest,
            Xlib.X.ConfigureRequest: self.configureRequest,
            Xlib.X.MotionNotify: self.mouseMotion,
            Xlib.X.ButtonPress: self.mousePress,
            Xlib.X.ButtonRelease: self.mouseRelease,
            Xlib.X.KeyPress: self.keyPress,
        }
       
       
    
    # Function to be called from main loop
    def events(self):
        event = self.display.next_event()
            
        if event.type in self.requestedEvent:
            handle = self.requestedEvent[event.type]
            handle(event)
            
    # Where to map event
    def mapRequest(self, event):
        event.window.map()
        self.grabWindowEvents(event.window)
        
    # Set options for configuring a window
    def configureRequest(self, event):
        window = event.window
        args = { "borderWidth": 3 }
        if event.value_mask & Xlib.X.CWX:
            args["x"] = event.x
        if event.value_mask & Xlib.X.CWY:
            args["y"] = event.y
        if event.value_mask & Xlib.X.CWWidth:
            args["width"] = event.width
        if event.value_mask & Xlib.X.CWHeight:
            args["height"] = event.height
        if event.value_mask & Xlib.X.CWSibling:
            args["sibling"] = event.above
        if event.value_mask & Xlib.X.CWStackMode:
            args["stackMode"] = event.stack_mode
        window.configure(**args)

	# Redirect screen events
    def screenEvent(self, screenID):
        root_window = self.display.screen(screenID).root

        mask = Xlib.X.SubstructureRedirectMask
        root_window.change_attributes(event_mask=mask)
        self.display.sync()

        for code in self.enterCodes:
            # Grab Shift-Enter
            root_window.grab_key(code,
                Xlib.X.ShiftMask & ~Xlib.X.AnyModifier,
                1, Xlib.X.GrabModeAsync, Xlib.X.GrabModeAsync)

        # Find all existing windows.
        for window in root_window.query_tree().children:
            self.grabWindowEvents(window)

        return True
        
    # Recognize and handle RightClick and drag events.
    def grabWindowEvents(self, window):
        
        window.grab_button(3, 0, True,
            Xlib.X.ButtonMotionMask | Xlib.X.ButtonReleaseMask | Xlib.X.ButtonPressMask,
            Xlib.X.GrabModeAsync,
            Xlib.X.GrabModeAsync,
            Xlib.X.NONE,
            Xlib.X.NONE,
            None)

    # RightClick and drag to move the window about your X session
    def mouseMotion(self, event):
        #Right click & drag to move window.
        if event.state & Xlib.X.Button3MotionMask:
            if self.dragWindow is None:
                # Start RightClick Drag
                self.dragWindow = event.window
                geom = self.dragWindow.get_geometry()
                self.dragOffset = geom.x - event.root_x, geom.y - event.root_y
            else:
                # Continue RightClick Drag
                x, y = self.dragOffset
                self.dragWindow.configure(x=x + event.root_x, y=y + event.root_y)
    
    # What to do when Shift-Enter is pressed
    def mousePress(self, event):
        if event.detail == 3:
            # Right-click: raise window
            event.window.configure(stackMode=Xlib.X.Above)

    # Do nothing when the mouse is released, or let
    # go of window that is being dragged.
    def mouseRelease(self, event):
        self.dragWindow = None

    # Open an instance of urxvt for Shift+Enter
    def keyPress(self, event):
        if event.state & Xlib.X.ShiftMask and event.detail in self.enterCodes:
            # Shift-Enter: start urxvt
            self.systemCommand(urxvtCommand)
            
    # System command to be called
    def systemCommand(self, command):
        
        # OS stuff for the command to run.
        if os.fork() != 0:
            return
        os.setsid()
        os.umask(0)
        os.execve(command[0], command, os.environ)

        sys.exit(1)

# Main loop for events
def main():

    display, appname, resource_database, args = Xlib.rdb.get_display_opts(Xlib.rdb.stdopts)

    wm = WindowManager(display)
    while True:
		wm.events()
 
if __name__ == "__main__":
    sys.exit(main())
