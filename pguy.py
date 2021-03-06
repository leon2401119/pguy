import os
import glob
import sys
import argparse


IODIR = 'stdio'


def ftp_getfile(id):
	pass


def main(id):
	clean_up_list = glob.glob(os.path.join('.', '*.txt'))
	for file in clean_up_list:
		os.remove(file)

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

		## compile phase

		os.system(f'g++ {id}_{problem_num}.cpp -o {problem_num} 2>{problem_num}_err.txt')
		if os.stat(f'./{problem_num}_err.txt').st_size:
			# compile error
			print(f'Score for problem {problem_num} : 0 (Compile Error)')
			continue

		os.remove(f'./{problem_num}_err.txt')

		## test phase
		score = 0
		test_num = 1
		while f'./{IODIR}/{problem_num}-{test_num}.in' in test_list:
			os.system(f'./{problem_num} <./{IODIR}/{problem_num}-{test_num}.in >{problem_num}-{test_num}.txt 2>&1')
			os.system(f'diff -B ./{IODIR}/{problem_num}-{test_num}.out {problem_num}-{test_num}.txt >{problem_num}-{test_num}_diff.txt')
			if not os.stat(f'{problem_num}-{test_num}_diff.txt').st_size:
				score += 1
				os.remove(f'{problem_num}-{test_num}_diff.txt')
				os.remove(f'{problem_num}-{test_num}.txt')
			else:
				print(f'Incorrect ans for {problem_num}-{test_num}')

			test_num += 1

		print(f'Score for problem {problem_num} : {score}/{test_num - 1}')
		os.remove(f'{problem_num}')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="i'm pguy. i p guy")
	parser.add_argument('id', type=str, help='student id')
	args = parser.parse_args()
	ftp_getfile(args.id)
	main(args.id)
