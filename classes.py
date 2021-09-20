import datetime
from random import randint

# For web framework
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy

# For database
from sqlalchemy.orm import relationship, noload
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, Date, Time, Text

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisisthesecretkey'

#Important!!!!! Change the URI to the URL of the database on your device, then run this file
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/User/Desktop/Timetable-App/database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Zhang Jikun/Projects/Timetable-App/database.db'

db = SQLAlchemy(app)

class Lesson(db.Model):
	__tablename__ = "Lesson"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Title = Column(String(100), nullable=False)
	Day = Column(Integer, nullable=False)
	StartTime = Column(Time, nullable=False)
	EndTime = Column(Time, nullable=False)
	Level = Column(Integer)

	TeacherId = Column(Integer, ForeignKey('Teacher.id'))

	def __init__(self, title, day, starttime, endtime, teacher):
		self.Title = title
		self.Day = day
		self.StartTime = starttime
		self.EndTime = endtime
		self.TeacherId = teacher.id
		self.Level = None
		teacher.Lessons.append(self)
		db.session.add(self)

	def check_clash(self, date):
		papers = Paper.query.options(noload("Invigilators")).all()
		for paper in papers:
			if (paper.Level == self.Level or self.Level not in [1, 2, 3, 4, 5, 6]) and paper.Date == date:
				return False
		return True

	def set_level(self, level):
		self.Level = level

class Excusal(db.Model):
	__tablename__ = "Excusal"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Title = Column(String(100))
	Description = Column(Text)
	StartTime = Column(Time, nullable=False)
	EndTime = Column(Time, nullable=False)
	Date = Column(Date, nullable=False)

	TeacherId = Column(Integer, ForeignKey('Teacher.id'))

	def __init__(self, starttime, endtime, date, title, description, teacher):
		self.StartTime = starttime
		self.Endtime = EndTime
		self.Date = date
		self.Title = title
		self.Description = description
		self.TeacherId = teacher.id
		teacher.Excusals.append(self)
		db.session.add(self)

class Teacher(db.Model):
	__tablename__ = "Teacher"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Name = Column(String(100), nullable=False)
	Department = Column(String(50), nullable=False)
	Load = Column(Float, nullable=False)

	Excusals = relationship("Excusal")
	Lessons = relationship("Lesson")
	Pool = relationship('Pool')
	Fixed_Invigilations = relationship("Fixed_Invigilation")
	Invigilations = relationship('Invigilation')

	def __init__(self, name, department, load):
		self.Name = name
		self.Department = department
		self.Load = load
		db.session.add(self)

	# For pool generation
	def check_availability(self, date, starttime, endtime):
		excusals = Excusal.query.all()
		for excusal in self.Excusals:
			if endtime > excusal.StartTime and starttime < excusal.EndTime and excusal.Date == date:
				return False
		for lesson in self.Lessons:
			if endtime > lesson.StartTime and starttime < lesson.EndTime and lesson.Day == date.day and lesson.check_clash(date):
				return False
		for invigilation in self.Fixed_Invigilations:
			paper = Paper.query.options(noload("Invigilators")).get(invigilation.PaperId)
			if endtime > paper.StartTime and starttime < paper.EndTime and paper.Date == date:
				return False
		return True

	def get_day_time_without_invigilations(self, date):
		total_time = datetime.timedelta()
		for lesson in self.Lessons:
			if lesson.Day == date.day and lesson.check_clash(date):
				total_time +=  datetime.datetime(2000, 1, 1, lesson.EndTime.hour, lesson.EndTime.minute, lesson.EndTime.second) - datetime.datetime(2000, 1, 1, lesson.StartTime.hour, lesson.StartTime.minute, lesson.StartTime.second)
		return total_time.seconds/60

	def get_day_time(self, date, version):
		total_time = datetime.timedelta()
		invigilations = []
		for invigilation in version.Invigilations:
			if invigilation.TeacherId == self.id:
				invigilations.append(invigilation)
		for invigilation in invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			if paper.Date == date:
				if self.Department == paper.Department:
					total_time += (datetime.datetime(2000, 1, 1, paper.EndTime.hour, paper.EndTime.minute, paper.EndTime.second) - datetime.datetime(2000, 1, 1, paper.StartTime.hour, paper.StartTime.minute, paper.StartTime.second))
				else:
					total_time += datetime.datetime(2000, 1, 1, paper.EndTime.hour, paper.EndTime.minute, paper.EndTime.second) - datetime.datetime(2000, 1, 1, paper.StartTime.hour, paper.StartTime.minute, paper.StartTime.second)
		for invigilation in self.Fixed_Invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			if paper.Date == date:
				if self.Department == paper.Department:
					total_time += (datetime.datetime(2000, 1, 1, paper.EndTime.hour, paper.EndTime.minute, paper.EndTime.second) - datetime.datetime(2000, 1, 1, paper.StartTime.hour, paper.StartTime.minute, paper.StartTime.second))
				else:
					total_time += datetime.datetime(2000, 1, 1, paper.EndTime.hour, paper.EndTime.minute, paper.EndTime.second) - datetime.datetime(2000, 1, 1, paper.StartTime.hour, paper.StartTime.minute, paper.StartTime.second)
		for lesson in self.Lessons:
			if lesson.Day == date.day and lesson.check_clash(date):
				total_time +=  datetime.datetime(2000, 1, 1, lesson.EndTime.hour, lesson.EndTime.minute, lesson.EndTime.second) - datetime.datetime(2000, 1, 1, lesson.StartTime.hour, lesson.StartTime.minute, lesson.StartTime.second)
		return total_time.seconds/60

	def get_paper_time(self, version):
		total_min = 0
		invigilations = []
		for invigilation in version.Invigilations:
			if invigilation.TeacherId == self.id:
				invigilations.append(invigilation)
		for invigilation in invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			total_min += (paper.EndTime.hour - paper.StartTime.hour) * 60 + paper.EndTime.minute - paper.StartTime.minute
		for invigilation in self.Fixed_Invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			total_min += (paper.EndTime.hour - paper.StartTime.hour) * 60 + paper.EndTime.minute - paper.StartTime.minute
		return total_min

	def get_score(self, optimal_paper_time, day_time_threshold, version):
		day_time_score = 0
		dates = []
		invigilations = []
		for invigilation in version.Invigilations:
			if invigilation.TeacherId == self.id:
				invigilations.append(invigilation)
		for invigilation in invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			if paper.Date not in dates:
				dates.append(paper.Date)
		for invigilation in self.Fixed_Invigilations:
			paper = Paper.query.options(noload("Invigilators")).options(noload('Pool')).get(invigilation.PaperId)
			if paper.Date not in dates:
				dates.append(paper.Date)
		for date in dates:
			day_time_score += max(abs(self.get_day_time(date, version) - day_time_threshold * self.Load), 0)
		return abs(self.get_paper_time(version) - optimal_paper_time * self.Load) ** 3 + day_time_score

class Paper(db.Model):
	__tablename__ = "Paper"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Name = Column(String(100), nullable=False)
	Subject = Column(String(100), nullable=False)
	Level = Column(Integer, nullable=False)
	Department = Column(String(50), nullable=False)
	Count = Column(Integer, server_default='0')
	Date = Column(Date, nullable=False)
	StartTime = Column(Time, nullable=False)
	EndTime = Column(Time, nullable=False)

	Pool = relationship('Pool')
	Invigilators = relationship('Invigilation')
	Fixed_Invigilators = relationship('Fixed_Invigilation')

	def __init__(self, subject, name, department, count, date, starttime, endtime, level):
		self.Subject = subject
		self.Name = name
		self.Department = department
		self.Count = count
		self.Date = date
		self.StartTime = starttime
		self.EndTime = endtime
		self.Level = level
		db.session.add(self)

class Version(db.Model):
	__tablename__ = "Version"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Score = Column(Float)
	Generation = Column(Integer, nullable=False)

	Invigilations = relationship('Invigilation', lazy='select')

	def __init__(self, generation):
		self.Generation = generation
		self.Score = 99999999999999
		db.session.add(self)

	def set_score(self, optimal_paper_time, day_time_threshold):
		teachers = Teacher.query.options(noload('Invigilations')).options(noload('Pool')).all()
		score = 0
		for teacher in teachers:
			score += teacher.get_score(optimal_paper_time, day_time_threshold, self)
		self.Score = score

	def random_assignment(self):
		papers = Paper.query.options(noload('Invigilators')).all()
		for paper in papers:
			count = 0
			pool = paper.Pool.copy()
			while count < paper.Count - len(paper.Fixed_Invigilators):
				index = randint(0, len(pool)-1)
				teacher = Teacher.query.options(noload('Invigilations')).get(pool[index].TeacherId)
				Invigilation(teacher, paper, self)
				pool.pop(index)
				count += 1

	def generate_with_dictionary(self, paper_to_teachers):
		papers = Paper.query.options(noload('Invigilators')).all()
		for paper in papers:
			teachers = paper_to_teachers[paper.id]
			for teacher in teachers:
				Invigilation(teacher, paper, self)

class Pool(db.Model):
	__tablename__ = "Pool"
	id =  Column(Integer, primary_key=True, autoincrement=True)

	TeacherId = Column(Integer, ForeignKey('Teacher.id'))
	PaperId = Column(Integer, ForeignKey('Paper.id'))

	def __init__(self, teacher, paper):
		self.TeacherId = teacher.id
		self.PaperId = paper.id
		paper.Pool.append(self)
		teacher.Pool.append(self)
		db.session.add(self)

class Fixed_Invigilation(db.Model):
	__tablename__ = "Fixed_Invigilation"
	id = Column(Integer, primary_key=True, autoincrement=True)
	chief_invigilator = Column(Boolean, server_default="0")
	coordinator = Column(Boolean, server_default="0")

	TeacherId = Column(Integer, ForeignKey('Teacher.id'))
	PaperId = Column(Integer, ForeignKey('Paper.id'))

	def __init__(self, teacher, paper, chief_invigilator = False, coordinator = False):
		self.chief_invigilator = chief_invigilator
		self.coordinator = coordinator
		self.TeacherId = teacher.id
		self.PaperId = paper.id
		teacher.Fixed_Invigilations.append(self)
		paper.Fixed_Invigilators.append(self)
		db.session.add(self)

class Invigilation(db.Model):
	__tablename__ = "Invigilation"
	id = Column(Integer, primary_key=True, autoincrement=True)
	Reserve = Column(Boolean, server_default="0")

	TeacherId = Column(Integer, ForeignKey('Teacher.id'))
	PaperId = Column(Integer, ForeignKey('Paper.id'))
	VersionId = Column(Integer, ForeignKey('Version.id'))

	def __init__(self, teacher, paper, version, reserve = False):
		self.TeacherId = teacher.id
		self.PaperId = paper.id
		self.VersionId = version.id
		self.Reserve = reserve
		teacher.Invigilations.append(self)
		paper.Invigilators.append(self)
		version.Invigilations.append(self)
		db.session.add(self)

def create_db():
	db.create_all()
	db.session.commit()
