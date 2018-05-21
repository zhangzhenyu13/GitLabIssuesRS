from QueryMongoDB.IssueData import *
from sklearn.cluster import KMeans

class DataSet:

    def __init__(self):
        self.Xdata=[]
        self.Ydata=[]
        self.issueID=[]
        self.clusterID=-1
    def genFilters(self,n_label):
        self.filterUsers=[]
        labels=set(self.Ydata)
        for i in range(n_label):
            if i not in labels:
                self.filterUsers.append(i)

        #print(self.filterUsers)

    def splitData(self,splitRatio):

        train,validate,test=splitRatio

        if len(self.Xdata)==0:
            return

        n=len(self.Xdata)
        train=int(n*train)
        validate=int(n*validate)
        test=int(n*test)
        self.trainX=self.Xdata[:train]
        self.validateX=self.Xdata[train:train+validate]
        self.testX=self.Xdata[train+validate:]

        self.trainY = self.Ydata[:train]
        self.validateY = self.Ydata[train:train + validate]
        self.testY = self.Ydata[train + validate:]
        #print("#%d"%self.clusterID,splitRatio,n)

        self.trainID=self.issueID[:train]
        self.validateID=self.issueID[train:train+validate]
        self.testID=self.issueID[train+validate:]
class DataModel:

    def predictCluster(self,Xdata):
        knos=self.clustermodel.predict(Xdata)
        return knos

    def __init__(self,projectID,splitRatio=(0.8,0.1,0.1)):
        self.data=IssueData(projectID)
        self.data.vectorize()
        self.config=loadConfig()
        self.clusterNum=len(self.data.issuesID)//self.config["cluster_users"]

        self.clustermodel=KMeans(n_clusters=self.clusterNum,verbose=False)

        self.clustermodel.fit(self.data.Xdata)

        with open("../data/saved_ML_models/clusterModels/"+str(projectID)+".pkl","wb") as f:
            pickle.dump(self.clustermodel,f,True)
            pass
        self.dataSet={}
        for i in range(self.clusterNum):
            self.dataSet[i]=DataSet()
            self.dataSet[i].clusterID=i

        knos = self.clustermodel.predict(self.data.Xdata)

        for i in range(len(self.data.Xdata)):
            kno=knos[i]
            self.dataSet[kno].Xdata.append(self.data.Xdata[i])
            self.dataSet[kno].Ydata.append(self.data.Ydata[i])
            #self.dataSet[kno].issueID.append(self.data.issuesID[i])

        filters={}

        for i in range(self.clusterNum):
            self.dataSet[i].genFilters(len(self.data.userIndex))
            filters[i]=self.dataSet[i].filterUsers
            self.dataSet[i].splitData(splitRatio)

        with open("../data/filteredUsers/"+str(projectID)+".pkl","wb") as f:
            pickle.dump(filters,f,True)

        n = len(self.data.Xdata)
        train,validate,test=splitRatio
        self.Xdata=self.data.Xdata
        self.Ydata=self.data.Ydata
        self.issueID=self.data.issuesID

        train = int(n * train)
        validate = int(n * validate)
        test = int(n * test)
        self.trainX = self.Xdata[:train]
        self.validateX = self.Xdata[train:train + validate]
        self.testX = self.Xdata[train + validate:]

        self.trainY = self.Ydata[:train]
        self.validateY = self.Ydata[train:train + validate]
        self.testY = self.Ydata[train + validate:]
        #print("total", splitRatio, n)

        self.trainID=self.issueID[:train]
        self.validateID=self.issueID[train:train+validate]
        self.testID=self.issueID[train+validate:]

if __name__ == '__main__':
    db=getHanle()
    projects=db["project"].find()
    for project in projects:
        projectID=project["pid"]
        DataModel(projectID)
