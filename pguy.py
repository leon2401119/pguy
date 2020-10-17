import os
import glob
import sys
import argparse
from ftplib import FTP
import getpass
import zipfile
import subprocess


TIMEOUT = 5	# for countering infinite loop executables
IODIR = 'stdio'
SERVER_URL = 'ceiba.ntu.edu.tw'
SERVER_PORT = 21
GSPREAD_READY = True
GSPREAD_DEPENDENCIES = []



############ for gspread ###############
try:
	import gspread
except Exception as e:
	GSPREAD_READY = False
	GSPREAD_DEPENDENCIES.append('gspread')
	
try:
	from oauth2client.service_account import ServiceAccountCredentials
except Exception as e:
	GSPREAD_READY = False
	GSPREAD_DEPENDENCIES.append('oauth2client.service_account')
	
	
gss_scopes = ['https://spreadsheets.google.com/feeds']
spreadsheet_key = '1P11Krwj7CP5zGP4Q9YPmJMGy3WDSJLLcU9SaUMNSPjg'
########################################




def ftp_getfile(id, username, pwd, hw_number):

	ftp = FTP()
	ftp.connect(SERVER_URL, int(SERVER_PORT))
	ftp.login(username, pwd)
	ftp.cwd('hw')
	ftp.cwd('hw' + hw_number)

	ftp_file_list = ftp.nlst()
	version = 0
	src_file = None
	for file in ftp_file_list:
		if id in file and 'zip' in file:

			v = 0
			i = -5  # hwxxxxxx_id_hash_version.zip
			while file[i] != '_':
				v = v + int(file[i])*pow(10,-5-i)
				i -= 1

			if v > version:
				src_file = file
				version = v


	if not src_file:
		print(f'zip file for {id} not found on ftp')
		return False

	else:
		# file found for student
		# print(src_file)
		with open(src_file, 'wb') as f:
			ftp.retrbinary(f'RETR {src_file}', f.write)

		with zipfile.ZipFile(src_file, 'r') as zip_ref:
			zip_ref.extractall('.')

		os.remove(src_file)
		return True


def set_config():
	try:
		os.mkdir('.ftpinfo')
	except Exception as e:
		pass

	with open(os.path.join('.', '.ftpinfo', 'info'), 'w') as f:
		while True:
			try:
				print('username: ', end='')
				username = input()
				pwd = getpass.getpass(prompt='password: ')
				ftp = FTP()
				ftp.connect(SERVER_URL, int(SERVER_PORT))
				ftp.login(username, pwd)
				break

			except Exception as e:
				print('login incorrect... please try again')

		ftp.cwd('stdio')

		while True:
			try:
				print('ceiba hw serial number for this week: ', end='')
				hw_postfix = input()
				ftp.cwd('hw' + hw_postfix)
				testcase_zip = ftp.nlst()[0]
				with open(testcase_zip, 'wb') as file:
					ftp.retrbinary(f'RETR {testcase_zip}', file.write)
				ensure_iodir_exist()
				with zipfile.ZipFile(testcase_zip, 'r') as zip_ref:
					zip_ref.extractall(os.path.join('.',IODIR))
				os.remove(testcase_zip)
				break

			except Exception as e:
				print(f'cannot find testcase for "hw{hw_postfix}" on ceiba. try again')

		print('this hw is for week _? (eg. 1 for W1) ', end='')
		hw_week = input()

		ftp.cwd('..')
		ftp.cwd('..')
		ftp.cwd('hw')

		while True:
			try:
				print('ceiba hw serial number for last week: ', end='')
				hw_postfix_prev = input()
				ftp.cwd('hw' + hw_postfix_prev)
				break

			except Exception as e:
				print(f'cannot find "hw{hw_postfix_prev}" on ceiba. try again')

		f.writelines([username + '\n', pwd + '\n', hw_postfix + '\n', hw_week + '\n', hw_postfix_prev + '\n'])


		return username, pwd, hw_postfix, hw_week, hw_postfix_prev


def get_config():
	username, pwd, hw_postfix, hw_week, hw_postfix_prev = None, None, None, None, None

	try:
		f = open(os.path.join('.', '.ftpinfo', 'info'), 'r')
		username, pwd, hw_postfix, hw_week, hw_postfix_prev = f.read().splitlines()
		f.close()

	except Exception as e:
		pass

	return username, pwd, hw_postfix, hw_week, hw_postfix_prev



def change_config():
	with open(os.path.join('.', '.ftpinfo', 'info'), 'r') as f:
		username, pwd, hw_postfix, hw_week, hw_postfix_prev = f.read().splitlines()

	ftp = FTP()
	ftp.connect(SERVER_URL, int(SERVER_PORT))
	ftp.login(username, pwd)
	ftp.cwd('stdio')

	while True:
		try:
			print(f'ceiba hw serial number for this week (prev value = {hw_postfix}): ', end='')
			hw_postfix = input()
			ftp.cwd('hw' + hw_postfix)
			testcase_zip = ftp.nlst()[0]
			with open(testcase_zip, 'wb') as file:
				ftp.retrbinary(f'RETR {testcase_zip}', file.write)
			ensure_iodir_exist()
			with zipfile.ZipFile(testcase_zip, 'r') as zip_ref:
				zip_ref.extractall(os.path.join('.', IODIR))
			os.remove(testcase_zip)
			break

		except Exception as e:
			print(f'cannot find testcase for "hw{hw_postfix}" on ceiba. try again')


	ftp.cwd('..')
	ftp.cwd('..')
	ftp.cwd('hw')


	print(f'this hw is for week _? (prev value = {hw_week}): ', end='')
	hw_week = input()

	while True:
		try:
			print(f'ceiba hw serial number for last week (prev value = {hw_postfix_prev}): ', end='')
			hw_postfix_prev = input()
			ftp.cwd('hw' + hw_postfix_prev)
			break

		except Exception as e:
			print(f'cannot find testcase for "hw{hw_postfix_prev}" on ceiba. try again')


	with open(os.path.join('.', '.ftpinfo', 'info'), 'w') as f:
		f.writelines([username + '\n', pwd + '\n', hw_postfix + '\n', hw_week + '\n', hw_postfix_prev + '\n'])

	return hw_postfix, hw_week, hw_postfix_prev



def syspause_cleaner(filename):
	mod = False

	origin = open(filename, 'r', encoding='ascii')

	try:
		line = origin.readline()
	except Exception as e:
		return

	target = open(filename + 'bak', 'w')  # rxxxxxxxx_1.cppbak

	while(line):
		# print(line)
		if 'system' in line:
			if 'pause' in line or 'Pause' in line:
				mod = True
		else:
			target.writelines([line])
		line = origin.readline()

	origin.close()
	target.close()

	if mod:
		os.remove(filename)
		if os.name == 'posix':
			os.system(f'mv {filename}bak {filename}')
		else:
			os.system(f'move {filename}bak {filename}')
	else:
		os.remove(f'{filename}bak')


def ensure_iodir_exist():
	try:
		os.mkdir(IODIR)
	except Exception as e:
		pass

	oldtest_list = glob.glob(os.path.join('.',IODIR,'*.in'))
	oldtest_list.extend(glob.glob(os.path.join('.',IODIR,'*.out')))
	for file in oldtest_list:
		os.remove(file)


def pguy(id, hw_week, late, update):

	test_list = glob.glob(os.path.join('.', IODIR, '*.in'))  # 1-2.in

	problem_count = 0
	for test in test_list:
		prob_no = int(os.path.basename(test).split('-')[0])
		problem_count = prob_no if prob_no > problem_count else problem_count


	gspread_row = [id]

	for problem_num in range(1, problem_count + 1):
		## check existence phase

		try:
			f = open(f'{id}_{problem_num}.cpp', 'r')
		except Exception as e:
			print(f'Score for problem {problem_num} : 0 ({id}_{problem_num}.cpp not found)')
			gspread_row.append('0')
			continue

		f.close()
		syspause_cleaner(f'{id}_{problem_num}.cpp')

		## compile phase

		os.system(f'g++ {id}_{problem_num}.cpp -o {problem_num} 2>{problem_num}_err.txt')
		if os.stat(os.path.join('.',f'{problem_num}_err.txt')).st_size:
			# compile error
			print(f'Score for problem {problem_num} : 0 (Compile Error)')
			continue

		os.remove(os.path.join('.',f'{problem_num}_err.txt'))

		## test phase
		score = 0
		test_num = 1
		while os.path.join('.',IODIR,f'{problem_num}-{test_num}.in') in test_list:

			prefix = os.path.join('.',IODIR,f'{problem_num}')
			prog = os.path.join('.',f'{problem_num}')

			# os.system(f'{prog} <{prefix}-{test_num}.in >{problem_num}-{test_num}.txt 2>&1')
			with open(f'{prefix}-{test_num}.in', 'r') as f:
				ff = open(f'{problem_num}-{test_num}.txt', 'w')
				to_write = ''
				try:
					output = subprocess.run([prog], stdin=f, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
				except Exception as e:
					to_write = 'infinite loop detected...'

				if not len(to_write):
					try:
						to_write = output.stdout.decode('ascii')
					except Exception as e:
						to_write = 'the answer is not ASCII encoded'

				ff.write(to_write)
				ff.close()


			# if os.name == 'posix':
			# 	os.system(f'diff -B {prefix}-{test_num}.out {problem_num}-{test_num}.txt >{problem_num}-{test_num}_diff.txt')
			# else:
			# 	diff(f'{prefix}-{test_num}.out',f'{problem_num}-{test_num}.txt', f'{problem_num}-{test_num}_diff.txt')
			diff(f'{prefix}-{test_num}.out', f'{problem_num}-{test_num}.txt', f'{problem_num}-{test_num}_diff.txt')
			if not os.stat(f'{problem_num}-{test_num}_diff.txt').st_size:
				score += 1
				os.remove(f'{problem_num}-{test_num}_diff.txt')
				os.remove(f'{problem_num}-{test_num}.txt')
			else:
				print(f'Incorrect ans for {problem_num}-{test_num}')
				os.remove(f'{problem_num}-{test_num}.txt')

			test_num += 1

		print(f'Score for problem {problem_num} : {score}/{test_num - 1}')
		if os.name == 'posix':
			os.remove(f'{problem_num}')
		else:
			os.remove(f'{problem_num}.exe')

		if late:
			score = score/2
		gspread_row.append(str(score))


	## gspread update
	if update:
		if GSPREAD_READY:
			auth_json_path = get_credential()
			if auth_json_path:
				sheet = connect_to_gspread(auth_json_path, hw_week, len(gspread_row) - 1)
				update_score(sheet,gspread_row)
			else:
				print('unable to get correct JSON file for credential authentication')
		else:
			print('google spreadsheet API failure. plz install the dependencies and try again')
			print(f'{len(GSPREAD_DEPENDENCIES)} unmateched gspread module dependecies : ')
			for item in GSPREAD_DEPENDENCIES:
				print(item)



def diff(file1,file2,outfile):

	f1 = open(file1,'r', encoding='ascii')
	f2 = open(file2,'r', encoding='ascii')
	out = open(outfile, 'w')


	f1_str = f1.read(-1)
	try:
		f2_str = f2.read(-1)
	except Exception as e:
		out.writelines(['the answer is not ASCII encoded'])
		out.close()
		return


	f1_trail_cr = 0
	f2_trail_cr = 0

	if len(f1_str):
		while(f1_str[-1-f1_trail_cr] == '\n'):
			f1_trail_cr = f1_trail_cr + 1
	if len(f2_str):
		while(f2_str[-1-f2_trail_cr] == '\n'):
			f2_trail_cr = f2_trail_cr + 1

	# print(f1_trail_cr)
	# print(f2_trail_cr)


	f1_trail_cr = -f1_trail_cr if f1_trail_cr else None
	f2_trail_cr = -f2_trail_cr if f2_trail_cr else None


	if f1_str[:f1_trail_cr] != f2_str[:f2_trail_cr]:
		out.writelines(['Correct Answer :\n',f1_str+'\n','Your Answer :\n',f2_str])


	f1.close()
	f2.close()
	out.close()


def clean_dir():
	clean_up_list = glob.glob(os.path.join('.', '*.txt'))
	clean_up_list.extend(glob.glob(os.path.join('.', '*.cpp')))
	for file in clean_up_list:
		os.remove(file)



def main(args):

	if args.offline:
		clean_dir()

	username, pwd, hw_postfix, hw_week, hw_postfix_prev = get_config()

	if not username or args.init:
		# config not found
		username, pwd, hw_postfix, hw_week, hw_postfix_prev = set_config()

		if args.init:
			exit(0)

	elif args.config:
		hw_postfix, hw_week, hw_postfix_prev = change_config()


	if args.id:
		id = args.id.lower()
		if args.boode:
			ftp_getfile(id, username, pwd, hw_postfix_prev)

		elif args.offline:
			pguy(id, hw_week, args.late, args.update)

		else:
			res = ftp_getfile(id, username, pwd, hw_postfix)
			if res and not args.file:
				pguy(id, hw_week, args.late, args.update)



def get_credential():
	json_list = glob.glob(os.path.join('.','*.json'))
	if len(json_list) == 1:
		auth_json_path = glob.glob(os.path.join('.','*.json'))[0]
	elif len(json_list):
		print('no credential JSON file found')
		auth_json_path = None
	else:
		print('more than one JSON file found')
		auth_json_path = None
	return auth_json_path



def connect_to_gspread(auth_json_path, hw_week, problem_total):
	credentials = ServiceAccountCredentials.from_json_keyfile_name(auth_json_path, gss_scopes)
	gss_client = gspread.authorize(credentials)
	try:
		sheet = gss_client.open_by_key(spreadsheet_key).worksheet('W' + hw_week)
		# sheet = gss_client.open_by_key(spreadsheet_key).worksheet('工作表1')

	except Exception as e:
		sheet = gss_client.open_by_key(spreadsheet_key).add_worksheet('W' + hw_week, 1004, 26)
		new_row = ['Student ID']
		for i in range(problem_total):
			new_row.append(f'Problem {i+1}')
		sheet.insert_row(new_row)

	return sheet


def update_score(sheet, new_row):
	## new_row = [id,score1,score2,...]
	info = sheet.findall(new_row[0])
	if not len(info):
		# no entry found, create row
		sheet.insert_row(new_row,2)

	elif len(info) == 1:
		# found an old entry, update score
		row_num = info[0].row
		old_row = sheet.row_values(row_num)
		for index in range(1,len(new_row)):
			if float(old_row[index]) < float(new_row[index]):
				sheet.update_cell(row_num, index + 1, new_row[index])

	else:
		# unexpected behavior
		print(f'duplicate row for {id}')

	sheet.sort((1,'asc'), range='A2:Z100')



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="i'm pguy. i p guy")
	parser.add_argument('id', type=str, nargs='?', help='student id')
	parser.add_argument('--init', '-i', action='store_true', help='set/reset all configuration')
	parser.add_argument('--config', '-c', action='store_true', help='configure which homeworks to track on ceiba')
	parser.add_argument('--boode', '-b', action='store_true', help='download src code for previos homework')
	parser.add_argument('--file', '-f', action='store_true', help='only download src code')
	parser.add_argument('--late', '-l', action='store_true', help='late turn-in. 50% pt deduction')
	parser.add_argument('--update', '-u', action='store_true', help='update google spreadsheet')
	parser.add_argument('--offline', '-o', action='store_true', help='use local {id}_{prob_num}.cpp files for judging')
	args = parser.parse_args()
	if len(sys.argv) < 2:
		parser.print_usage()
	main(args)
