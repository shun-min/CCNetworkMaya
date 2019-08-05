import maya.cmds as cmds
from __builtin__ import range
from __builtin__ import dict
from __builtin__ import True
from maya import OpenMayaUI as omui
import os.path
from functools import partial

try:
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *
	from PySide2.QtUiTools import *
	from shiboken2 import wrapInstance
except ImportError: 
	from PySide.QtCore import *
	from PySide.QtGui import *
	from PySide.QtUiTools import *
	from shiboken import wrapInstance


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
# The above code is for importing my interface into maya

# PRE-REQUISITES:
# Must have geometry in scene and named them with *_geo
# must have aiStandardSurface shader created, and named with *_shdr

class CCNetworkCreator(QWidget):

	# Global Variables
	global tickedAttribList
	tickedAttribList = []

	global textboxesArr
	textboxesArr = []

	global aiCCNodeList
	aiCCNodeList = []

	global createdtexture
	createdtexture = []

	global filename
	filename = [] 


	def __init__(self,*args, **kwargs):
		super(CCNetworkCreator,self, *args).__init__(**kwargs)
		self.setParent(mayaMainWindow)
		self.setWindowFlags(Qt.Window)
		self.initUI()
		
		self.numberOfNodesCreated = 0

		# populate combo box for selecting geometry 
		cmds.select( '*_geo', r= True)
		list = cmds.ls( selection=True)
		self.ui.aiSScomboBox.addItems(list)
		#-->Invokes function when combo box value changes
		self.ui.aiSScomboBox.currentIndexChanged.connect(self.updateaiSScomboBox)
		

		# populate combo box for selecting shader
		cmds.select( '*_shdr', r= True)
		list2 = cmds.ls( selection=True)
		self.ui.shaderComboBox.addItems(list2) 
		# invokes function when shader combo box value changes
		self.ui.shaderComboBox.currentIndexChanged.connect(self.updateshaderComboBox)
	

		#Button to assign shader to geometry
		self.ui.assignShaderBtn.clicked.connect(self.clickedShaderBtn)


		# populate second shaderCombo box
		# select shader for assigning
		cmds.select( '*_shdr', r= True)
		list3 = cmds.ls( selection=True)
		self.ui.shaderComboBox2.addItems(list3)  
		self.ui.shaderComboBox2.currentIndexChanged.connect(self.updateshaderComboBox2)


		# set up the check box to create colorCorrect nodes. All checkboxes are listened by the function updateCheckbox
		self.ui.baseColCheck.stateChanged.connect(lambda:self.updateCheckbox(self.ui.baseColCheck))
		self.ui.specColCheck.stateChanged.connect(lambda:self.updateCheckbox(self.ui.specColCheck))
		self.ui.specRoughCheck.stateChanged.connect(lambda:self.updateCheckbox(self.ui.specRoughCheck))
		# self.ui.specColCheck.stateChanged.connect(self.updateCheckbox)
		# self.ui.specRoughCheck.stateChanged.connect(self.updateCheckbox)
		

		#button to create aiImage file (ultility)
		self.ui.createAIImg.clicked.connect(self.createAIImg)

		# open file Dialog to link actual image file to aiImage 
		self.ui.fileLinkBtn1.clicked.connect(self.openFileDialog)
		self.ui.fileLinkBtn2.clicked.connect(self.openFileDialog2)
		self.ui.fileLinkBtn3.clicked.connect(self.openFileDialog3)
		self.ui.fileLinkBtn4.clicked.connect(self.openFileDialog4)


		#create ai color correct nodes
		self.ui.createCCNode.clicked.connect(self.createCCNode)

		#activate select shader button 
		self.ui.selShaderBtn.clicked.connect(self.selShaderBtnPressed)

		# connect ai CC to channels button
		self.ui.connectaiCCBtn.clicked.connect(self.connectCCNetwork)

#----------this section calls up the initial value for blank boxes that need them------------------------
	def loadInitialValues(self):
		self.updateaiSScomboBox
		self.updateshaderComboBox
		self.updateassignShaderBtn
		self.updateshaderComboBox2
	

#-----------this section gives instructions to the button's function------------------

	def initUI(self):
		loader = QUiLoader()
		currentDir = os.path.dirname(__file__)
		file = QFile(currentDir + "/CCNetworkCreator.ui")
		file.open(QFile.ReadOnly)
		self.ui = loader.load(file, parentWidget=self)
		file.close()

	#create dropdown list for geometry box
	def updateaiSScomboBox(self, *args):
		selectedGeoName = str(self.ui.aiSScomboBox.currentText())
		selectedGeo = cmds.select(selectedGeoName, r = True) 
		
	#create dropdown list for shader box 
	def updateshaderComboBox(self, *args):
		selectedShaderName = str(self.ui.shaderComboBox.currentText())
		selectedShader = cmds.select(selectedShaderName, r = True)

	#assign shader to geometry
	def clickedShaderBtn(self, *args):
		selectedGeo = str(self.ui.aiSScomboBox.currentText())
		cmds.select(selectedGeo)
		selectedShader = self.ui.shaderComboBox.currentText()
		cmds.hyperShade(assign=selectedShader)

	#shader information needed for the assignments below to work
	def updateshaderComboBox2(self, *args):
		selectedShaderName = str(self.ui.shaderComboBox2.currentText())
		selectedShader = cmds.select(selectedShaderName, r = True)

	
	# invoke when any checkbox is ticked / unticked
	# aiImage will be renamed according to which checkboxes are checked
	def updateCheckbox(self, updatedCheckbox):
		isTicked = updatedCheckbox.isChecked()
		updatedAttrWtSpace = updatedCheckbox.text()
		updatedAttr = updatedAttrWtSpace.replace(" ", "")

		if isTicked: 
			tickedAttribList.append(updatedAttr)

		else:
			tickedAttribList.remove(updatedAttr)

	# create Textures (aiImage) 
	''' 
	Will only work when checkbox is ticked
	TODO: add exception to catch error when user doesn't specify textures to be created. 
	In 2nd for loop, replace the hard-coded "aiImage" string
	'''
	def createAIImg(self,*args):

		# hard coded array to store texboxes. Look for comments above connectCCNetwork().
		self.textboxesArr = [[self.ui.INtexture1,self.ui.fileBox1],[self.ui.INtexture2,self.ui.fileBox2],[self.ui.INtexture3,self.ui.fileBox3],[self.ui.INtexture4,self.ui.fileBox4]]

		# clear textbox before creating new aiImg node for another round
		for items in self.textboxesArr:
			items[0].setText("")

		# create aiImages according to selected checkboxes and renamed 
		for attrName in tickedAttribList:
			# rename the newly created aiImage according to the ticked checkboxes
			newImgName = "aiImg" + str(attrName)
			aiImage_node = cmds.shadingNode("aiImage", asTexture=True)
			originalName = str(cmds.ls(aiImage_node)[0])
			cmds.rename(originalName, newImgName)

			# list the name and directory of aiImage nodes that are created
			index = tickedAttribList.index(attrName)
			textbox = self.textboxesArr[index]
			textbox[0].setText(newImgName)
			textbox[1].setEnabled(True)

	def openDialog(self, *args):
		multipleFilters = "TX Files (*.tx);;Exr Files (*.exr);;All Files (*.*)"
		filePath = cmds.fileDialog2(fileFilter = multipleFilters, dialogStyle = 2, fileMode = 1, caption = "Select texture", okCaption = "Select")[0]
		return filePath

	def assignTexture(self, imgName, filePath):
		imgAttrName = str(imgName) + ".filename"
		cmds.setAttr(imgAttrName, filePath, type = "string")
		cmds.select(imgName)

	# invokes dialog to browse for textures
	def openFileDialog(self, *args):
		filePath = self.openDialog()
		# displays path in UI
		self.ui.fileBox1.setText(filePath)
		# craft texture path string
		imgName = self.ui.INtexture1.toPlainText()
		# assign texture path to aiImage node
		self.assignTexture(imgName, filePath)
		

	def openFileDialog2(self, *args):
		filePath = self.openDialog()
		self.ui.fileBox2.setText(filePath)
		imgName = self.ui.INtexture2.toPlainText()
		self.assignTexture(imgName, filePath)
		 
	def openFileDialog3(self, *args):
		filePath = self.openDialog()
		self.ui.fileBox3.setText(filePath)
		imgName = self.ui.INtexture3.toPlainText()
		self.assignTexture(imgName, filePath)

	def openFileDialog4(self, *args):
		filePath = self.openDialog()
		self.ui.fileBox4.setText(filePath)
		imgName = self.ui.INtexture4.toPlainText()
		self.assignTexture(imgName, filePath)
		

		# This button only works when checkbox is checked; works alongside it
		# It creates a colour correct node and renames it according to the chnl
		# e.g.: aiCC_baseColour or aiCC_specColour 
	def createCCNode(self,*args):
		# clear list of CC nodes that will have their CCNodes created.
		aiCCNodeList[:] = []

		for attrName in tickedAttribList:
			aiCCNode = cmds.shadingNode("aiColorCorrect",asUtility = True)
			ccName = str(cmds.ls(aiCCNode)[0])
			renamedCC = cmds.rename(ccName,"aiCC_" + attrName)
			aiCCNodeList.append(renamedCC)

	# Select shader again for assignment to work
	def selShaderBtnPressed(self, *args):
		activeShaderName = str(self.ui.shaderComboBox2.currentText())
		cmds.select(activeShaderName)

	'''
	Connects aiImage to aiColorCorrect and then to selected shader. 
	The code loops through the hard-coded global textboxes array, looks for the aiImg node name that matches the ticked attribute name. 
	Name of the correct node is retrieved as str for connectAttr()
 
	TODO: 
	1.All attribute checkboxes are ticked WITH THE RIGHT ORDER
	2. This code only works once. If a new set of aiImg nodes, are created, the code breaks
	'''
	def connectCCNetwork(self, *args):
		activeShaderName = str(self.ui.shaderComboBox2.currentText())
		cmds.select(activeShaderName, r = True)

		# if base color checkbox is ticked, connect aiImagebase color -> base colour CC node -> shader
		if self.ui.baseColCheck.isChecked():
			# Users might tick the checkboxes in various orders. This step makes sure that the correct CC node is connected to the correct channel

			# Put values of 3 checkbox into array
			for i in range(0,3):
				activeCC = aiCCNodeList[i]

				# connect aiImage to aiCCNode
				# TODO: get number of textboxes to loop this.
				for j in range(0, 4):
					currentTextureName = self.textboxesArr[j][0].toPlainText()
					if "BaseColour" in currentTextureName:
						cmds.connectAttr('%s.outColor' % activeCC, '%s.baseColor' % activeShaderName)
						textureNodeList = cmds.ls(currentTextureName)
						print textureNodeList
						baseColTextureNode = textureNodeList[0]
						cmds.connectAttr('%s.outColor'%baseColTextureNode, '%s.input' %activeCC)

					if "SpecularColour" in currentTextureName:
						cmds.connectAttr('%s.outColor' % activeCC, '%s.specularColor' % activeShaderName)
						textureNodeList = cmds.ls(currentTextureName)
						specColTextureNode = textureNodeList[0]
						cmds.connectAttr('%s.outColor' % specColTextureNode, '%s.input' % activeCC)

					if "SpecularRoughness" in currentTextureName:
						cmds.connectAttr('%s.outColorR' % activeCC, '%s.specularRoughness' % activeShaderName)
						textureNodeList = cmds.ls(currentTextureName)
						specRoughTextureNode = textureNodeList[0]
						cmds.connectAttr('%s.outColor' % specRoughTextureNode, '%s.input' % activeCC)
	
#================================end of main code====================================================
def main():
	ui= CCNetworkCreator()
	ui.show()
	return ui

if __name__ == '__main__':
	main()