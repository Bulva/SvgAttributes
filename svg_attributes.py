# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SvgAttributes
                                 A QGIS plugin
 This plugin creates SVG with attributes
                              -------------------
        begin                : 2016-07-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Petr Silhak
        email                : petrsilhak@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import *
from qgis.PyQt import QtCore
from random import randint
import os.path

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QListWidgetItem, QListView
# Initialize Qt resources from file resources.py
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QStandardItem
from PyQt4.QtGui import QStandardItemModel
from qgis.core import QgsFeatureRequest
from qgis.core import QgsMessageLog
from qgis.core import QGis
import GeometryError

import resources
# Import the code for the dialog
from svg_attributes_dialog import SvgAttributesDialog
import os.path

class SvgAttributes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SvgAttributes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SvgAttributesDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Svg With Attributes')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SvgAttributes')
        self.toolbar.setObjectName(u'SvgAttributes')

        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(lambda: self.selectOutputFile())


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SvgAttributes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SvgAttributes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create SVG'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Svg With Attributes'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def selectOutputFile(self):
        """
        Function for selecting path for output file
        :return:
        """
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file", "", '*.svg')
        self.dlg.lineEdit.setText(filename)

    def fillCheckboxes(self, layers, name):
        """
        Function for filling listView with checkboxes
        :param layers: layers from Qgis legend
        :param name: name of current layer from comboBox
        :return:
        """
        layer = None

        model = QStandardItemModel()
        self.dlg.listView.reset()

        for layer in layers:
            if layer.name() == name:
                fields = layer.pendingFields()
                fieldNames = [field.name() for field in fields]
                for fieldName in fieldNames:
                    item = QStandardItem(fieldName)
                    item.setCheckable(True)
                    item.setText(fieldName)
                    model.appendRow(item)

        self.dlg.listView.setModel(model)

    def createSVG(self, filename, attributes_dict):
        width = self.iface.mapCanvas().size().width()
        height = self.iface.mapCanvas().size().height()
        with open(filename, 'w') as outputfile:
            outputfile.write('''<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n''')
            outputfile.write('<svg width="'+str(width)+'" height="'+str(height)+'" version="1.1" xmlns="http://www.w3.org/2000/svg">\n\n')

            features_list = self.writeLayer(attributes_dict)
            for svg_feature in features_list:
                outputfile.write(svg_feature)

            outputfile.write('</svg>')
            QMessageBox.information(None, "SVG Writing:", 'Writing SVG was finished')

    def writeLayer(self, attributes_dict):
        current_layer = self.dlg.comboBox_layers.currentText()
        layers = self.iface.legendInterface().layers()
        for layer in layers:
            if layer.name() == current_layer:
                return self.geometryLayerType(layer, attributes_dict)



    def writePointFeature(self, layer, attributes_dict):
        points_svg = []
        request = QgsFeatureRequest()
        request.setFilterRect(self.iface.mapCanvas().extent())
        for feature in layer.getFeatures(request):
            points_svg.append(self.writePointToSVG(feature, attributes_dict))
        return points_svg

    def writeLineFeature(self, layer, attributes_dict):
        lines_svg = []
        request = QgsFeatureRequest()
        request.setFilterRect(self.iface.mapCanvas().extent())
        for feature in layer.getFeatures(request):
            lines_svg.append(self.writeLineToSVG(feature, attributes_dict))
        return lines_svg

    def writePolygonFeature(self, layer, attributes_dict):
        polygons_svg = []
        request = QgsFeatureRequest()
        request.setFilterRect(self.iface.mapCanvas().extent())
        for feature in layer.getFeatures(request):
            polygons_svg.append(self.writePolygonToSVG(feature, attributes_dict))
        return polygons_svg

    def writeLineToSVG(self, feature, attributes_dict):
        line = feature.geometry().asPolyline()
        attributes = feature.attributes()
        atr_string = ''
        line_string = 'M'
        pixel_value = self.iface.mapCanvas().mapUnitsPerPixel()
        extent = self.iface.mapCanvas().extent()
        iterator_number = 0

        #TODO Need find only points in mapcanvas - not working for big features outside of canvas

        for key, value in attributes_dict.iteritems():
            atr_string += ' '+value.encode('utf-8')+'="'+attributes[key].encode('utf-8')+'"'

        for coordinates in line:
                pixelX = (coordinates[0]-extent.xMinimum())/pixel_value
                pixelY = (coordinates[1]-extent.yMaximum())/pixel_value
                if iterator_number == 0:
                    line_string += str(pixelX)+' '+str(-pixelY)+' '
                    iterator_number += 1
                else:
                    line_string += 'L'+str(pixelX) + ' ' + str(-pixelY) + ' '
        return '<path fill="None" fill-opacity="0" stroke="#000" stroke-width="0.26" d="'+line_string+'" '+atr_string+' />\n'

    def writePolygonToSVG(self, feature, attributes_dict):
        polygon = feature.geometry().asPolygon()
        attributes = feature.attributes()
        atr_string = ''
        polygon_string = 'M'
        pixel_value = self.iface.mapCanvas().mapUnitsPerPixel()
        extent = self.iface.mapCanvas().extent()
        iterator_number = 0

        #TODO Needed find why some polygons are problematic for export

        for key, value in attributes_dict.iteritems():
            atr_string += ' '+value.encode('utf-8')+'="'+attributes[key].encode('utf-8')+'"'

        for polygon_list in polygon:
            QgsMessageLog.logMessage('Zapisuji Polygon','Zkouska')
            if polygon_list:
                for coordinates in polygon_list:
                    pixelX = (coordinates[0]-extent.xMinimum())/pixel_value
                    pixelY = (coordinates[1]-extent.yMaximum())/pixel_value
                    if iterator_number == 0:
                        polygon_string += str(pixelX)+' '+str(-pixelY)+' '
                        iterator_number += 1
                    else:
                        polygon_string += 'L'+str(pixelX) + ' ' + str(-pixelY) + ' '

        multiPolygon = feature.geometry().asMultiPolygon()
        for multiPolygon_list in multiPolygon:
            QgsMessageLog.logMessage('Zapisuji Multipolygon', 'Zkouska')
            if multiPolygon_list:
                for multiPolygon_parts in multiPolygon_list:
                    if multiPolygon_parts:
                        for coordinates in multiPolygon_parts:
                            pixelX = (coordinates[0] - extent.xMinimum()) / pixel_value
                            pixelY = (coordinates[1] - extent.yMaximum()) / pixel_value
                            if iterator_number == 0:
                                polygon_string += str(pixelX) + ' ' + str(-pixelY) + ' '
                                iterator_number += 1
                            else:
                                polygon_string += 'L' + str(pixelX) + ' ' + str(-pixelY) + ' '
        QgsMessageLog.logMessage('Konec zapisu', 'Zkouska')

        return '<path stroke-width="0.26" d="'+polygon_string+'" '+atr_string+' />\n'


    def writePointToSVG(self, feature, attributes_dict):
        point = feature.geometry().asPoint()
        attributes = feature.attributes()
        atr_string = ''
        for key, value in attributes_dict.iteritems():
            #QgsMessageLog.logMessage(str(key)+' '+str(value), 'Repaired')
            atr_string += ' '+value.encode('utf-8')+'="'+attributes[key].encode('utf-8')+'"'
            pixel_value = self.iface.mapCanvas().mapUnitsPerPixel()
            extent = self.iface.mapCanvas().extent()
            pixelX = (point.x()-extent.xMinimum())/pixel_value
            pixelY = (point.y()-extent.yMaximum())/pixel_value
        return '<circle cx="' + str(pixelX) + '" cy="' + str(-pixelY) + '" r="3" '+atr_string+'/>\n'


    def createAttributesDictionary(self):
        checked_attributes = {}
        model = self.dlg.listView.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                checked_attributes[row] = item.text()
        return checked_attributes

    def geometryLayerType(self, layer, attributes_dict):
        if layer.wkbType() == QGis.WKBPoint:
            return self.writePointFeature(layer, attributes_dict)
        elif layer.wkbType() == QGis.WKBLineString:
            return self.writeLineFeature(layer, attributes_dict)
        elif layer.wkbType() == QGis.WKBPolygon:
            return self.writePolygonFeature(layer, attributes_dict)
        elif layer.wkbType() == QGis.WKBMultiLineString:
            return self.writeLineFeature(layer, attributes_dict)
        elif layer.wkbType() == QGis.WKBMultiPolygon:
            return self.writePolygonFeature(layer, attributes_dict)
        else:
            raise GeometryError('Unknown geometry type')



    def run(self):
        """Run method that performs all the real work"""
        layers = self.iface.legendInterface().layers()
        layers_list = []
        for layer in layers:
            layers_list.append(layer.name())
        self.dlg.comboBox_layers.clear()
        self.dlg.comboBox_layers.addItems(layers_list)



        #Initial setting list of checkboxes
        initialLayerComboBox = str(self.dlg.comboBox_layers.currentText())
        self.fillCheckboxes(layers, initialLayerComboBox)

        #signal for filling listView
        self.dlg.comboBox_layers.currentIndexChanged.connect(lambda: self.fillCheckboxes(layers, str(self.dlg.comboBox_layers.currentText())))

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            filename = self.dlg.lineEdit.text()
            selectedLayerIndex = self.dlg.comboBox_layers.currentIndex()

            #TODO Create reprojection of layer because it is not working with other CRS than EPSG: 4326


            self.createSVG(filename, self.createAttributesDictionary())
            pass



