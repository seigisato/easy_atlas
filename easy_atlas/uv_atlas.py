import maya.cmds as cmds
import maya.mel as mel


def createAtlas(aItems):
    """Create UV atlas."""

    mel.eval('scriptEditorInfo -e -suppressWarnings true;')

    for k in aItems:
        cmds.select("%s.map[0:]" % k.mesh)
        cmds.polyEditUV(pivotU = 0, pivotV = 1, scaleU = k.sizeX, scaleV = k.sizeY)
        cmds.polyMoveUV(tu = k.posX, tv = -k.posY)
