from collections import defaultdict

from stanfordcorenlp import StanfordCoreNLP
import logging
import json


class StanfordNLP:
    def __init__(self, host='http://localhost', port=9000):
        self.nlp = StanfordCoreNLP(host, port=port,
                                   timeout=30000 , quiet=True, logging_level=logging.DEBUG)
        self.props = {
            'annotators': 'tokenize,ssplit,pos,lemma,ner',
            'pipelineLanguage': 'en',
            'outputFormat': 'json'
        }

    def word_tokenize(self, sentence):
        return self.nlp.word_tokenize(sentence)

    def pos(self, sentence):
        return self.nlp.pos_tag(sentence)

    def ner(self, sentence):
        return self.nlp.ner(sentence)

    def parse(self, sentence):
        return self.nlp.parse(sentence)

    def dependency_parse(self, sentence):
        return self.nlp.dependency_parse(sentence)

    def annotate(self, sentence):
        return json.loads(self.nlp.annotate(sentence, properties=self.props))

    @staticmethod
    def tokens_to_dict(_tokens):
        tokens = defaultdict(dict)
        for token in _tokens:
            tokens[int(token['index'])] = {
                'word': token['word'],
                'lemma': token['lemma'],
                'pos': token['pos'],
                'ner': token['ner']
            }
        return tokens







if __name__ == '__main__':
    sNLP = StanfordNLP()
    text = "Assuming the Offer Price of HK$2.48 (being the low-end of the Offer Price range set out in this Prospectus), the total aggregate number of Shares to be subscribed for by the Cornerstone Investor will be 84,204,000 Shares (rounded down to the nearest whole board lot), representing approximately 33.68% of the Offer Shares and approximately 8.42% of the Shares in issue immediately upon completion of the Global Offering, assuming the Over-allotment Option is not exercised, no options are granted under thePost-IPO Share Option Scheme and no shares are granted under the Share Award Scheme."
    ANNOTATE =  sNLP.annotate(text)
    sentences=ANNOTATE['sentences']
    for sentence in sentences:
        entities=sentence['entitymentions']
        for entity in entities:
            print(entity['text'],entity['characterOffsetBegin'],entity['characterOffsetEnd'],entity['ner'])
