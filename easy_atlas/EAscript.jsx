var args = "53345,d:/easyatlas/sourceimages/__out.tga,512,512,D:/EasyAtlas/sourceimages/crate01_diff.tga,0,0,256,256,D:/EasyAtlas/sourceimages/chair_diff.tga,256,0,256,256,D:/EasyAtlas/sourceimages/mailbox_diff.tga,0,256,256,256,D:/EasyAtlas/sourceimages/shield_diff.tga,256,256,256,256"
var argList = args.split(",")

var oldRulerUnits = preferences.rulerUnits;
var oldTypeUnits = preferences.typeUnits;

preferences.rulerUnits = Units.PIXELS;
preferences.typeUnits = TypeUnits.PIXELS;

var TCP_PORT = parseInt(argList.shift())
var fileName = (argList.shift()).replace("/", "\\")
var outputSizeX = parseInt(argList.shift())
var outputSizeY = parseInt(argList.shift())

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
    filename = argList[i].replace("/", "\\")
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
    var layerName = filename.split("\\").pop()
    layerName = filename.split("/").pop()
    layerName = layerName.substr(0,layerName.lastIndexOf("."))

    docTemp.resizeImage(sizeX, sizeY, docTemp.resolution, ResampleMethod.NEARESTNEIGHBOR)
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
