
import time
from flashtext import KeywordProcessor


class gazetteer():
    def __init__(self,type_link,isLower,iscase_sensitive,currFlag):
        self.keyword_processor = KeywordProcessor(case_sensitive=iscase_sensitive)
        if type_link is None:
            return
        curr_dict = {"USD": ["$","$", "dollars", "U.S. Dollar", "USD", "US$", "United States dollar"]}
        # Temp logic for hierarchy identification -- remove
        # asset_dict ={"Assets": ["assets","total assets"]}
        # curAss_Dict={"Current Assets": ["current assets","total current assets"]}
        # nonCurAss_Dict={"NonCurrent Assets": ["longterm assets","long-term assets","non current assets","non-current assets","total noncurrent assets","total non-current assets"]}
        # liab_Dict={"Liabilities": ["liabilities","liabilities and common shareholders equity","liabilities and shareholders equity","total liabilities","total liabilities and equity","total liabilities and shareholders equity","total liabilities and stockholders equity","total liabilities and common shareholders equity"]}
        # curLiab_Dict ={"Current Liabilities" : ["current liabilities","total current liabilities"]}
        # nonCurrLiab_Dict = {"NonCurrent Liabilities" : ["non current liabilities","non-current liabilities","longterm liabilities","long-term liabilities","total noncurrent liabilities","total non-current liabilities"]}
        # shrEq_Dict = {"Shareholders Equity" : ["shareholders equity","equity","stockholders equity","total equity","total stockholders equity","total common shareholders equity","total wells fargo stockholders equity"]}


        with open(type_link,encoding='utf-8',errors='ignore') as inf:
            lines = inf.readlines()

        for line in lines:
            if len(line.strip()) >0 :
                if isLower:
                    self.keyword_processor.add_keyword(line.strip().lower())
                else:
                    self.keyword_processor.add_keyword(line.strip())
        if currFlag:
            self.keyword_processor.add_keywords_from_dict(curr_dict)
    #     temp logic for hierarchy identification -- remove
    #     self.keyword_processor.add_keywords_from_dict(asset_dict)
    #     self.keyword_processor.add_keywords_from_dict(curAss_Dict)
    #     self.keyword_processor.add_keywords_from_dict(nonCurAss_Dict)
    #     self.keyword_processor.add_keywords_from_dict(liab_Dict)
    #     self.keyword_processor.add_keywords_from_dict(curLiab_Dict)
    #     self.keyword_processor.add_keywords_from_dict(nonCurrLiab_Dict)
    #     self.keyword_processor.add_keywords_from_dict(shrEq_Dict)

    def findPhrases(self,text):
        list_phrases = list()
        flash_text=self.keyword_processor.extract_keywords(text, span_info=True)
        for flash in flash_text:
            list_phrases.append(flash[0])
        return set(list_phrases)


#
# text=open('/Users/raghav/Downloads/profitbmw.txt','r').read()
# text = '(sadada)  (Millions) 2017 2016 Assets:  '
# tries.make_automaton()
#
# if __name__=='__main__':
#     import time
#
#     start_time = time.time()
#     gaz=gazetteer(os.path.join(baseDataDirectory, 'unit.txt'),False,False)
#     print("--- %s seconds ---" % (time.time() - start_time))
#
#     start_time = time.time()
#
#     print(gaz.findPhrases(text))
#     print("--- %s seconds ---" % (time.time() - start_time))











