import pandas as pd
import numpy as np
from statistics import mode
# import pdfplumber
# bounding_box_vertical_padding = 2.5
# horizontal_space_dis = 6.5
#
#
# def is_intersecting(curr_top, curr_bottom, prev_top, prev_bottom):
#     if curr_top >= prev_top and curr_top <= prev_bottom:
#         return True
#     if prev_top >= curr_top and prev_top <= curr_bottom:
#         return True
#     return False
#
# def get_line_objs(page_extracts):
#     curr_line = list()
#     lines = []
#     i = 0
#     prev_stop = 0
#     for index, extract in enumerate(page_extracts):
#         if index is 0:
#             prev_top = float(-1)
#             prev_bottom = float(-1)
#         else:
#             prev_top = float(page_extracts[index-1]['top'])
#             prev_bottom = float(page_extracts[index-1]['bottom'])
#         curr_top = float(page_extracts[index]['top'])
#         curr_bottom = float(page_extracts[index]['bottom'])
#
#         lines_intersection_bool = is_intersecting(curr_top+bounding_box_vertical_padding,
#                                                   curr_bottom-bounding_box_vertical_padding,
#                                                   prev_top+bounding_box_vertical_padding,
#                                                   prev_bottom-bounding_box_vertical_padding)
#
#         if (curr_top == prev_top and curr_bottom == prev_bottom) or lines_intersection_bool: #same line add to list
#             if len(lines[i-1]) > 0:
#                 for k in range(len(lines[i-1])):
#                     if abs(float(extract['x0']) - float(lines[i-1][k]['x1'])) < horizontal_space_dis:
#                         if extract['x1'] > lines[i-1][k]['x1']:
#                             lines[i-1][k]['x1'] = extract['x1']
#                         if extract['x0'] < lines[i-1][k]['x0']:
#                             lines[i-1][k]['x0'] = extract['x0']
#                         lines[i-1][k]['text'] = lines[i-1][k]['text'] + ' ' + extract['text']
#                         break
#                     if abs(float(extract['x1']) - float(lines[i-1][k]['x0'])) < horizontal_space_dis:
#                         if extract['x1'] > lines[i-1][k]['x1']:
#                             lines[i-1][k]['x1'] = extract['x1']
#                         if extract['x0'] < lines[i-1][k]['x0']:
#                             lines[i-1][k]['x0'] = extract['x0']
#                         if extract['bottom'] > lines[i-1][k]['bottom']:
#                             lines[i-1][k]['bottom'] = extract['bottom']
#                         lines[i-1][k]['text'] = extract['text'] + ' ' + lines[i-1][k]['text']
#                         break
#                 else:
#                     lines[i-1].append(extract)
#             else:
#                 lines[i-1].append(extract)
#             continue
#         elif (prev_top < prev_bottom and prev_bottom < curr_top and curr_top < curr_bottom) and not lines_intersection_bool: #new line
#             lines.append([extract])
#             i += 1
#             continue
#         else:
#             if ((curr_top - prev_top) > (prev_bottom - curr_top) or abs(curr_top - prev_top) <= 2 ) and not lines_intersection_bool: #new line
#                 lines.append([extract])
#                 i += 1
#                 continue
#     # line_objs_dict[pnum] = lines
#     return lines
#
#
# def get_page_extracts(path):
#     page_extract_dict = dict()
#     line_obj_dict = dict()
#     with pdfplumber.open(path, password='') as pdf:
#         for index, page in enumerate(pdf.pages):
#             page_extracts = page.extract_words(x_tolerance=1, y_tolerance=1)
#             page_extract_dict[index] =page_extracts
#             line_obj_dict[index] = get_line_objs(page_extracts)
#             if index > 253 and index < 259:
#                 page_extracts = page.extract_words(x_tolerance=1, y_tolerance=1)
#                 page_extract_dict[index] =page_extracts
#                 line_obj_dict[index] = get_line_objs(page_extracts)
#             elif index > 258:
#                 break
#     return page_extract_dict, line_obj_dict


def extract_relevant_pages(line_obj_dict, title1, title2):
    # title1 = 'DIRECTORS AND PARTIES INVOLVED IN THE GLOBAL OFFERING'
    # title2 = 'DIRECTORS, SUPERVISORS AND PARTIES INVOLVED IN THE GLOBAL OFFERING'
    pages_matched = dict()
    found = False
    for page_num in line_obj_dict.keys():
        try:
            page_title = line_obj_dict[page_num][0][0]['text'].strip()
        except Exception as e:
            print('exception occured while processing pagenum:',page_num)
            continue
        if title1.strip() in page_title or title2.strip() in page_title:
              found = True
              pages_matched[page_num] = line_obj_dict[page_num]
        else:
            if found:
                return pages_matched
    return pages_matched


def has_token_info(lines, text_tobe_searched):
    for linenum, line in enumerate(lines):
        first_token = line[0]['text'].strip()
        if text_tobe_searched.lower() in  first_token.lower():
            if line[0]['x0'] < 250:
                return (True, linenum)
    return False, -1


def get_value_object(line_objects, pnum, lnum, relevance, token_lnums,threshold):
    result = list()
    end_of_object = False
    prev_bottom = None
    while (not end_of_object):
        if lnum == 0:
            lnum += 1
        elif lnum >= len(line_objects[pnum])-1:
            return result,False,0,[]
        if lnum in token_lnums:
            index = 1
            # has_token = False
        else:
            index = 0
        if pnum not in line_objects.keys():
            return result,True,lnum,[]
        try:
            sub_object = line_objects[pnum][lnum][index]
        except:
            print('n')
        if index != 1 and sub_object['x0'] < relevance:
             return result,True,lnum,[]
        if prev_bottom is not None:
            if (sub_object['top'] - prev_bottom >= threshold):
                return result,False,lnum,[]
        result.append(sub_object['text'])
        prev_bottom = sub_object['bottom']
        lnum = lnum+1


def has_end(value):
    end_tokens = ['limited', 'l.l.c.', 'plc', 'branch']
    for token in end_tokens:
        if value.lower().strip().endswith(token):
            return True
    return False

def is_intersecting(curr_left,curr_right,prev_left,prev_right):
    if prev_left <= curr_left and curr_left < prev_right and prev_right <= curr_right:
        return True
    elif prev_left <= curr_left and curr_right <= prev_right:
        return True
    elif curr_left < prev_left and prev_right < curr_right:
        return True
    elif curr_left <= prev_left and prev_left < curr_right and curr_right <= prev_right:
        return True
    return False

def get_first_line(lines,lnum):
    lnums_with_token = [lnum]
    curr_lnum = lnum
    first_lnum = lnum
    # going up
    while(True):
        curr_line = lines[curr_lnum][0]
        curr_left = curr_line['x0']
        curr_right = curr_line['x1']
        if curr_lnum-1 > 0:
            prev_line = lines[curr_lnum-1][0]
            prev_left = prev_line['x0']
            prev_right = prev_line['x1']
            if is_intersecting(curr_left,curr_right,prev_left,prev_right):
                if curr_line['top'] - prev_line['bottom'] < 7:
                    lnums_with_token.append(curr_lnum-1)
                    curr_lnum = curr_lnum-1
                else:
                    break
            else:
                break
        else:
            break
    first_lnum = lnums_with_token[-1]
    # going down
    prev_lnum = lnum
    while (True):
        prev_line = lines[prev_lnum][0]
        prev_left = prev_line['x0']
        prev_right = prev_line['x1']
        if prev_lnum + 1 < len(lines):
            curr_line = lines[prev_lnum+1][0]
            curr_left = curr_line['x0']
            curr_right = curr_line['x1']
            if is_intersecting(curr_left, curr_right, prev_left, prev_right):
                if curr_line['top'] - prev_line['bottom'] < 7:
                    lnums_with_token.append(prev_lnum+1)
                    prev_lnum = prev_lnum + 1
                else:
                    break
            else:
                break
        else:
            break
    return first_lnum,lnums_with_token

def get_token_values(line_objects, pnum, lnum):
    threshold = dict()
    for page in line_objects.keys():
        page_lines = line_objects[page]
        page_lines = page_lines[1:-1]
        dist_list = list()
        for ln, line in enumerate(page_lines):
            if ln == 0:
                continue
            prev_line_bottom = page_lines[ln - 1][0]['bottom']
            curr_line_top = line[0]['top']
            dist_list.append(round(curr_line_top-prev_line_bottom,1))
        try:
            rel = mode(dist_list) + 3
        except :
            rel = 6.5
        threshold[page] = rel
    current_page = pnum
    extraction_finished = False
    current_lnum, token_lnums = get_first_line(line_objects[pnum],lnum)
    token_lnums.sort()
    relevance = line_objects[pnum][token_lnums[-1]][0]['x1']
    result = list()
    page_numbers = list()
    # has_token = True
    # second_line = False
    while (not extraction_finished):
        resultant_object,extraction_finished,current_lnum,token_lnums  = get_value_object(line_objects, current_page, current_lnum, relevance, token_lnums , threshold[current_page])
        # has_token = False
        # extract from resultant_object
        if len(resultant_object)>0:
            first_line = resultant_object[0]
            if has_end(first_line):
                result.append(first_line)
                page_numbers.append(current_page + 1)
            elif len(resultant_object)>1:
                second_line = resultant_object[1]
                if has_end(second_line):
                    result.append(str(first_line).strip()+' '+str(second_line).strip())
                    page_numbers.append(current_page+1)
                else:
                    result.append(first_line)
                    page_numbers.append(current_page + 1)
            else:
                result.append(first_line)
                page_numbers.append(current_page + 1)

        if extraction_finished:
            return result,page_numbers

        if current_lnum == 0:
            current_page = current_page+1
    return result,page_numbers


def extract_values(line_objects, token):
    token = token.strip()
    values = list()
    pnums = list()
    for pnum in line_objects.keys():
        print(pnum)
        lines = line_objects[pnum]
        result, resultant_line = has_token_info(lines, token)
        if result:
            values_temp,pnums_temp = get_token_values(line_objects, pnum, resultant_line)
            values.extend(values_temp)
            pnums.extend(pnums_temp)
    return values,pnums




def get_bookrunners_and_coordinators(relevant_pages):
    result = dict()
    extracted_info,pnums = extract_values(relevant_pages, 'Date of Grant:')
    result['Bookrunners'] = extracted_info
    result['Bookrunners_page_numbers'] = pnums
    # print('Joint Bookrunners:\n')
    # for val in extracted_info:
    #     print(val)
    extracted_info,pnums = extract_values(relevant_pages, 'Coordinator')
    result['Global Coordinators'] = extracted_info
    result['Global Coordinators_page_numbers'] = pnums
    # print('Joint Global Coordinators:\n')
    # for val in extracted_info:
    #         print(val)
    max_len = 0
    for name in result.keys():
        l = len(result[name])
        if l>max_len:
            max_len = l
    for name in result.keys():
        vals = result[name]
        if len(vals)<max_len:
            for i in range(len(vals),max_len):
                vals.append(np.nan)
            result[name] = vals
    for name in result.keys():
        print(result[name])
    df = pd.DataFrame(result)
    return df
