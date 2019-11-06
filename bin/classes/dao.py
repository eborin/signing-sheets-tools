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
				name TEXT NOT NULL UNIQUE
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
				present INTEGER NOT NULL,
				veracity REAL,
				FOREIGN KEY(form_id) REFERENCES forms(id),
				FOREIGN KEY(student_ra) REFERENCES students(ra)
			) ''')

		conn.commit()
		conn.close()

	def insertClass(self, className):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		try:
			cursor.execute(''' INSERT INTO classes (name) VALUES (?) ''', (className,))
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
			classes.append(disciplineClass.DisciplineClass(result[0], result[1]))

		conn.close()

		return classes

	def insertStudents(self, studentList):
		pass

	def dropDatabase(self):
		conn = sqlite3.connect('database/database.db')
		cursor = conn.cursor()

		cursor.execute(''' DROP TABLE classes ''')
		cursor.execute(''' DROP TABLE forms ''')
		cursor.execute(''' DROP TABLE students ''')
		cursor.execute(''' DROP TABLE signatures ''')

		conn.close()
