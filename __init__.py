# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SvgAttributes
                                 A QGIS plugin
 This plugin creates SVG with attributes
                             -------------------
        begin                : 2016-07-30
        copyright            : (C) 2016 by Petr Silhak
        email                : petrsilhak@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SvgAttributes class from file SvgAttributes.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .svg_attributes import SvgAttributes
    return SvgAttributes(iface)
