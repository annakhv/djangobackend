from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from  .models import profile, PERSONAL_STATUSES, education, workPlace
from django.urls import reverse
import jwt
import datetime
from newforum.settings import SECRET_KEY
from functools import wraps 
import requests
from django.core import serializers
secretKey=SECRET_KEY
from django.db.models import Q

def token_req(f):
    @wraps(f)
    def decorated(request, *args, **kwargs):
        bearerToken=request.headers['Authorization']
        token=bearerToken.split(" ",1)[1]
        if not token:
            return JsonResponse({'message': "token not valid"})
        try:
            print(token)
            data=jwt.decode(token, secretKey,algorithms=["HS256"] )
        except:
            print("tokennot working")
            return JsonResponse({'message': "token not valid"})
        
        return f(request, *args, **kwargs)
    return decorated

@csrf_exempt
def register_view(request):
    print("hello world")
    body_unicode=request.body.decode('utf-8')
    body=json.loads(body_unicode)
    username=body['username']
    fname=body['firstname']
    lname=body['lastname']
    email=body['email']
    password=body['password']
    _password=body['repeatpassword']
    num = 0
    lenList= [len(username), len(fname) , len(lname) , len(email) , len(password)]
    digitInPassword=[p for p in password if p in "1234567890"]
    if  num  in lenList:
        message="please fill in  all the  fields"
    elif User.objects.filter(username=username).count() > 0:
        message="this username is already in use"
    elif password != _password:
        message="passwords do not match"
    elif len(password) < 6:
        message= "password  should contain at least 6 characters"
    elif len(digitInPassword) == 0:
    
        message= "password should contain at least one digit"
    else:
        message="ok"
        user=User.objects.create_user(username,  email, password)
        user.first_name=fname
        user.last_name=lname
        user.save()
        userprofile=profile.objects.create(user=user)
        print(userprofile)
        userprofile.save()
    data={
        "message" : message
    }
    return JsonResponse(data)
  

@csrf_exempt
def login_view(request):
    body_unicode=request.body.decode('utf-8')
    body=json.loads(body_unicode)
    username=body['username']
    password=body['password']
    user=authenticate(request, username=username, password=password)
    token=jwt.encode({'user':username, 'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=60)}, secretKey,algorithm="HS256"  )
    if user is not None:
        login(request, user)
        userprof=profile.objects.get(user__username=username)
        userprof.is_active=True
        userprof.save()
        return JsonResponse({"res" : True, 'token' : token })
    return JsonResponse({"res" : False})



@csrf_exempt
@token_req
def profile_view(request, username):
    ctx={}
    user=User.objects.filter(username=username).values('first_name', 'last_name', "id")[0]
    firstname=user['first_name']
    lastname=user['last_name']
    ctx["firstname"]=firstname
    ctx["lastname"]=lastname
    id=user['id']
    basicInfo=profile.objects.get(user=id)
    if basicInfo:
       ctx["res"]=True
       if basicInfo.birthdate is not None:
          ctx["Birthdate"]=basicInfo.birthdate
       if basicInfo.currentcountry is not None:
           ctx["Lives in"]=basicInfo.currentcountry
       if basicInfo.relationshipstatus is not None:
           for status in PERSONAL_STATUSES:
               if status[0] == basicInfo.relationshipstatus:
                  ctx["Relationship status"] = status[1]
       if basicInfo.origincountry is not None:
           ctx["From"]=basicInfo.origincountry
    return JsonResponse(ctx)


@csrf_exempt
@token_req
def logout_view(request, username):
        print(request)
        logout(request)
        userProf=profile.objects.get(user__username=username)
        userProf.is_active=False
        userProf.save()
        return JsonResponse({"res":True})


@csrf_exempt
@token_req
def updateProfile_view(request, username):
    body_unicode=request.body.decode('utf-8')
    body=json.loads(body_unicode)
    birthdate=body['birthdate']
    originCountry=body['originCountry']
    currentCountry=body['currentCountry']
    status=body['status']
    print(birthdate)
    birthdateField=birthdate if  birthdate != "birthdate" else None
    originCountryField=originCountry if originCountry != "select" and originCountry !="country of origin"  else None
    currentCountryFIeld=currentCountry if currentCountry != "select" and currentCountry!="current country"  else None
    statusField=status[0:1] if status != "select" and status != "relationship status" else None
    userprofile=profile.objects.filter(user__username=username).count()
    user=User.objects.get(username=username)
    if userprofile == 0 :
        print("profile none")
        profile.objects.create(user=user, birthdate=birthdateField, origincountry=originCountryField, currentcountry=currentCountryFIeld, relationshipstatus=statusField)
        userprofile=profile.objects.filter(user__username=username).values()
        message="profile created successfully"
        print(userprofile)
    else:
        exitinguserprofile=profile.objects.get(user__username=username)
        print(exitinguserprofile)
        exitinguserprofile.currentcountry=currentCountryFIeld if currentCountryFIeld !=None else exitinguserprofile.currentcountry
        exitinguserprofile.relationshipstatus=statusField if statusField != None else  exitinguserprofile.relationshipstatus
        exitinguserprofile.origincountry=originCountryField if originCountryField != None else exitinguserprofile.origincountry
        exitinguserprofile.birthdate=birthdateField if birthdateField != None else exitinguserprofile.birthdate
        exitinguserprofile.save()
        message="profile updated successfully"
        print(exitinguserprofile)
    return JsonResponse({"res" : True, "message": message})


@csrf_exempt
@token_req
def addAndUpdateEdu_view(request, username, id):
    user=User.objects.get(username=username)
    body_unicode=request.body.decode('utf-8')
    body=json.loads(body_unicode)
    level=body['level']
    institution=body['institution']
    country=body['country']
    startdate=body['startdate']
    enddate=body['enddate']
    levelField=level if level!="" and level!="type" else None
    institutionField=institution if institution!="" and institution!="institution" else None
    countryField=country if country !="" and country!="country" and country !="select" else None
    startdateField=startdate if startdate !="" and startdate!="startdate" else None
    enddateField=enddate if enddate != "" and enddate!="enddate" else None
    if id == "add":
       if (institutionField and levelField):
           education.objects.create(user=user, educationType=levelField, institution=institutionField,country=countryField, startDate=startdateField, endDate=enddateField)
           return JsonResponse({"res" : True, "message":"education added successfully" })
       else:
           return JsonResponse({"res" : True, "message":"please fill in all the required fields" })
    else:
        existingEdu=education.objects.get(id=id)
        print(existingEdu)
        existingEdu.educationType=levelField if levelField != None else existingEdu.educationType
        existingEdu.institution=institutionField if institutionField != None else existingEdu.institution
        existingEdu.country=countryField if countryField != None else existingEdu.country
        existingEdu.startDate=startdateField if startdateField != None else existingEdu.startDate
        existingEdu.endDate=enddateField if enddateField != None else existingEdu.endDate
        existingEdu.save()
        return JsonResponse({"res" : True, "message":"education has been updated successfully" })

@csrf_exempt
@token_req
def addAndUpdateWork_view(request, username, id):
    user=User.objects.get(username=username)
    body_unicode=request.body.decode('utf-8')
    body=json.loads(body_unicode)
    workplace=body['workplace']
    country=body['country']
    startdate=body['startdate']
    enddate=body['enddate']
    workField=workplace if workplace!="" and workplace!="workplace" else None
    countryField=country if country !="" and country!="country" and country !="select" else None
    startdateFIeld=startdate if startdate !="" and startdate!="startdate" else None
    enddateField=enddate if enddate != "" and enddate!="enddate" else None
    if id=="add":
       if (workField ):
           workPlace.objects.create(user=user, company=workField, country=countryField, startDate=startdateFIeld, endDate=enddateField)
           return JsonResponse({"res" : True, "message":"workplace added successfully" })
       else:
           return JsonResponse({"res" : True, "message":"please fill in all the required fields" })
    else:
        existingWorkPlace=workPlace.objects.get(id=id)  
        print(existingWorkPlace) 
        existingWorkPlace.company=workField if workField != None else existingWorkPlace.company
        existingWorkPlace.country=countryField if countryField != None else existingWorkPlace.country
        existingWorkPlace.startDate=startdateFIeld if startdateFIeld != None else existingWorkPlace.startDate
        existingWorkPlace.endDate=enddateField if enddateField != None else existingWorkPlace.endDate
        existingWorkPlace.save()
        print(existingWorkPlace)
        return JsonResponse({"res" : True, "message":"workplace has been udated successfully" })


@csrf_exempt
@token_req
def getWork_view(request, username):
    user=User.objects.get(username=username)
    work=workPlace.objects.filter(user=user).count()
    if work != 0:
        workList=workPlace.objects.filter(user=user).values().order_by('endDate')
        for item in workList:
           for data in item:
               if type(item[data])== datetime.date:
                   datestr=item[data].strftime("%m/%d/%Y")
                   item[data]=datestr
        listData=[item for item in workList]
        jsona=json.dumps(listData)
        return JsonResponse({"res" : True, "json" :jsona})
    else:
        return JsonResponse({"res" : False})

@csrf_exempt
@token_req
def getEdu_view(request, username):
    user=User.objects.get(username=username)
    edu=education.objects.filter(user=user).count()
    if edu != 0:
       eduList=education.objects.filter(user=user).values().order_by('endDate')
       for item in eduList:
           for data in item:
               if type(item[data])== datetime.date:
                   datestr=item[data].strftime("%m/%d/%Y")
                   item[data]=datestr
       listData=[item for item in eduList]
       jsona=json.dumps(listData)
       return JsonResponse({"res" : True, "json": jsona})
    else:
        return JsonResponse({"res" : False})


@csrf_exempt
@token_req
def search_view(request, searchtext):
    print(searchtext)
    userDict={}
    if searchtext != "":
       searchtext=searchtext.split(" ")
       for text in searchtext:
           users=User.objects.filter(Q(username__icontains=text) | Q(first_name__icontains=text) | Q(last_name__icontains=text)).values('username', 'first_name', 'last_name')
           if users:
              for user in users:
                  uniqeName=user['username']
                  userDict[uniqeName]=[user['first_name'], user['last_name']]
           else:
                return JsonResponse({"res" : False, 'message':"no user found" })
       jsona=json.dumps(userDict)        
       return JsonResponse({"res" : True, 'json':jsona })
    else:
        return JsonResponse({"res" : False, 'message':"no user found" })



@csrf_exempt
@token_req
def followUser_view(request, thisUsername, otherUsername):
    print("ented follow this user")
    thisProfile=profile.objects.get(user__username=thisUsername)
    otherProfile=profile.objects.get(user__username=otherUsername)
    results= thisProfile.following.all()
    print("this user follow these")
    print(results)
    names=results.filter().values_list('user__username', flat=True)
    if otherUsername not in names:
       thisProfile.following.add(otherProfile)
      # thisProfile.save()
    else:
       thisProfile.following.remove(otherProfile)
       print(otherProfile)
       print(thisProfile.following.all())
    return JsonResponse({"res":True})

@csrf_exempt
@token_req
def ifThisUsernameFollows_view(request, thisUsername, otherUsername):
    print("works if user follows")
    thisUserProfile=profile.objects.get(user__username=thisUsername)
    otherUserProfile=profile.objects.get(user__username=otherUsername).id
    print(thisUserProfile.following.filter(id=otherUserProfile).exists())
    if thisUserProfile.following.filter(id=otherUserProfile).exists():
       return JsonResponse({"following":True})
    else:
       return JsonResponse({"following":False})



@csrf_exempt
@token_req
def getFollowers_view(request, thisUsername):
    userDict={}
    userProfile=profile.objects.get(user__username=thisUsername)
    results=userProfile.follower.all()
    print(results)
    valuesList=results.filter().values('user__username', 'user__first_name', 'user__last_name')
    if valuesList:
        for eachUser in valuesList:
            user=eachUser['user__username']
            userDict[user]=[eachUser['user__first_name'], eachUser['user__last_name']]
        jsona=json.dumps(userDict)  
        return JsonResponse({"res":True, "json": jsona})
    else:
        return JsonResponse({"res":False, "message": "no followers found"})

@csrf_exempt
@token_req
def getFollowing_view(request, thisUsername):
    userDict={}
    userProfile=profile.objects.get(user__username=thisUsername)
    print(userProfile)
    results=userProfile.following.all()
    valuesList=results.filter().values('user__username', 'user__first_name', 'user__last_name')
    print("getfollowingview")
    print(valuesList)
    if valuesList:
        for eachUser in valuesList:
            user=eachUser['user__username']
            userDict[user]=[eachUser['user__first_name'], eachUser['user__last_name']]
        jsona=json.dumps(userDict)  
        return JsonResponse({"res":True, "json": jsona})
    else:
        return JsonResponse({"res":False, "message": "no user is followed by this user"})

@csrf_exempt
@token_req
def deleteEdu_view(resuest, edu_id):
    edu=education.objects.get(id=edu_id)
    print(edu)
    if edu:
       edu.delete()
       return JsonResponse({"res":True, 'message' : "education deleted successfuly"})
    else:
        return JsonResponse({"res":False, 'message' : "no object has been found to remove"})

@csrf_exempt
@token_req
def deleteWork_view(request, work_id):
    work=workPlace.objects.get(id=work_id)
    if work:
       work.delete()
       return JsonResponse({"res":True, 'message' : "workplace deleted successfuly"})
    else: 
       return JsonResponse({"res":False, 'message' : "no object has been found to remove"})