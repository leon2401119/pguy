import os
import glob
import sys
import argparse


def ftp_getfile(id):
	pass


def main(id):

	clean_up_list = glob.glob(os.path.join('.','*.txt'))
	for file in clean_up_list:
		os.remove(file)


	test_list = glob.glob(os.path.join('.','*.in'))	# 1-2.in

	problem_count = 0
	for test in test_list:
		prob_no = int(os.path.basename(test).split('-')[0])
		problem_count = prob_no if prob_no > problem_count else problem_count


	for problem_num in range(1,problem_count+1):
		## compile phase
		os.system(f'g++ {id}_{problem_num}.cpp -o {problem_num} 2>{problem_num}_err.txt')
		if os.stat(f'./{problem_num}_err.txt').st_size:
			# compile error
			print(f'Compile Error : {id}_{problem_num}.cpp')
			print(f'Score for problem {problem_num} : 0')
			continue

		os.remove(f'./{problem_num}_err.txt')


		## test phase
		score = 0
		test_num = 1
		while f'./{problem_num}-{test_num}.in' in test_list:
			os.system(f'./{problem_num} <{problem_num}-{test_num}.in >{problem_num}-{test_num}.txt 2>&1')
			os.system(f'diff -B {problem_num}-{test_num}.out {problem_num}-{test_num}.txt >{problem_num}-{test_num}_diff.txt')
			if not os.stat(f'{problem_num}-{test_num}_diff.txt').st_size:
				score += 1
				os.remove(f'{problem_num}-{test_num}_diff.txt')
				os.remove(f'{problem_num}-{test_num}.txt')
			else:
				print(f'Incorrect ans for problem {problem_num}, test case {test_num}')

			test_num += 1

		print(f'Score for problem {problem_num} : {score}/{test_num-1}')
		os.remove(f'{problem_num}')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="i'm p guy. i p guy")
	parser.add_argument('id', type=str, help='student id')
	args = parser.parse_args()
	ftp_getfile(args.id)
	main(args.id)

