import socket,sys,json
from QueryMongoDB.IssueData import IssueData

if __name__ == '__main__':
    projectID=14155
    issuedata=IssueData(projectID,trainMode=False)
    issueTrain=IssueData(projectID)
    print("==============================>\n")
    host = '192.168.3.125'
    port = 8010

    testNum=3
    count=0
    for issueid in issueTrain.issuesID:
        if count>testNum:
            break
        else:
            count+=1

        sock=socket.socket()
        sock.connect((host, port))

        request = {
            "mode": "ID",
            "data": issueid
        }
        request=json.dumps(request)

        objsize=int(sys.getsizeof(request))
        print("size=",objsize)
        objsize = str(objsize).encode()
        sock.send(objsize)

        reponse=sock.recv(1024)
        if reponse.decode()=='OK':
            sock.send(request.encode())
            users=sock.recv(1024)

            users=json.loads(users.decode())

            #print(users)
            if users["status"]=="OK":
                print("recommended users:",users["users"])

        sock.close()

        print()