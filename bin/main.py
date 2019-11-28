import argparse
import sys
import generate_signing_sheet as gss
import extract_table_cells as etc
import matplotlib.pyplot as plt
import numpy as np
import validate_signatures as vs
import pytesseract
import cv2
from os import path
from classes import student
from PIL import Image
from classes.dao import Dao

STUDENT_RA = 0
CROPPED_SIGNATURE_PATH = 1
BASE_SIGNATURE_PATH = 2

import pdb

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
					#ra = pytesseract.image_to_string(Image.open(raFilePath), lang="por", config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789')
					#studentRaSignatures.append((ra, signatureFilePath))
					raImage = Image.open(raFilePath)
					width, height = raImage.size
					crop_img = raImage.crop((width/50, height/3, 49*width/50, 2*height/3))
					ocrResult = pytesseract.image_to_string(crop_img, lang="eng", config='digits')
					numberList = [int(s) for s in ocrResult.split() if s.isdigit()]
					ra = next(iter(numberList), None)
					print("OCR result: {}".format(ra))
					if ra is not None:
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

	formId = dao.insertForm(queriedClass.id, formDate, formFilepath)

	etc.extract(formFilepath)

	studentRaSignatures = []

	cellPrefix = "cells/{}-cell".format(formFilepath[:-4])
	row = 1
	raSignatureColumns = [(1,3),(4,6)]
	flag = True
	while flag:
		for columnIndexes in raSignatureColumns:
			raFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[0]).zfill(2))
			signatureFilePath = "{}-{}-{}.png".format(cellPrefix, str(row).zfill(2), str(columnIndexes[1]).zfill(2))
			#print("Ra File Path: {}".format(raFilePath))
			if path.exists(raFilePath):
				if path.exists(signatureFilePath):
					raImage = Image.open(raFilePath)
					width, height = raImage.size
					crop_img = raImage.crop((width/50, height/3, 49*width/50, 2*height/3))
					#raImage.show()
					#crop_img.show()
					crop_img = raImage
					ocrResult = pytesseract.image_to_string(crop_img, lang="eng", config='digits')
					numberList = [int(s) for s in ocrResult.split() if s.isdigit()]
					ra = next(iter(numberList), None)
					print("OCR result2: {}".format(ra))
					if ra is not None:
						studentRaSignatures.append((ra, signatureFilePath))
			elif columnIndexes == (1,3):
				flag = False
		row = row + 1

	raPresenceTuples = []
	studentRaSignatures = dao.getBaseSignatures(studentRaSignatures)

	classAbsenceThreshold = dao.getClassAbsenceThreshold(className)
	if classAbsenceThreshold == -1:
		classAbsenceThreshold = 0.01
	else:
		classAbsenceThreshold = classAbsenceThreshold*0.6
	for raSignature in studentRaSignatures:
		studentPresent = False
		rate = getImageBlackPixelRating(raSignature[CROPPED_SIGNATURE_PATH], raSignature[STUDENT_RA], formDate)
		if rate >= classAbsenceThreshold:
			studentPresent = True
		try:
			signatureVeracity = vs.is_signature_equal(raSignature[BASE_SIGNATURE_PATH], raSignature[CROPPED_SIGNATURE_PATH])
		except:
			signatureVeracity = -1
		raPresenceTuples.append((raSignature[STUDENT_RA], studentPresent, signatureVeracity, raSignature[CROPPED_SIGNATURE_PATH]))

	# TODO: Handle exceptions: try: except sqlite3.Error as error ...                
	dao.insertStudentsPresence(formId, raPresenceTuples)

def statistics():
	ap = argparse.ArgumentParser(description='Calculates the current presence statistics of a class.')
	ap.add_argument('-n', '--class_name', required=True, help='Class name')

	args = vars(ap.parse_args(sys.argv[2:]))

	className = args["class_name"]

	dao = Dao()
	queriedClass = dao.getClassByName(className)
	if queriedClass is None:
		print("No class with that name exists. Exiting.")
		exit(1)

	formsFromClass = dao.getFormsFromClass(queriedClass.id)
	signatures = dao.getSignaturesFromForms(formsFromClass)
	studentPresenceDict = {}
	studentSinaturesDict = {}
	for signature in signatures:
		studentPresenceDict[signature.studentRa] = studentPresenceDict.get(signature.studentRa, 0) + signature.present
		studentSinaturesDict[signature.studentRa] = studentSinaturesDict.get(signature.studentRa, []) + [signature]
	formDict = {}
	formId2Date = {}
	validDates = set()
	for form in formsFromClass:
		formDict[form.date] = formDict.get(form.date, []) + [form]
		validDates.add(form.date)                
		formId2Date[form.id] = form.date

	generate_signatures_html(studentSinaturesDict, validDates, formId2Date)
	generate_forms_html(formsFromClass)
                
	numberOfClasses = len(formDict.keys())

	generalFrequence = {}
	for key, value in studentPresenceDict.items():
		generalFrequence[key] = value/numberOfClasses

	for key, value in generalFrequence.items():
		print("{} frequence: {}".format(key, value))

	histogram = {}
	for i in studentPresenceDict.values():
		histogram[i] = histogram.get(i,0) + 1
                        
	x = list(histogram.keys())
	y = histogram.values()
	plt.bar(x, y, color='#0504aa')
	plt.xticks(np.arange(min(x), max(x)+1, 1.0))
	plt.yticks(np.arange(min(y), max(y)+1, 2.0))
	plt.xlabel('Número de presença em aulas')
	plt.ylabel('Frequência')
	plt.title('Frequência de alunos por número de presença aulas')
	plt.grid(axis='y', alpha=0.25)
	plt.show()

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

def getImageBlackPixelRating(imagePath, ra=None, formDate="01/01/2019"):
	signatureImage = cv2.imread(imagePath)
	graySignature = cv2.cvtColor(signatureImage, cv2.COLOR_BGR2GRAY)
	thresholdedSignature = cv2.adaptiveThreshold(graySignature,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,7,5)
	denoisedSignature = cv2.medianBlur(thresholdedSignature, 3)
	rate = 1 - cv2.countNonZero(denoisedSignature)/(denoisedSignature.shape[0]*denoisedSignature.shape[1])
	#print("RA: {}, Rate: {}".format(ra, rate))
	#cv2.imwrite("./testDir/{}_{}.png".format(formDate.replace("/", "-"), ra), denoisedSignature)
	return rate

def generate_forms_html(formsFromClass):
	for form in formsFromClass:
		print("Form: ",form.id)
		with open("form-{}.png".format(form.id), 'wb') as fh:
			fh.write(form.form_img)	                       
                
def generate_signatures_html(studentsSignatures, validDates, formId2Date):
	sf = open("signatures.html","w") 
	sf.write("<html>\n")
	sf.write("<body>\n")
	sf.write("  <h1>Signatures</h1>\n")
	for ra, siglist in studentsSignatures.items():
		basename="ra{}".format(ra)
		sf.write("  <h2>RA: {}</h2>\n".format(ra))
		sf.write("  <table border=\"1\">\n")
		for date in validDates:
			sf.write("    <tr>\n")
			sf.write("      <td>{}</td>\n".format(date))
			found = False
			for sig in siglist:
				formDate = formId2Date[sig.formId]
				if formDate == date :
					found = True
					date_str = formDate.replace('/','_')
					fname = basename + "-{}.png".format(date_str)                        
					with open(fname, 'wb') as fh:
						fh.write(sig.sig_img)
					if sig.present == 1:	                
						sf.write("      <td><img height=\"40\" src=\"{}\"/> | OK</td>\n".format(fname))
					else:
						sf.write("      <td><img height=\"40\" src=\"{}\"/> | <font color=\"red\">Faltou!</font></td>\n".format(fname))
			if not found:
				sf.write("      <td><font color=\"red\">Signature not found!</font></td>\n")
			sf.write("    </tr>\n")
		sf.write("  </table>\n")
	sf.write("</body>\n")
	sf.write("</html>\n")
	sf.close()

main()
