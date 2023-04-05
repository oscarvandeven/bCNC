# $Id$
#
# Author: @CarlosGS
# Date:      2-Jan-2017

import math
import numpy as np
from CNC import CNC, Block
from ToolsPage import Plugin


__author__ = "Oscar van de Ven"
__email__ = "@"

__name__ = _("Box joint")
__version__ = "0.0.1"

# =============================================================================
# Create a box joint by milling away material from the edge of a board
# =============================================================================
class Tool(Plugin):
    __doc__ = _("Create a box joint path")

    def __init__(self, master):
        Plugin.__init__(self, master, "Box-joint")
        self.icon = "cut"
        self.group = "CAM_Core+"#"Generator"
        self.variables = [
            ("name", "db", "", _("Name")),
            ("Margin", "mm", 2, _("Margin")),
            ("Totalwidth", "mm", 100, _("Total width")),
            ("BoxWidthOdd", "mm", 20, _("Single odd box width")),
            ("BoxWidthEven", "mm", 20, _("Single even box width")),
            ("CutOdd", "bool", True, _("Cut the odd boxes")),
        ]
        self.buttons.append("exe")
        self.help = """This plugin mills box joints on the side of a panel:
#boxjoint
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
        cutodd = self["CutOdd"]

        total_width = self.fromMm("Totalwidth")
        box_width_odd = self.fromMm("BoxWidthOdd")
        box_width_even = self.fromMm("BoxWidthEven")
        margin = self.fromMm("Margin")

        if not name or name == "default":
            name = f"Box joint-{box_width_odd}-{box_width_even}-{total_width}-" + ('odd' if cutodd else 'even')

        # Check parameters
        if box_width_odd > total_width:
            app.setStatus(_("Boxjoint abort: box is smaller than total"))
            return
        if box_width_odd < diameter or box_width_even < diameter:
            app.setStatus(_("Boxjoint abort: box is smaller than tool"))
            return
        total_box_width = 0
        box_widths = []
        while total_box_width < total_width:
            odd = len(box_widths) % 2 == 0
            if odd:
                new_box_width = box_width_odd
            else:
                new_box_width = box_width_even
            if total_box_width + new_box_width <= total_width:
                box_widths.append(new_box_width)
            total_box_width += new_box_width
        total_box_width = np.sum(box_widths)
        total_remainder = total_width - total_box_width
        if total_remainder > 0:
            # If there is space left, an additional partial box is added to the front and the back
            box_widths.append(total_remainder / 2)
            box_widths.insert(0, total_remainder / 2)
            # This causes odd and even to swap, this compensated this unwanted behaviour
            cutodd = not cutodd

        number_of_boxes = len(box_widths)
        number_of_layers = math.ceil(thickness/stepz)

        y_low = -diameter/2 - margin
        y_high = thickness + diameter/2 + margin

        # Initialize blocks that will contain our gCode
        blocks = []
        block = Block(name)
        box_locations = np.cumsum([0]+box_widths)
        margin_x = max(margin, (diameter - total_remainder / 2 if total_remainder > 0 else 0))
        box_locations[0] -= margin_x
        box_locations[-1] += margin_x

        print(box_locations)
        print(box_widths)
        x_start = box_locations[0] + diameter / 2

        y = 0
        for n_z in range(1, int(number_of_layers)):
            z = max(-n_z*stepz, -thickness)
            block.append(CNC.zsafe())  # <<< Move rapid Z axis to the safe height in Stock Material
            y = y_low
            x = x_start
            block.append(CNC.grapid(x, y))  # <<< Move rapid to X and Y coordinate
            block.append(CNC.zenter(z))

            for n_box in range(int(cutodd == False), int(number_of_boxes), 2):
                x = box_locations[n_box] + diameter / 2
                block.append(CNC.grapid(x, y))
                box_width = box_locations[n_box+1] - box_locations[n_box]
                number_of_lines = 1 + math.ceil((box_width - diameter) / (diameter * (1 - stepover / 100)))
                if number_of_lines > 1:
                    x_increment = (box_width - diameter) / (number_of_lines - 1)
                else:
                    x_increment = 0
                for n_line in range(int(number_of_lines)):
                    if y == y_low:
                        y = y_high
                    else:
                        y = y_low
                    block.append(CNC.glinev(1, [x, y, z], feed))

                    if n_line < number_of_lines - 1:
                        x += x_increment
                        block.append(CNC.grapid(x, y))
        blocks.append(block)
        active = app.activeBlock()
        if active == 0:
            active = 1
        app.gcode.insBlocks(active, blocks, "Box joint")
        app.refresh()
        app.setStatus(_("Generated: Box joint"))
