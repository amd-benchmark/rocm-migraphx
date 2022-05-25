import os
import pandas
import pathlib
import argparse
from colorama import Fore,Style
from tabulate import tabulate

#set execution arguments
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test', type=str, required=True, help="Path to test results")
args = parser.parse_args()

#get script path
script_path = os.path.dirname(os.path.realpath(__file__))

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

print(f"Comparing commits: {commit1} to {commit2}")

#Combine two dataframes
combined = pandas.concat([data1,data2], axis=1, ignore_index=True)

#Rename columns
combined.columns = ['Test','Batch','Time new','Time old']

#Calculate rates and diff
combined['Rate new'] = combined['Batch'] * 1000 / combined['Time new']
combined['Rate old'] = combined['Batch'] * 1000 / combined['Time old']
combined['Diff'] = combined['Rate new'] / combined['Rate old'] - 1

l_formated = combined.copy()

#Format columns for markdown
def symbol_md(val):
    if val > 0:
        val = "{0:.2%}".format(val)
        val = f":white_check_mark: {val}"
    elif val < 0:
        val = "{0:.2%}".format(val)
        val = f":red_circle: {val}"
    return val
combined['Diff']=combined['Diff'].apply(symbol_md)

def format_rate(val):
    return str('{:,.2f}'.format(val))
combined['Rate new'] = combined['Rate new'].apply(format_rate)
combined['Rate old'] = combined['Rate old'].apply(format_rate)

#Format columns for log
def check_diff(val):
    if val < 0:
        color = Fore.RED
    else:
        color = Fore.GREEN
    return color + str('{0:.2%}'.format(val)) + Style.RESET_ALL
l_formated['Diff']=l_formated['Diff'].apply(check_diff)

#Print out table for log
def pprint_df(dframe):
    print(tabulate(dframe, headers='keys', tablefmt='grid', showindex=False, colalign=('left','right','right','right')))

pprint_df(l_formated[['Test','Rate new','Rate old','Diff']])

#Markdown for comment
os.chdir(script_path)
m_formated = combined.drop(columns=['Batch','Time new','Time old'])
print(m_formated.to_markdown('temp.md', index=False, colalign=('left','right','right','right')))