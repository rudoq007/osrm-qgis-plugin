# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSRM
                                 A QGIS plugin
 Display your routing results from OSRM
                              -------------------
        begin                : 2015-10-29
        git sha              : $Format:%H$
        copyright            : (C) 2015 by mthh
        email                : matthieu.viry@cnrs.fr
 ***************************************************************************/

"""
#from qgis.utils import QgsInterface
from qgis.utils import iface
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings, pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

import os.path
import resources
from osrm_dialog import (
    OSRMDialog, OSRM_table_Dialog, OSRM_access_Dialog,
    OSRM_batch_route_Dialog, OSRM_DialogTSP
)


class OSRM:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)
        self.dlg = None

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'OSRM_{locale}.qm')

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Routing with OSRM')
        self.toolbar = self.iface.addToolBar('Routing with OSRM')
        self.toolbar.setObjectName('Routing with OSRM')

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        
        :param message: String for translation.
        :type message: str
        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate('Routing with OSRM', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, 
                   add_to_menu=True, add_to_toolbar=True, status_tip=None, 
                   whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. 
        :type icon_path: str
        :param text: Text for menu items.
        :type text: str
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        :param enabled_flag: A flag indicating if the action should be enabled
        :type enabled_flag: bool
        :param add_to_menu: Flag for adding to the menu.
        :type add_to_menu: bool
        :param add_to_toolbar: Flag for adding to the toolbar.
        :type add_to_toolbar: bool
        :param status_tip: Text to show when mouse hovers over the action.
        :type status_tip: str
        :param whats_this: Text to show in status bar when hovered.
        :param parent: Parent widget for the new action.
        :type parent: QWidget
        :returns: The action created, also added to self.actions list.
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
            self.iface.addPluginToWebMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.add_action(
            ':/plugins/OSRM/img/icon.png',
            text=self.tr('Find a route with OSRM'),
            callback=self.run_route,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/plugins/OSRM/img/icon_table.png',
            text=self.tr('Get a time matrix with OSRM'),
            callback=self.run_table,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/plugins/OSRM/img/icon_access.png',
            text=self.tr('Make accessibility isochrones with OSRM'),
            callback=self.run_accessibility,
            parent=self.iface.mainWindow())

        self.add_action(
            None,
            text=self.tr('Solve the Traveling Salesman Problem with OSRM'),
            callback=self.run_tsp,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)

        self.add_action(
            None,
            text=self.tr('Export many routes from OSRM'),
            callback=self.run_batch_route,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(self.tr('&Routing with OSRM'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    @pyqtSlot()
    def run_route(self):
        """Run the window to compute a single viaroute"""
        self.dlg = OSRMDialog(self.iface)
        self.dlg.originEmit.canvasClicked.connect(self.dlg.store_origin)
        self.dlg.intermediateEmit.canvasClicked.connect(self.dlg.store_intermediate)
        self.dlg.destinationEmit.canvasClicked.connect(self.dlg.store_destination)
        self.dlg.pushButtonOrigin.clicked.connect(self.get_origin)
        self.dlg.pushButtonIntermediate.clicked.connect(self.get_intermediate)
        self.dlg.pushButtonDest.clicked.connect(self.get_destination)
        self.dlg.pushButton_about.clicked.connect(self.dlg.print_about)
        self.dlg.show()

    @pyqtSlot()
    def run_batch_route(self):
        """Run the window to compute many viaroute"""
        self.dlg = OSRM_batch_route_Dialog(self.iface)
        self.dlg.pushButton_about.clicked.connect(self.dlg.print_about)
        self.dlg.show()

    @pyqtSlot()
    def run_table(self):
        """Run the window for the table function"""
        self.dlg = OSRM_table_Dialog(self.iface)
        self.dlg.pushButton_about.clicked.connect(self.dlg.print_about)
        self.dlg.show()

    @pyqtSlot()
    def run_tsp(self):
        """Run the window for solving the Traveling Salesman Problem"""
        self.dlg = OSRM_DialogTSP(self.iface)
        self.dlg.pushButton_about.clicked.connect(self.dlg.print_about)
        self.dlg.show()

    @pyqtSlot()
    def run_accessibility(self):
        """Run the window for making accessibility isochrones"""
        self.dlg = OSRM_access_Dialog(self.iface)
        self.dlg.originEmit.canvasClicked.connect(self.dlg.store_origin)
        self.dlg.intermediateEmit.canvasClicked.connect(self.dlg.store_intermediate_acces)
        self.dlg.pushButtonOrigin.clicked.connect(self.get_origin)
        self.dlg.pushButton_about.clicked.connect(self.dlg.print_about)
        self.dlg.toolButton_poly.clicked.connect(self.polycentric)
        self.dlg.show()

    @pyqtSlot()
    def polycentric(self):
        QMessageBox.information(
            self.iface.mainWindow(), 'Info',
            "Experimental:\n\nAdd other source points and compute "
            "polycentric accessibility isochrones")
        self.get_intermediate()

    def get_origin(self):
        self.canvas.setMapTool(self.dlg.originEmit)

    def get_destination(self):
        self.canvas.setMapTool(self.dlg.destinationEmit)

    def get_intermediate(self):
        self.canvas.setMapTool(self.dlg.intermediateEmit)
