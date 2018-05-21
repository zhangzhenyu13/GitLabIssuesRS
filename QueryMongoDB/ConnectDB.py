from pymongo import MongoClient
import json

def getHanle():
    client=MongoClient("192.168.7.125",27017)
    db=client.get_database("gitlab")
    return db

def getIssues(projectID):
    givenIssues=issues.find({"project_id":projectID})
    return givenIssues
def getCommits(projectID):
    givenCommits=commits.find({"project_id":str(projectID)})
    return givenCommits
def getComments(projectID):
    givenComments=comments.find({"project_id":str(projectID)})
    return givenComments

def loadConfig():
    with open("../data/config.json","r") as f:
        config=json.load(f)
    return config

if __name__ == '__main__':
    db=getHanle()
    projects=db["project"]
    issues=db["issue"]
    commits=db["commit"]
    comments=db["comment"]
    for project in projects.find():
        prjid=project["pid"]
        gissues=getIssues(prjid)
        gcommits=getCommits(prjid)
        gcomments=getComments(prjid)
        print("projectID, users, issues, comments, commits\n",prjid,"#",gissues.count(),gcomments.count(),gcommits.count())
