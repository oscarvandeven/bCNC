# $Id$
#
# Author: @CarlosGS
# Date:      2-Jan-2017

import math
import numpy as np
from CNC import CNC, Block
from ToolsPage import Plugin
import numpy as np

__author__ = "Oscar van de Ven"
__email__ = "@"

__name__ = _("Feedrate test")
__version__ = "0.0.1"

# =============================================================================
# Try a range of feedrates to see the resulting cuts
# =============================================================================
class Tool(Plugin):
    __doc__ = _("Try a range of feedrates to see the resulting cuts")

    def __init__(self, master):
        Plugin.__init__(self, master, "FeedrateTest")
        self.icon = "cut"
        self.group = "CAM_Core"#"Generator"
        self.variables = [
            ("name", "db", "", _("Name")),
            ("Testlength", "mm", 50, _("Test length")),
            ("MaxFeedrate", "float", 1200, _("Maximum feedrate")),
            ("MinFeedrate", "float", 100, _("Minimum feedrate")),
            ("FeedrateIncrement", "float", 100, _("Feedrate increment")),
            ("Depth", "mm", 5, _("Depth")),
            ("Margin", "mm", 5, _("Margin")),
        ]
        self.buttons.append("exe")
        self.help = """This plugin tests different feedrates

        """

    # ----------------------------------------------------------------------
    def execute(self, app):
        name = self["name"]
        thickness = app.cnc["thickness"]
        stepover = app.cnc["stepover"]
        feed = app.cnc["cutfeed"]
        feedz = app.cnc["cutfeedz"]
        safe = app.cnc["safe"]
        stepz = app.cnc["stepz"]
        diameter = app.cnc["diameter"]

        Depth = self.fromMm("Depth")
        MaxFeedrate = self["MaxFeedrate"]
        MinFeedrate = self["MinFeedrate"]
        FeedrateIncrement = self["FeedrateIncrement"]
        margin = self.fromMm("Margin")
        Testlength = self.fromMm("Testlength")
        blocks = []
        if not name or name == "default":
            new_name = f"feedratetest-{MinFeedrate}-{MaxFeedrate}-{FeedrateIncrement}-{diameter}"

        block = Block(new_name)

        x_start = - diameter / 2 - margin
        x_end = Testlength + diameter / 2 + margin
        x = x_start
        y = 0
        block.append(CNC.zsafe())  # <<< Move rapid Z axis to the safe height in Stock Material
        block.append(CNC.grapid(x, y))  # <<< Move rapid to X and Y coordinate
        z = -Depth
        block.append(CNC.zenter(z))
        for F in np.arange(MinFeedrate, MaxFeedrate + 1, FeedrateIncrement):

            block.append(CNC.grapid(x, y))  # <<< Move rapid to X and Y coordinate

            x = x_end
            block.append(CNC.glinev(1, [x, y, z], F))
            y -= diameter * (1 - stepover / 100)
            block.append(CNC.grapid(x, y))  # <<< Move rapid to X and Y coordinate
            x = x_start
            block.append(CNC.glinev(1, [x, y, z], F))
            y -= diameter + margin
            print(y)
        block.append(CNC.zsafe())
        blocks.append(block)
        active = app.activeBlock()
        if active == 0:
            active = 1

        app.gcode.insBlocks(active, blocks, "Feedratetest")
        app.refresh()
        app.setStatus(_("Generated: Box joint"))
