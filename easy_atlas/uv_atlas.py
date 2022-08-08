import maya.cmds as cmds
import maya.mel as mel

def createAtlas(aItems):
    """Create UV atlas."""
    
    mel.eval('scriptEditorInfo -e -suppressWarnings true;')  # @UndefinedVariable
       
    for k in aItems:
        
        cmds.select("%s.map[0:]" % k.mesh)  # @UndefinedVariable
        cmds.polyEditUV(pivotU=0, pivotV=1, scaleU=k.sizeX, scaleV=k.sizeY)  # @UndefinedVariable
        cmds.polyMoveUV(tu=k.posX, tv=-k.posY)  # @UndefinedVariable