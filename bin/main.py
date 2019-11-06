import argparse
import sys
from classes.dao import Dao
import generate_signing_sheet as gss

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
	ap.add_argument('-a', '--auth', required=False, help='Filepath to the image of the form containing all of the original student signatures')

	args = vars(ap.parse_args(sys.argv[2:]))

	className = args["name"]

	print("Creating the {} class in the database".format(className))
	dao = Dao()
	classId = dao.insertClass(className)
	if classId is None:
		print("Failed inserting class in the database. Exiting.")
		exit(1)

	gss.generate(args["filepath"], "form_{}.pdf".format(className), className)


def insertAuthForm():
	ap = argparse.ArgumentParser(description='Insert a auth form which corresponds to a class.')
	ap.add_argument('-n', '--class-name', required=True, help='Class name')
	ap.add_argument('-f', '--filepath', required=True, help='FFilepath to the image of the form containing all of the original student signatures')

	args = vars(ap.parse_args(sys.argv[2:]))

def addForm():
	ap = argparse.ArgumentParser(description='Add a new signed form to a class.')
	ap.add_argument('-n', '--class-name', required=True, help='Class name')
	ap.add_argument('-f', '--filepath', required=True, help='Filepath to the signed form image')
	ap.add_argument('-d', '--date', required=True, help='Form date')

	args = vars(ap.parse_args(sys.argv[2:]))

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

main()