"""
Holds global constants for the script.

"""

"""
General
"""
WindowName =  "EasyAtlasWindow"
PrefWindowName = "EAprefWindow"
DockName = "EasyAtlas"

diaWarning = "Warning"


"""
Resampling Modes
"""

# Do not change index order !
ResamplingModeValues = [
    'none',
    'nearest',
    'bilinear',
    'bicubic',
    'bicubic-sharper',
    'bicubic-smoother',
    'bicubic-automatic',
    'automatic',
    'preserve-details'
]

# Converts the pretty text to be put inside the config file.
ResamplingExportValues = {
    "None": ResamplingModeValues[0],
    "Nearest Neighbor": ResamplingModeValues[1],
    "Bilinear": ResamplingModeValues[2],
    "Bicubic": ResamplingModeValues[3],
    "Bicubic (Sharper)": ResamplingModeValues[4],
    "Bicubic (Smoother)": ResamplingModeValues[5],
    "Bicubic (Automatic)": ResamplingModeValues[6],
    "Automatic": ResamplingModeValues[7],
    "Preserve Details": ResamplingModeValues[8],
}
