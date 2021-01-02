import pickle
import re


def get_str_btw(s, b, e):
    a = list()
    index1 = 0
    index2 = 0
    for x in range(len(s)):
        if s[x] == b:
            index1 = x
            continue
        if s[x] == e:
            index2 = x
            a.append(int(s[index1+1:index2]))
    # print(a)
    return a
class CRF:
    scoreMap = dict()
    template = list()

    def __init__(self):
        self.template = self.readTemplate("dataset/dataset1/template.utf8")
        self.scoreMap = load_obj("scoreMap")

    def readTemplate(self, fileName):
        gram = list()
        file = open(fileName, encoding='UTF-8')
        unigram=list()
        bigram=list()
        for line in file:
           if len(line)>1:
               term = get_str_btw(line,"[",",")
               if (line[0] == "U")and(len(term)>0):
                   unigram.append(term)
               if (line[0] == "B")and(len(term)>0):
                   bigram.append(term)
        gram.append(unigram)
        gram.append(bigram)
        # print(gram)
        return gram


    def getStatus(self, row):
        if row == 0:
            return "B"
        if row == 1:
            return "I"
        if row == 2:
            return "E"
        if row == 3:
            return "S"
        return


    def statusToRow(self, status):
        if status == "B":
            return 0
        if status == "I":
            return 1
        if status == "E":
            return 2
        if status == "S":
            return 3
        return


    def getMaxIndex(self, list):
        index = 0
        for i in range(len(list)):
            if(list[index]<list[i]):
                index = i
        return index


    def getUniTemplate(self):
        return self.template[0]


    def getBiTemplate(self):
        return self.template[1]

    def segment(self, sentence):
        lenth = len(sentence)
        statusFrom = [["" for col in range(lenth)] for row in range(4)]
        maxScore = [[-1 for col in range(lenth)] for row in range(4)]
        for col in range(lenth):
            for row in range(4):
                thisStatus = self.getStatus(row)
                if(col == 0):
                    uniScore = self.getUniScore(sentence, 0, thisStatus)
                    biScore = self.getBiScore(sentence, 0, " ", thisStatus)
                    maxScore[row][0] = uniScore + biScore
                else:
                    scores = [-1,-1,-1,-1]
                    for i in range(4):
                        preStatus = self.getStatus(i)
                        transScore = maxScore[i][col - 1]
                        uniScore = self.getUniScore(sentence, col, thisStatus)
                        biScore = self.getBiScore(sentence, col, preStatus, thisStatus)
                        scores[i] = transScore + uniScore + biScore
                        maxIndex = self.getMaxIndex(scores)
                        maxScore[row][col] = scores[maxIndex]
                        statusFrom[row][col] = self.getStatus(maxIndex)
        resBuf = ['' for col in range(lenth)]
        scoreBuf = [0 for col in range(4)]
        for i in range(4):
            scoreBuf[i] = maxScore[i][lenth - 1]
        resBuf[lenth - 1] = self.getStatus(self.getMaxIndex(scoreBuf))
        for backIndex in range(lenth-2, -1 , -1):
            resBuf[backIndex] = statusFrom[self.statusToRow(resBuf[backIndex + 1])][backIndex + 1]
        temp = ""
        for i in range(lenth):
            temp+=resBuf[i]
        return temp





    def getBiScore(self, sentence, thisPos, preStatus, thisStatus):
        biScore = 0
        biTemplate = self.getBiTemplate()
        num = len(biTemplate)
        for i in range(num):
            key = self.makeKey(biTemplate[i], "" + str(i), sentence, thisPos, preStatus + thisStatus)
            if(key in self.scoreMap.keys()):
                biScore += self.scoreMap[key]
        return biScore

    def getUniScore(self, sentence, thisPos, thisStatus):
        uniScore = 0
        uniTemplate = self.getUniTemplate()
        num = len(uniTemplate)
        for i in range(num):
            key = self.makeKey(uniTemplate[i], ""+str(i), sentence, thisPos, thisStatus)
            if (key in self.scoreMap.keys()):
                uniScore += self.scoreMap[key]
        return uniScore


    def makeKey(self, template, identity, sentence, pos, statusCovered):
        string = ""
        string=string + identity
        for offset in template:
            index = pos + offset
            if ((index < 0)or(index >= len(sentence))):
                string+=" "
            else:
                thisCharacter = sentence[index : index + 1]
                string+=thisCharacter
        string+="/"
        string+=statusCovered
        return string


    def train(self, sentence, theoryRes):
        # print(sentence)
        myRes = self.segment(sentence)
        length = len(sentence)
        wrongNum = 0
        for i in range(length):
            myResI = myRes[i: i + 1]
            theoryResI = theoryRes[i: i + 1]
            if (myResI!=theoryResI):
                wrongNum = wrongNum+1
                # update Unigram template
                uniTem = self.getUniTemplate()
                uniNum = len(uniTem)
                for uniIndex in range(uniNum):
                    uniMyKey = self.makeKey(uniTem[uniIndex], str(uniIndex), sentence, i, myResI)
                    if (not (uniMyKey in self.scoreMap.keys())):
                        self.scoreMap[uniMyKey] = -1
                    else:
                        myRawVal = self.scoreMap[uniMyKey]
                        self.scoreMap[uniMyKey] = myRawVal - 1
                    uniTheoryKey = self.makeKey(uniTem[uniIndex], str(uniIndex), sentence, i, theoryResI)
                    if (not (uniTheoryKey in self.scoreMap.keys())):
                        self.scoreMap[uniTheoryKey] = 1
                    else:
                        theoryRawVal = self.scoreMap[uniTheoryKey]
                        self.scoreMap[uniMyKey] = theoryRawVal + 1
                # update Bigram template
                biTem = self.getBiTemplate()
                biNum = len(biTem)
                for biIndex in range(biNum):
                    biMyKey = ""
                    biTheoryKey = ""
                    if i >= 1:
                        biMyKey = self.makeKey(biTem[biIndex], str(biIndex), sentence, i, myRes[i - 1: i + 1])
                        biTheoryKey = self.makeKey(biTem[biIndex], str(biIndex), sentence, i,theoryRes[i - 1: i + 1])
                    else:
                        biMyKey = self.makeKey(biTem[biIndex], str(biIndex), sentence, i, " " + myResI)
                        biTheoryKey = self.makeKey(biTem[biIndex], str(biIndex), sentence, i, " " + theoryResI)
                    if (not (biMyKey in self.scoreMap.keys())):
                        self.scoreMap[biMyKey] = -1
                    else:
                        myRawVal = self.scoreMap[biMyKey]
                        self.scoreMap[biMyKey] = myRawVal - 1
                    if (not (biTheoryKey in self.scoreMap.keys())):
                        self.scoreMap[biTheoryKey] = 1
                    else:
                        theoryRawVal = self.scoreMap[biTheoryKey]
                        self.scoreMap[biTheoryKey] = theoryRawVal + 1
        save_obj(self.scoreMap, "scoreMap")
        return wrongNum
    def start_to_train(self, iter, TRAIN_DATA_PATH):
        data = pre_process_Data(TRAIN_DATA_PATH)
        sentences = data[0]
        tags = data[1]
        for it in range(iter):
            wr = 0
            totalTest = 0
            for i in range(len(sentences)):
                sentence = sentences[i]
                totalTest+= len(sentence)
                tag = tags[i]
                if len(sentence)==0:
                    continue
                wr += self.train(sentence, tag)
                corrNum = totalTest - wr
                print("iter:"+str(iter)+"   accuracy:"+str((corrNum/totalTest)))

    def predict(self, sentence):
        return self.segment(sentence)


def pre_process_Data(TRAIN_DATA_PATH):
    print("数据准备中。。。")
    ifp = open(TRAIN_DATA_PATH, encoding='UTF-8')
    sentence_set = list()
    tag_set = list()
    sentence = ""
    tag = ""
    for line in ifp:
        # print()
        if (len(line)<4):
            sentence_set.append(sentence)
            tag_set.append(tag)
            sentence=""
            tag=""
        else:
            line.split()
            sentence+=line[0]
            tag+=line[2]
    train_data = [sentence_set, tag_set]
    print("数据准备完成")
    return train_data

def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)





if __name__ == '__main__':
    crf = CRF()
    crf.start_to_train(1, "dataset/dataset2/train.utf8")
    # print(crf.predict("银中国行与中国进出口银行加强合作。"))
    # scoreMap = load_obj("scoreMap")