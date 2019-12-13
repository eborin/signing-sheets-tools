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
				ra_image TEXT NOT NULL,
				signature_image TEXT NOT NULL,
				present INTEGER NOT NULL,
				veracity INTEGER,
				checkout INTEGER,
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

	def insertForm(self, classId, date):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' INSERT INTO forms (class_id, form_date) VALUES (?, ?) ''', (classId, date))

		formId = cursor.lastrowid

		conn.commit()
		conn.close()

		return formId

	def insertStudentsPresence(self, formId, studentsPresenceTuples):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		for raPresence in studentsPresenceTuples:
			if raPresence[1]:
				present = 1
			else:
				present = 0
			cursor.execute(''' INSERT INTO signatures (form_id, student_ra, ra_image, signature_image, present, 
			veracity) VALUES (?, ?, ?, ?, ?, ?) ''', (formId, raPresence[0], raPresence[3], raPresence[4], present,
													  raPresence[2]))

		conn.commit()
		conn.close()

	def getFormsFromClass(self, classId):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' SELECT * FROM forms WHERE class_id = ? ''', (classId,))

		forms = []
		for result in cursor.fetchall():
			forms.append(form.Form(result[0], result[1], result[2]))

		conn.close()

		return forms

	def getSignaturesFromForms(self, forms):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		signatures = []
		for form in forms:
			cursor.execute(''' SELECT id, form_id, student_ra, present, veracity FROM signatures WHERE form_id = ? ''', (form.id,))

			for result in cursor.fetchall():
				signatures.append(signature.Signature(result[0], result[1], result[2], result[3], result[4]))

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
				studentRaBaseSignature.append((raSignatureTuple[0], raSignatureTuple[1], raSignatureTuple[2], resultList[0]))

		conn.close()

		return studentRaBaseSignature

	def getCheckoutDictionary(self, className):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		checkoutDictionary = {}

		cursor.execute(''' SELECT students.name, student_ra, form_date, ra_image, signature_image, present, veracity, 
		checkout, signatures.id FROM (((SELECT forms.id, forms.form_date FROM forms JOIN (SELECT * FROM classes WHERE name=?)) AS F 
		 INNER JOIN signatures on F.id = signatures.form_id) INNER JOIN students on student_ra = ra) ORDER BY student_ra; ''', (className,))

		resultList = cursor.fetchall()
		for result in resultList:
			key = (result[1], result[0])
			if key not in checkoutDictionary:
				checkoutDictionary[key] = []
			checkoutDictionary[key].append({"date": result[2], "raImagePath": result[3], "signatureImagePath": result[4],
										   "present": result[5], "similar": result[6], "checkout": result[7], "signatureId": result[8]})

		conn.close()

		return checkoutDictionary

	def switchPresence(self, signatureId):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		presence = -1
		newPresence = -1

		cursor.execute(''' SELECT present FROM signatures WHERE id = ? ''', (signatureId,))

		resultList = cursor.fetchall()
		if len(resultList) > 0:
			presence = resultList[0][0]

		print("Old presence: {}".format(presence))

		if presence == 0:
			newPresence = 1
		elif presence == 1:
			newPresence = 0

		cursor.execute(''' UPDATE signatures SET present = ? WHERE id = ? ''', (newPresence, signatureId))

		conn.commit()
		conn.close()
		return newPresence

	def switchSimilarity(self, signatureId):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		similarity = -1
		newSimilarity = -1

		cursor.execute(''' SELECT veracity FROM signatures WHERE id = ? ''', (signatureId,))

		resultList = cursor.fetchall()
		if len(resultList) > 0:
			similarity = resultList[0][0]

		if similarity == 0:
			newSimilarity = 1
		elif similarity == 1:
			newSimilarity = 0

		cursor.execute(''' UPDATE signatures SET veracity = ? WHERE id = ? ''', (newSimilarity, signatureId))

		conn.commit()
		conn.close()
		return newSimilarity

	def switchCheckout(self, signatureId):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()
		checkout = None

		cursor.execute(''' SELECT checkout FROM signatures WHERE id = ? ''', (signatureId,))

		resultList = cursor.fetchall()
		if len(resultList) > 0:
			checkout = resultList[0][0]

		if checkout is None or checkout >= 3:
			newCheckout = 0
		else:
			newCheckout = checkout+1

		cursor.execute(''' UPDATE signatures SET checkout = ? WHERE id = ? ''', (newCheckout, signatureId))

		conn.commit()
		conn.close()
		return newCheckout

	def generateCheckout(self, dic):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		for signatureId, checkout in dic.items():
			cursor.execute(''' UPDATE signatures SET checkout = ? WHERE id = ? ''', (checkout, signatureId))

		conn.commit()
		conn.close()
