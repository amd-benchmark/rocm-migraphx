import os
import pandas
import pathlib
import argparse
import numpy
from colorama import Fore,Style
from tabulate import tabulate

#set execution arguments
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test', type=str, required=True, help="Path to test results")
args = parser.parse_args()

#get script path
script_path = os.path.dirname(os.path.realpath(__file__))

#get threshold
threshold = pandas.read_csv(r'C:\AMD\threshold.csv', header=None, usecols=[1],skiprows=[0])

#find path to lastest test result
find_last = max(pathlib.Path(args.test).glob('*/'), key=os.path.getmtime)
os.chdir(find_last)

#read lastest test result data and commit
data1 = pandas.read_csv('results.csv', header=None)
with open('commit.txt') as git:
    commit1 = str(git.readlines(1))[9:15]
git.close()

#find path to 2nd lastest test result
find_2last = sorted(pathlib.Path(args.test).glob('*/'), key=os.path.getmtime)[-2]
os.chdir(find_2last)

#read 2nd lastest test result data and commit
data2 = pandas.read_csv('results.csv', header=None, usecols=[2])
with open('commit.txt') as git:
    commit2 = str(git.readlines(1))[9:15]
git.close()

#print(f"Comparing commits: {commit1} to {commit2}")

#Combine two dataframes
combined = pandas.concat([data1,data2,threshold], axis=1, ignore_index=True)

#Rename columns
combined.columns = ['Test','Batch','Time new','Time old','Threshold']

#Calculate rates and diff
Rate_new = f'Rate new\n{commit1}'
Rate_old = f'Rate old\n{commit2}'
combined[Rate_new] = combined['Batch'] * 1000 / combined['Time new']
combined[Rate_old] = combined['Batch'] * 1000 / combined['Time old']
combined['Diff_tmp'] = combined[Rate_new] / combined[Rate_old] - 1
l_formated = combined.copy()

#Format columns for markdown
conditions = [combined['Diff_tmp'].abs() < combined['Threshold'], combined['Diff_tmp'] > combined['Threshold'], combined['Diff_tmp'] < combined['Threshold'], combined['Diff_tmp'].isnull()]
choices = [':white_check_mark:',':high_brightness:',':red_circle:',':x:']
combined['Compare'] = numpy.select(conditions,choices)
def conv_to_per(val):
    val = "{0:.2%}".format(val)
    return(val)
combined['Diff_tmp']=combined['Diff_tmp'].apply(conv_to_per)
combined['Diff']=combined.agg('{0[Compare]} {0[Diff_tmp]}'.format,axis=1)

def format_rate(val):
    return str('{:,.2f}'.format(val))
combined[Rate_new] = combined[Rate_new].apply(format_rate)
combined[Rate_old] = combined[Rate_old].apply(format_rate)

#Format columns for log
def check_diff(val):
    if val < 0:
        color = Fore.RED
    else:
        color = Fore.GREEN
    return color + str('{0:.2%}'.format(val)) + Style.RESET_ALL
l_formated['Diff']=l_formated['Diff_tmp'].apply(check_diff)

#Print out table for log
def pprint_df(dframe):
    print(tabulate(dframe, headers='keys', tablefmt='grid', showindex=False, colalign=('left','right','right','right')))

pprint_df(l_formated[['Test',Rate_new,Rate_old,'Diff']])

#Markdown for comment
os.chdir(script_path)
m_formated = combined.drop(columns=['Batch','Time new','Time old','Threshold','Diff_tmp','Compare'])
print(m_formated.to_markdown('temp.md', index=False, colalign=('left','right','right','right')))