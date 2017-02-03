# -*- coding: utf-8 -*-

import os
import numpy
from .tvb.recon.model.constants import CC_POINT_FILE

try:
    from io import StringIO
except ImportError:  # Py 3
    from io import BytesIO as StringIO


class GenericIO(object):
    point_line_flag = "CC-CRS"

    def read_cc_point(self, file_path, line_flag):
        """
        Read vector values from ponscc.cut.log file generated by FreeSurfer
        """
        cc_point = []
        with open(os.path.expandvars(file_path)) as file_ref:
            for line in file_ref:
                if line.startswith(line_flag):
                    line = line.replace(line_flag, "").strip()
                    cc_point = list(map(float, line.split()))
                    break
        cc_point.append(1)
        return cc_point

    def get_ras_coordinates(self, matrix):
        vector = self.read_cc_point(CC_POINT_FILE, self.point_line_flag)

        a = numpy.array(matrix)
        b = numpy.array(vector)
        ras_vector = a.dot(b)

        return ras_vector[0:3]

    # Save a NumPy array to text in a StringIO object.
    def np_save_strio(self, out_array, fmt):
        string_io = StringIO()
        numpy.savetxt(string_io, out_array, fmt)
        return string_io