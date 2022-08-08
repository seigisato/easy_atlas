import maya.cmds as cmds
import subprocess, os
import socket
import threading
from .EAGlobals import ResamplingModeValues

PSScript = """var args = "ITEMLIST"
var argList = args.split(",")

var oldRulerUnits = preferences.rulerUnits;
var oldTypeUnits = preferences.typeUnits;

preferences.rulerUnits = Units.PIXELS;
preferences.typeUnits = TypeUnits.PIXELS;

var TCP_PORT = parseInt(argList.shift())
var fileName = (argList.shift()).replace("/", "\\\\")
var outputSizeX = parseInt(argList.shift())
var outputSizeY = parseInt(argList.shift())
var resamplingInt = parseInt(argList.shift())
var resamplingMode;

switch (resamplingInt) {
    case 1:
        resamplingMode = ResampleMethod.NONE;
        break;
    case 2:
        resamplingMode = ResampleMethod.NEARESTNEIGHBOR;
        break;
    case 3:
        resamplingMode = ResampleMethod.BILINEAR;
        break;
    case 4:
        resamplingMode = ResampleMethod.BICUBIC;
        break;
    case 5:
        resamplingMode = ResampleMethod.BICUBICSHARPER;
        break; 
    case 6:
        resamplingMode = ResampleMethod.BICUBICSMOOTHER;
        break;
    case 7:
        resamplingMode = ResampleMethod.BICUBICAUTOMATIC;
        break;
    case 8:
        resamplingMode = ResampleMethod.AUTOMATIC;
        break;
    case 9:
        resamplingMode = ResampleMethod.PRESERVEDETAILS;
        break;
    default:
        resamplingMode = ResampleMethod.AUTOMATIC;
}

function MoveLayerTo(fLayer, refPosX, refPosY, fX, fY) {

    var Position = [0, 0]
    Position[0] = fX + refPosX
    Position[1] = fY + refPosY

    try {
        fLayer.translate(Position[0], Position[1])
    }
    catch(err) {
        alert ("Error translating " + fLayer.name + ". "+err)
    }
}

function UniqueName(name, index) {
    
    var tempName = name+index.toString()
    
    for (i=0; i<documents.length; i+=1) {
        if (tempName.toLowerCase() == documents[i].name.toLowerCase()) {
            tempName = UniqueName(name, index+1)
        }
    }
    
    return tempName
}

function MakeLayerMask(maskType) {
    if( maskType == undefined) maskType = 'RvlS' ; //from selection
    //requires a selection 'RvlS'  complete mask 'RvlA' otherThanSelection 'HdSl'
    var desc140 = new ActionDescriptor();
    desc140.putClass( charIDToTypeID('Nw  '), charIDToTypeID('Chnl') );
    var ref51 = new ActionReference();
    ref51.putEnumerated( charIDToTypeID('Chnl'), charIDToTypeID('Chnl'), charIDToTypeID('Msk ') );
    desc140.putReference( charIDToTypeID('At  '), ref51 );
    desc140.putEnumerated( charIDToTypeID('Usng'), charIDToTypeID('UsrM'), charIDToTypeID(maskType) );
    executeAction( charIDToTypeID('Mk  '), desc140, DialogModes.NO );
}

var docName = UniqueName("EasyAtlas", 0)

var outputDoc = app.documents.add(outputSizeX, outputSizeY, 72, docName, NewDocumentMode.RGB, DocumentFill.TRANSPARENT, 1)
var outputAlphaChannel = outputDoc.channels.add()

for (i=0; i<argList.length; i+=5) {

    // Parse incoming string
    filename = argList[i].replace("/", "\\\\")
    posX = parseInt(argList[i+1])
    posY = parseInt(argList[i+2])
    sizeX = parseInt(argList[i+3])
    sizeY =parseInt(argList[i+4])
    fileNameSplit = filename.split(".")
    fileExtension = fileNameSplit.pop()

    // Open original file and duplicate it into docTemp
    var docOriginalImage = open(File(filename))
    var docTemp = docOriginalImage.duplicate()
    docOriginalImage.close(SaveOptions.DONOTSAVECHANGES)
    
    // Get the layerset name from filename
    var layerName = filename.split("\\\\").pop()
    layerName = filename.split("/").pop()
    layerName = layerName.substr(0,layerName.lastIndexOf("."))

    docTemp.resizeImage(sizeX, sizeY, docTemp.resolution, resamplingMode)
    docTemp.crop([0, 0, sizeX, sizeY])
    docTemp.channels.add() // <--------- WORKAROUND
    
    var alpha = false
    
    for (k=0; k<docTemp.channels.length; k+=1) {
        
        if (docTemp.channels[k].kind != ChannelType.MASKEDAREA) {continue}
        
        alpha = true
        docTemp.activeChannels = [docTemp.channels[k]]
        docTemp.selection.selectAll()
        docTemp.selection.copy()
        docTemp.selection.deselect()
        docTemp.artLayers.add()
        docTemp.paste()
        
        break

    }
    
    app.activeDocument = outputDoc
    var newLayerSet = outputDoc.layerSets.add()
    newLayerSet.name = layerName

    for (k=docTemp.layers.length-1; k>=0; k-=1) {
        
        app.activeDocument = outputDoc
        outputDoc.selection.deselect()        
        
        app.activeDocument = docTemp
        docTemp.selection.deselect()
        visibility = docTemp.layers[k].visible
        docTemp.activeLayer = docTemp.layers[k]
        
        if (docTemp.activeLayer.typename == "LayerSet") {
            var refLayer
            refLayer = null
            if (newLayerSet.layers.length == 0) {
                app.activeDocument = outputDoc
                refLayer = outputDoc.artLayers.add()
                refLayer.move(newLayerSet, ElementPlacement.INSIDE)
                app.activeDocument = docTemp
            }
            docTemp.activeLayer.duplicate(newLayerSet.layers[0], ElementPlacement.PLACEBEFORE)
            app.activeDocument = outputDoc
            if (refLayer != null) {
                refLayer.remove()
            }
            app.activeDocument = docTemp
        }
        else {
            docTemp.activeLayer.duplicate(newLayerSet)
        }
    
        app.activeDocument = outputDoc
        tempLayer = outputDoc.activeLayer
        tempLayer.visible = visibility
        
        // Copy alpha layer into alpha channel
        if (k==0 && alpha==true) {
            
            MoveLayerTo(tempLayer, 0, 0, posX, posY)
            LB = tempLayer.bounds
            outputDoc.selection.selectAll()
            outputDoc.selection.copy()
            outputDoc.selection.deselect()
            outputDoc.activeChannels = [outputAlphaChannel]
            selectedRegion = Array(Array(LB[0].value,LB[1].value),Array(LB[2].value,LB[1].value),Array(LB[2].value,LB[ 3].value),Array(LB[0].value,LB[3].value))
            outputDoc.selection.select(selectedRegion)
            outputDoc.paste(true)
            outputDoc.activeChannels = [outputDoc.channels[0], outputDoc.channels[1], outputDoc.channels[2]]
            outputDoc.activeLayer = tempLayer
            tempLayer.name = layerName + "_alpha"
            tempLayer.remove()
            
        }
        
    }

    // Move layers into place
    app.activeDocument = outputDoc
    outputDoc.activeLayer = newLayerSet
    
    myRegion = Array([0,0], [sizeX,0], [sizeX,sizeY], [0,sizeY])
    outputDoc.selection.select (myRegion)
    MakeLayerMask()
    outputDoc.selection.deselect()
    
    MoveLayerTo(newLayerSet, 0, 0, posX, posY)

    docTemp.close(SaveOptions.DONOTSAVECHANGES)
}

outputDoc.selection.deselect()
outputDoc.artLayers[outputDoc.artLayers.length-1].remove()
refresh()

fileNameSplit = fileName.split(".")
fileExtension = fileNameSplit.pop()

var saveOptions
var saveAsCopy = true

switch(fileExtension.toLowerCase()) {    
        
        case "jpg":
            saveOptions = new JPEGSaveOptions()
            break;
        
        case "png":
            saveOptions = new PNGSaveOptions()        
            break;
            
        case "tga":
            saveOptions = new TargaSaveOptions()
            saveOptions.alphaChannels = true
            saveOptions.resolution = TargaBitsPerPixels.THIRTYTWO
            saveOptions.rleCompression = true
            break;
            
        case "psd":
                saveOptions = new PhotoshopSaveOptions()
                saveAsCopy = false
                break;
            
        default:
            saveOptions = null
            alert("File extension not supported by Easy Atlas. This document will not be saved.")

}

if (saveOptions != null) {
    outputDoc.saveAs(new File(fileName), saveOptions, saveAsCopy, Extension.LOWERCASE)

    reply = ""
    conn = new Socket

    if (conn.open ("127.0.0.1:"+TCP_PORT)) {
        conn.write (TCP_PORT)
        conn.close()
    }
}

preferences.rulerUnits = oldRulerUnits
preferences.typeUnits = oldTypeUnits
"""


def getFreeSocket():
    '''Get a free socket.'''

    TCP_IP = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, 0))
    TCP_PORT = s.getsockname()[1]
    s.listen(1)
    return s, TCP_PORT

def waitForPSConfirmation(s, TCP_PORT):
    '''Method that will be added to a thread that waits for Photoshop connection.'''

    BUFFER_SIZE = 1024

    conn, addr = s.accept()
    while 1:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        if data == str(TCP_PORT):
            refreshTextures = """string $fileNodes[]  = `ls -type file`;for($f in $fileNodes) {string $attrName = $f + ".fileTextureName";string $fileName = `getAttr $attrName`;setAttr -type "string" $attrName $fileName;}"""
            cmds.evalDeferred('import maya.mel as mel;mel.eval(\'%s\')' % refreshTextures)  # @UndefinedVariable

        #conn.send(data)
    conn.close()



def createAtlas (aItems, txtFinalFilename, sizeX, sizeY, photoshopPath, resamplingMode):
    '''Send information to Photoshop to create texture atlas.'''

    if not os.path.exists(photoshopPath):
        cmds.confirmDialog(message="Photoshop path does not exist.", button=["ok"])  # @UndefinedVariable
        return

    resampleMode = ResamplingModeValues.index(resamplingMode) + 1

    commandList = [txtFinalFilename, sizeX, sizeY, resampleMode]

    for k in aItems:

        kPosX = int(sizeX * k.posX)
        kPosY = int(sizeY * k.posY)
        kSizeX = int(sizeX * k.sizeX)
        kSizeY = int(sizeY * k.sizeY)

        commandList.extend([k.file, kPosX, kPosY, kSizeX, kSizeY])


    # Setup thread to wait for Photoshop response - STEP 1
    s, TCP_PORT = getFreeSocket()
    commandList.insert(0, TCP_PORT)

    t = threading.Thread(target=waitForPSConfirmation, args=(s, TCP_PORT))
    threads = []
    threads.append(t)
    t.start()

    # Send job to Photoshop
    commandString = (','.join(map(str, commandList))).replace("\\", "/")
    PSscriptOutput = PSScript.replace("ITEMLIST", commandString)
    
    scriptFile = (os.path.dirname(__file__)+"/EAscript.jsx").replace("/", "\\")
    with open(scriptFile, "w") as script:
        script.write(PSscriptOutput)
    
    subprocess.Popen((photoshopPath, scriptFile))