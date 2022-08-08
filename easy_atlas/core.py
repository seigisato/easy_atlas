from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *
import maya.cmds as cmds
import maya.mel as mel
import os, random, json
from . import uv_atlas          # @UnresolvedImport
from . import texture_atlas     # @UnresolvedImport
from . import qt_utils          # @UnresolvedImport
from . import utils             # @UnresolvedImport
from .EAGlobals import *

class AtlasItem:
    """This class is used to help organize the atlas output data."""

    def __init__ (self, mesh, file, posX, posY, sizeX, sizeY):
        self.mesh = mesh
        self.file = file
        self.posX = posX
        self.posY = posY
        self.sizeX = sizeX
        self.sizeY = sizeY

class Atlas:
    """This class holds the main data while an atlas is being created."""

    __EAAtlasFile = "EApresetFile"

    atlasSize = None
    listOfAtlasMeshes = []

    fileOutput = ""
    outputWidth = ""
    outputHeight = ""

    def getAtlasMeshByName(self, meshName):

        for k in self.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if k.meshName == meshName:
                return k

    def getAtlasMeshByCoord(self, coord):

        for k in self.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if coord in k.coords:
                return k

    def savePreset(self):

        dir = utils.INIHandler.load_info(self.__EAAtlasFile, "dir")
        if dir: dir += "/"

        file = cmds.fileDialog(m=1, dm=dir+'*.atl')  # @UndefinedVariable

        if file:

            jsonOUT = json.loads('{}')

            jsonOUT["atlasSize"] = self.atlasSize
            jsonOUT["fileOutput"] = self.fileOutput
            jsonOUT["outputWidth"] = int(self.outputWidth)
            jsonOUT["outputHeight"] = int(self.outputHeight)
            jsonOUT["meshList"] = {}

            for k in self.listOfAtlasMeshes:

                assert isinstance(k, AtlasMesh)
                item = {"texture": k.texture, "color": k.color, "id": k.id, "coords": k.coords}
                jsonOUT["meshList"][k.meshName] = item

            with open(file, 'wb') as fp:
                json.dump(jsonOUT, fp)

            utils.INIHandler.save_info(self.__EAAtlasFile, "dir", os.path.dirname(file))

    def loadPreset(self):

        dir = utils.INIHandler.load_info(self.__EAAtlasFile, "dir")
        if dir: dir += "/"

        file = cmds.fileDialog(m=0, dm=dir+'*.atl')  # @UndefinedVariable

        if os.path.exists(file):

            self.listOfAtlasMeshes = []

            jsonIN = None

            with open(file, 'rb') as fp:
                jsonIN = json.load(fp)

            self.atlasSize = jsonIN["atlasSize"]
            self.fileOutput = jsonIN["fileOutput"]
            self.outputWidth = jsonIN["outputWidth"]
            self.outputHeight = jsonIN["outputHeight"]
            for k in jsonIN["meshList"]:

                meshName = k
                texture = jsonIN["meshList"][k]["texture"]
                id = int(jsonIN["meshList"][k]["id"])
                color = jsonIN["meshList"][k]["color"]
                coords = jsonIN["meshList"][k]["coords"]

                mesh = AtlasMesh(meshName, texture, id, color, coords)
                self.listOfAtlasMeshes.append(mesh)

                utils.INIHandler.save_info(self.__EAAtlasFile, "dir", os.path.dirname(file))

class AtlasMesh:
    """An instance of this class will have all the information about an individual mesh."""

    meshName = ""
    texture = ""
    id = -1
    color = ""
    coords = []

    def __init__(self, meshName, texture="", id=-1, color="", coords=[]):

        self.meshName = meshName
        self.texture = texture
        self.id = id
        self.color = color
        self.coords = coords

    def resetAtlasAssignment(self):

        self.id = -1
        self.color = ""
        self.coords = []

class EasyAtlas():
    """This class creates the Easy Atlas interface and handles the human interaction."""

    windowName              = WindowName
    prefWindowName          = PrefWindowName
    windowUI                = None
    dockName                = DockName
    suspendUpdate           = False
    suspendCellChangeSignal = False
    AtlasInfo               = None
    _atlasTable             = qt_utils.RawWidget("EAatlasTable", QTableWidget)
    _meshTable              = qt_utils.RawWidget("EAmeshTable", QTableWidget)
    _bResizeAtlasTable      = qt_utils.RawWidget("EAresizeAtlasTable", QPushButton)
    _bAddMesh               = qt_utils.RawWidget("EAaddMesh", QPushButton)
    _bRemoveMesh            = qt_utils.RawWidget("EAremoveMesh", QPushButton)
    _bClearMeshTable        = qt_utils.RawWidget("EAclearMeshTable", QPushButton)
    _bPickFile              = qt_utils.RawWidget("EApickFile", QPushButton)
    _bMakeAtlas             = qt_utils.RawWidget("EAmakeAtlas", QPushButton)
    _tRowCount              = qt_utils.RawWidget("EArowCount", QLineEdit)
    _tColCount              = qt_utils.RawWidget("EAcolCount", QLineEdit)
    _tFileOutput            = qt_utils.RawWidget("EAfileOutput", QLineEdit)
    _tOutputWidth           = qt_utils.RawWidget("EAoutputWidth", QLineEdit)
    _tOutputHeight          = qt_utils.RawWidget("EAoutputHeight", QLineEdit)
    _lEasyAtlasImage        = qt_utils.RawWidget("EAeasyAtlasImage", QLabel)
    _aSavePreset            = qt_utils.RawWidget("EAsavePreset", QAction)
    _aLoadPreset            = qt_utils.RawWidget("EAloadPreset", QAction)
    _aPrefs                 = qt_utils.RawWidget("EApreferences", QAction)
    _aAddEAtoShelf          = qt_utils.RawWidget("EAaddEAtoShelf", QAction)
    _aAbout                 = qt_utils.RawWidget("EAAbout", QAction)
    _configFile             = ("%s/config/EasyAtlas.cfg" % os.path.dirname(__file__))
    _uiFile                 = ("%s/ui/easy_atlas.ui" % os.path.dirname(__file__))
    _uiPrefsFile            = ("%s/ui/prefs.ui" % os.path.dirname(__file__))
    _easyAtlasImage         = ("%s/img/easy_atlas.png" % os.path.dirname(__file__))
    _easyAtlasIcon          = ("%s/img/easy_atlas_icon.png" % os.path.dirname(__file__))
    _colorList              = QColor.colorNames()
    _color                  = _colorList[random.randint(0, len(_colorList)-1)]

    def __init__(self):
        # Shuffle colors
        random.shuffle(self._colorList)

        self.windowUI = qt_utils.loadQtWindow(self._uiFile, self.windowName)  # @UndefinedVariable

        # create dock
        if (cmds.dockControl(self.dockName, exists=True)):  # @UndefinedVariable
            cmds.deleteUI(self.dockName)  # @UndefinedVariable
        cmds.dockControl(self.dockName, allowedArea=["right", "left"], area="right", content=self.windowName, visible=True)  # @UndefinedVariable

        self.AtlasInfo = Atlas()
        self.AtlasInfo.listOfAtlasMeshes = []

        pixmap = QPixmap(self._easyAtlasImage);
        if pixmap:
            lEasyAtlasImage = qt_utils.getControl(self._lEasyAtlasImage)
            lEasyAtlasImage.setPixmap(pixmap);

        # Connect stuff
        bAddMesh = qt_utils.getControl(self._bAddMesh)
        bRemoveMesh = qt_utils.getControl(self._bRemoveMesh)
        bUpdateGrid = qt_utils.getControl(self._bResizeAtlasTable)
        bClear = qt_utils.getControl(self._bClearMeshTable)
        bPickFileOutput = qt_utils.getControl(self._bPickFile)
        bMakeAtlas = qt_utils.getControl(self._bMakeAtlas)
        aSavePreset = qt_utils.getControl(self._aSavePreset)
        aLoadPreset = qt_utils.getControl(self._aLoadPreset)
        aAbout = qt_utils.getControl(self._aAbout)
        aPrefs = qt_utils.getControl(self._aPrefs)
        aAddEAtoShelf = qt_utils.getControl(self._aAddEAtoShelf)
        tOutputFile = qt_utils.getControl(self._tFileOutput)
        toutputWidth = qt_utils.getControl(self._tOutputWidth)
        tOutputHeight = qt_utils.getControl(self._tOutputHeight)

        bAddMesh.clicked.connect(lambda: self.addMesh())
        bRemoveMesh.clicked.connect(lambda: self.removeMesh())
        bUpdateGrid.clicked.connect(lambda: self.resizeAtlasTable())
        bClear.clicked.connect(lambda: self.clearMeshes())
        bPickFileOutput.clicked.connect(lambda: self.pickOutputTexture())
        bMakeAtlas.clicked.connect(lambda: self.makeAtlas())
        aSavePreset.triggered.connect(lambda: self.savePreset())
        aLoadPreset.triggered.connect(lambda: self.loadPreset())
        aAbout.triggered.connect(lambda: self.about())
        aAddEAtoShelf.triggered.connect(lambda: self.addEAtoShelf())
        aPrefs.triggered.connect(lambda: self.preferences())
        tOutputFile.textChanged.connect(lambda: self.updateMeshList())
        toutputWidth.textChanged.connect(lambda: self.updateMeshList())
        tOutputHeight.textChanged.connect(lambda: self.updateMeshList())

        tableMeshes = qt_utils.getControl(self._meshTable)
        assert isinstance(tableMeshes, QTableWidget)
        tableMeshes.setContextMenuPolicy(Qt.CustomContextMenu)
        tableMeshes.customContextMenuRequested.connect(self.contextMenu_meshTable)
        tableMeshes.scrollToItem(tableMeshes.item(0,0))
        tableMeshes.itemChanged.connect(lambda: self.updateAtlasInfoFromMeshTableChange())

        # Attach context menu to atlas table
        table = qt_utils.getControl(self._atlasTable)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.contextMenu_atlasTable)

        # Show window and reset tables
        self.resizeAtlasTable()
        self.updateAtlasTable()

    def about(self):
        cmds.confirmDialog(t="About", message="Easy Atlas was made by Seigi Sato.\nMore info at www.seigisato.com.", button=["Ok"])  # @UndefinedVariable

    def addEAtoShelf(self):
        shelf = mel.eval("string $gShelfTopLevel; string $currentShelf = `tabLayout -q -st $gShelfTopLevel`;")  # @UndefinedVariable
        cmds.shelfButton(rpt=True, i1=self._easyAtlasIcon, ann="Easy Atlas", command="import easy_atlas\neasy_atlas.launch()", p=shelf)  # @UndefinedVariable

    def preferences(self):
        prefWindow = qt_utils.loadQtWindow(self._uiPrefsFile, self.prefWindowName)

        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        pickButton = qt_utils.getControl(qt_utils.RawWidget("EApickPhotoshopPath", QPushButton))
        resampleComboBox = qt_utils.getControl(qt_utils.RawWidget("EAresampleOptions", QComboBox))
        saveButton = qt_utils.getControl(qt_utils.RawWidget("EAsavePref", QPushButton))
        cancelButton = qt_utils.getControl(qt_utils.RawWidget("EAcancelPref", QPushButton))

        cancelButton.clicked.connect(lambda: prefWindow.close())
        pickButton.clicked.connect(lambda: self.pickPhotoshopPath())
        saveButton.clicked.connect(lambda: self.savePreferences(prefWindow))

        photoshopPath = utils.INIHandler.load_info(self._configFile, "photoshopDir")
        photoshopLineEdit.setText(photoshopPath)

        currentResampleMode = utils.INIHandler.load_info(self._configFile, "resampleMode")
        resampleComboBox.setCurrentIndex(ResamplingModeValues.index(currentResampleMode))

        prefWindow.show()

    def pickPhotoshopPath(self):
        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        folder = os.path.dirname(photoshopLineEdit.text())

        photoshopPath = cmds.fileDialog(m=0, dm='%s/*.exe' % folder)  # @UndefinedVariable
        if os.path.exists(photoshopPath):
            photoshopLineEdit.setText(photoshopPath)
    
    def savePreferences(self, window):
        # Photoshop Path
        photoshopLineEdit = qt_utils.getControl(qt_utils.RawWidget("EAprefPhotoshopPath", QLineEdit))
        utils.INIHandler.save_info(self._configFile, "photoshopDir", photoshopLineEdit.text())
        
        # Resampling Mode
        resamplingMode = qt_utils.getControl(qt_utils.RawWidget("EAresampleOptions", QComboBox))
        resampleConfig = ResamplingExportValues.get(resamplingMode.currentText(), "automatic")
        utils.INIHandler.save_info(self._configFile, "resampleMode", resampleConfig)
        
        window.close()

    def updateAtlasInfoFromMeshTableChange(self):
        if self.suspendCellChangeSignal:
            return

        row = 0
        for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            tableMeshes = qt_utils.getControl(self._meshTable)
            k.meshName = tableMeshes.item(row, 1).text()
            k.texture = tableMeshes.item(row, 2).text()
            row += 1

        self.updateMeshList()

    def savePreset(self):
        self.AtlasInfo.savePreset()

    def loadPreset(self):
        self.AtlasInfo.loadPreset()

        self.suspendUpdate = True
        qt_utils.getControl(self._tFileOutput).setText(self.AtlasInfo.fileOutput)
        qt_utils.getControl(self._tOutputWidth).setText(str(self.AtlasInfo.outputWidth))
        qt_utils.getControl(self._tOutputHeight).setText(str(self.AtlasInfo.outputHeight))
        qt_utils.getControl(self._tRowCount).setText(str(self.AtlasInfo.atlasSize[0]))
        qt_utils.getControl(self._tColCount).setText(str(self.AtlasInfo.atlasSize[1]))
        self.suspendUpdate = False

        self.resizeAtlasTable(False)
        self.updateAtlasTable()

    def contextMenu_meshTable(self):
        menu = QMenu()
        menu.addAction('Assign Texture to Mesh', self.assignTextureToMesh)
        menu.exec_(QCursor.pos())
        menu.show()

    def contextMenu_atlasTable(self):

        menu = QMenu()

        if self.AtlasInfo.listOfAtlasMeshes:

            menu.addSeparator()

            for k in self.AtlasInfo.listOfAtlasMeshes:
                assert isinstance(k, AtlasMesh)
                if k.id == -1:
                    menu.addAction("Assign to %s" %k.meshName, lambda mesh=k: self.setAtlasIdToMesh(mesh))

        menu.addSeparator()
        menu.addAction("Add mesh from viewport selection", self.addMeshFromViewportSelection)
        menu.addAction('Unassign Mesh', self.celeteAtlasRegion)

        menu.exec_(QCursor.pos())
        menu.show()

    def setAtlasIdToMesh(self, mesh):

        table = qt_utils.getControl(self._atlasTable)

        # Make sure the new region doesn't overlap another region
        allTakenCoords = []
        for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            allTakenCoords.extend(k.coords)

        selectedCoords = []
        for k in table.selectedItems():
            selectedCoord = [k.row(), k.column()]
            selectedCoords.append(selectedCoord)
            if selectedCoord in allTakenCoords:
                cmds.confirmDialog(t=diaWarning, message="Cannot overlap Atlas region.", button=["ok"])  # @UndefinedVariable
                return

        # Find unique atlas id
        idList = []
        for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            idList.append(k.id)

        nextIdAtlas = -1
        index = 0
        while nextIdAtlas == -1:
            if not index in idList:
                nextIdAtlas = index
                break
            index += 1

        # Assign new region
        colorName = self.getNextColor()

        assert isinstance(mesh, AtlasMesh)
        mesh.color = colorName
        mesh.id = nextIdAtlas
        mesh.coords = selectedCoords
        self.updateAtlasTable()

    def assignTextureToMesh(self):

        dir = utils.INIHandler.load_info(self._configFile, "loadTextureDir")
        file = cmds.fileDialog(m=0, dm=dir+'/*.*')  # @UndefinedVariable

        if file:

            tableMeshes = qt_utils.getControl(self._meshTable)
            sel = tableMeshes.selectedItems()
            if sel:
                sel = sel[0]
                row = tableMeshes.row(sel)
                itemText = tableMeshes.item(row, 1).text()
                mesh = self.AtlasInfo.getAtlasMeshByName(itemText)
                assert isinstance(mesh, AtlasMesh)
                mesh.texture = file
            self.updateMeshList()

            dir = os.path.dirname(file)
            utils.INIHandler.save_info(self._configFile, "loadTextureDir", dir)

    def resizeAtlasTable(self, resetItems=True):
        """Rezises the table.

        Clear id, color and coords info from meshes.
        """

        table = qt_utils.getControl(self._atlasTable)
        tRowcount = qt_utils.getControl(self._tRowCount)
        tColCount = qt_utils.getControl(self._tColCount)

        rowCount = int(tRowcount.text())
        colCount = int(tColCount.text())

        self.AtlasInfo.atlasSize = [rowCount, colCount]

        if resetItems:
            for k in self.AtlasInfo.listOfAtlasMeshes:
                assert isinstance(k, AtlasMesh)
                k.resetAtlasAssignment()

        table.setRowCount(rowCount)
        table.setColumnCount(colCount)

        tableSize = table.size()

        for k in range(rowCount):
            table.setRowHeight(k, (tableSize.height()*1.0)/rowCount)

        for k in range(colCount):
            table.setColumnWidth(k, (tableSize.width()*1.0)/colCount)

        self.updateAtlasTable()

    def resetAtlasTable(self):
        """
            Reset all the table colors to initial state.
        """

        table = qt_utils.getControl(self._atlasTable)

        for m in range(table.rowCount()):
            for n in range(table.columnCount()):
                table.setItem(m, n, QTableWidgetItem(""))
                brush = QBrush(QColor().fromRgb(128, 128, 128))
                table.item(m,n).setBackground(brush)

        table.scrollToItem(table.item(0, 0))

    def updateAtlasTable(self):
        """
            Assign colors and id to table item.
        """

        self.resetAtlasTable()
        table = qt_utils.getControl(self._atlasTable)

        for k in self.AtlasInfo.listOfAtlasMeshes:
            assert isinstance(k, AtlasMesh)
            if k.id != -1:
                coordList = k.coords
                for m in coordList:
                    brush = QBrush(QColor(k.color))
                    brushFont = QBrush(QColor().black())
                    table.item(m[0], m[1]).setBackground(brush)
                    table.item(m[0], m[1]).setForeground(brushFont)
                    table.item(m[0], m[1]).setText(str(k.id))
                    table.item(m[0], m[1]).setTextAlignment(Qt.AlignCenter)

        table.scrollToItem(table.item(0, 0))

        self.updateMeshList()

    def getNextColor(self):

        index = self._colorList.index(self._color)
        index += 1
        if index > len(self._colorList)-1:
            index = 0
        self._color = self._colorList[index]

        return self._color

    def addMesh(self):

        meshes = cmds.ls(sl=True, l=True)  # @UndefinedVariable
        if not meshes:
            cmds.confirmDialog(t=diaWarning, message="At least one mesh must be selected for adding.", button=["ok"])  # @UndefinedVariable
            return

        for k in meshes:

            if not self.AtlasInfo.getAtlasMeshByName(k):
                texture = ""
                try:
                    rel = cmds.listRelatives(k)                                 # @UndefinedVariable
                    sg = cmds.listConnections(rel, type="shadingEngine")        # @UndefinedVariable
                    materials = cmds.listConnections(sg[0]+".surfaceShader")    # @UndefinedVariable
                    files = cmds.listConnections(materials[0], type="file")     # @UndefinedVariable
                    texture = cmds.getAttr(files[0]+".fileTextureName")         # @UndefinedVariable
                except:
                    pass

                item = AtlasMesh(k, texture)
                self.AtlasInfo.listOfAtlasMeshes.append(item)

        self.updateMeshList()

    def addMeshFromViewportSelection(self):

        meshes = cmds.ls(sl=True, l=True)  # @UndefinedVariable
        if not meshes:
            cmds.confirmDialog(t=diaWarning, message="A mesh must be selected for adding.", button=["ok"])  # @UndefinedVariable
            return

        if len(meshes) > 1:
            cmds.confirmDialog(t=diaWarning, message="Please select only one mesh at a time.", button=["ok"])  # @UndefinedVariable
            return

        self.addMesh()
        self.setAtlasIdToMesh(self.AtlasInfo.getAtlasMeshByName(meshes[0]))

    def removeMesh(self):

        tableMeshes = qt_utils.getControl(self._meshTable)
        selectedItems = tableMeshes.selectedItems()

        if selectedItems:

            sel = selectedItems[0]
            row = tableMeshes.row(sel)
            itemText = tableMeshes.item(row, 1).text()

            mesh = self.AtlasInfo.getAtlasMeshByName(itemText)
            self.AtlasInfo.listOfAtlasMeshes.remove(mesh)

            self.updateAtlasTable()

    def clearMeshes(self):

        self.AtlasInfo.listOfAtlasMeshes = []
        self.updateAtlasTable()

    def updateMeshList(self):

        if self.suspendUpdate:
            return

        # Must suspend Cell Change Signal
        self.suspendCellChangeSignal = True

        tableMeshes = qt_utils.getControl(self._meshTable)

        itemSelectedName = None
        if tableMeshes.selectedItems():
            itemSelectedName = tableMeshes.selectedItems()[1].text()

        tableMeshes.clear()

        rowCount = len(self.AtlasInfo.listOfAtlasMeshes)
        colCount = 3
        tableMeshes.setRowCount(rowCount)
        tableMeshes.setColumnCount(colCount)

        index = 0
        for k in self.AtlasInfo.listOfAtlasMeshes:

            assert isinstance(k, AtlasMesh)

            if k.id == -1:
                tableMeshes.setItem(index, 0, QTableWidgetItem(""))
            else:
                tableMeshes.setItem(index, 0, QTableWidgetItem(str(k.id)))

            tableMeshes.item(index, 0).setTextAlignment(Qt.AlignHCenter)
            tableMeshes.setItem(index, 1, QTableWidgetItem(k.meshName))
            tableMeshes.setItem(index, 2, QTableWidgetItem(k.texture))


            color = QColor().fromRgb(150, 150, 150)
            brush = QBrush(color)
            brushFont = QBrush(QColor("white"))
            if k.color:
                color = QColor(k.color)
                brush = QBrush(color)
                brushFont = QBrush(QColor().black())

            for i in range(3):
                tableMeshes.item(index, i).setBackground(brush)
                tableMeshes.item(index, i).setForeground(brushFont)

            if itemSelectedName == k:
                tableMeshes.setCurrentCell(index, 0)

            index += 1

        #tableMeshes.horizontalHeader().setStretchLastSection(True)
        tableMeshes.setHorizontalHeaderLabels(["Atlas", "Mesh", "Texture"])
        tableMeshes.horizontalHeaderItem(0).setTextAlignment(Qt.AlignHCenter)
        tableMeshes.horizontalHeaderItem(1).setTextAlignment(Qt.AlignLeft)
        tableMeshes.horizontalHeaderItem(2).setTextAlignment(Qt.AlignLeft)
        tableMeshes.setColumnWidth(0, 40)
        tableMeshes.setColumnWidth(1, 150)
        tableMeshes.resizeColumnToContents(2)

        self.AtlasInfo.fileOutput = qt_utils.getControl(self._tFileOutput).text()
        self.AtlasInfo.outputWidth = qt_utils.getControl(self._tOutputWidth).text()
        self.AtlasInfo.outputHeight = qt_utils.getControl(self._tOutputHeight).text()

        tRowcount = qt_utils.getControl(self._tRowCount)
        tColCount = qt_utils.getControl(self._tColCount)

        rowCount = int(tRowcount.text())
        colCount = int(tColCount.text())

        self.AtlasInfo.atlasSize = [rowCount, colCount]

        # Must revert Cell Change Signal to false
        self.suspendCellChangeSignal = False

        #=======================================================================
        # with open(self._jsonFile, 'wb') as fp:
        #     json.dump(__REPLACE_JSON__, fp)
        #=======================================================================

    def celeteAtlasRegion(self):

        table = qt_utils.getControl(self._atlasTable)

        for k in table.selectedItems():
            coord = [k.row(), k.column()]
            mesh = self.AtlasInfo.getAtlasMeshByCoord(coord)
            if mesh:
                mesh.resetAtlasAssignment()

        self.updateAtlasTable()

    def pickOutputTexture(self):

        outputFilename = qt_utils.getControl(self._tFileOutput)
        dir = ""

        if outputFilename.text() != "":
            dir = os.path.dirname(outputFilename.text())

        if not os.path.exists(dir):
            dir = utils.INIHandler.load_info(self._configFile, "loadTextureDir")

        file = cmds.fileDialog(m=1, dm=dir+'/*.*')  # @UndefinedVariable

        if file:

            outputFilename.setText(file)

            dir = os.path.dirname(file)
            utils.INIHandler.save_info(self._configFile, "loadTextureDir", dir)

    def getCoordRangeNormalized(self, coordList, totalSize):


        totalSizeX = totalSize[1]
        totalSizeY = totalSize[0]

        xList = []
        yList = []
        for k in coordList:
            xList.append(k[1])
            yList.append(k[0])

        posX = min(xList)
        maxPosX = max(xList)
        sizeX = maxPosX+1-posX

        posY = min(yList)
        maxPosY = max(yList)
        sizeY = maxPosY+1-posY

        posXNormalized = float(posX) / totalSizeX
        posYNormalized = float(posY) / totalSizeY
        sizeXNormalized = float(sizeX) / totalSizeX
        sizeYNormalized = float(sizeY) / totalSizeY

        return posXNormalized, posYNormalized, sizeXNormalized, sizeYNormalized

    def makeAtlas(self):

        # Work around for the editing text PySide issue on the mesh table
        t = qt_utils.getControl(self._meshTable)
        t.focusNextChild()
        t.focusPreviousChild()
        self.updateAtlasInfoFromMeshTableChange()

        # Make sure Photoshop path is set up
        photoshopPath = utils.INIHandler.load_info(self._configFile, "photoshopDir")
        if not photoshopPath:
            setUpPS = cmds.confirmDialog(t=diaWarning, message="Photoshop path missing. Do you want to pick a Photoshop path now?", button=["Yes", "No"], defaultButton='Yes', cancelButton='No', dismissString='No')  # @UndefinedVariable

            if setUpPS == "No":
                return

            else:
                photoshopPath = cmds.fileDialog(m=0, dm='c:/*.exe')  # @UndefinedVariable
                if os.path.exists(photoshopPath):
                    utils.INIHandler.save_info(self._configFile, "photoshopDir", photoshopPath)
                else:
                    return

        # Now the script
        atlasItems = []
        txtFinalFilename = qt_utils.getControl(self._tFileOutput).text().lower()
        outputSizeX = int(qt_utils.getControl(self._tOutputWidth).text())
        outputSizeY = int(qt_utils.getControl(self._tOutputHeight).text())
        
        # Resampling Mode
        resamplingMode = utils.INIHandler.load_info(self._configFile, "resampleMode")

        # Check that output file extension is valid
        if not os.path.splitext(txtFinalFilename)[1] in SupportedFileExtensions:
            cmds.confirmDialog(t=diaWarning, message="Output file type not supported by Easy Atlas.\n Supported types are {}".format(SupportedFileExtensions), button=["ok"])  # @UndefinedVariable
            return

        for mesh in self.AtlasInfo.listOfAtlasMeshes:

            assert isinstance(mesh, AtlasMesh)
            if mesh.id != -1:
                texture = mesh.texture
                rawCoords = mesh.coords
                posX, posY, sizeX, sizeY = self.getCoordRangeNormalized(rawCoords, self.AtlasInfo.atlasSize)
                aItem = AtlasItem(mesh.meshName, texture, posX, posY, sizeX, sizeY)
                atlasItems.append(aItem)

                if not os.path.exists(mesh.texture):
                    cmds.confirmDialog(t=diaWarning, message="Input texture doesn't exist: \n%s." % mesh.texture, button=["ok"])  # @UndefinedVariable
                    return

                # Make sure the mesh has a valid maya name (names that use non-standard characters break maya)
                try:
                    cmds.ls(mesh.meshName)  # @UndefinedVariable
                except:
                    cmds.confirmDialog(t=diaWarning, message="Invalid mesh name: \n%s." % (mesh.meshName), button=["ok"])  # @UndefinedVariable
                    return

                if not cmds.ls(mesh.meshName):  # @UndefinedVariable
                    cmds.confirmDialog(t=diaWarning, message="Mesh doesn't exist: \n%s." % mesh.meshName, button=["ok"])  # @UndefinedVariable
                    return

        if not atlasItems:
            cmds.confirmDialog(t=diaWarning, message="No item has been assigned to the Atlas.", button=["ok"])  # @UndefinedVariable
            return

        texture_atlas.createAtlas(atlasItems, txtFinalFilename, int(outputSizeX), int(outputSizeY), photoshopPath, resamplingMode)
        uv_atlas.createAtlas(atlasItems)

        meshes = [x.mesh for x in atlasItems]
        cmds.select(meshes)  # @UndefinedVariable

        shader=cmds.shadingNode("lambert",asShader=True)  # @UndefinedVariable
        file_node=cmds.shadingNode("file",asTexture=True)  # @UndefinedVariable
        shading_group= cmds.sets(renderable=True,noSurfaceShader=True,empty=True)  # @UndefinedVariable
        cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %shading_group)  # @UndefinedVariable
        cmds.connectAttr('%s.outColor' %file_node, '%s.color' %shader)  # @UndefinedVariable
        cmds.setAttr(file_node+'.fileTextureName', txtFinalFilename, type='string')  # @UndefinedVariable
        cmds.sets(meshes, edit=True, forceElement=shading_group)  # @UndefinedVariable

        cmds.select(meshes) # @UndefinedVariable

def launch():
    """Method for launching the Easy Atlas interface."""

    EA = EasyAtlas()

# Quick launch script if debug mode is on
if bool(mel.eval('getenv "EASY_DEBUG_MODE"')):  # @UndefinedVariable
    launch()