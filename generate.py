import datetime
from classes import db, Teacher, Paper, Invigilation, Version, Pool, Fixed_Invigilation
from random import randint, random, shuffle
from sqlalchemy.orm import noload, lazyload

day_time_threshold = 210
pop_size = 300
mutation_rate = 0.05
max_gen = 200
optimal_paper_time = 0

def get_optimal_paper_time():
	global optimal_paper_time
	optimal_paper_time = 0
	total_dur = datetime.timedelta(0,0)
	papers = Paper.query.options(noload("Invigilators")).all()
	teachers = Teacher.query.options(noload("Invigilations")).all()
	for paper in sorted(papers, key=lambda paper:paper.Count):
		starttime = paper.StartTime
		endtime = paper.EndTime
		total_dur += (datetime.datetime(2000, 1, 1, endtime.hour, endtime.minute, endtime.second) - datetime.datetime(2000, 1, 1, starttime.hour, starttime.minute, starttime.second)) * paper.Count
	total_load = 0
	for teacher in teachers:
		total_load += teacher.Load
	optimal_paper_time = (total_dur.days*24*60 + total_dur.seconds/60)/total_load

def set_fixed_invigilations():
	for paper in Paper.query.options(noload("Invigilators")).all():
		lst = []
		for teacher in Teacher.query.options(noload("Invigilations")).all():
			if teacher.check_availability(paper.Date, paper.StartTime, paper.EndTime):
				current_mins = 0
				delete = False
				for invigilation in teacher.Fixed_Invigilations:
					if invigilation.PaperId == paper.id:
						delete = True
						break
					temp = Paper.query.get(invigilation.PaperId)
					current_mins = (temp.EndTime.hour - temp.StartTime.hour) * 60 + (temp.EndTime.minute - temp.StartTime.minute)
				if delete:
					break
				current_mins += (paper.EndTime.hour - paper.StartTime.hour) * 60 + (paper.EndTime.minute - paper.StartTime.minute)
				for lesson in teacher.Lessons:
					if lesson.Level == paper.Level and paper.Subject in lesson.Title and current_mins < optimal_paper_time:
						lst.append(teacher)
						break
		while len(lst) > 0 and paper.Count > 0:
			index = randint(0, len(lst) - 1)
			Fixed_Invigilation(lst[index], paper)
			lst.remove(lst[index])

def generate_level_pools():
	pools = Pool.query.all()
	for pool in pools:
		db.session.delete(pool)
	papers = Paper.query.options(noload("Invigilators")).all()
	teachers = Teacher.query.options(noload("Invigilations")).all()
	matrix = {}
	for paper in papers:
		lst = []
		for teacher in teachers:
			if teacher.check_availability(paper.Date, paper.StartTime, paper.EndTime):
				for lesson in teacher.Lessons:
					if lesson.Level == paper.Level:
						lst.append(teacher)
						break
		matrix[paper] = lst
	clashes = []
	for i in range(len(papers)):
		for j in range(i+1, len(papers)):
			if papers[i].EndTime > papers[j].StartTime and papers[i].StartTime < papers[j].EndTime and papers[i].Date == papers[j].Date:
				lst = []
				index = 0
				while index < len(matrix[papers[i]]):
					teacher = matrix[papers[i]][index]
					if teacher in matrix[papers[j]]:
						if teacher.Department == papers[i].Department and teacher.Department != papers[j].Department:
							matrix[papers[j]].remove(teacher)
							index += 1
						elif teacher.Department == papers[j].Department and teacher.Department != papers[i].Department:
							matrix[papers[i]].remove(teacher)
						else:
							matrix[papers[i]].remove(teacher)
							matrix[papers[j]].remove(teacher)
							teacher.score = teacher.get_day_time_without_invigilations(papers[i].Date)
							lst.append(teacher)
					else:
						index += 1
				lst.sort(key=lambda teacher:teacher.score)
				clashes.append([papers[i], papers[j], lst])
	for clash in clashes:
		first_duration = datetime.datetime(2000, 1, 1, clash[0].EndTime.hour, clash[0].EndTime.minute, clash[0].EndTime.second) - datetime.datetime(2000, 1, 1, clash[0].StartTime.hour, clash[0].StartTime.minute, clash[0].StartTime.second)
		second_duration = datetime.datetime(2000, 1, 1, clash[1].EndTime.hour, clash[1].EndTime.minute, clash[1].EndTime.second) - datetime.datetime(2000, 1, 1, clash[1].StartTime.hour, clash[1].StartTime.minute, clash[1].StartTime.second)
		while len(clash[2]) > 0:
			if len(matrix[clash[0]]) == 0:
				matrix[clash[0]].append(clash[2][0])
				clash[2].pop(0)
			elif len(matrix[clash[1]]) == 0:
				matrix[clash[1]].append(clash[2][0])
				clash[2].pop(0)
			elif first_duration.seconds / len(matrix[clash[0]]) >= second_duration.seconds / len(matrix[clash[1]]):
				matrix[clash[0]].append(clash[2][0])
				clash[2].pop(0)
			else:
				matrix[clash[1]].append(clash[2][0])
				clash[2].pop(0)
	for paper, lst in matrix.items():
		for teacher in lst:
			Pool(teacher, paper)
	db.session.commit()

def generate_department_pools():
	pools = Pool.query.all()
	for pool in pools:
		db.session.delete(pool)
	papers = Paper.query.options(noload("Invigilators")).all()
	teachers = Teacher.query.options(noload("Invigilations")).all()
	for paper in papers:
		lst = []
		for teacher in teachers:
			if teacher.Department == paper.Department and teacher.check_availability(paper.Date, paper.StartTime, paper.EndTime):
				lst.append(teacher)
		clashes = []
		for paper_clash in papers:
			if paper != paper_clash and paper_clash.EndTime > paper.StartTime and paper_clash.StartTime < paper.EndTime and paper_clash.Date == paper.Date:
				clashes.append(paper_clash)
		for teacher in lst:
			clashing = False
			for clash in clashes:
				for pool_ob in clash.Pool:
					if teacher.id == pool_ob.TeacherId:
						clashing = True
						break
				if clashing:
					break
			if clashing == False:
				Pool(teacher, paper)
	db.session.commit()

def generate_largest_pools():
	pools = Pool.query.all()
	for pool in pools:
		db.session.delete(pool)
	papers = Paper.query.options(noload("Invigilators")).all()
	teachers = Teacher.query.options(noload("Invigilations")).all()
	matrix = {}
	for paper in papers:
		lst = []
		for teacher in teachers:
			if teacher.check_availability(paper.Date, paper.StartTime, paper.EndTime):
				lst.append(teacher)
		matrix[paper] = lst
	clashes = []
	for i in range(len(papers)):
		for j in range(i+1, len(papers)):
			if papers[i].EndTime > papers[j].StartTime and papers[i].StartTime < papers[j].EndTime and papers[i].Date == papers[j].Date:
				lst = []
				index = 0
				while index < len(matrix[papers[i]]):
					teacher = matrix[papers[i]][index]
					if teacher in matrix[papers[j]]:
						if teacher.Department == papers[i].Department and teacher.Department != papers[j].Department:
							matrix[papers[j]].remove(teacher)
							index += 1
						elif teacher.Department == papers[j].Department and teacher.Department != papers[i].Department:
							matrix[papers[i]].remove(teacher)
						else:
							matrix[papers[i]].remove(teacher)
							matrix[papers[j]].remove(teacher)
							lst.append(teacher)
					else:
						index += 1
				clashes.append([papers[i], papers[j], lst])

	for clash in clashes:
		first_duration = datetime.datetime(2000, 1, 1, clash[0].EndTime.hour, clash[0].EndTime.minute, clash[0].EndTime.second) - datetime.datetime(2000, 1, 1, clash[0].StartTime.hour, clash[0].StartTime.minute, clash[0].StartTime.second)
		second_duration = datetime.datetime(2000, 1, 1, clash[1].EndTime.hour, clash[1].EndTime.minute, clash[1].EndTime.second) - datetime.datetime(2000, 1, 1, clash[1].StartTime.hour, clash[1].StartTime.minute, clash[1].StartTime.second)
		while len(clash[2]) > 0:
			if len(matrix[clash[0]]) == 0:
				matrix[clash[0]].append(clash[2][0])
				clash[2].pop(0)
			elif len(matrix[clash[1]]) == 0:
				matrix[clash[1]].append(clash[2][0])
				clash[2].pop(0)
			elif first_duration.seconds / len(matrix[clash[0]]) >= second_duration.seconds / len(matrix[clash[1]]):
				matrix[clash[0]].append(clash[2][0])
				clash[2].pop(0)
			else:
				matrix[clash[1]].append(clash[2][0])
				clash[2].pop(0)
	for paper, lst in matrix.items():
		for teacher in lst:
			Pool(teacher, paper)
	db.session.commit()

def random_generate_version(num):
	for i in range(num):
		version = Version(0)
		version.random_assignment()
		version.set_score(optimal_paper_time, day_time_threshold)
	db.session.commit()

def population_minimum(generation):
	versions = Version.query.filter(Version.Generation == generation).options(lazyload("Invigilations")).all()
	lowest = versions[0]
	for version in versions[1:]:
		if version.Score < lowest.Score:
			lowest = version
	return lowest

def selection(generation) :
	versions = Version.query.filter(Version.Generation == generation).options(lazyload("Invigilations")).all()
	versions.sort(key=lambda version:version.Score)
	return versions[:len(versions)//3*2]

def mutate(initial, excluded):
	new = {}
	for key, value in initial.items():
		for i in range(len(value)):
			if random() <= mutation_rate:
				index = randint(0, len(excluded[key]) - 1)
				value[i] = excluded[key][index]
				excluded[key].pop(index)
		new[key] = value
	return new

def cross_over(parent_1, parent_2, generation):
	papers = Paper.query.options(noload('Invigilators')).all()
	teachers_lst = Teacher.query.options(noload('Invigilations')).all()
	excluded_teachers = []
	teachers = {}
	for teacher in teachers_lst:
		teachers[teacher.id] = teacher
	paper = papers[randint(0, len(papers)-1)]
	combined = {}
	excluded_teachers = {}
	for paper in papers:
		combined[paper.id] = []
		excluded_teachers[paper.id] = teachers_lst.copy()
	for i in range(len(parent_1.Invigilations)):
		invigilation_1 = parent_1.Invigilations[i]
		combined[invigilation_1.PaperId].append(teachers[invigilation_1.TeacherId])
		if teachers[invigilation_1.TeacherId] in excluded_teachers[invigilation_1.PaperId]:
			excluded_teachers[invigilation_1.PaperId].remove(teachers[invigilation_1.TeacherId])
	for i in range(len(parent_2.Invigilations)):
		invigilation_2 = parent_2.Invigilations[i]
		combined[invigilation_2.PaperId].append(teachers[invigilation_2.TeacherId])
		if teachers[invigilation_2.TeacherId] in excluded_teachers[invigilation_2.PaperId]:
			excluded_teachers[invigilation_2.PaperId].remove(teachers[invigilation_2.TeacherId])
	for key, value in combined.items():
		value = list(set(value))
		paper = Paper.query.options(noload('Invigilators')).get(key)
		if len(value) > 0:
			while len(value) > paper.Count - len(paper.Fixed_Invigilators):
				index = randint(0, len(value)-1)
				value.pop(index)
			combined[key] = value
	combined = mutate(combined, excluded_teachers)
	new_version = Version(generation)
	new_version.generate_with_dictionary(combined)
	new_version.set_score(optimal_paper_time, day_time_threshold)

def population_cross_over(generation):
	parents = selection(generation)
	shuffle(parents)
	while len(parents) >= 2:
		cross_over(parents[0], parents[1], generation + 1)
		parents[0].Generation += 1
		parents[1].Generation += 1
		parents.pop(0)
		parents.pop(0)
		marker = datetime.datetime.now()
	db.session.commit()

def delete_all():
	invigilations = Invigilation.query.all()
	for invigilation in invigilations:
		db.session.delete(invigilation)
	versions = Version.query.all()
	for version in versions:
		db.session.delete(version)
	db.session.commit()

def genetic_algo(generation):
	get_optimal_paper_time()
	print("Optimal time:", optimal_paper_time)
	if generation == 0:
		delete_all()
		set_fixed_invigilations()
		generate_level_pools()
		print("Generating random sample")
		marker = datetime.datetime.now()
		random_generate_version(pop_size)
		print("Time taken:", str(datetime.datetime.now() - marker))
	min_score = population_minimum(generation)
	marker = datetime.datetime.now()
	while generation < 9999:
		population_cross_over(generation)
		generation += 1
		min_score = population_minimum(generation)
		print("Generation:", generation ,"Min-Score:", str(min_score.Score), "Time:", str(datetime.datetime.now() - marker))
		marker = datetime.datetime.now()
	print("Score:", str(min_score.Score))
