import os
import pandas
import pathlib
import argparse
import numpy

#set symbols
s_green = ":white_check_mark:"
s_red = ":red_circle:"
s_yellow = ":high_brightness:"
s_nok = ":x:"

#set execution arguments
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test', type=str, required=True, help="Path to test results")
parser.add_argument('-r', '--range', type=str, required=True, help="Path to threshold config")
args = parser.parse_args()

#get script path
script_path = os.path.dirname(os.path.realpath(__file__))

#get threshold
os.chdir(args.range)
threshold = pandas.read_csv('threshold.csv', header=None, usecols=[1], skiprows=[0])

#find path to lastest test result
find_last = max(pathlib.Path(args.test).glob('perf*'), key=os.path.getmtime)
os.chdir(find_last)

#read lastest test result data and commit
data1 = pandas.read_csv('results.csv', header=None)
with open('commit.txt') as git:
    commit1 = str(git.readlines(1))[9:15]
git.close()

#find path to 2nd lastest test result
find_2last = sorted(pathlib.Path(args.test).glob('perf*'), key=os.path.getmtime)[-2]
os.chdir(find_2last)

#read 2nd lastest test result data and commit
data2 = pandas.read_csv('results.csv', header=None, usecols=[2])
with open('commit.txt') as git:
    commit2 = str(git.readlines(1))[9:15]
git.close()

#Combine two dataframes
combined = pandas.concat([data1,data2,threshold], axis=1, ignore_index=True)

#Rename columns
combined.columns = ['Test','Batch','Time new','Time old','Threshold']

#Calculate rates and diff
Rate_new = f'Rate new <br />{commit1}'
Rate_old = f'Rate old <br />{commit2}'
combined[Rate_new] = combined['Batch'] * 1000 / combined['Time new']
combined[Rate_old] = combined['Batch'] * 1000 / combined['Time old']
combined['Diff_tmp'] = combined[Rate_new] / combined[Rate_old] - 1

#Format columns for markdown
conditions = [combined['Diff_tmp'].abs() < combined['Threshold'], combined['Diff_tmp'] > combined['Threshold'], combined['Diff_tmp'] < combined['Threshold'], combined['Diff_tmp'].isnull()]
choices = [s_green,s_yellow,s_red,s_nok]
combined['Compare'] = numpy.select(conditions, choices)
def conv_to_per(val):
    val = "{0:.2%}".format(val)
    return(val)
combined['Diff_tmp'] = combined['Diff_tmp'].apply(conv_to_per)
combined['Diff'] = combined.agg('{0[Compare]} {0[Diff_tmp]}'.format, axis=1)

def format_rate(val):
    return str('{:,.2f}'.format(val))
combined[Rate_new] = combined[Rate_new].apply(format_rate)
combined[Rate_old] = combined[Rate_old].apply(format_rate)

#Status check
check_red = (combined.Compare==s_red).sum()
check_nok = (combined.Compare==s_nok).sum()
check_yellow = (combined.Compare==s_yellow).sum()

if check_red >= 1 or check_nok >= 1:
    status = f'This build is not recommended to merge {s_red}'
elif check_yellow >= 1:
    status = f'Check results before merge {s_yellow}'
else:
    status = f'This build is OK for merge {s_green}'

#Markdown for comment
os.chdir(script_path)
formated = combined.drop(columns=['Batch','Time new','Time old','Threshold','Diff_tmp','Compare'])
print(formated.to_markdown('temp.md', index=False, colalign=('left','right','right','right')))

#Append status to markdown
md_file = open('temp.md', 'a')
md_file.write(f'\n\n\n{status}')
md_file.close()