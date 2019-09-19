from imageProcessor import get_page_extracts
from directors_extract import get_directors_table
from Extract_Bookrunners import get_bookrunners_and_coordinators
from extract_CornerStoneInvestors import extract_cornerstone_investors, extract_cornerstone_shares, get_cornerstone_investors_from_table, modify_investor_names
import pikepdf
from pikepdf._qpdf import Pdf
import os
import pandas as pd
import json
import pdftotext
import traceback

def splitPDFPages(path,outputPath,fname_fmt=u"{num_page:04d}.pdf"):
    # deleteDirectoryContents(outputPath)
    path_dict = dict()
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)

    pdf = pikepdf.open(path)
    num_pages = len(pdf.pages)
    for n, page in enumerate(pdf.pages):
        outpdf = Pdf.new()
        outpdf.pages.append(page)
        file_name = os.path.join(outputPath, fname_fmt.format(num_page=n+1))
        path_dict[n] = file_name
        outpdf.save(file_name)
    return path_dict

def extract_relevant_pages(pdf2text_dict, title_list):
    pages_matched = list()
    found = False
    found_now = True
    for page_num in pdf2text_dict.keys():
        try:
            page_title = pdf2text_dict[page_num][0].strip()
        except Exception as e:
            print('exception occured while processing pagenum:',page_num)
            continue
        for title in title_list:
            if title.strip().lower() in page_title.lower():
                found = True
                found_now = True
                pages_matched.append(page_num)
                break
        # if found and not found_now:
        #     return pages_matched
        # found_now = False
    return pages_matched

def get_bookrunners(pdf2text_dict, path_dict):
    title_list = ['DIRECTORS AND PARTIES INVOLVED IN THE GLOBAL OFFERING', 'DIRECTORS, SUPERVISORS AND PARTIES INVOLVED IN THE GLOBAL OFFERING', 'DIRECTORS AND PARTIES INVOLVED IN THE SHARE OFFER']
    #title_list=['DEFINITIONS','GLOSSARY OF TECHNICAL TERMS','DIRECTORS AND PARTIES INVOLVED IN THE SHARE OFFER','CORPORATE INFORMATION']
    relevant_pages = extract_relevant_pages(pdf2text_dict, title_list)
    do_image_processing = False
    relevant_line_obj = dict()
    for page in relevant_pages:
        line_obj = get_page_extracts(path_dict[page], do_image_processing)
        relevant_line_obj[page] = line_obj[0]
    result = get_bookrunners_and_coordinators(relevant_line_obj)
    return result


def get_bookrunners1(pdf2text_dict,path_dict):
    title_list = ['GRANT OF SHARE OPTIONS']
    relevant_pages = extract_relevant_pages(pdf2text_dict, title_list)
    relevant_pages=[0]
    do_image_processing = False
    relevant_line_obj = dict()
    for page in relevant_pages:
        line_obj = get_page_extracts(path_dict[page], do_image_processing)
        relevant_line_obj[page] = line_obj[0]
    result = get_bookrunners_and_coordinators(relevant_line_obj)
    return result




def get_directors(pdf2text_dict, path_dict,baseDataDirectory):
    title_list = ['DIRECTORS AND SENIOR MANAGEMENT',
                  'DIRECTORS, SUPERVISORS AND SENIOR MANAGEMENT',
                  'DIRECTORS, SENIOR MANAGEMENT AND STAFF',
                  'DIRECTORS, SENIOR MANAGEMENT AND EMPLOYEES']
    relevant_pages = extract_relevant_pages(pdf2text_dict, title_list)
    # relevant_pg_numbers = relevant_pages.keys()
    path_list = list()
    for pnum in relevant_pages:
        path_list.append(path_dict[pnum])
    arr_objs = []
    for page_path in path_list:
        print(page_path)
        do_image_processing = True
        line_obj_with_underlines = get_page_extracts(page_path, do_image_processing)
        arr_objs.append(line_obj_with_underlines[0])
    df = get_directors_table(arr_objs,baseDataDirectory, relevant_pages)
    return df


def get_cornerstone_investors(pdf2text_dict, path_dict,baseDataDirectory):
   title_list = ['CORNERSTONE INVESTORS', 'CORNERSTONE INVESTOR', 'CORNERSTONE PLACING']
   relevant_pages = extract_relevant_pages(pdf2text_dict, title_list)
   do_image_processing = False
   relevant_line_obj = dict()
   for page in relevant_pages:
       line_obj = get_page_extracts(path_dict[page], do_image_processing)
       relevant_line_obj[page] = line_obj[0]
   result,page_numbers = extract_cornerstone_investors(relevant_line_obj)
   path_list = list()
   for pnum in relevant_pages:
       path_list.append(path_dict[pnum])
   arr_objs = []
   for page_path in path_list:
       # print(page_path)
       do_image_processing = True
       line_obj_with_underlines = get_page_extracts(page_path, do_image_processing)
       arr_objs.append(line_obj_with_underlines[0])
   result_from_table = get_cornerstone_investors_from_table(arr_objs,baseDataDirectory,relevant_pages)
   result = modify_investor_names(result, result_from_table)
   offer_prices_df = extract_cornerstone_shares(relevant_line_obj)
   data = {'Cornerstone Investors':result,'page_number':page_numbers}
   df = pd.DataFrame(data)
   return df, offer_prices_df

def get_pdftotexts(path_dict):
    pdf2text_dict = dict()
    for idx in path_dict.keys():
        path = path_dict[idx]
        with open(path, "rb") as f:
            pdf = pdftotext.PDF(f)
        page = pdf[0]
        lines = str(page).split('\n')
        pdf2text_dict[idx] = lines
    return pdf2text_dict

class controller():
    def __init__(self):
        pass

    def ProcessData(self,input_path,output_path,baseDataDirectory):
        try:
            fileName = str(input_path).lower().split('/')[-1].replace('.pdf', '')
            output_path = output_path + '/' + fileName

            if not os.path.exists(output_path):
                os.makedirs(output_path)

            finalDict = dict()
            path_dict = splitPDFPages(input_path, output_path)
            pdf2text_dict = get_pdftotexts(path_dict)
            # line_obj_dict = get_page_extracts(input_path, do_image_processing)
            # df_directors = get_directors(pdf2text_dict, path_dict, baseDataDirectory)
            df_bookrunners = get_bookrunners(pdf2text_dict,path_dict)
            df_bookrunners1=get_bookrunners1(pdf2text_dict,path_dict)



            df_cornerstoneinvestors, offer_prices_df = get_cornerstone_investors(pdf2text_dict,path_dict,baseDataDirectory)

            # finalDict['directors'] = df_directors.reset_index(drop=True).to_json(force_ascii=False)
            # finalDict['bookrunners'] = df_bookrunners.reset_index(drop=True).to_json(force_ascii=False)
            finalDict['cornerstonePlacing'] = offer_prices_df.reset_index(drop=True).to_json(force_ascii=False)
            finalDict['cornerstoneInvestors'] = df_cornerstoneinvestors.reset_index(drop=True).to_json(force_ascii=False)

            out_json_path = output_path + '/' + fileName + '.json'

            with open(out_json_path, 'w', encoding='utf-8') as outfile:
                json.dump(finalDict, outfile, ensure_ascii=False,indent=3)

            return json.dumps(finalDict)
        except Exception as e:
            print(e)
            traceback.print_exc()
            print(input_path)
            return json.dumps(finalDict)


if __name__ == "__main__":
    output_path = "/home/almug/Documents/Projects/sfc_extraction/output_2"
    input_path = "/home/almug/Downloads/Nagesh/ltn20190611031.pdf"
    baseDataDirectory = '/home/almug/Documents/Projects/sfc_extraction/SFC_PoC/Data'

    ctrlr = controller()
    final_json = ctrlr.ProcessData(input_path,output_path,baseDataDirectory)
    # print(final_json)
    print('done')

    # path_dict = splitPDFPages(input_path, output_path)
    # do_image_processing = False
    # line_obj_dict = get_page_extracts(input_path, path_dict, do_image_processing)
    # print('extracting directors \n\n')
    # df_directors = get_directors(line_obj_dict,path_dict,baseDataDirectory)
    # with open (output_path + '/' + 'directors'  + '.tsv', 'w',encoding='utf-8') as handle:
    #     df_directors.to_csv(handle, sep='\t', index=False, encoding='utf-8')
    # print(df_directors)
    # print('extracting bookrunners \n\n')
    # df_bookrunners = get_bookrunners(line_obj_dict)
    # print(df_bookrunners)
    # with open (output_path + '/' + 'bookrunners_coordinators'  + '.tsv', 'w',encoding='utf-8') as handle:
    #     df_bookrunners.to_csv(handle, sep='\t', index=False, encoding='utf-8')
    # print('extracting cornerstone_investors \n\n')
    # df_cornerstoneinvestors = get_cornerstone_investors(line_obj_dict)
    # print(df_cornerstoneinvestors)
    # with open (output_path + '/' + 'cornerstone_investors'  + '.tsv', 'w',encoding='utf-8') as handle:
    #     df_cornerstoneinvestors.to_csv(handle, sep='\t', index=False, encoding='utf-8')




