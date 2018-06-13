import sys
sys.path.append('../')
import jieba,jieba.analyse
from sklearn.feature_extraction.text import CountVectorizer
from QueryMongoDB.ConnectDB import *
from dateutil import parser
import datetime,_pickle as pickle,time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.decomposition import TruncatedSVD
import random,json

def IDF(n_features,docs):
    vectorizer = TfidfVectorizer(max_features=n_features,
                                 use_idf=True)
    return vectorizer.fit(docs)
class LSACHFlow:
    def __init__(self):
        self.n_features=120
        self.name = ""
        self.keywords=set()
        self.docnum=1

    def cleanDocs(self,docs):
        corporus = []

        for doc in docs:
            words = jieba.analyse.tfidf(doc)
            words = self.keywords.intersection(words)
            corporus.append(" ".join(words))
        print("cleaning from",len(docs),len(docs[0]),"to",len(corporus),len(corporus[0]))

        return corporus

    def transformVec(self,docs):
        # print("transfering docs to LSA factors")
        corporus=self.cleanDocs(docs)

        X = self.tfidf.transform(corporus)
        X = self.lsa.transform(X)

        return X



    def train_doctopics(self,docs):
        t0=time.time()
        self.docnum=len(docs)
        self.keywords=set(jieba.analyse.textrank(". ".join(docs),topK=self.n_features))
        corporus=self.cleanDocs(docs)

        self.tfidf=TfidfVectorizer(max_features=self.n_features).fit(corporus)
        X=self.tfidf.transform(corporus).toarray()
        self.n_features = len(X[0])
        print("Performing  Chinese LSA(%d features) from doc shape(%d,%d)" % (self.n_features, len(X), len(X[0])))
        # Vectorizer results are normalized, which makes KMeans behave as
        # spherical k-means for better results. Since LSA/SVD results are
        # not normalized, we have to redo the normalization.
        svd = TruncatedSVD(self.n_features)
        normalizer = Normalizer(copy=False)
        self.lsa = make_pipeline(svd, normalizer)
        self.lsa = self.lsa.fit(X)
        explained_variance = svd.explained_variance_ratio_.sum()
        print("Explained variance of the SVD step: {}%".format(int(explained_variance * 100)))

        print("LSA for Chinese built in %fs" % (time.time() - t0))
        with open("../data/saved_ML_models/docModels/" + self.name + "-lsamodel-ch.pkl", "wb") as f:
            model = {}
            model["n_features"] = self.n_features
            model["keywords"]=self.keywords
            model["lsa"] = self.lsa
            model["tfidf"] = self.tfidf
            pickle.dump(model, f, True)

    def loadModel(self):
        # print("loading lsa model")
        with open("../data/saved_ML_models/docModels/" + self.name + "-lsamodel-ch.pkl", "rb") as f:
            model = pickle.load(f)
            self.n_features = model["n_features"]
            self.keywords=model["keywords"]
            self.lsa = model["lsa"]
            self.tfidf = model["tfidf"]
        # print("loaded %d feature model"%self.n_features)
        print()


class LSAFlow:

    def __init__(self):
        self.n_features=120
        self.name=""

    def transformVec(self,docs):
        #print("transfering docs to LSA factors")
        X=self.idfmodel.transform(docs)
        X = self.lsa.transform(X)
        return X

    def train_doctopics(self,docs):
        t0 = time.time()
        #print("test")
        #print(docs)
        #print("\n")

        self.idfmodel=IDF(self.n_features,docs)
        X = self.idfmodel.transform(docs)

        X=X.toarray()
        self.n_features=min(int(0.8*len(X[0])),self.n_features)
        print("Performing  LSA(%d features) from doc shape(%d,%d)"%(self.n_features,len(X),len(X[0])))
        # Vectorizer results are normalized, which makes KMeans behave as
        # spherical k-means for better results. Since LSA/SVD results are
        # not normalized, we have to redo the normalization.
        svd = TruncatedSVD(self.n_features)
        normalizer = Normalizer(copy=False)
        self.lsa = make_pipeline(svd, normalizer)
        self.lsa=self.lsa.fit(X)
        explained_variance = svd.explained_variance_ratio_.sum()
        print("Explained variance of the SVD step: {}%".format(int(explained_variance * 100)))

        print("LSA built in %fs" % (time.time() - t0))
        with open("../data/saved_ML_models/docModels/"+self.name+"-lsamodel.pkl","wb") as f:
            model={}
            model["n_features"]=self.n_features
            model["lsa"]=self.lsa
            model["idfmodel"]=self.idfmodel
            pickle.dump(model,f,True)


    def loadModel(self):
        #print("loading lsa model")
        with open("../data/saved_ML_models/docModels/"+self.name+"-lsamodel.pkl","rb") as f:
            model=pickle.load(f)
            self.n_features=model["n_features"]
            self.lsa=model["lsa"]
            self.idfmodel=model["idfmodel"]
        #print("loaded %d feature model"%self.n_features)
        print()

class IssueData:

    def initTrainData(self):
        projectID=int(self.projectID)
        issuedata = self.db["issue"].find({"project_id": projectID})
        project = self.db["project"].find({"pid": projectID})

        userIDs = project[0]["members"]
        # print(userIDs)
        self.userIndex = {}
        for i in range(len(userIDs)):
            self.userIndex[userIDs[i]] = i

        with open("../data/UserIndex/" + str(projectID) + ".pkl", "wb") as f:
            pickle.dump(self.userIndex, f, True)
        print("checking issues items,projectID=",projectID," size=",issuedata.count())
        for issue in issuedata:
            if len(issue["assignees"])<1:
#                print("lack of assignees",len(issu["assignees"]))
                continue

            self.issuesID.append(issue["issue_id"])
            beginT = issue["created_at"]
            endT = issue["updated_at"]
            # beginT=beginT[:beginT.find("T")]
            # endT=endT[:endT.find("T")]
            # print("begin:"+beginT,"end:"+endT)

            beginT = parser.parse(beginT)
            if endT == "":
                duration = (datetime.datetime.now().date() - beginT.date()).days
                duration *= 2
            else:
                endT = parser.parse(endT)
                duration = (endT - beginT).days

            beginT = (datetime.datetime.now().date() - beginT.date()).days
            description = issue["description"]
            labels = ','.join(issue["labels"])

            title = issue["title"]
            downvotes = issue["downvotes"]
            upvotes = issue["upvotes"]
            notes_count = issue["notes_count"]

            doc = title + "," + labels
            # print(beginT,'\n',duration,'\n',labels,'\n',downvotes,'\n',upvotes,'\n',notes_count,'\n')
            self.assignees.append(issue["assignees"])

            self.docs.append(doc)
            
            numx=np.array([beginT, duration, downvotes, upvotes, notes_count])
            for z in range(len(numx)):
                if numx[z] in (np.NAN,np.NaN,np.inf,-np.inf):
                    numx[z]=0
            self.issues.append(numx)

            # self.assignees.append()
            # break

        print("finished for projectID=", projectID, len(self.issues))

    def fetchData(self,data):
        #data=json.loads(request)

        self.docs=[]
        self.issues=[]

        if data["mode"]=='ID':
            issueID=int(data["data"])
            issues = self.db["issue"].find({"issue_id": issueID})
        elif data["mode"]=='title':
            issue_title=str(data["data"])
            issues=self.db["issue"].find({"title":issue_title})
        elif data["mode"]=="issue":
            issues = [data["data"]]
        else:
            return

        #print("issues count before",len(issues))
        for issue in issues:
            beginT = issue["created_at"]
            endT = issue["updated_at"]
            beginT = parser.parse(beginT)
            if endT == "":
                duration = (datetime.datetime.now().date() - beginT.date()).days
                duration *= 2
            else:
                endT = parser.parse(endT)
                duration = (endT - beginT).days

            beginT = (datetime.datetime.now().date() - beginT.date()).days
            description = issue["description"]
            labels = ','.join(issue["labels"])

            title = issue["title"]
            downvotes = issue["downvotes"]
            upvotes = issue["upvotes"]
            notes_count = issue["notes_count"]

            doc = title + ","  + labels

            self.docs.append(doc)
            self.issues.append([beginT, duration, downvotes, upvotes, notes_count])

        #print("issues count after",len(issues))

        self.vectorize()

        #print("fetched",len(self.Xdata),self.Xdata.shape)

    def __init__(self,projectID=None,trainMode=True):
        self.projectID=projectID
        self.Xdata=None
        self.Ydata=None
        self.issues = []
        self.docs = []
        self.assignees = []
        self.issuesID = []

        self.trainMode=trainMode
        self.db=getHanle()

        config=loadConfig()
        if config["language"]=="ch":
            self.lsa=LSACHFlow()
        elif config["language"]=="en":
            self.lsa=LSAFlow()
        else:
            raise Exception("language not suported")

        self.lsa.name=str(self.projectID)

        if self.trainMode:
            self.initTrainData()
        else:
            self.lsa.loadModel()

    def getDocX(self):

        if self.trainMode:
            self.lsa.train_doctopics(self.docs)

        docX = self.lsa.transformVec(self.docs)

        return docX
    def vectorize(self):
        if len(self.issues)<30 and self.trainMode:
            return
        #lsa.n_features=100
        self.docX=self.getDocX()

        #print(self.docX.shape,len(self.issues))
        self.Xdata=np.concatenate((self.docX,self.issues),axis=1)
        #self.Xdata=np.array(self.issues)

        if self.trainMode==False:
            return

        self.Ydata = np.zeros(shape=len(self.Xdata), dtype=np.int)

        for i in range(len(self.Ydata)):
            assignees=self.assignees[i]
            for user in assignees:
                if user in self.userIndex.keys():
                    index=self.userIndex[user]
                else:
                    index=random.randint(0,len(self.userIndex)-1)
                    print("member outliers exist in issues ID",self.issuesID[i])
                self.Ydata[i]=index
        
        labels=np.unique(self.Ydata)
        alllabels=set(np.arange(len(self.userIndex)))
        misslabels=alllabels.difference(labels)
        xlen=len(self.Xdata[0])
        extraX=[]
        extraY=[]
        for l in misslabels:
            extraX.append(np.zeros(shape=xlen))
            extraY.append(l)

        if len(misslabels)>0:
            extraX=np.array(extraX)
            extraY=np.array(extraY,dtype=np.int)
            self.Xdata=np.concatenate((self.Xdata,extraX),axis=0)
            self.Ydata=np.concatenate((self.Ydata,extraY),axis=0)

        #print("docL,issueL,featureL",len(self.docX[0]),len(self.issues[0]),len(self.Xdata[0]))
        print("==============================================================================\n")

if __name__ == '__main__':
    db = getHanle()
    projects = db["project"]
    for project in projects.find():
        prjid=project["pid"]
        piss=IssueData(prjid)
        piss.vectorize()
