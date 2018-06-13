import sys
sys.path.append('../')
#print(sys.path)

from argparse import ArgumentParser
import numpy as np
from sklearn import ensemble
from sklearn import metrics
import time,pickle
from sklearn.model_selection import GridSearchCV
import warnings
from Model.sortProba import XSort
from Model.GitLabDataSet import DataModel
from QueryMongoDB.ConnectDB import getHanle

warnings.filterwarnings("ignore")

class EnsembleClassifier:

    def initParameters(self):
        self.params={
            'n_estimators':60,
            'criterion':"gini",
            'max_depth':12,
            'min_samples_split':25,
            'min_samples_leaf':13,
            'max_features':"auto",
            'max_leaf_nodes':None,
            'bootstrap':False,
            'n_jobs':-1,
            'verbose':0,
            'class_weight':{0:1,1:1}
        }

    def __init__(self):
        self.initParameters()
        self.verbose=0
        self.name=""
        self.filterUsers=[]

    def sortedPredict(self,X):

        Y_proba=self.predict(X)
        Y=[]

        for i in range(len(Y_proba)):
            yp=Y_proba[i]
            y=[]
            for j in range(len(yp)):
                y.append([j,yp[j]])

            sorter=XSort(y)
            sorter.compare_vec_index=-1
            y=sorter.mergeSort()
            y=np.array(y,dtype=np.int)

            Y.append(y[:,0])

        Y=np.array(Y)

        return Y

    def predict(self,X):
        if  len(X)==0:
            return np.array([],dtype=np.int)
        if self.verbose>0:
            print(self.name," Extrees is predicting")

        Y=self.model.predict_proba(X)

        #filtered users who are in the given list
        for i in range(len(Y)):
            for j in self.filterUsers:
                Y[i][j]=0

        return Y

    def updateParameters(self,paras):
        for k in paras:
            self.params[k]=paras[k]

    def searchParameters(self,dataSet):
        print("searching for best parameters")

        selParas=[
            {'n_estimators':[i for i in range(10,200,10)]},
            {'criterion':["gini","entropy"]},
            {'max_depth':[i for i in range(3,20)]},
            {'min_samples_split':[i for i in range(20,100,5)]},
            {'min_samples_leaf':[i for i in range(5,30,2)]},
            {'max_features':["auto","sqrt","log2",None]},
        ]


        for i in range(len(selParas)):
            para=selParas[i]
            model=ensemble.ExtraTreesClassifier(**self.params)
            gsearch=GridSearchCV(model,para,scoring=metrics.make_scorer(metrics.accuracy_score))
            gsearch.fit(dataSet.trainX,dataSet.trainY)
            print("best para",gsearch.best_params_)
            self.updateParameters(gsearch.best_params_)

        self.model=ensemble.ExtraTreesClassifier(**self.params)

    def trainModel(self,dataSet):
        print("labels\n",np.unique(dataSet.trainY))
        print("training")
        t0=time.time()

       # self.searchParameters(dataSet)
        self.model=ensemble.ExtraTreesClassifier(**self.params)

        self.model.fit(dataSet.trainX,dataSet.trainY)

        t1=time.time()

        #measure training result
        vpredict=self.model.predict(dataSet.trainX)
        #print(vpredict)
        score=metrics.accuracy_score(dataSet.trainY,vpredict)
        print("model",self.name,"trainning finished in %ds"%(t1-t0),"validate score=%f"%score)
    def saveModel(self):
        with open("../data/saved_ML_models/predictorModels/"+self.name+"extrees.pkl","wb") as f:
            pickle.dump(self.model,f,True)
    def loadModel(self):
        with open("../data/saved_ML_models/predictorModels/"+self.name+"extrees.pkl","rb") as f:
            self.model=pickle.load(f)

def runBuldAll():
    print("build all models for all projects")
    db = getHanle()
    projects = db["project"].find()
    for project in projects:
        projectID = project["pid"]
        print("building model for project ID=",projectID)
        #data = DataModel(projectID)
       # try:
        data = DataModel(projectID)
       # except Exception as e:
            
       #     print("data inner error",e.args)
       #     continue

        if len(data.data.userIndex) < 2:
            print("need not train model")
            continue

        if len(data.data.issuesID)<30:
            print("lack data to train model")
            continue

        model = EnsembleClassifier()
        model.name = str(projectID)
        model.trainModel(data)
        model.saveModel()

        print("\ntraining for projectID=", projectID, "finished\n")

if __name__ == '__main__':
    parse0 = ArgumentParser(description="recommender service program", usage="program_file.py projectName")
    parse0.add_argument("-n", "--projectName",
                        help="optional argument for project name",
                        dest="projectName", default="all")
    parse0.add_argument("-m", "--modelName",
                        help="optional argument for model name",
                        dest="modelName", default="all")

    args = parse0.parse_args()

    if args.projectName.lower()=='all':
        runBuldAll()
        exit(0)

    db = getHanle()
    projects = db["project"].find({"name":args.projectName})

    projectID = int(projects[0]["pid"])
    print("building model for project ID=",projectID)
   # try:
    data = DataModel(projectID)
   # except:
   #         print("data inner error")
   #         exit(1)

    if len(data.data.userIndex) < 2:
            print("need not train model")
            exit(2)

    if len(data.data.issuesID)<30:
            print("lack data to train model")
            exit(3)
#    data=DataModel(projectID)
#    if len(data.data.userIndex)<2:
#        print("need not train model")

    model=EnsembleClassifier()

    if args.modelName is not None or args.modelName!='':
        model.name=args.modelName
    else:
        model.name=str(projectID)

    model.trainModel(data)
    model.saveModel()

    print("\ntraining for projectID=",projectID,"finished\n")
