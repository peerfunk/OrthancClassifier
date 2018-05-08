import tkinter as tk
from tkinter.ttk import Frame, Button, Style
from PIL import Image, ImageTk
import json
import urllib.request
import queue
import threading
import time
from io import BytesIO
#eigentlich ein producer, consumer-pattern wobei es 1 worker gibt = die eingebende person und 1 master = imageloader
class Example():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Join")
        self.window.geometry("300x300")
        self.window.configure(background='grey')
        
        self.orth = OrthancLoader(';')

        #implement 1 thread that loads the queue
        self.imageQ = queue.Queue(10)
        self.t = threading.Thread(target=self.fill_image_queue)
        self.t.daemon = True
        self.t.start()

        
        while(self.imageQ.empty()):
            time.sleep(1)
            print('Warte auf erste Bild')
        self.curimg = self.imageQ.get()
        img = ImageTk.PhotoImage(self.curimg.image) #Image.open(path)
        self.window.title(self.curimg.string)
        self.panel = tk.Label(self.window, image=img)
        self.panel.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        self.window.bind('<Key>',self.cathegorize_current )
   
        self.window.mainloop()
        
    def update_image(self):
        if not self.imageQ.empty():
            self.curimg = self.imageQ.get()
            img = ImageTk.PhotoImage(self.curimg.image) #Image.open(path)
            self.window.title(self.curimg.string)
            self.window.geometry(str(img.width()) + "x" + str(img.height()))
          
            self.panel.configure(image=img)
            self.panel.image = img

            
            
    def cathegorize_current(self, event):
        if (self.curimg != None and event.keysym in ['k','h','p','n','u'] and not self.imageQ.empty()):
            string =(self.curimg.string + event.keysym)
            print(string)
            self.orth.writeToFile('classification.csv',string)
            self.curimg=None
            self.update_image()
            
        else:
            print('Kein Bild verfuegbar bitte warten!')
    def fill_image_queue(self): #thread1
        while True:
            if not self.imageQ.full():
                print("---------------------------------------------------")
                print("ImageQ:")
                
                DO=self.orth.getNextImage()
                DO.image = Image.open(BytesIO(DO.image))
                DO.image = DO.image.resize((512,512))
                self.imageQ.put(DO)
                print("---------------------------------------------------")
        
class dataObject:
    def __init__(self, string, image):
        self.string = string
        self.image = image

class OrthancLoader():
    def __init__(self, delim):
        self.studies = self.getStudies()
        self.curIndex = 0
      
        self.delim = delim
        self.maxIndex = len(self.studies)
        self.initIndexFromFile()
        #self.writeAllToFile("auto.csv")
    def get(self, url):
        return json.load(urllib.request.urlopen('http://192.168.10.2:8042/'+url))
    def getStudies(self):
        return self.get('studies')#patients
    def getStudy(self, ID):
        return self.get('studies/'+ ID)
    def getNextStudy(self):
        if(self.curIndex < self.maxIndex):
            img = self.getStudy(self.studies[self.curIndex])
            self.curIndex += 1
            return img
        else:
            return False
    def setcurIndex(self, index):
        self.curIndex=index
    def initIndexFromFile(self):
        self.setcurIndex(self.getLastIndex())
    def getLastIndex(self):
        filename='classification.csv'
        import os
        if os.path.isfile(filename):
            with open(filename) as file:
                current = list(file)[-1].split(self.delim)[0]
            return self.getIndexOfID(current)+1
        else:
            return 0
    def getIndexOfID(self,ID):
        try:
            return self.studies.index(ID)
        except:
            return 0
    def getSeries(self, ID):
        return self.get('series/'+ ID)
    def getInstance(self, ID):
        return self.get('instance/' + ID)
    def getInstancefromStudy(self, studyJSON):
        return self.getSeries(studyJSON['Series'][0])['Instances'][0]
    def getLastPatientDataString(self):
        ID = self.getPatientDataString(self.getStudy(self.studies[self.curIndex]))
        print("Lade Letzten Patienten aus Tabelle")
        return ID
    def getPatientDataString(self,json):
        print(json)
        return json['ID'] + self.delim + json['MainDicomTags']['StudyDate'] + self.delim + json['PatientMainDicomTags']['PatientName'] + self.delim
    def getStudySingleImage(self):
        #print("Lade naechstes Bild")
        print(self.studies[self.curIndex] + '  ')
        #print (self.getNextStudy())
        url = 'http://192.168.10.2:8042/instances/' + self.getInstancefromStudy(self.getNextStudy())+ '/preview' #
        print(url)
        u =urllib.request.urlopen(url)
        rawData = u.read()
        u.close()
        return (rawData)
    def countSeries(self,studyJSON):
        return len(studyJSON['Series'])
    def getNextImage(self):
        print(self.curIndex)
        study = self.getNextStudy()#self.getStudy(self.studies[self.curIndex])
        instance = self.getInstancefromStudy(study)
        #print(instance)
        studyId=study['ID']
        pName=study['PatientMainDicomTags']['PatientName']
        sTime=study['MainDicomTags']['StudyDate']
        retStringp= studyId + self.delim + pName + self.delim + sTime + self.delim + str(self.countSeries(study)) + self.delim
        url = 'http://192.168.10.2:8042/instances/' + instance + '/preview'
        print(url)
        u =urllib.request.urlopen(url)
        rawData = u.read()
        u.close()
        data = dataObject(retStringp, rawData)
        return (data)
    def writeAllToFile(self,filename):
        print('Schreibe alle in file')
        with open(filename, 'a') as csvfile:
            while self.curIndex <= self.maxIndex :
                string= self.getLastPatientDataString()+'\n'
                print(string)
                csvfile.write(string)
                self.getNextStudy()
    def writeToFile(self,filename, text):
        with open(filename, 'a') as csvfile:
                csvfile.write(text+'\n')

app = Example()

#orth = OrthancLoader(';')
##orth.getNextImage()
#orth.getNextImage()
#orth.getNextImage()
#orth.getNextImage()
#orth.getNextImage()
#orth.getNextImage()
#orth.getNextImage()

