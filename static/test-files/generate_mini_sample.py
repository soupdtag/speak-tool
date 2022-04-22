# given a large list of file names, one on each line,
# generate a list of 1000 entries from that list.
import random, os

source_file = "dave_task_filenames.txt"
output_file = "dave_task_filenames_mini1000.txt"
source_list = []
output_list = []
i = 0


# read source file
with open(source_file, "r") as source:
	source_list = source.readlines()
	i += 1


# sample 1000 random lines
output_list = random.sample(source_list, 1000)


# save new file
with open(output_file, "w") as output:
	for line in output_list:
		line = line.replace("./places/trainSet_for_AMT_audio/","dave_task/")
		output.write(line)