from maya import OpenMayaUI as omui  # @UnresolvedImport
from PySide.QtCore import * 
from PySide.QtGui import *
from PySide.QtUiTools import *
from shiboken import wrapInstance
import maya.cmds as cmds

class RawWidget:
    '''Auxiliary class that is used to grab widgets.'''
    
    def __init__(self, name, type):
        self.name = name
        self.type = type

def loadQtWindow(uiFile, windowName):
    '''Auxiliary method that loads .ui files under main Maya window.'''

    # Delete previously loaded UI
    if (cmds.window(windowName, exists=True)):  # @UndefinedVariable
        cmds.deleteUI(windowName)  # @UndefinedVariable
    
    # Define Maya window
    global mayaMainWindow
    mayaMainWindow = None
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
    
    # Load UI
    loader = QUiLoader()
    file = QFile(uiFile)
    file.open(QFile.ReadOnly)
    windowUI = loader.load(file, parentWidget=mayaMainWindow)
    file.close()
    
    return windowUI
    
def getControl(rawWidget):
    '''Auxiliary method to grab a widget.'''
    
    ptr = None
    if rawWidget.type == QAction:
        ptr = omui.MQtUtil.findMenuItem(rawWidget.name)
    else:
        ptr = omui.MQtUtil.findControl(rawWidget.name)
    foundControl = wrapInstance(long(ptr), rawWidget.type)
    return foundControl