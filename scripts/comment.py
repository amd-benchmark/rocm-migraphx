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
parser.add_argument('-r', '--range', type=str, help="Path to threshold config")
parser.add_argument('-n', '--number', type=int, required=True, help="Number of results for calculation")
parser.add_argument('-s', '--std_dev', action='store_true', help="Calculate standard deviation of last n results")
parser.add_argument('-m', '--max_value', action='store_true', help="Compare to max value from last n results")
args = parser.parse_args()

#find last Nth report path
def get_last_nth(n):
    path = sorted(pathlib.Path(args.test).glob('perf*'), key=os.path.getmtime)[-n]
    return path

#extract commit id
def get_commit(path):
    os.chdir(path)
    with open('commit.txt') as git:
        commit_id = str(git.readlines(1))[9:15]
    git.close()
    return commit_id

#get test result data
def get_result(path):
    os.chdir(path)
    result_data = pandas.read_csv('results.csv', header=None, usecols=[2])
    return result_data

#get test parameters
def get_name(path):
    os.chdir(path)
    test_names = pandas.read_csv('results.csv', header=None, usecols=[0,1])
    return test_names

#get script path
script_path = os.path.dirname(os.path.realpath(__file__))

#create necessary data structures
commits = {}
performance_data = {}
performance_tests = {}
stdev = []
max_val = []

#extract data from result
for i in range(1,args.number+1):
    if i==1:
        performance_tests[f'tests'] = get_name(get_last_nth(i))
        performance_data[f'data_{i}'] = get_result(get_last_nth(i))
        commits[f'commit{i}'] = get_commit(get_last_nth(i))
    elif i==2:
        performance_data[f'data_{i}'] = get_result(get_last_nth(i))
        commits[f'commit{i}'] = get_commit(get_last_nth(i))
    else:
        performance_data[f'data_{i}'] = get_result(get_last_nth(i))

performance_calc = {f'test_{i}':[] for i in range(0,len(performance_data['data_1']))}

for key, value in performance_data.items():
    for i,test in enumerate(performance_calc):
        performance_calc[f'test_{i}'].append(value.iloc[i][2])

#calculate standard deviation and max value
for i in range(0,len(performance_data['data_1'])):
    max_val.append(numpy.max(performance_calc.get(f'test_{i}')))
    stdev.append(numpy.std(performance_calc.get(f'test_{i}')))

#convert to dataframes
st_dev = pandas.DataFrame(stdev)
tests = pandas.DataFrame(performance_tests['tests'])
data1 = pandas.concat([tests,performance_data['data_1']], axis=1, ignore_index=True)
data2 = pandas.DataFrame(performance_data['data_2'])

#select threshold type
if args.max_value:
    threshold = pandas.DataFrame(max_val)
elif args.range:
    os.chdir(args.range)
    threshold = pandas.read_csv('threshold.csv', header=None, usecols=[1], skiprows=[0])
elif args.std_dev:
    threshold = pandas.DataFrame(stdev)
     
#combine dataframes
combined = pandas.concat([data1,data2,threshold], axis=1, ignore_index=True)

#rename columns
combined.columns = ['Test','Batch','Time new','Time old','Threshold']

#calculate rates and diff
Rate_new = f"Rate new <br />{commits['commit1']}"
Rate_old = f"Rate old <br />{commits['commit2']}"
combined[Rate_new] = combined['Batch'] * 1000 / combined['Time new']
combined[Rate_old] = combined['Batch'] * 1000 / combined['Time old']
combined['Diff_tmp'] = combined[Rate_new] / combined[Rate_old] - 1

#format columns for markdown depending on calculation type
def convert_to_percent(val):
    val = "{0:.2%}".format(val)
    return(val)

def format_rate(val):
    return str('{:,.2f}'.format(val))

if args.max_value:
    conditions = [combined['Time new'] >= combined['Threshold'], combined['Time new'] < combined['Threshold'], combined['Time new'].isnull()]
    choices = [s_green,s_red,s_nok]
    combined['Diff_tmp'] = combined['Time new'] / combined['Threshold'] - 1
else:
    conditions = [combined['Diff_tmp'].abs() < combined['Threshold'], combined['Diff_tmp'] > combined['Threshold'], combined['Diff_tmp'] < combined['Threshold'], combined['Diff_tmp'].isnull()]
    choices = [s_green,s_yellow,s_red,s_nok]

combined['Compare'] = numpy.select(conditions, choices)
combined['Diff_tmp'] = combined['Diff_tmp'].apply(convert_to_percent)
combined['Diff'] = combined.agg('{0[Compare]} {0[Diff_tmp]}'.format, axis=1)

if args.max_value:
    new_name = f"Compared to best <br />of last {args.number} runs"
    combined.rename(columns={'Diff':new_name}, inplace=True) 

combined[Rate_new] = combined[Rate_new].apply(format_rate)
combined[Rate_old] = combined[Rate_old].apply(format_rate)

#status check
check_red = (combined.Compare==s_red).sum()
check_nok = (combined.Compare==s_nok).sum()
check_yellow = (combined.Compare==s_yellow).sum()

if check_red >= 1 or check_nok >= 1:
    status = f'This build is not recommended to merge {s_red}'
elif check_yellow >= 1:
    status = f'Check results before merge {s_yellow}'
else:
    status = f'This build is OK for merge {s_green}'

#markdown for comment
os.chdir(script_path)
formated = combined.drop(columns=['Batch','Time new','Time old','Threshold','Diff_tmp','Compare'])
print(formated.to_markdown('temp.md', index=False, colalign=('left','right','right','right')))

#append status to markdown
md_file = open('temp.md', 'a')
md_file.write(f'\n\n\n{status}')
md_file.close()