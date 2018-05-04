import json
import codecs
import sys
import os

if __name__ == "__main__":
    jsonFilePath = "C:\\Users\\Sumeet Singh\\PycharmProjects\\multiNLI\\multiNLI\\data\\multinli_1.0_train_all.spatial.jsonl"\
        if len(sys.argv)<2 else sys.argv[1]

    # with open(jsonFilePath) as data_file:
    #     data = json.load(data_file)
    data = [json.loads(line.strip()) for line in open(jsonFilePath)]

    filename, file_extension = os.path.splitext(jsonFilePath)
    sentencePairPath = filename + ".sep.txt"
    # sentenceGoldPath = filename + ".gold.txt"
    with codecs.open(sentencePairPath, 'w', encoding='utf-8') as txtWriter:
        # with codecs.open(sentenceGoldPath, 'w', encoding='utf-8') as gldWriter:
            counter = 0
            for sentenceJsonPair in data:
                sentencePair = [sentenceJsonPair["sentence1"], sentenceJsonPair["sentence2"]]
                for sentence in sentencePair:
                    sentence.strip()
                    if not '.' in sentence:
                        sentence += '.'
                    txtWriter.write("{}\n".format(sentence))
                    # numTokens = len(sentence.split())
                    # IOB = " ".join(["O" for i in range(numTokens)]) # dummy IOB tags
                    # gldWriter.write("{} {} ||| {}\n".format(counter,sentence,IOB))
                    # counter+=1