import os
import glob
import sys
import argparse
from ftplib import FTP
import getpass
import zipfile


IODIR = 'stdio'


def ftp_getfile(id, init):

	if init:
		try:
			os.mkdir('.ftpinfo')
		except Exception as e:
			pass

		server, port, hw_postfix, username, pwd = set_config()


	else:
		try:
			f = open(os.path.join('.', '.ftpinfo', 'info'), 'r')
			f.close()
			server, port, hw_postfix, username, pwd = get_config()

		except Exception as e:
			os.mkdir('.ftpinfo')
			server, port, hw_postfix, username, pwd = set_config()


	ftp = FTP()
	ftp.connect(server, int(port))
	ftp.login(username, pwd)
	ftp.cwd('hw')
	ftp.cwd('hw' + hw_postfix)

	ftp_file_list = ftp.nlst()
	id_file_list = []
	version = 0
	src_file = None
	for file in ftp_file_list:
		if id in file:
			v = int(file[-5:-4])
			if v > version:
				src_file = file


	if not src_file:
		print(f'zip file for {id} not found on ftp')
		return False

	else:
		# file found for student
		with open(src_file, 'wb') as f:
			ftp.retrbinary(f'RETR {src_file}', f.write)

		with zipfile.ZipFile(src_file, 'r') as zip_ref:
			zip_ref.extractall('.')

		os.remove(src_file)
		return True






def set_config():
	with open(os.path.join('.', '.ftpinfo', 'info'), 'w') as f:
		print('server url: ', end='')
		server = input()
		print('server port: ', end='')
		port = input()
		print('hw number: ', end='')
		hw_postfix = input()
		print('username: ', end='')
		username = input()
		pwd = getpass.getpass(prompt='password: ')

		f.writelines([server + '\n', port + '\n', hw_postfix + '\n', username + '\n', pwd + '\n'])

		return server, port, hw_postfix, username, pwd


def get_config():
	with open(os.path.join('.', '.ftpinfo', 'info'), 'r') as f:
		server, port, hw_postfix, username, pwd = f.read().splitlines()

	return server, port, hw_postfix, username, pwd


def syspause_cleaner(filename):
	mod = False

	origin = open(filename, 'r')
	target = open(filename + 'bak' , 'w')	# rxxxxxxxx_1.cppbak
	line = origin.readline()
	while(line):
		# print(line)
		if 'system("pause");' in line:
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



def main(id):

	test_list = glob.glob(os.path.join('.', IODIR, '*.in'))  # 1-2.in

	problem_count = 0
	for test in test_list:
		prob_no = int(os.path.basename(test).split('-')[0])
		problem_count = prob_no if prob_no > problem_count else problem_count

	for problem_num in range(1, problem_count + 1):
		## check existence phase

		try:
			f = open(f'{id}_{problem_num}.cpp', 'r')
		except Exception as e:
			print(f'Score for problem {problem_num} : 0 ({id}_{problem_num}.cpp not found)')
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

			os.system(f'{prog} <{prefix}-{test_num}.in >{problem_num}-{test_num}.txt 2>&1')
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

			test_num += 1

		print(f'Score for problem {problem_num} : {score}/{test_num - 1}')
		if os.name == 'posix':
			os.remove(f'{problem_num}')
		else:
			os.remove(f'{problem_num}.exe')


def diff(file1,file2,outfile):
	f1 = open(file1,'r')
	f2 = open(file2,'r')

	f1_str = f1.read(-1)
	f2_str = f2.read(-1)

	out = open(outfile,'w')


	f2_str = f2_str[:-1] if f2_str[-1:]=='\n' else f2_str
	if f1_str != f2_str:
		out.writelines(['<<<<\n',f1_str+'\n','>>>>\n',f2_str])

	f1.close()
	f2.close()
	out.close()


def clean_dir():
	clean_up_list = glob.glob(os.path.join('.', '*.txt'))
	clean_up_list.extend(glob.glob(os.path.join('.', '*.cpp')))
	for file in clean_up_list:
		os.remove(file)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="i'm pguy. i p guy")
	parser.add_argument('id', type=str, help='student id')
	parser.add_argument('--init', '-i', action='store_true' , help='init/interactive mode for ftp server configuration')
	args = parser.parse_args()
	clean_dir()
	res = ftp_getfile(args.id, args.init)
	if res:
		main(args.id)
