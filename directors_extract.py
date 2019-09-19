import os
import re
import pandas as pd
from tableExtraction import getFirstTable

def check_word_match(word1, word2):
    word1 = str(word1)
    word2 = str(word2)
    if len(word1.split()) > 1 or len(word2.split()) > 1:
        word1 = re.sub("\(\w\)", '', word1)
        word2 = re.sub("\(\w\)", '', word2)
    word1 = str(word1).replace('$', '').replace(' ', '').replace('.', '').lower()
    word2 = str(word2).replace('$', '').replace(' ', '').replace('.', '').lower()
    if word1 == word2:
        return True
    else:
        return False

def get_directors_table(lst_line_objs,baseDataDirectory, pnums):
    lst_dfs = []
    for i, line_objs in enumerate(lst_line_objs):
        df = getFirstTable(line_objs, baseDataDirectory)
        te_bl = True
        if df is not None:
            df['PageNum'] = [pnums[i]+1 for _ in range(df.shape[0])]
            if len(lst_dfs) > 0 and len(lst_dfs[0].columns) == len(df.columns):
                for i in range(len(lst_dfs[0].columns)):
                    if len(str(df.columns[i])) == 1:
                        continue
                    if not check_word_match(lst_dfs[0].columns[i], df.columns[i]):
                        te_bl = False
                        break
            else:
                te_bl = False
                if len(lst_dfs) == 0:
                    lst_dfs.append(df)
                    continue
            if te_bl:
                df.columns = lst_dfs[0].columns
                lst_dfs[0] = pd.concat([lst_dfs[0], df], axis=0)

    if len(lst_dfs) > 0 and lst_dfs[0] is not None:
        nan_row = [[float('NaN') for i in range(len(lst_dfs[0].columns))]]
        first_col = lst_dfs[0].iloc[:,0].to_list()
        result_df = pd.DataFrame(columns=lst_dfs[0].columns)
        prev = 0
        for i in range(1, len(first_col)):
            if str(first_col[i-1]) == 'nan' and str(first_col[i]) != 'nan':
                result_df = pd.concat([result_df, lst_dfs[0].iloc[prev:i]], axis=0)
                nan_row[0][-1] = result_df['PageNum'].to_list()[-1]
                nan_df = pd.DataFrame(nan_row, columns=lst_dfs[0].columns)
                result_df = pd.concat([result_df, nan_df], axis=0)
                prev = i
        te_df = lst_dfs[0].iloc[prev:]
        if 'note' not in str(te_df.iloc[:,0].to_list()[0]).lower():
            result_df = pd.concat([result_df, te_df], axis=0)
        return result_df
    else:
        return pd.DataFrame()



