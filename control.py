from classes import create_db, Paper, Teacher, Version
from import_data import import_paper_data, import_to_db
from generate import genetic_algo
from openpyxl import Workbook
from export_data import export_analytics

#create_db()
#import_to_db('timetables.xml')
#import_paper_data('papers.xlsx')
genetic_algo(157)
#export_teachers()
#export_analytics()
