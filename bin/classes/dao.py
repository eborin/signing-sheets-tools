import sqlite3
from . import form
from . import disciplineClass
from . import student
from . import signature

class Dao:
	
	def initializeDatabase(self):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' CREATE TABLE IF NOT EXISTS classes (
				id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				absence_threshold REAL NOT NULL
			) ''')

		cursor.execute(''' CREATE TABLE IF NOT EXISTS forms (
				id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
				class_id INTEGER NOT NULL,
				form_date INTEGER NOT NULL,
				form_img BLOB NOT NULL,
				FOREIGN KEY(class_id) REFERENCES classes(id)
			) ''')

		cursor.execute(''' CREATE TABLE IF NOT EXISTS students (
				ra INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				signature_path TEXT
			) ''')

		cursor.execute(''' CREATE TABLE IF NOT EXISTS signatures (
				id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
				form_id INTEGER NOT NULL,
				student_ra INTEGER NOT NULL,
				present INTEGER NOT NULL,
				veracity INTEGER,
				sig_img BLOB NOT NULL,
				FOREIGN KEY(form_id) REFERENCES forms(id),
				FOREIGN KEY(student_ra) REFERENCES students(ra)
			) ''')

		conn.commit()
		conn.close()

	def insertClass(self, className):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		try:
			cursor.execute(''' INSERT INTO classes (name, absence_threshold) VALUES (?,-1) ''', (className,))
		except sqlite3.IntegrityError:
			print("Error inserting class in the database. The class name should be unique.")
			return None
		except:
			print("Error inserting class in the database.")
			return None

		classId = cursor.lastrowid

		conn.commit()
		conn.close()

		return classId

	def findAllClasses(self):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM classes''')

		classes = []
		for result in cursor.fetchall():
			classes.append(disciplineClass.DisciplineClass(result[0], result[1], result[2]))

		conn.close()

		return classes

	def insertStudents(self, raNameTuples):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		for raName in raNameTuples:
			cursor.execute(''' INSERT INTO students (ra, name, signature_path) VALUES (?, ?, "") ''', raName)

		conn.commit()
		conn.close()

	def findAllStudents(self):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM students ''')

		students = []
		for result in cursor.fetchall():
			students.append(student.Student(result[0], result[1], result[2]))

		conn.close()

		return students

	def dropDatabase(self):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		print("Dropping database tables")
		cursor.execute(''' DROP TABLE classes ''')
		cursor.execute(''' DROP TABLE forms ''')
		cursor.execute(''' DROP TABLE students ''')
		cursor.execute(''' DROP TABLE signatures ''')

		conn.close()

	def updateStudentSignatures(self, raSignatureList):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		for raSignature in raSignatureList:
			cursor.execute(''' UPDATE students SET signature_path = ? WHERE ra = ? ''', (raSignature[1], raSignature[0]))

		conn.commit()
		conn.close()

	def updateClassAbsenceThreshold(self, name, absenceThreshold):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' UPDATE classes SET absence_threshold = ? WHERE name = ? ''', (absenceThreshold, name))

		conn.commit()
		conn.close()

	def getClassAbsenceThreshold(self, name):
		threshold = -1
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM classes WHERE name = ? ''', (name,))

		resultList = cursor.fetchall()
		if len(resultList) > 0:
			threshold = resultList[0][2]

		conn.close()

		return threshold

	def getClassByName(self, name):
		queriedClass = None
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM classes WHERE name = ? ''', (name,))

		resultList = cursor.fetchall()
		if len(resultList) > 0:
			queriedClass = disciplineClass.DisciplineClass(resultList[0][0], resultList[0][1], resultList[0][2])

		conn.close()

		return queriedClass

	def insertForm(self, classId, date, form_img_path):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		with open(form_img_path, "rb") as imageFile:
			formImg = imageFile.read()
		cursor.execute(''' INSERT INTO forms (class_id, form_date, form_img) VALUES (?, ?, ?) ''', (classId, date, formImg))

		formId = cursor.lastrowid

		conn.commit()
		conn.close()

		return formId
        
	def insertStudentsPresence(self, formId, studentsPresenceTuples):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		for raPresence in studentsPresenceTuples:
			sig_img_path = raPresence[3]
			with open(sig_img_path, "rb") as imageFile:
				sig_blob = imageFile.read()
			if raPresence[1]:
				present = 1
			else:
				present = 0
			cursor.execute(''' INSERT INTO signatures (form_id, student_ra, present, sig_img) VALUES (?, ?, ?, ?) ''',
				(formId, raPresence[0], present, sig_blob))

		conn.commit()
		conn.close()

	def getFormsFromClass(self, classId):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM forms WHERE class_id = ? ''', (classId,))

		forms = []
		for result in cursor.fetchall():
			forms.append(form.Form(result[0], result[1], result[2], result[3]))

		conn.close()

		return forms

	def getSignaturesFromForms(self, forms):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		signatures = []
		for form in forms:
			cursor.execute(''' SELECT id, form_id, student_ra, present, veracity, sig_img FROM signatures WHERE form_id = ? ''', (form.id,))

			for result in cursor.fetchall():
				sig_img = result[5]                                 
				signatures.append(signature.Signature(result[0], result[1], result[2], result[3], result[4], sig_img))

		conn.close()

		return signatures

	def getBaseSignatures(self, studentRaSignatures):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		studentRaBaseSignature = []

		for raSignatureTuple in studentRaSignatures:
			cursor.execute(''' SELECT signature_path FROM students WHERE ra = ? ''', (raSignatureTuple[0],))
			resultList = cursor.fetchall()
			if len(resultList) > 0:
				studentRaBaseSignature.append((raSignatureTuple[0], raSignatureTuple[1], resultList[0]))
		
		conn.close()

		return studentRaBaseSignature
