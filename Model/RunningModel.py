import sys
sys.path.append('../')
#print(sys.path)

from Model.GitLabDataSet import *
from Model.CBC import EnsembleClassifier
import socket,json,sys
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler,HTTPServer,SimpleHTTPRequestHandler
from io import BytesIO

class ModelLoader:

    def loadModel(self,projectName):
        projects=self.db["project"].find({"name":projectName})
        #print(projectName,projects.count(),projects)
        projectID=projects[0]["pid"]

        self.predictor.name = str(projectID)
        self.predictor.loadModel()

        with open("../data/saved_ML_models/clusterModels/" + str(projectID) + ".pkl", "rb") as f:
            self.cluster = pickle.load(f)
        with open("../data/filteredUsers/" + str(projectID) + ".pkl", "rb") as f:
            self.filters = pickle.load(f)
        with open("../data/UserIndex/" + str(projectID) + ".pkl", "rb") as f:
            userIndex = pickle.load(f)

        self.UserIndex = {}
        for k in userIndex.keys():
            index = userIndex[k]
            self.UserIndex[index] = k

        self.topK = self.conifg["topK"]
        self.issueInvoker = IssueData(projectID, trainMode=False)

        # print(self.UserIndex)
        # print(self.filters)


        #print("loaded recommender for top%d with %d users\n" % (self.topK, len(self.UserIndex)))


    def __init__(self):

        self.conifg=loadConfig()
        self.db = getHanle()
        self.users = self.db["user"]

        self.predictor=EnsembleClassifier()


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

class RunningService:

    def __init__(self):
        self.config=loadConfig()
        self.port=self.config["port"]
        self.hostIP=self.config["listen-host"]
        self.running=True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recommender=ModelLoader()

    def startTcpService(self):
        self.socket.bind((self.hostIP, self.port))
        self.socket.listen(5)
        print("service listen:",self.hostIP,self.port)
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
                projectname=request["data"]["name"]
                self.recommender.loadModel(projectname)

                #print(request)

                self.recommender.issueInvoker.fetchData(request)

                _,recusers=self.recommender.recommendAssignees(self.recommender.issueInvoker.Xdata)


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

    def startHttpService(self):
        #extract method
        recommender=self.recommender
        #define data handler
        class MySimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                SimpleHTTPRequestHandler.end_headers(self)

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write("OK".encode())

            def do_POST(self):
                self.do_OPTIONS()
            def do_OPTIONS(self):

                #print("==========>headers\n",self.headers,"\n")
                content_length = int(self.headers['Content-Length'])
                #print("rfile",self.rfile)
                body = self.rfile.read(content_length)
                self.send_response(200)
                self.end_headers()
                response = BytesIO()
                #print("===========>body\n",body,"\n")
                request = json.loads(body.decode())
                projectname=request["data"]["name"]
                recommender.loadModel(projectname)
                #print("===========>request data\n",request,"\n")
                recommender.issueInvoker.fetchData(request)

                _, recusers = recommender.recommendAssignees(recommender.issueInvoker.Xdata)

                userIDs=recusers[0].tolist()
                usersnames=[]
                for i in range(len(userIDs)):
                    uid=userIDs[i]
                    usersnames.append(recommender.users.find({"uid":uid})[0]["username"])

                result = {
                    "status": "OK",
                    "users": usersnames,
                    "userIDs":userIDs
                }

                # print(result)

                result = json.dumps(result).encode()
                #print("================>send result\n",result)
                response.write(result)

                self.wfile.write(response.getvalue())
                print("finished one recommendation(%s)=>"%projectname,userIDs,"\n")

        #run http service
        httpd = HTTPServer((self.hostIP, self.port), MySimpleHTTPRequestHandler)
        print("http server start:",httpd.server_address)
        httpd.serve_forever()

if __name__ == '__main__':
    #parse0=ArgumentParser(description="recommender service program",usage="program_file.py projectID")
    #parse0.add_argument("-p", "--port", help="optional argument", dest="port", default="8020")
    #parse0.add_argument("-H", "--host", help="optional argument", dest="host", default="0.0.0.0")
    #args=parse0.parse_args()

    #RunningService.hostIP=args.host
    #RunningService.port=int(args.port)

    model=RunningService()


    #model.StartService()
    model.startHttpService()


