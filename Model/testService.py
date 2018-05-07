import socket,sys,json
from QueryMongoDB.IssueData import IssueData
from QueryMongoDB.ConnectDB import getHanle

if __name__ == '__main__':
    db=getHanle()
    projectID=14155
    issues=db["issue"].find({"project_id":projectID})

    issuedata=IssueData(projectID,trainMode=False)
    issueTrain=IssueData(projectID)
    print("==============================>\n")
    host = '192.168.3.125'
    port = 8010

    testNum=10000
    count=0

    for issue in issues:
        if count>testNum:
            break
        else:
            count+=1

        sock=socket.socket()
        sock.connect((host, port))

        data={
            "created_at":issue["created_at"],
            "closed_at":issue["closed_at"],
            "description":issue["description"],
            "labels":issue["labels"],
            "title":issue["title"],
            "downvotes":issue["downvotes"],
            "upvotes":issue["upvotes"],
            "notes_count":issue["notes_count"],
        }

        request = {
            "mode": "issue",
            "data": data
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