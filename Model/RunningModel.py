from Model.GitLabDataSet import *
from Model.CBC import EnsembleClassifier
import socket,json,sys
from argparse import ArgumentParser

class RunningModel:
    port=8012
    hostIP='192.168.3.125'

    def __init__(self,projectID):

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
        self.issueInvoker=IssueData(projectID,trainMode=False)

        #print(self.UserIndex)
        #print(self.filters)
        print("init recommender for top%d with %d users\n"%(self.topK,len(self.UserIndex)))

    def recommendAssignees(self,X):
        #print("recommend users")
        knos=self.cluster.predict(X)
        Y=[]
        YN=[]
        #print(knos)
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

    def StartService(self):
        self.socket.bind((RunningModel.hostIP, RunningModel.port))
        self.socket.listen(5)
        while self.running:
            connection, address=self.socket.accept()
            print("connect request from",address)
            try:
                connection.settimeout(5)

                dataSize = connection.recv(8)
                #print("received for size", dataSize)

                dataSize = int(dataSize.decode())
                print("request data size=", dataSize)

                if dataSize > 0:
                    connection.send('OK'.encode())
                else:
                    connection.send('Illegal Data size!'.encode())
                    continue

                #print("show data")


                request = bytes()
                block_no=1
                while sys.getsizeof(request)<dataSize:
                    print("recv block#",block_no,"recv data size",sys.getsizeof(request))
                    recv=connection.recv(1024)
                    print("received",recv)
                    request=request+recv
                    block_no+=1

                request=json.loads(request.decode())

                #print(request)

                self.issueInvoker.fetchData(request)

                _,recusers=self.recommendAssignees(self.issueInvoker.Xdata)


                result={
                    "status":"OK",
                    "users":recusers[0].tolist()
                }

                #print(result)

                result=json.dumps(result)
                connection.send(result.encode())

            except Exception  as e:
                print('time out or other error occured',e.args)

            connection.close()
            print()
if __name__ == '__main__':
    parse0=ArgumentParser(description="recommender service program",usage="program_file.py projectID")
    parse0.add_argument("-p", "--projectID", help="optional argument", dest="projectID", default="14155")
    args=parse0.parse_args()
    if args.projectID is not None and args.projectID!='' and int(args.projectID)>0:
        projectID=args.projectID

    projectID = 14155

    data = DataModel(projectID)


    model=RunningModel(projectID)

    Y,YN=model.recommendAssignees(data.testX)
    #print(Y)
    #print()
    for i in range(len(data.testID)):
        print(data.testID[i],YN[i])

    print("\n model-%d predict finished\n"%projectID)

    model.StartService()

