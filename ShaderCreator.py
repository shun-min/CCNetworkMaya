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

# import PyQt interface
mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class ShaderCreator(QWidget):

	# Global Variables
	global tickedAttribList
	tickedAttribList = []

	global textboxes
	textboxes = []

	global aiCCnodeList
	aiCCnodeList = []

	global createdtexture
	createdtexture = []

	global filename
	filename = [] 


	def __init__(self,*args, **kwargs):
		super(ShaderCreator,self, *args).__init__(**kwargs)
		self.setParent(mayaMainWindow)
		self.setWindowFlags(Qt.Window)
		self.initUI()
		
		self.numberOfNodesCreated = 0

		# populate combo box for selecting geometry 
			# NOTE: user must have geometry in scene and named them with *_geo
		cmds.select( '*_geo', r= True)
		list = cmds.ls( selection=True)
		self.ui.aiSScomboBox.addItems(list)
		#-->Invokes function when combo box value changes
		self.ui.aiSScomboBox.currentIndexChanged.connect(self.updateaiSScomboBox)
		

		# populate combo box for selecting shader
			# NOTE: user must have aiStandardSurface and named them with *_shdr
		cmds.select( '*_shdr', r= True)
		list2 = cmds.ls( selection=True)
		self.ui.shaderComboBox.addItems(list2) 
		#-->invokes function when shader combo box value changes
		self.ui.shaderComboBox.currentIndexChanged.connect(self.updateshaderComboBox)
	

		# Button to assign shader to geometry
		self.ui.assignShaderBtn.clicked.connect(self.clickedShaderBtn)


		# populate second shaderCombo box
		# select shader for assigning
		cmds.select( '*_shdr', r= True)
		list3 = cmds.ls( selection=True)
		self.ui.shaderComboBox2.addItems(list3)  
		self.ui.shaderComboBox2.currentIndexChanged.connect(self.updateshaderComboBox2)


		# set up the check box to create colorCorrect nodes
		self.ui.baseColCheck.stateChanged.connect(self.updatebaseColCheck)
		self.ui.specColCheck.stateChanged.connect(self.updatespecColCheck)
		self.ui.specRoughCheck.stateChanged.connect(self.updatespecRoughCheck)
		

		# button to create aiImage file (ultility)
		self.ui.createaii.clicked.connect(self.createaii_buttonPressed)


		# populate aiImage (texture) box 
			#Renamed image populate itself in every next box when aiImage is created 
		self.ui.INtexture1.textChanged.connect(self.updateINtexture)


		# open file Dialog to link actual image file to aiImage 
		self.ui.fileLinkBtn1.clicked.connect(self.openFileDialog1)
		self.ui.fileLinkBtn2.clicked.connect(self.openFileDialog2)
		self.ui.fileLinkBtn3.clicked.connect(self.openFileDialog3)
		self.ui.fileLinkBtn4.clicked.connect(self.openFileDialog4)


		# create ai color correct nodes
		self.ui.createaiCCBtn.clicked.connect(self.createaiCCBtn_buttonPressed)

		# activate select shader button 
		self.ui.selShaderBtn.clicked.connect(self.selShaderBtnPressed)

		# connect ai CC to channels button
		self.ui.connectaiCCBtn.clicked.connect(self.clickedconnectCCBtn)

#----------this section calls up the initial value for blank boxes that need them------------------------
	def loadInitialValues(self):
		self.updateaiSScomboBox()
		self.updateshaderComboBox
		self.updateassignShaderBtn()
		self.updateINtexture 
		self.updateINtexture2
		self.updateshaderComboBox2
	

#-----------this section gives instructions to the button's function------------------

	def initUI(self):
		loader = QUiLoader()
		currentDir = os.path.dirname(__file__)
		file = QFile(currentDir + "/ShaderCreator.ui")
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
		print("Selected: " + selectedShaderName + " " + str(selectedShader))

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

	
	# invoke when checkbox is ticked
		#aiImage will be renamed according to which checkboxes are checked
		#must tick checkbox before creating aiImage;  limit:4 
	def updatebaseColCheck(self,*args):
		isTicked = self.ui.baseColCheck.isChecked()
		attribName = "baseColor"
		if isTicked: 
			tickedAttribList.append(attribName)

		else:
			tickedAttribList.remove(attribName)

	def updatespecColCheck(self,*args):
		isTicked = self.ui.specColCheck.isChecked()
		attribName = "specColor"
		if isTicked: 
			tickedAttribList.append(attribName)

		else:
			tickedAttribList.remove(attribName)

		
	def updatespecRoughCheck(self,*args):
		isTicked = self.ui.specRoughCheck.isChecked()
		attribName = "specRoughness"
		if isTicked: 
			tickedAttribList.append(attribName)

		else:
			tickedAttribList.remove(attribName)
		

	#create Textures (aiImage) 
			#will only work when checkbox is ticked 

	def createaii_buttonPressed(self,*args):
		self.textboxes = [[self.ui.INtexture1,self.ui.fileBox1],[self.ui.INtexture2,self.ui.fileBox2],[self.ui.INtexture3,self.ui.fileBox3],[self.ui.INtexture4,self.ui.fileBox4]]
		# create aiImages according to selected checkboxes and renamed 
		for obj in tickedAttribList:
			#rename the newly created aiImage to the ticked checkbox
			newImgName = "aiImg" + str(obj)
			aiImage_node = cmds.shadingNode("aiImage", asTexture=True)
			originalName = str(cmds.ls(aiImage_node)[0])
			cmds.rename(originalName, newImgName)

			if self.numberOfNodesCreated <= 3:
				textbox = self.textboxes[self.numberOfNodesCreated]
				textbox[0].setText(newImgName)
				textbox[1].setEnabled(True)
			else:
				print('max nodes created')
			self.numberOfNodesCreated += 1

	def updateINtexture(self,*args):
		print("Texture Created")


	#calls up the file dialog browser 
	def openFileDialog1(self, *args):

		multipleFilters = "TX Files (*.tx);;Exr Files (*.exr);;All Files (*.*)"
		filepath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2)
		#put infomation into file box 1 and link up to aiImage
		self.ui.fileBox1.setText(filepath[0])
		imgName = self.ui.INtexture1.toPlainText()
		imgAttrName = str(imgName) + ".filename"
		cmds.setAttr(imgAttrName, filepath, type = "string")
		cmds.select(imgName)

	def openFileDialog2(self, *args):

		multipleFilters = "TX Files (*.tx);;Exr Files (*.exr);;All Files (*.*)"
		filepath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2)
		#put infomation into file box 2
		self.ui.fileBox2.setText(filepath[0])
		imgName = self.ui.INtexture2.toPlainText()
		imgAttrName = str(imgName) + ".filename"
		cmds.setAttr(imgAttrName, filepath, type = "string")
		cmds.select(imgName)
		 
	def openFileDialog3(self, *args):

		multipleFilters = "TX Files (*.tx);;Exr Files (*.exr);;All Files (*.*)"
		filepath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2)
		#put infomation into file box 3
		self.ui.fileBox3.setText(filepath[0])
		imgName = self.ui.INtexture3.toPlainText()
		imgAttrName = str(imgName) + ".filename"
		cmds.setAttr(imgAttrName, filepath, type = "string")
		cmds.select(imgName)
		print(imgName)
		print(imgAttrName)
		print(filepath)

	def openFileDialog4(self, *args):

		multipleFilters = "TX Files (*.tx);;Exr Files (*.exr);;All Files (*.*)"
		filepath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2)
		#put infomation into file box 4
		self.ui.fileBox4.setText(filepath[0])
		imgName = self.ui.INtexture4.toPlainText()
		imgAttrName = str(imgName) + ".filename"
		cmds.setAttr(imgAttrName, filepath, type = "string")
		cmds.select(imgName)

		

		#this button only works when checkbox is check; works alongside it
		#it creates a colour correct node and renames it according to the chnl
		#e.g.: aiCC_baseColour or aiCC_specColour 

	def createaiCCBtn_buttonPressed(self,*args):
		for obj in tickedAttribList:
			aiColorCorrect_node=cmds.shadingNode("aiColorCorrect",asUtility=True)
			ccName = str(cmds.ls(aiColorCorrect_node)[0])
			newlynamedCC = cmds.rename(ccName,"aiCC_" + obj)
			aiCCnodeList.append(newlynamedCC)

	#select shader again for assignment to work
	def selShaderBtnPressed(self, *args):		
		activeShaderName = str(self.ui.shaderComboBox2.currentText())
		cmds.select(activeShaderName)

	#Connects aiImage to aiColorCorrect to selected shader

	def clickedconnectCCBtn(self, *args):
		activeShaderName = str(self.ui.shaderComboBox2.currentText())
		activeShader = cmds.select(activeShaderName, r = True)

		
		#if base color checkbox is ticked, connect aiImagebase color -> base colour CC node -> shader
		if self.ui.baseColCheck.isChecked():
			activeCC = aiCCnodeList[0]
			cmds.connectAttr('%s.outColor' %activeCC ,'%s.baseColor' %activeShaderName)
			# connect aiImage to aiCCNode
			for i in range(0, 4): 
				currentTextureName = self.textboxes[i][0].toPlainText()
				if "baseCol" in currentTextureName:
					textureNodeList = cmds.ls(currentTextureName)
					baseColTextureNode = textureNodeList[0]
					cmds.connectAttr('%s.outColor'%baseColTextureNode, '%s.input' %activeCC)
		
		#if spec color checkbox is ticked, connect aiImagespeccolor ->spec colour CC node -> shader
		if self.ui.specColCheck.isChecked():
			activeCC = aiCCnodeList[1]
			cmds.connectAttr('%s.outColor' %activeCC, '%s.specularColor' %activeShaderName)
			# connect aiImage to aiCCNode
			for i in range(0, 4): 
				currentTextureName = self.textboxes[i][0].toPlainText()
				if "specCol" in currentTextureName:
					textureNodeList = cmds.ls(currentTextureName)
					specColTextureNode = textureNodeList[0]
					cmds.connectAttr('%s.outColor'%specColTextureNode, '%s.input' %activeCC)

		#if spec Roughness is ticked, connect aiImageSpecRoughness -> spec roughness CC -> shader
		if self.ui.specRoughCheck.isChecked():
			activeCC = aiCCnodeList[2]
			cmds.connectAttr('%s.outColorR' %activeCC, '%s.specularRoughness' %activeShaderName)
			# connect aiImage to aiCCNode
			for i in range(0, 4): 
				currentTextureName = self.textboxes[i][0].toPlainText()
				if "specRoughness" in currentTextureName:
					textureNodeList = cmds.ls(currentTextureName)
					specRoughTextureNode = textureNodeList[0]
					cmds.connectAttr('%s.outColor'%specRoughTextureNode, '%s.input' %activeCC)
	
	
#================================end of main code====================================================
def main():
	ui= ShaderCreator()
	ui.show()
	return ui

if __name__ == '__main__':
	main()