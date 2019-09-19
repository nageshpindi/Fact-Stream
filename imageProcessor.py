import pdfplumber
import numpy as np
import cv2
from skimage.measure import label, regionprops
from pdf2image import convert_from_path
from skimage.measure import label
k=0.0000000001
horizontal_space_dis = 6.5
bounding_box_vertical_padding = 2.5


def horiz_lines(I):
    coord = np.zeros(4)
    count = 0
    I = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(I, (5, 5), 0)
    th, BW = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    label_img = label(BW)

    # print(label_img)
    # props = regionprops(np.squeeze(label_img))
    for region in regionprops(label_img):
        # print(region.minor_axis_length)
        idx = (region.minor_axis_length / np.float(region.major_axis_length + k) <= 0.1) & (
                    np.abs(region.orientation) <= 5);
        if idx:
            minr, minc, maxr, maxc = region.bbox
            t = np.asarray([minr, minc, minr, maxc - (maxr - minr)])
            coord = np.vstack((coord, t))
            count = count + 1
            # print(count)
    # print('total no.of horizental lines : ', count)
    if count>0:
        return coord[1:, :] / 6.94
    else:
        return []
    # return coord[1:, :] / 6.97

def is_intersecting(curr_top, curr_bottom, prev_top, prev_bottom):
    if curr_top >= prev_top and curr_top <= prev_bottom:
        return True
    if prev_top >= curr_top and prev_top <= curr_bottom:
        return True
    return False


def expand_spans_byUnderline(line_obj, t, prev_stop):
    if len(line_obj) == 1:
        if line_obj[0]['text'].strip()[0] == '(' and line_obj[0]['text'].strip()[-1] == ')':
            return prev_stop, line_obj

    sen_line_dis_threshold = 3.5
    line_sentences_count = {}
    is_row_has_underlines = False
    for sen_obj in line_obj:
        for i in range(prev_stop, len(t)):
            # checking line is bottom to it or not
            if is_intersecting(float(sen_obj['top']), float(sen_obj['bottom']),
                               t[i][0]-sen_line_dis_threshold, t[i][2]) and \
                    (float(sen_obj['bottom']) <= t[i][2] + sen_line_dis_threshold):# or \
                    # is_intersecting(float(sen_obj['top']), float(sen_obj['bottom']),
                    #                 t[i][0]+sen_line_dis_threshold, t[i][2]):

                if sen_obj['x0'] >= t[i][1] - horizontal_space_dis and \
                        sen_obj['x1'] <= t[i][3] + horizontal_space_dis:

                    if (t[i][0], t[i][1], t[i][2], t[i][3]) in line_sentences_count:
                        line_sentences_count[(t[i][0], t[i][1], t[i][2], t[i][3])] += 1
                    else:
                        line_sentences_count[(t[i][0], t[i][1], t[i][2], t[i][3])] = 1

                    prev_line_pos = i
                    is_row_has_underlines = True
                    sen_obj['has_true_underline'] = True
                    # print(sen_obj['text'])
                    break
            elif t[i][2] - float(sen_obj['bottom']) > 15:  # break if we are going more deep in table.
                break

    prev_stop_te = prev_stop
    for sen_obj in line_obj:
        sen_obj['underline_exists'] = is_row_has_underlines
        sen_obj['x0_or'] = sen_obj['x0']
        sen_obj['x1_or'] = sen_obj['x1']
        for i in range(prev_stop_te, len(t)):
            # checking line is bottom to it or not
            if is_intersecting(float(sen_obj['top']), float(sen_obj['bottom']),
                               t[i][0] - sen_line_dis_threshold, t[i][2]) and \
                    (float(sen_obj['bottom']) < t[i][2] + sen_line_dis_threshold):# or \
                    # is_intersecting(float(sen_obj['top']), float(sen_obj['bottom']),
                    #                 t[i][0] + sen_line_dis_threshold, t[i][2]):
                if (sen_obj['x0'] >= t[i][1] - horizontal_space_dis and
                        sen_obj['x1'] <= t[i][3] + horizontal_space_dis):
                    if line_sentences_count[(t[i][0], t[i][1], t[i][2], t[i][3])] < 2:
                        sen_obj['x0'] = t[i][1]
                        sen_obj['x1'] = t[i][3]
                    break
            elif t[i][2] - float(sen_obj['bottom']) > 15: # break if we are going more deep in table.
                break
    return prev_stop + len(line_sentences_count), line_obj

def get_page_extracts(path, do_image_processing):
    page_extract_dict = dict()
    line_obj_dict = dict()
    with pdfplumber.open(path, password='') as pdf:
        for index, page in enumerate(pdf.pages):
            page_extracts = page.extract_words(x_tolerance=1, y_tolerance=1)
            page_extract_dict[index] = page_extracts
            line_obj_dict[index] = get_line_objs(path, page_extracts, do_image_processing)
            # if index > 50 and index < 55:
            #     page_extracts = page.extract_words(x_tolerance=1, y_tolerance=1)
            #     page_extract_dict[index] =page_extracts
            #     line_obj_dict[index] = get_line_objs(path, page_extracts, do_image_processing)
            # elif index > 54:
            #     break
    return line_obj_dict

def modify_line_objs(lines, lines_spans):
    prev_stop = 0
    for i in range(len(lines)):
        te = {}
        x0s = []
        for sen_obj in lines[i]:
            x0s.append(sen_obj['x0'])
            te[sen_obj['x0']] = sen_obj
        x0s.sort()
        sorted_sen_obj = [te[x0] for x0 in x0s]
        res_sen_objs = []
        for j in range(len(sorted_sen_obj)):
            if j+1 < len(sorted_sen_obj) and \
                    abs(float(sorted_sen_obj[j+1]['x0']) - float(sorted_sen_obj[j]['x1'])) < horizontal_space_dis and \
                            not (sorted_sen_obj[j]['text'] == 'Date of Joining' and sorted_sen_obj[j+1]['text'] == 'Appointment as'):
                te_sen_obj = {}
                te_sen_obj['x0'] = sorted_sen_obj[j]['x0']
                te_sen_obj['x1'] = sorted_sen_obj[j+1]['x1']
                if sorted_sen_obj[j]['top'] < sorted_sen_obj[j+1]['top']:
                    te_sen_obj['top'] = sorted_sen_obj[j]['top']
                else:
                    te_sen_obj['top'] = sorted_sen_obj[j+1]['top']

                if sorted_sen_obj[j]['bottom'] > sorted_sen_obj[j+1]['bottom']:
                    te_sen_obj['bottom'] = sorted_sen_obj[j]['bottom']
                else:
                    te_sen_obj['bottom'] = sorted_sen_obj[j+1]['bottom']
                te_sen_obj['text'] = sorted_sen_obj[j]['text'] + ' ' + sorted_sen_obj[j+1]['text']
                sorted_sen_obj[j+1] = te_sen_obj
            else:
                res_sen_objs.append(sorted_sen_obj[j])
        prev_stop, lines[i] = expand_spans_byUnderline(res_sen_objs, lines_spans, prev_stop)
    return lines


def get_line_objs(path, page_extracts, do_image_processing):
    currency_list = ['$', 'USD']
    if do_image_processing:
        pages = convert_from_path(path, 500)
        lines_spans = []
        for page in pages:
            I = np.array(page)
            # print(I)
            lines_spans = horiz_lines(I)
    # line_objs_dict = dict()
    lines = []
    i = 0
    prev_stop = 0
    for index, extract in enumerate(page_extracts):
        extract['underline_exists'] = False
        extract['has_true_underline'] = False
        if len(str(extract['text']).replace('.', '').strip()) == 0:
            continue
        if index is 0:
            prev_top = float(-1)
            prev_bottom = float(-1)
        else:
            prev_top = float(lines[i-1][0]['top'])
            prev_bottom = float(lines[i-1][0]['bottom'])
        curr_top = float(page_extracts[index]['top'])
        curr_bottom = float(page_extracts[index]['bottom'])

        lines_intersection_bool = is_intersecting(curr_top+bounding_box_vertical_padding,
                                                  curr_bottom-bounding_box_vertical_padding,
                                                  prev_top+bounding_box_vertical_padding,
                                                  prev_bottom-bounding_box_vertical_padding)

        if (curr_top == prev_top and curr_bottom == prev_bottom) or lines_intersection_bool: #same line add to list
            if len(lines[i-1]) > 0:
                for k in range(len(lines[i-1])):
                    if abs(float(extract['x0']) - float(lines[i-1][k]['x1'])) < horizontal_space_dis and \
                            not (lines[i-1][k]['text'] == 'Date of Joining' and extract['text'] == 'Appointment'):
                        if extract['x1'] > lines[i-1][k]['x1']:
                            lines[i-1][k]['x1'] = extract['x1']
                        if extract['x0'] < lines[i-1][k]['x0']:
                            lines[i-1][k]['x0'] = extract['x0']
                        lines[i-1][k]['text'] = lines[i-1][k]['text'] + ' ' + extract['text']
                        break
                    if abs(float(extract['x1']) - float(lines[i-1][k]['x0'])) < horizontal_space_dis and \
                            not (lines[i-1][k]['text'] == 'Date of Joining' and extract['text'] == 'Appointment'):
                        if extract['x1'] > lines[i-1][k]['x1']:
                            lines[i-1][k]['x1'] = extract['x1']
                        if extract['x0'] < lines[i-1][k]['x0']:
                            lines[i-1][k]['x0'] = extract['x0']
                        if extract['bottom'] > lines[i-1][k]['bottom']:
                            lines[i-1][k]['bottom'] = extract['bottom']
                        lines[i-1][k]['text'] = extract['text'] + ' ' + lines[i-1][k]['text']
                        break
                else:
                    # prev_stop, extract= expand_spans_byUnderline(extract, lines_spans, prev_stop)
                    lines[i-1].append(extract)
            else:
                # prev_stop, extract = expand_spans_byUnderline(extract, lines_spans, prev_stop)
                lines[i-1].append(extract)
            continue
        elif (prev_top < prev_bottom and prev_bottom < curr_top and curr_top < curr_bottom) and not lines_intersection_bool: #new line
            # if i > 0:
            #     prev_stop, lines[i-1] = expand_spans_byUnderline(lines[i-1], lines_spans, prev_stop)
            lines.append([extract])
            i += 1
            continue
        else:
            if ((curr_top - prev_top) > (prev_bottom - curr_top) or abs(curr_top - prev_top) <= 2 ) and not lines_intersection_bool: #new line
                # if i > 0:
                #     prev_stop, lines[i-1] = expand_spans_byUnderline(lines[i-1], lines_spans, prev_stop)
                lines.append([extract])
                i += 1
                continue
            # print('text1: ',page_extracts[index-1]['text'],'text2: ',page_extracts[index]['text'])
            # print('top1: ',page_extracts[index - 1]['top'], 'top2: ',page_extracts[index]['top'],'bottom1: ',page_extracts[index - 1]['bottom'], 'bottom2: ',page_extracts[index]['bottom'])
            # print('------------------------------------------------------------------------')
    # return lines[:df_startLineNum+1]
    if do_image_processing:
        lines = modify_line_objs(lines, lines_spans)
    # line_objs_dict[path] = lines
    return lines




