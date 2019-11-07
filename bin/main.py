import argparse
import sys
import generate_signing_sheet as gss
import extract_table_cells as etc
import pytesseract
import cv2
from os import path
from classes import student
from PIL import Image
from classes.dao import Dao

def main():
	commands = {'create-class': createClass, 'insert-auth-form': insertAuthForm, 'add-form': addForm, 'statistics': statistics, 'classes': printClasses,
	'clear': clearDatabase}

	ap = argparse.ArgumentParser()

	ap.add_argument('command', help='Subcommand to run')
	args = ap.parse_args(sys.argv[1:2])
	if not args.command in list(commands.keys()):
		print('Unrecognized command')
		ap.print_help()
		exit(1)

	dao = Dao()
	dao.initializeDatabase()

	commands[args.command]()

def createClass():
	ap = argparse.ArgumentParser(description='Create a new class and store it in the database.')
	ap.add_argument('-n', '--name', required=True, help='Class name')
	ap.add_argument('-f', '--filepath', required=True, help='Filepath to the CSV containing the student names and RAs')

	args = vars(ap.parse_args(sys.argv[2:]))

	className = args["name"]

	print("Creating the {} class in the database".format(className))
	dao = Dao()
	classId = dao.insertClass(className)
	if classId is None:
		print("Failed inserting class in the database. Exiting.")
		exit(1)

	raNameTuples = gss.generate(args["filepath"], "form_{}.pdf".format(className), className)
	raNameTuples = [(t[0], t[1][:-1]) for t in raNameTuples]
	
	dao.insertStudents(raNameTuples)

def insertAuthForm():
	ap = argparse.ArgumentParser(description='Insert a auth form which corresponds to a class.')
	ap.add_argument('-n', '--class_name', required=True, help='Class name')
	ap.add_argument('-f', '--filepath', required=True, help='Filepath to the image of the form containing all of the original student signatures')

	args = vars(ap.parse_args(sys.argv[2:]))

	authFormFilepath = args["filepath"]
	className = args["class_name"]

	dao = Dao()

	queriedClass = dao.getClassByName(className)
	if queriedClass is None:
		print("No class with that name exists. Exiting.")
		exit(1)

	etc.extract(authFormFilepath)

	studentRaSignatures = []

	cellPrefix = "cells/{}-cell".format(authFormFilepath[:-4])
	row = 2
	raSignatureColumns = [(1,3),(4,6)]
	flag = True
	while flag:
		for columnIndexes in raSignatureColumns:
			raFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[0]).zfill(2))
			signatureFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[1]).zfill(2))
			if path.exists(raFilePath):
				if path.exists(signatureFilePath):
					ra = pytesseract.image_to_string(Image.open(raFilePath), lang="por")
					studentRaSignatures.append((ra, signatureFilePath))
			else:
				flag = False
		row = row + 1		

	smallestRate = 1
	for raSignature in studentRaSignatures:
		rate = getImageBlackPixelRating(raSignature[1])
		if smallestRate > rate:
			smallestRate = rate
	print("Smallest black pixels rate of this class signature: {}".format(smallestRate))

	dao.updateStudentSignatures(studentRaSignatures)
	dao.updateClassAbsenceThreshold(args["class_name"], smallestRate)

def addForm():
	ap = argparse.ArgumentParser(description='Add a new signed form to a class.')
	ap.add_argument('-n', '--class_name', required=True, help='Class name')
	ap.add_argument('-f', '--filepath', required=True, help='Filepath to the signed form image')
	ap.add_argument('-d', '--date', required=True, help='Form date')

	args = vars(ap.parse_args(sys.argv[2:]))

	formFilepath = args["filepath"]
	className = args["class_name"]
	formDate = args["date"]

	dao = Dao()

	queriedClass = dao.getClassByName(className)
	if queriedClass is None:
		print("No class with that name exists. Exiting.")
		exit(1)

	formId = dao.insertForm(queriedClass.id, formDate)

	etc.extract(formFilepath)

	studentRaSignatures = []

	cellPrefix = "cells/{}-cell".format(formFilepath[:-4])
	row = 2
	raSignatureColumns = [(1,3),(4,6)]
	flag = True
	while flag:
		for columnIndexes in raSignatureColumns:
			raFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[0]).zfill(2))
			signatureFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[1]).zfill(2))
			if path.exists(raFilePath):
				if path.exists(signatureFilePath):
					ra = pytesseract.image_to_string(Image.open(raFilePath), lang="por")
					studentRaSignatures.append((ra, signatureFilePath))
			else:
				flag = False
		row = row + 1

	raPresenceTuples = []

	classAbsenceThreshold = dao.getClassAbsenceThreshold(className)
	if classAbsenceThreshold == -1:
		classAbsenceThreshold = 0.3
	else:
		classAbsenceThreshold = classAbsenceThreshold*0.9
	for raSignature in studentRaSignatures:
		studentPresent = False
		rate = getImageBlackPixelRating(raSignature[1], raSignature[0])
		if rate >= classAbsenceThreshold:
			studentPresent = True
		raPresenceTuples.append((raSignature[0], studentPresent))

	dao.insertStudentsPresence(formId, raPresenceTuples)

def statistics():
	ap = argparse.ArgumentParser(description='Calculates the current presence statistics of a class.')
	ap.add_argument('-n', '--class-name', required=True, help='Class name')

	args = vars(ap.parse_args(sys.argv[2:]))

def printClasses():
	ap = argparse.ArgumentParser(description='Shows all of the stored classes.')
	dao = Dao()

	classes = dao.findAllClasses()
	for disciplineClass in classes:
		print(vars(disciplineClass))

def clearDatabase():
	ap = argparse.ArgumentParser(description='Drops the whole database.')
	dao = Dao()

	dao.dropDatabase()

def getImageBlackPixelRating(imagePath, ra=None):
	signatureImage = cv2.imread(imagePath)
	graySignature = cv2.cvtColor(signatureImage, cv2.COLOR_BGR2GRAY)
	thresholdedSignature = cv2.adaptiveThreshold(graySignature,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,3,5)
	rate = 1 - cv2.countNonZero(thresholdedSignature)/(thresholdedSignature.shape[0]*thresholdedSignature.shape[1])
	#print("RA: {}, Rate: {}".format(ra, rate))
	#cv2.imwrite("test/{}.png".format(ra), thresholdedSignature)
	return rate


main()