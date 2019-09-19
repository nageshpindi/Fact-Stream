from intervaltree import IntervalTree, Interval
import pandas as pd
import os
import re
import copy
from trie_gazetteer import gazetteer


months = ['Dec', 'December', 'Nov', 'November', 'Oct', 'October', 'Sept', 'September', 'Aug', 'August', 'Jul', 'July', 'Jun', 'June', 'Apr', 'April', 'May', 'Mar', 'March', 'Feb', 'Febraury', 'Jan', 'January']
yrs = ['2019', '2016', '2017', '2018', '2015', '2014', '2013', '2012', '2011', '2020', '2021', '2022', '2023', '2010', '2024', '2025']


def get_table_start(line_objs):
   symbols_to_remove = ['%', '$', 'HK$', ',']
   table_start = -1
   for i in range(len(line_objs)):
       line_obj = line_objs[i]
       # if len(line_obj) >= 1 and line_obj[0]['underline_exists']:
       #     return i+1
       # if i > 6:
       #     if len(line_objs[1]) > 1:
       #         return 1
       if len(line_objs[i]) >= 3:
           for sen_obj in line_objs[i]:
               try:
                   txt = str(sen_obj['text']).strip().lower()
                   for sym in symbols_to_remove:
                       txt = txt.replace(str(sym).lower(), '')
                   num = float(txt.strip())
                   if num > 1.0 and num < 100.0:
                       return i
               except:
                   continue
   return table_start


duration=['year','month','day']
class headers():
    def __init__(self,baseDataDirectory,months,yrs):
        self.yrs=yrs
        self.months=months
        self.unit=gazetteer(os.path.join(baseDataDirectory, 'unit.txt'),False,False,False)

    def extractDuration(durationList, months, yrs):
        date_range = list()
        date_dict = dict()
        for line in durationList:
            tokens = str(line).split(' ')
            monthcount = 0
            yearcount = 0
            datecount = 0
            for index, token in enumerate(tokens):
                for durat in duration:
                    if durat in token:
                        date_dict['duration'] = tokens[index - 1] + ' ' + token
                if len(token) > 1:
                    for mon in months:
                        if mon.strip().lower() in token.lower() and len(token) - len(mon.strip()) < 2:
                            if 'month' in date_dict:
                                lst = date_dict['month']
                                lst.append(token.lower())
                            else:
                                lst = list()
                                lst.append(token.lower())
                                date_dict['month'] = lst
                            date_range.append(token + ' month')
                            monthcount = monthcount + 1
                    for yr in yrs:
                        if token == yr.strip() or yr.strip() in token:
                            if 'year' in date_dict:
                                lst = date_dict['year']
                                lst.append(token)
                            else:
                                lst = list()
                                lst.append(token)
                                date_dict['year'] = lst
                            date_range.append(token + ' year')
                            yearcount = yearcount + 1
                    if re.match("\d{1,2}[.\-\/]\d{1,2}[.\-\/]\d{2,4}", token):
                        if 'date' in date_dict:
                            lst = date_dict['date']
                            lst.append(token)
                        else:
                            lst = [token]
                            date_dict['date'] = lst
                        datecount += 1
            if monthcount + yearcount + datecount >= 3:
                break
        return (date_dict)

    def IsHeader(self, token_splits):
        spl_characters = ['%', '$', '€']
        ln_list = 0
        len_list = 0
        for token in token_splits:
            found = False
            if len(token['text'].strip()) > 0:
                len_list = len_list + 1

            for ch in token['text']:
                if ch.isalpha() or ch in spl_characters:
                    ln_list = ln_list + 1
                    found = True
                    break
            if not found:
                if self.constainsPeriod(token['text'], self.months, self.yrs):
                    ln_list = ln_list + 1
                    found = True
        if ln_list == len_list:
            return True
        else:
            return False

    def checkRegex(self,text):
        txt=re.findall('\(([^)]+)', text)
        if len(txt)==0:
            return False
        val=str(text).replace(txt[0],'').replace('(','').replace(')','')
        unitPresent=self.unitCheck(txt[0])
        if len(val.strip())>0:
            return False
        else:
            if unitPresent:
                return True
            else:
                return False



    def constainsPeriod(self,token,months,yrs):
        if len(self.extractDuration([token], months, yrs)) > 0:
            return True
        else:
            return False

    def unitCheck(self, txt):
        unitValues = self.unit.findPhrases(txt)
        if len(unitValues) > 0:
            return True
        else:
            return False

    def isHalfSentance(self, line):
        isHsen = False
        if (line.endswith(':')):
            return True
        if 'earnings per share'.lower() in line.lower() or (('common stock'.lower() in line.lower() or 'preferred stock' in line.lower()) and 'authorized' in line.lower()) \
                or 'affiliates' in line.lower():
            return True
        # tokens = line.split()
        # if (len(tokens) <= 12):
        #     isHsen = True
        return isHsen

    def  isStringHeader(self,line):
        # return False
        lstTokens = re.compile('\s{2,}').split(line)

        strCount = 0
        numCount = 0
        if len(lstTokens) == 1:
            return False
        for i, val in enumerate(lstTokens):
            dict_duration = self.extractDuration([val], self.months, self.yrs)
            if self.isNumber(val):
                if ('year' not in dict_duration) and '606' not in str(val):
                    numCount = numCount + 1
                else:
                    strCount = strCount + 1
            elif 'Not ' in str(val) or 'years' in str(val).lower() or 'indefinite-lived' in str(
                    val).lower() or 'ASC 606' in str(val) or 'nil' in str(val).lower():
                numCount = numCount + 1
            else:
                strCount = strCount + 1

        if strCount >= 2 and numCount == 0:
            return True
        return False

    def extractDuration(self,durationList, months, yrs):
        date_range = list()
        date_dict = dict()
        for line in durationList:
            tokens = str(line).split(' ')
            monthcount = 0
            yearcount = 0
            for index, token in enumerate(tokens):
                for durat in duration:
                    if durat in token:
                        date_dict['duration'] = tokens[index - 1] + ' ' + token
                if len(token) > 1:
                    for mon in months:
                        if mon.strip().lower() in token.lower() and len(token) - len(mon.strip()) < 2:
                            if 'month' in date_dict:
                                lst = date_dict['month']
                                lst.append(token.lower())
                            else:
                                lst = list()
                                lst.append(token.lower())
                                date_dict['month'] = lst
                            date_range.append(token + ' month')
                            monthcount = monthcount + 1
                    for yr in yrs:
                        if token == yr.strip() or yr.strip() in token:
                            if 'year' in date_dict:
                                lst = date_dict['year']
                                lst.append(token)
                            else:
                                lst = list()
                                lst.append(token)
                                date_dict['year'] = lst
                            date_range.append(token + ' year')
                            yearcount = yearcount + 1
            if monthcount + yearcount >= 3:
                break
        return (date_dict)

    def isNumber(self,num_val):
        val = False

        if num_val is None or pd.isnull(num_val) or len(num_val.strip()) == 0:
            return False

        num_val = num_val.replace(',', '').replace('$', '').replace('.', '').replace(')', '').replace('(', '') \
            .replace(' ', '').replace('%', '').replace('–', '')
        try:
            float(num_val)
            val = True
        except:
            if num_val == '-' or num_val == '–' or num_val == '—' or \
                    num_val == '$' or num_val == 'nm':
                val = True
            elif len(num_val.strip()) == 0:
                val = True
            else:
                if self.isRomanNumeral(num_val):
                    val = True
                # else:
                #     print('cant convert '+num_val)
        return val

    def value(self,r):
        if (r == 'I'):
            return 1
        if (r == 'V'):
            return 5
        if (r == 'X'):
            return 10
        if (r == 'L'):
            return 50
        if (r == 'C'):
            return 100
        if (r == 'D'):
            return 500
        if (r == 'M'):
            return 1000
        return -1

    def isRomanNumeral(self,str):
        res = 0

        if 'I.' in str or 'V.' in str or 'X.' in str:
            # return False
            i = 0
            str = str.replace('.', '')

            while (i < len(str)):

                # Getting value of symbol s[i]
                s1 = self.value(str[i])

                if (i + 1 < len(str)):

                    # Getting value of symbol s[i+1]
                    s2 = self.value(str[i + 1])

                    # Comparing both values
                    if (s1 >= s2):

                        # Value of current symbol is greater
                        # or equal to the next symbol
                        res = res + s1
                        i = i + 1
                    else:

                        # Value of current symbol is greater
                        # or equal to the next symbol
                        res = res + s2 - s1
                        i = i + 2
                else:
                    res = res + s1
                    i = i + 1

        if res != 0:
            return True

        return False


def reprocessForColHeader(lst,months,yrs,firstRow, df_columns_len,baseDataDirectory):
    mainTree = IntervalTree()
    mainList = list()
    # baseDataDirectory = '/home/swaroop/Documents/Projects/SFC_extraction/Data'
    hd=headers(baseDataDirectory,months,yrs)
    count=0

    reversed_list = []

    if lst is not None and len(lst) > 0:
        reversed_list = lst[::-1]
        # tree_start = IntervalTree()

        # removing extra lines from df starting line.
        while True:
            if len(reversed_list) <= 0:
                break
            firstLine = reversed_list.pop(0)
            reference = firstLine[0]['x1']
            line = ''
            for sen_obj in firstLine:
                line = line + sen_obj['text'] + '  '
            cnt = 0
            for val in firstRow:
                if str(val).replace(' ', '').lower() in line.replace(' ', '').lower():
                    cnt += 1
            if cnt == len(firstRow) or cnt >= 3:
                # for sen_obj in firstLine:
                #     tree_start.add(Interval(sen_obj['x0'], sen_obj['x1'], sen_obj))
                break

        cols_start_y = 0
        for line_obj in reversed_list:
            if line_obj[0]['text'].lower().replace(' ', '') == 'Table of Contents'.lower().replace(' ', ''):
                break
            if len(line_obj) == 0:
                continue
            line = ''
            for sen_obj in line_obj:
                line = line + sen_obj['text'] + '  '
            if len(mainTree) == 0:
                if (not hd.checkRegex(line) and (
                        hd.IsHeader(line_obj) or hd.isStringHeader(line)) and not hd.isHalfSentance(line)):
                    for sen_obj in line_obj:
                        if len(line_obj) == 1:
                            if sen_obj['x0'] < reference:
                                count = count + 1
                                if count >= 2:
                                    sTree = sorted(mainTree)
                                    for tr in sTree:
                                        # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
                                        mainList.append(tr.data['text'])
                                    # print(mainList)
                                    return mainList, len(reversed_list)
                                continue
                        # if len(sen_obj['text'].strip()) > 0 and sen_obj['underline_exists']:
                        if len(sen_obj['text'].strip()) > 0:
                            cols_start_y = sen_obj['top']
                            mainTree.add(Interval(sen_obj['x0_or'], sen_obj['x1_or'], sen_obj))
            elif line_obj[0]['x0'] > reference or True:
                if not (hd.checkRegex(line)):
                    for sen_obj in line_obj:
                        if sen_obj['x0'] > 0 and len(sen_obj['text'].strip()) > 0 and \
                                len(sen_obj['text'].strip().split()) < 10:
                            overlapInt = mainTree.overlap(sen_obj['x0'], sen_obj['x1'])
                            dataToAppend = ''
                            if len(overlapInt) > 0:
                                for overLap in overlapInt:
                                    dataToAppend = overLap
                                    if float(dataToAppend.data['top']) - float(sen_obj['bottom']) <= 7 or sen_obj['underline_exists']:
                                        if sen_obj['underline_exists']:
                                            # sen_obj_te = copy.deepcopy(sen_obj)
                                            # sen_obj_te['text'] = sen_obj_te['text'] + '\n' + str(dataToAppend.data['text'])
                                            prev_sen_obj = copy.deepcopy(dataToAppend.data)
                                            prev_sen_obj['text'] = sen_obj['text'] + '\n' + str(prev_sen_obj['text'])
                                            prev_sen_obj['top'] = sen_obj['top']
                                            prev_sen_obj['bottom'] = sen_obj['bottom']
                                            mainTree.remove(dataToAppend)
                                            mainTree.add(Interval(sen_obj['x0_or'], sen_obj['x1_or'], prev_sen_obj))
                                        else:
                                            previous_starts = set([overLap.begin for overLap in overlapInt])
                                            previous_ends = set([overLap.end for overLap in overlapInt])
                                            if len(overlapInt) == 1 or (len(previous_starts) == 1 and
                                                                        len(previous_ends) == 1):
                                                # sen_obj_te = copy.deepcopy(sen_obj)
                                                # sen_obj_te['text'] = sen_obj_te['text'] + '\n' + str(
                                                #     dataToAppend.data['text'])
                                                prev_sen_obj = copy.deepcopy(dataToAppend.data)
                                                prev_sen_obj['text'] = sen_obj['text'] + '\n' + str(
                                                    prev_sen_obj['text'])
                                                prev_sen_obj['top'] = sen_obj['top']
                                                prev_sen_obj['bottom'] = sen_obj['bottom']
                                                mainTree.remove(dataToAppend)
                                                mainTree.add(Interval(sen_obj['x0_or'], sen_obj['x1_or'], prev_sen_obj))
                                            else:
                                                if len(set([overLap.begin for overLap in overlapInt])) == 1 and \
                                                        len(set([overLap.end for overLap in overlapInt])) == 1:
                                                    # sen_obj_te = copy.deepcopy(sen_obj)
                                                    # sen_obj_te['text'] = sen_obj_te['text'] + '\n' + str(
                                                    #     dataToAppend.data['text'])
                                                    prev_sen_obj = copy.deepcopy(dataToAppend.data)
                                                    prev_sen_obj['text'] = sen_obj['text'] + '\n' + str(
                                                        prev_sen_obj['text'])
                                                    prev_sen_obj['top'] = sen_obj['top']
                                                    prev_sen_obj['bottom'] = sen_obj['bottom']
                                                    prev_sen_obj['bottom'] = sen_obj['bottom']
                                                    mainTree.remove(dataToAppend)
                                                    mainTree.add(Interval(sen_obj['x0_or'], sen_obj['x1_or'], prev_sen_obj))
                                                else:
                                                    count = count + 1
                                                    if count >= 1:
                                                        for tr in mainTree:
                                                            dataToAppend = tr
                                                            mainTree.remove(dataToAppend)
                                                            mainTree.add(
                                                                Interval(dataToAppend.data['x0'], dataToAppend.data['x1'], dataToAppend.data))
                                                        sTree = sorted(mainTree)
                                                        for tr in sTree:
                                                            # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
                                                            mainList.append(tr.data['text'])
                                                        # print(mainList)
                                                        return mainList, len(reversed_list)
                                    else:
                                        count = count + 1
                                        if count >= 1:
                                            for tr in mainTree:
                                                dataToAppend = tr
                                                mainTree.remove(dataToAppend)
                                                mainTree.add(
                                                    Interval(dataToAppend.data['x0'], dataToAppend.data['x1'],
                                                             dataToAppend.data))
                                            sTree = sorted(mainTree)
                                            for tr in sTree:
                                                # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
                                                mainList.append(tr.data['text'])
                                            # print(mainList)
                                            return mainList, len(reversed_list)
                            else:
                                if len(mainTree) < df_columns_len and ( sen_obj['x0'] >= reference or
                                                                        len(line_obj) > 1) and \
                                        (cols_start_y - sen_obj['bottom'] <= 7):
                                    mainTree.add(Interval(sen_obj['x0_or'], sen_obj['x1_or'], sen_obj))
                                else:
                                    count = count + 1
                                    if count >= 1:
                                        for tr in mainTree:
                                            dataToAppend = tr
                                            mainTree.remove(dataToAppend)
                                            mainTree.add(
                                                Interval(dataToAppend.data['x0'], dataToAppend.data['x1'],
                                                         dataToAppend.data))
                                        sTree = sorted(mainTree)
                                        for tr in sTree:
                                            # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
                                            mainList.append(tr.data['text'])
                                        # print(mainList)
                                        return mainList, len(reversed_list)

                else:
                    if (len(mainTree) > 0) and (line_obj[0]['text'].isupper() or hd.checkRegex(line)):
                        break
            else:
                if (len(mainTree) > 0):
                    count=count+1
                    if count>=1:
                        break
            sorted(mainTree)
        else:
            if len(mainTree) > 0:
                for tr in mainTree:
                    dataToAppend = tr
                    mainTree.remove(dataToAppend)
                    mainTree.add(
                        Interval(dataToAppend.data['x0'], dataToAppend.data['x1'], dataToAppend.data))
                sTree = sorted(mainTree)
                for tr in sTree:
                    # '\n'.join(str(tr.data).split('\n')[::-1])
                    # mainList.append(tr.data)
                    # mainList.append('\n'.join(str(tr.data).split('\n')[::-1]))
                    mainList.append(tr.data['text'])
                return mainList, len(reversed_list)
    for tr in mainTree:
        dataToAppend = tr
        mainTree.remove(dataToAppend)
        mainTree.add(
            Interval(dataToAppend.data['x0'], dataToAppend.data['x1'], dataToAppend.data))
    sTree = sorted(mainTree)
    for tr in sTree:
        # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
        mainList.append(tr.data['text'])
    # print(mainList)
    return mainList, len(reversed_list)


def getcolHeaders(df_startLineNum, dataFrame, line_objs,baseDataDirectory):
    lst_full = line_objs
    lst = lst_full[1: df_startLineNum+1]
    if lst is not None and len(lst) > 0:
        firstRow = []
        for val in list(dataFrame.iloc[0]):
            if len(str(val)) > 0 and str(val) != 'nan':
                firstRow.append(val)
        lstColHeaders, table_start_bbox = reprocessForColHeader(lst, months, yrs, firstRow, dataFrame.shape[1],baseDataDirectory)
        return lstColHeaders
    else:
        return None


def getFirstTable(line_objs,baseDataDirectory):
    symbols_to_ignore = ['$', '%', '(', ')', '((', '))', '()']
    mainTree = IntervalTree()
    mainList = list()
    table_start_bbox = get_table_start(line_objs)
    if table_start_bbox == -1:
        return None
    table_end_bbox = -1
    lst = line_objs[table_start_bbox: table_end_bbox]
    lines_com_len = 0
    if lst is not None and len(lst) > 0:
        for line_obj in lst:
            if len(mainTree) == 0:
                for sen_obj in line_obj:
                    if sen_obj['text'].replace(' ', '').lower() in symbols_to_ignore:
                        continue
                    if len(sen_obj['text'].strip()) > 0:
                        if sen_obj['underline_exists']:
                            x0 = sen_obj['x0_or']
                            x1 = sen_obj['x1_or']
                        else:
                            x0 = sen_obj['x0']
                            x1 = sen_obj['x1']
                        if len(sen_obj['text'].strip()) == 1:
                            x0 = x0 - 3
                            x1 = x1 - 3
                        if len(sen_obj['text'].strip()) == 2:
                            x0 = x0 - 3
                        mainTree.add(Interval(x0, x1, [sen_obj['text']]))
                lines_com_len += 1
            else:
                if len(line_obj[-1]['text'].replace('.', '').split()) > 10:
                    break
                for sen_obj in line_obj:
                    if sen_obj['text'].replace(' ', '').lower() in symbols_to_ignore:
                        continue
                    if sen_obj['underline_exists']:
                        x0 = sen_obj['x0_or']
                        x1 = sen_obj['x1_or']
                    else:
                        x0 = sen_obj['x0']
                        x1 = sen_obj['x1']
                    if len(sen_obj['text'].strip()) == 1:
                        x0 = x0 - 3
                        x1 = x1 - 3
                    if len(sen_obj['text'].strip()) == 2:
                        x0 = x0 - 3
                    overlapInt = mainTree.overlap(x0, x1)
                    if len(overlapInt) > 0:
                        if len(overlapInt) == 1:
                            first_col_start = min([overlap.begin for overlap in overlapInt])
                            for overlap in overlapInt:
                                if overlap.begin != first_col_start:
                                    continue
                                dataToAppend = overlap
                                te_arr = dataToAppend.data
                                for k in range(len(te_arr), lines_com_len):
                                    te_arr.append(float('NaN'))
                                te_arr.append(sen_obj['text'])
                                mainTree.remove(dataToAppend)
                                if overlap > 1:
                                    mainTree.add(Interval(dataToAppend.begin, dataToAppend.end, te_arr))
                                else:
                                    mainTree.add(Interval(min(x0, dataToAppend.begin),
                                                          max(x1, dataToAppend.end), te_arr))
                                break
                    else:
                        te_arr = []
                        for k in range(len(te_arr), lines_com_len):
                            te_arr.append(float('NaN'))
                        te_arr.append(sen_obj['text'])
                        if len(sen_obj['text'].strip()) == 1:
                            x0 = x0 - 3
                            x1 = x1 - 3
                        if len(sen_obj['text'].strip()) == 2:
                            x0 = x0 - 3
                        mainTree.add(Interval(x0, x1, te_arr))
                lines_com_len += 1
    sTree = sorted(mainTree)
    rows_to_drop = []
    max_len = max([len(tr.data) for tr in sTree])
    for tr in sTree:
        # mainList.append('\n'.join(str(tr.data).split('\n')[::-1])
        te_lst = tr.data
        for i in range(len(te_lst), max_len):
            te_lst.append(float('NaN'))
        mainList.append(te_lst)

    final_df = pd.DataFrame(mainList).T
    last_row = final_df.iloc[final_df.shape[0]-1].to_list()
    if 'note' in str(last_row[0]).replace(' ','').lower() or \
            'directors' in str(last_row[0]).replace(' ','').lower():
        final_df = final_df.drop([final_df.shape[0]-1], axis=0)
    lstColHeaders = getcolHeaders(table_start_bbox, final_df, line_objs,baseDataDirectory)
    if lstColHeaders is not None:
        # print(lstColHeaders, list(dataFrame.columns), len(lstColHeaders), len(list(dataFrame.columns)))

        if len(lstColHeaders) == len(final_df.columns):
            for index, colld in enumerate(lstColHeaders):
                final_df = final_df.rename(columns={final_df.columns[index]: str(colld)})
        elif len(lstColHeaders) == len(final_df.columns) - 1:
            for index, colld in enumerate(lstColHeaders):
                final_df = final_df.rename(columns={final_df.columns[index + 1]: str(colld)})

    return final_df
