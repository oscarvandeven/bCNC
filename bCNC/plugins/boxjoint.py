# $Id$
#
# Author: @CarlosGS
# Date:      2-Jan-2017

import math

from CNC import CNC, Block
from ToolsPage import Plugin


__author__ = "Oscar van de Ven"
__email__ = "@"

__name__ = _("Box joint")
__version__ = "0.0.1"

# =============================================================================
# Create a ZigZag path
# =============================================================================
class Tool(Plugin):
    __doc__ = _("Create a box joint path")

    def __init__(self, master):
        Plugin.__init__(self, master, "Box-joint")
        self.icon = "zigzag"
        self.group = "Generator"
        self.variables = [
            ("name", "db", "", _("Name")),
            ("Margin", "mm", 2, _("Margin")),
            ("Totalwidth", "mm", 100, _("Total width")),
            ("BoxWidth", "mm", 20, _("Single box width")),
            ("CutOdd", "bool", True, _("Cut the odd boxes")),
        ]
        self.buttons.append("exe")

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


        if not name or name == "default":
            name = "Box joint"
        cutodd = self["CutOdd"]
        total_width = self.fromMm("Totalwidth")
        box_width = self.fromMm("BoxWidth")
        margin = self.fromMm("Margin")

        # Check parameters
        if box_width > total_width:
            app.setStatus(_("Boxjoint abort: box is smaller than total"))
            return

        total_remainder = total_width % box_width
        total_box_width = total_width - total_remainder
        number_of_lines = math.ceil((box_width/diameter-1)/(1-stepover/100))
        number_of_boxes = round(total_box_width/box_width)
        number_of_layers = math.ceil(thickness/stepz)

        y_low = -diameter/2 - margin
        y_high = thickness + diameter/2 + margin

        # Initialize blocks that will contain our gCode
        blocks = []
        block = Block(name)

        box_start = [total_remainder / 2 + n_box*box_width for n_box in range(number_of_boxes)]
        box_end   = [total_remainder / 2 + (n_box + 1) * box_width for n_box in range(number_of_boxes)]
        print(box_start)
        print(box_end)
        x_start = total_remainder / 2 + diameter / 2
        x_increment = (box_width - diameter)/number_of_lines
        y = 0
        for n_z in range(1, number_of_layers):
            z = max(-n_z*stepz, -thickness)
            block.append(CNC.zsafe())  # <<< Move rapid Z axis to the safe height in Stock Material
            y = y_low
            x = x_start
            block.append(CNC.grapid(x, y))  # <<< Move rapid to X and Y coordinate
            block.append(CNC.zenter(z))

            for n_box in range(cutodd == False, number_of_boxes, 2):
                x = box_start[n_box]
                block.append(CNC.grapid(x, y))


                for n_line in range(number_of_lines):
                    if y == y_low:
                        y = y_high
                    else:
                        y = y_low
                    #block.append(CNC.gline(x, y))
                    block.append(CNC.glinev(1, [x, y, z], feed))

                    if n_line < number_of_lines - 1:
                        x += x_increment
                        #block.append(CNC.gline(x, y))
                        block.append(CNC.glinev(1, [x, y, z], feed))


        blocks.append(block)
        active = app.activeBlock()
        if active == 0:
            active = 1
        app.gcode.insBlocks(active, blocks, "Box joint")
        app.refresh()
        app.setStatus(_("Generated: Box joint"))
