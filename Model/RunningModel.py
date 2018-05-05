from Model.GitLabDataSet import *
from Model.CBC import EnsembleClassifier
import threading,socket

class RunningModel(threading.Thread):

    def __init__(self,projectID):
        threading.Thread.__init__(self)

        self.running=True

        self.socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.predictor=EnsembleClassifier()

        self.predictor.name=str(projectID)
        self.predictor.loadModel()

        with open("../data/saved_ML_models/clusterModels/"+str(projectID)+".pkl","rb") as f:
            self.cluster=pickle.load(f)
        with open("../data/filteredUsers/"+str(projectID)+".pkl","rb") as f:
            self.filters=pickle.load(f)
        with open("../data/UserIndex/"+str(projectID)+".pkl","rb") as f:
            userIndex=pickle.load(f)

        self.UserIndex={}
        for k in userIndex.keys():
            index=userIndex[k]
            self.UserIndex[index]=k

        self.topK=5
        print(self.UserIndex)
        print(self.filters)
        print("init recommender for top%d with %d users"%(self.topK,len(self.UserIndex)))

    def recommendAssignees(self,X):
        knos=self.cluster.predict(X)
        Y=[]
        YN=[]
        print(knos)
        for i in range(len(X)):
            kno=knos[i]

            self.predictor.filterUsers=self.filters[kno]
            x=[X[i]]
            y=self.predictor.sortedPredict(x)

            y=y[0][:self.topK]
            Y.append(y)

            yn=[]
            for j in y:
                yn.append(self.UserIndex[j])
            YN.append(yn)

        Y=np.array(Y,dtype=np.int)
        YN=np.array(YN,dtype=np.int)

        return Y,YN

    def run(self):
        self.socket.bind(('localhost', 8001))
        self.socket.listen(5)
        while self.running:
            connection, address=self.socket.accept()
            try:
                connection.settimeout(5)
                buf = connection.recv(1024)
                if buf == '1':
                    connection.send('welcome to server!')
                else:
                    connection.send('please go out!')
            except :
                print('time out or other error occured')
            connection.close()

if __name__ == '__main__':
    db = getHanle()
    projects = db["project"].find()
    pool_models={}
    for project in projects:
        projectID = project["pid"]

        data = DataModel(projectID)
        if len(data.data.userIndex)<2:
            print("no models built")
            continue

        model=RunningModel(projectID)
        pool_models[projectID]=model

        Y,YN=model.recommendAssignees(data.testX)
        print(Y)
        print()
        print(YN)

        print("\n model-%d predict finished\n"%projectID)

