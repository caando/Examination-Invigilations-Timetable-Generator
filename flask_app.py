import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from classes import db, app, Teacher, Paper, Version, Fixed_Invigilation, Invigilation, Pool
from sqlalchemy.orm import noload
from generate import generate_largest_pools, generate_department_pools

@app.route('/papers', methods=["GET", "POST"])
def papers():
	if request.method == "POST":
		if request.form.get('edit'):
			paper_id = request.form.get('edit')
			paper = Paper.query.options(noload('Invigilators')).get(int(paper_id))
			paper.Name = request.form.get(paper_id + '-name')
			paper.Subject = request.form.get(paper_id + '-subject')
			paper.SubjectCode = request.form.get(paper_id + '-subjcode')
			paper.Level = request.form.get(paper_id + '-level')
			paper.Department = request.form.get(paper_id + '-department')
			paper.Count = int(request.form.get(paper_id + '-count'))
			paper.Date = datetime.datetime.strptime(request.form.get(paper_id + '-date'), '%d-%m-%Y').date()
			paper.StartTime = datetime.datetime.strptime(request.form.get(paper_id + '-starttime'), '%I:%M %p').time()
			paper.EndTime = datetime.datetime.strptime(request.form.get(paper_id + '-endtime'), '%I:%M %p').time()
		if request.form.get('add'):
			name = request.form.get('add-name')
			subject = request.form.get('add-subject')
			subjcode = request.form.get('add-subjcode')
			level = request.form.get('add-level')
			department = request.form.get('add-department')
			count = int(request.form.get('add-count'))
			date = datetime.datetime.strptime(request.form.get('add-date'), '%d-%m-%Y').date()
			starttime = datetime.datetime.strptime(request.form.get('add-starttime'), '%I:%M %p').time()
			endtime = datetime.datetime.strptime(request.form.get('add-endtime'), '%I:%M %p').time()
			Paper(subject, subjcode, name, department, count, date, starttime, endtime, level)
		if request.form.get('delete'):
			paper_id = request.form.get('delete')
			paper = Paper.query.options(noload('Invigilators')).get(int(paper_id))
			db.session.delete(paper)
		db.session.commit()

	papers = Paper.query.options(noload('Invigilators')).all()
	for paper in papers:
		paper.date_str = paper.Date.strftime('%d-%m-%Y')
		paper.starttime_str = paper.StartTime.strftime('%I:%M %p')
		paper.endtime_str = paper.EndTime.strftime('%I:%M %p')
	return render_template('papers.html', papers=papers)

@app.route('/teachers', methods=["GET", "POST"])
def teachers():
	return

@app.route('/selection', methods=["GET", "POST"])
def selection():
	papers = Paper.query.options(noload('Invigilators')).all()
	for paper in papers:
		paper.teachers = []
		clashes = []
		for paper_clash in papers:
			if paper != paper_clash and paper_clash.EndTime > paper.StartTime and paper_clash.StartTime < paper.EndTime and paper_clash.Date == paper.Date:
				clashes.append(paper_clash)
		paper.not_included = Teacher.query.options(noload('Invigilations')).all()
		for pool_ob in paper.Pool:
			teacher = Teacher.query.options(noload('Invigilations')).get(pool_ob.TeacherId)
			paper.teachers.append(teacher)
			paper.not_included.remove(teacher)
		for clash in clashes:
			for pool_ob in clash.Pool:
				teacher = Teacher.query.options(noload('Invigilations')).get(pool_ob.TeacherId)
				if teacher in paper.not_included:
					paper.not_included.remove(teacher)
		for teacher in paper.not_included:
			if teacher.check_availability(paper.Date, paper.StartTime, paper.EndTime) == False:
				paper.not_included.remove(teacher)
		paper.teachers.sort(key=lambda teacher: teacher.Name)
		paper.not_included.sort(key=lambda teacher: teacher.Name)
		paper.pool_count = len(paper.teachers)
	if request.method == "POST":
		if request.form.get('largest'):
			generate_largest_pools()
		if request.form.get('department'):
			generate_department_pools()
		if request.form.get('remove'):
			remove = request.form.get('remove').split('-')
			paper_id, teacher_id = int(remove[0]), int(remove[1])
			pool_ob = Pool.query.filter(Pool.PaperId == paper_id and Pool.TeacherId == teacher_id).first()
			db.session.delete(pool_ob)
			db.session.commit()
		if request.form.get('add'):
			paper_id = request.form.get('add')
			for paper_temp in papers:
				if paper_temp.id == int(paper_id):
					paper = paper_temp
					break
			for teacher in paper.not_included:
				print(teacher.id)
				if request.form.get('add' + paper_id + '-' + str(teacher.id)):
					Pool(teacher, paper)
			db.session.commit()
		return redirect(url_for('selection'))

	return render_template('selection.html', papers= papers)

@app.route('/generate', methods=["GET", "POST"])
def generate():
	return

@app.route('/saves', methods=["GET", "POST"])
def saves():
	return

if __name__ == "__main__":
	app.run(debug=True)
