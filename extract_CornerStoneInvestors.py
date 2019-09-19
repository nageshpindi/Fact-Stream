import re
import copy
from stanford_ner import StanfordNLP
import pandas as pd
from directors_extract import get_directors_table

# from Extract_Bookrunners import get_page_extracts, extract_relevant_pages
other_headings = ['closing conditions', 'cornerstone investors', 'cornerstone placing', 'conditions precedent', 'corporate placing','offering, company','cornerstone investor']
invalid_list = ['the', 'mrs', 'mr']

def is_halfsentence(line_obj):
    num_sens = len(line_obj)
    if num_sens > 3:
        return False
    sen_text = ''
    for sen_obj in line_obj:
        sen_text += sen_obj['text']+' '
    for heading in other_headings:
        if heading in sen_text.lower().strip():
            return False
    num_tokens = len(sen_text.strip().split())
    if num_tokens > 9:
        return False
    return True

def is_token_present(line, next_line):
    line_text = ''
    for sen_obj in line:
        line_text += sen_obj['text'] + ' '
    line_text = line_text.strip()
    if line_text[0].isalpha() and not line_text[0].isupper():
        return False,''
    line_text_modified = line_text.lower().replace('.','')
    next_line_tokens = next_line[0]['text'].strip().lower().replace('.','').split()
    first_token = next_line_tokens[0].strip()
    if first_token in invalid_list:
        if len(next_line_tokens)>1:
            first_token += next_line_tokens[1].strip()
        elif len(next_line)>1:
            next_line_tokens = next_line[1]['text'].strip().lower().replace('.', '').split()
            first_token += next_line_tokens[0].strip()
    if first_token.replace(' ','') in line_text_modified.replace(' ',''):
        return True, line_text
    elif line_text_modified.endswith('funds') or line_text_modified.endswith('fund'):
        return True, line_text
    else:
        return False, ''

def get_investor_names(page_info):
    investors = list()
    num_lines = len(page_info)-1
    lnum = 1
    while(lnum < num_lines):
        line = page_info[lnum]
        if not is_halfsentence(line):
            lnum += 1
            continue
        next_line = page_info[lnum+1]
        if not '(' in next_line[0]['text'] and next_line[0]['text'].endswith(')') and lnum+2 < len(page_info):
            next_line = page_info[lnum+2]
        line_bottom = line[0]['bottom']
        next_line_top = next_line[0]['top']
        if next_line_top - line_bottom >= 4:
            bool, value = is_token_present(line, next_line)
            if bool:
                investors.append(value)
        lnum += 1
    return investors


def get_single_investor(page_info):
    num_lines = len(page_info)
    lnum = 1
    page_text = ''
    result = []
    while (lnum < num_lines):
        line = page_info[lnum]
        for sen_obj in line:
            page_text += sen_obj['text']+' '
        lnum += 1
    page_text = page_text.strip().replace('(','').replace(')','').replace('“','').replace('.','').replace('"','').replace('”','')
    page_text_tokens = page_text.split(' ')
    l = len(page_text_tokens)
    for idx in range(l-3):
        text = page_text_tokens[idx].lower()+page_text_tokens[idx+1].lower()+page_text_tokens[idx+2].lower()
        if 'thecornerstoneinvestor' in text:
            complete = False
            curr_idx = idx-1
            while(not complete):
                if curr_idx > 0:
                    token = page_text_tokens[curr_idx]
                    if token[0].isupper():
                        result.append(token)
                        curr_idx -= 1
                    else:
                        break
                else:
                    break
            if len(result)>0:
                investor = ''
                for token in result[::-1]:
                    investor += token+' '
                investor = investor.strip()
                if investor.lower().strip() == 'company':
                    investor = ''
                for heading in other_headings:
                    if heading in investor.lower():
                        investor = ''
                if investor  != '':
                    return [investor]
    return []


def extract_cornerstone_investors(line_obj_dict):
    investors = list()
    page_numbers = list()
    for page in line_obj_dict.keys():
        if 'cornerstone investors' in line_obj_dict[page][0][0]['text'].lower() or 'cornerstone placing' in line_obj_dict[page][0][0]['text'].lower():
            # investors.extend(get_investor_names(line_obj_dict[page]))
            result = get_investor_names(line_obj_dict[page])
            num = len(result)
            pages = [page+1]*num
            investors.extend(result)
            page_numbers.extend(pages)
        elif 'cornerstone investor' in line_obj_dict[page][0][0]['text'].lower():
            investors.extend(get_single_investor(line_obj_dict[page]))
            if len(investors) != len(page_numbers):
                page_numbers.append(page + 1)
            if len(investors) == 0:
                investors = list()
                page_numbers = list()
                investors.extend(get_investor_names(line_obj_dict[page]))
                page_numbers.append(page+1)
            else:
                break
    return investors,page_numbers


def check_word_present(word, big_word):
    w1 = word.replace(' ', '').lower()
    w2 = big_word.replace(' ', '').lower()
    if w1 in w2:
        return True
    else:
        return False

def is_number(txt):
    txt = str(txt).replace(',', '')
    try:
        float(txt)
        return True
    except:
        return False

def check_valid_page(relevant_line_obj):
    cnt = 0
    for line_obj in relevant_line_obj:
        if len(line_obj) < 2 and len(line_obj[0]['text']) > 10:
            cnt += 1
    if cnt > 5:
        return True
    else:
        return False

def get_para_objs(relevant_line_obj):
    heights = []
    for key in relevant_line_obj:
        for i in range(len(relevant_line_obj[key])-1):
            hght = relevant_line_obj[key][i + 1][0]['top'] - relevant_line_obj[key][i][0]['bottom']
            if hght > 0:
                heights.append(int(hght))
    frequent_height = max(set(heights), key=heights.count)
    had_para = False
    para_objS = []
    for key in relevant_line_obj:
        if not check_valid_page(relevant_line_obj[key]):
            break
        para_obj = {
            'text': '',
            'line_objS': []
        }
        for i in range(1, len(relevant_line_obj[key])-1):
            line_obj = relevant_line_obj[key][i]
            if len(para_obj['line_objS']) == 0:
                for sen_obj in line_obj:
                    para_obj['text'] = para_obj['text'] + ' ' + sen_obj['text']
                para_obj['line_objS'].append(line_obj)
            else:
                hght = line_obj[0]['top'] - para_obj['line_objS'][-1][0]['bottom']
                if hght > frequent_height + 1:
                    if had_para and len(para_obj['line_objS']) < 2:
                        if not check_word_present('to be published on or about 15 July', para_objS[-1]['text']):
                            return para_objS
                    para_objS.append(copy.deepcopy(para_obj))
                    para_obj = {
                        'text': '',
                        'line_objS': []
                    }
                    for sen_obj in line_obj:
                        para_obj['text'] = para_obj['text'] + ' ' + sen_obj['text']
                    para_obj['line_objS'].append(line_obj)
                else:
                    had_para = True
                    for sen_obj in line_obj:
                        para_obj['text'] = para_obj['text'] + ' ' + sen_obj['text']
                    para_obj['line_objS'].append(line_obj)
        if len(para_obj['line_objS']) > 0:
            para_objS.append(copy.deepcopy(para_obj))

    return para_objS


def entitiy_relations(sentences, txt, relations):
    # relations = []
    for sentence in sentences:
        entities = sentence['entitymentions']
        for entity in entities:
            print(entity['text'], entity['characterOffsetBegin'], entity['characterOffsetEnd'], entity['ner'])
            if entity['ner'] == 'MONEY' and \
                    check_word_present('offer price of',
                                       txt[entity['characterOffsetBegin']-20:entity['characterOffsetBegin']]):
                rel = ('Offer Price', entity['text'], entity['ner'])
                relations.append(rel)
                continue
            elif entity['ner'] == 'NUMBER':
                start = entity['characterOffsetBegin']
                for i in range(entity['characterOffsetBegin'], 0, -1):
                    if txt[i].lower() in ['.', ',', ';'] and not is_number(str(txt[i-1]).lower()):
                        start = i
                        break
                else:
                    start = 0
                end = entity['characterOffsetEnd']
                for i in range(entity['characterOffsetEnd']+1, len(txt)-1):
                    if txt[i].lower() in ['.', ',', ';'] and not is_number(str(txt[i+1]).lower()):
                        end = i
                        break
                else:
                    end = len(txt)
                if check_word_present('total', txt[start:end]) and \
                    check_word_present('shares', txt[start:end]):
                    rel = ('Total Number of Shares', entity['text'], entity['ner'])
                    relations.append(rel)
                    continue
            elif entity['ner'] == 'PERCENT':
                start = entity['characterOffsetBegin']
                for i in range(entity['characterOffsetBegin'], -1, -1):
                    if i < 4:
                        start = 0
                        break
                    elif (txt[i].lower() in ['.', ',', ';'] and not is_number(str(txt[i-1]).lower()) ) or \
                            txt[i-4:i].lower().strip() == 'and':
                        start = i
                        break
                end = entity['characterOffsetEnd']
                for i in range(entity['characterOffsetEnd']+1, len(txt)):
                    if i+4 > len(txt):
                        end = len(txt)
                        break
                    elif (txt[i].lower() in ['.', ',', ';'] and not is_number(str(txt[i-1]).lower())) or \
                            txt[i:i+4].lower().strip() == 'and':
                        end = i
                        break
                if entity['characterOffsetEnd']+1 < len(txt):
                    right_sentence = txt[entity['characterOffsetEnd'] + 1:end]
                else:
                    right_sentence = txt[entity['characterOffsetEnd']:end]
                tag = ''
                for token in right_sentence.split():
                    if token.lower().strip() in ['of', 'our', 'the']:
                        continue
                    else:
                        if '(' in token.lower().strip() or ')' in token.lower().strip():
                            break
                        tag = tag + ' ' + token
                        # if token.lower().strip() == 'shares':
                        #     break
                        # elif token.lower().strip() == 'share':
                        #     tag = tag + ' ' + 'capital'
                        #     break
                if len(tag) > 0:
                    rel = (tag, entity['text'], entity['ner'])
                    relations.append(rel)
            elif entity['ner'] == 'MISC':
                start = entity['characterOffsetBegin']
                for i in range(entity['characterOffsetBegin'], -1, -1):
                    if i < 4:
                        start = 0
                        break
                    elif txt[i].lower() in ['.', ',', ';'] or txt[i-4:i].lower().strip() == 'and':
                        start = i
                        break
                end = entity['characterOffsetEnd']
                for i in range(entity['characterOffsetEnd']+1, len(txt)):
                    if i+4 > len(txt):
                        end = len(txt)
                        break
                    elif txt[i].lower() in ['.', ',', ';'] or txt[i:i+4].lower().strip() == 'and':
                        end = i
                        break
                if entity['characterOffsetEnd']+1 < len(txt):
                    right_sentence = txt[entity['characterOffsetEnd'] + 1:end]
                else:
                    right_sentence = txt[entity['characterOffsetEnd']:end]
                if check_word_present('over-allotment', entity['text']):
                    if check_word_present('not exercised', right_sentence):
                        rel = ('Over-allotment Option is not exercised', entity['text'], entity['ner'])
                        relations.append(rel)
                    else:
                        rel = ('Over-allotment Option is exercised', entity['text'], entity['ner'])
                        relations.append(rel)
    return relations


def extract_cornerstone_shares(relevant_line_obj):
    if len(relevant_line_obj) == 0:
        return pd.DataFrame()
    para_objS = get_para_objs(relevant_line_obj)
    relations = []
    is_bottom_end_present = False
    for para_obj in para_objS:
        sNLP = StanfordNLP()
        # text = "Assuming the Offer Price of HK$2.48 (being the low-end of the Offer Price range set out in this Prospectus), the total aggregate number of Shares to be subscribed for by the Cornerstone Investor will be 84,204,000 Shares (rounded down to the nearest whole board lot), representing approximately 33.68% of the Offer Shares and approximately 8.42% of the Shares in issue immediately upon completion of the Global Offering, assuming the Over-allotment Option is not exercised, no options are granted under thePost-IPO Share Option Scheme and no shares are granted under the Share Award Scheme."
        # txt = re.sub(' *\([^)]*\) *', '', para_obj['text'])
        txt = para_obj['text']
        if check_word_present('Gaoling Fund, L.P. and YHG Investment, L.P.,', txt) or \
                check_word_present('Boyu Capital Opportunities Master Fund,', txt):
            continue
        ANNOTATE = sNLP.annotate(txt)
        sentences = ANNOTATE['sentences']
        if check_word_present('bottom end', txt):
            is_bottom_end_present = True
        relations = entitiy_relations(sentences, txt, relations)
        # if len(relations) > 0:
        #     relations_arr.append(relations)
        print(relations)
    print(relations)
    if len(relations) == 0:
        return pd.DataFrame()
    res_dic = {}
    ct = 0
    offer_prices = []
    total_shares = []
    prec_dic = {}
    for rel in relations:
        if rel[0] == 'Offer Price':
            ct += 1
            offer_prices.append(rel[1])
        elif rel[0] == 'Total Number of Shares':
            try:
                te_word = rel[1].replace(',', '')
                num = int(te_word)
                if num > 10000:
                    total_shares.append(rel[1])
            except:
                pass
        elif rel[2] == 'PERCENT':
            if rel[0] in prec_dic:
                prec_dic[rel[0]].append(rel[1])
            else:
                prec_dic[rel[0]] = [rel[1]]
        elif rel[2] == 'MISC':
            dic_keys = list(prec_dic.keys())
            for key in dic_keys:
                if len(key.split('\n')) < 2:
                    if str(rel[0]) + '\n' + str(key) in prec_dic:
                        prec_dic[str(rel[0]) + '\n' + str(key)].append(prec_dic[key][0])
                    else:
                        prec_dic[str(rel[0]) + '\n' + str(key)] = prec_dic[key]
                    prec_dic.pop(key)
    if ct >= 3:
        #
        # # ignoring bottom end offer price
        # if is_bottom_end_present:
        #     if ct > 3:
        #         offer_prices = offer_prices[1:4]
        #     if len(total_shares) > 3:
        #         total_shares = total_shares[1:4]
        #     sorted_keys = list(prec_dic.keys())
        #     sorted_keys.sort()
        #     for key in sorted_keys:
        #         if len(prec_dic[key]) > 3:
        #             prec_dic[key]
        #         for _ in range(, 3):
        #             prec_dic[key].append(prec_dic[key][0])

        if offer_prices[0] < offer_prices[2]:
            res_dic['point'] = ['Low-end price', 'Mid-point price', 'High-end price']
        else:
            res_dic['point'] = ['High-end price', 'Mid-point price', 'Low-end price']
        res_dic['Offer Price'] = offer_prices[0:3]
        if len(total_shares) > 0:
            for _ in range(len(total_shares), 3):
                total_shares.append(total_shares[0])
            res_dic['Total Number Shares'] = total_shares[0:3]
        sorted_keys = list(prec_dic.keys())
        sorted_keys.sort()
        for key in sorted_keys:
            for _ in range(len(prec_dic[key]), 3):
                prec_dic[key].append(prec_dic[key][0])
            res_dic[key] = prec_dic[key][0:3]
        res_dic['PageNumber'] = [list(relevant_line_obj.keys())[0]+1 for _ in range(3)]
    else:
        res_dic['point'] = ['Mid-point price']
        if len(offer_prices) > 0:
            res_dic['Offer Price'] = offer_prices[0]
        if len(total_shares) > 0:
            res_dic['Total Number Shares'] = total_shares[0]
        for key in prec_dic:
            res_dic[key] = prec_dic[key]
        res_dic['PageNumber'] = [list(relevant_line_obj.keys())[0]+1]
    res_df = pd.DataFrame(res_dic)
    return res_df


def get_cornerstone_investors_from_table(arr_objs,baseDataDirectory,relevant_pages):
    investors = list()
    list_dfs = get_directors_table(arr_objs,baseDataDirectory,relevant_pages)
    return investors

def modify_investor_names(result, result_from_table):
    final_result = list()
    return final_result


















