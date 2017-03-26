import wx
import os
import wx.lib.scrolledpanel as scrolled
class Align_Anal(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, size = (800,600))
        self.SetBackgroundColour((175,224,230))

        #setDict (a dict containing all information but no samples)
        self.setlst = []

        ###HEAD###
        self.topBox = wx.BoxSizer(wx.VERTICAL)
        ##1st sizer##
        fgs = wx.FlexGridSizer(5, 3, 10,0)

        ###Project Name###
        projectName = wx.StaticText(self, wx.NewId(), "Project Name")
        fgs.Add(projectName, flag =  wx.ALIGN_CENTER_HORIZONTAL, border = 7)

        self.projectTextCtrl = wx.TextCtrl(self, wx.NewId(), "My_project", size = (200,-1))
        fgs.Add(self.projectTextCtrl, flag = wx.ALIGN_CENTER_HORIZONTAL, border = 7)
        fgs.Add((-1,-1))

        self.setlst.append(self.projectTextCtrl)

        ###Genome faa file ###
        self.genome_faa(fgs)
        """
        genome = wx.StaticText(self, wx.NewId(), "Genome")
        fgs.Add(genome, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)

        self.GenomeTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        fgs.Add(self.GenomeTextCtrl, proportion = 1, flag = wx.CENTER, border = 7)

        self.buttonFile1 = wx.Button(self, id = 10, label = "Select File") #Add Open File Button
        self.Bind(wx.EVT_BUTTON, self.OpenFile, self.buttonFile1) #Add click event
        fgs.Add(self.buttonFile1, proportion = 1, flag = wx.CENTER, border = -1)

        self.setlst.append(self.GenomeTextCtrl)
        """

        ###ppt File
        ppt = wx.StaticText(self, wx.NewId(), "ppt")
        fgs.Add(ppt, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)

        self.pttTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        fgs.Add(self.pttTextCtrl, proportion = 1, flag = wx.CENTER, border = 7)

        self.buttonFile2 = wx.Button(self, id= 11, label = "Select File") #Add Open File Button
        self.Bind(wx.EVT_BUTTON, self.OpenFile, self.buttonFile2) #Add click event
        fgs.Add(self.buttonFile2, proportion = 1, flag = wx.CENTER, border = -1)

        self.setlst.append(self.pttTextCtrl)
        ###RNT Filefgs
        rnt = wx.StaticText(self, wx.NewId(), "rnt")
        fgs.Add(rnt, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)

        self.rntTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        fgs.Add(self.rntTextCtrl, proportion = 1, flag = wx.CENTER, border = 7)

        self.buttonFile3 = wx.Button(self, id = 12,  label = "Select File") #Add Open File Button
        self.Bind(wx.EVT_BUTTON, self.OpenFile, self.buttonFile3) #Add click event
        fgs.Add(self.buttonFile3, proportion = 1, flag = wx.CENTER, border = -1)

        self.setlst.append(self.rntTextCtrl)
        ##########
        ##2nd Sizer##
        #Trim Picard read (paired-single)
        fgs2 = wx.FlexGridSizer(1, 4, 10,0)
        fgs2.Add((50,10))
        self.trimCheckBox = wx.CheckBox(self, label="Sample Trim")
        self.trimCheckBox.SetValue(False)
        self.trimCheckBox.Bind(wx.EVT_CHECKBOX, self.TrimValue)
        fgs2.Add(self.trimCheckBox, proportion = 1, flag = wx.CENTER, border = -1)

        self.picardCheckBox = wx.CheckBox(self, label = "Metrics (paired-end only)")
        self.picardCheckBox.SetValue(False)
        self.picardCheckBox.Bind(wx.EVT_CHECKBOX, self.picardChoice)
        fgs2.Add(self.picardCheckBox, proportion = 1, flag = wx.CENTER, border = -1)

        self.pairedCheckBox = wx.CheckBox(self, label = "Paired-end")
        self.pairedCheckBox.SetValue(False)
        self.pairedCheckBox.Bind(wx.EVT_CHECKBOX, self.pairedChoice)
        fgs2.Add(self.pairedCheckBox, proportion = 1, flag = wx.CENTER, border = -1)


        #############################
        ##Add / Remove sample buttons
        fgs3 = wx.FlexGridSizer(1,2,10,0)
        self.ReadsDict = {} #ReadsDict
        self.AllDict = {} #Dict with all information
        self.toRemoveDict = {}
        self.sampleList = []

        self.fgs4 = wx.FlexGridSizer(100,3,10,0)

        self.samplenumber = 0
        self.addButton = wx.Button(self, label="Add Sample")
        self.Bind(wx.EVT_BUTTON, self.OnAddWidget, self.addButton)
        fgs3.Add(self.addButton, 0, wx.CENTER|wx.ALL, 5)

        self.removeButton = wx.Button(self, label = "Remove Sample")
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.removeButton)
        fgs3.Add(self.removeButton, 0, wx.CENTER|wx.ALL, 5)

        ####
        #Start Button
        fgs5 = wx.FlexGridSizer(1,3,0,0)
        fgs5.Add((100,-1))
        self.startButton = wx.Button(self, label = "Start")
        self.Bind(wx.EVT_BUTTON, self.StartAnalysis, self.startButton)
        fgs5.Add(self.startButton, 0, wx.CENTER|wx.ALL, 5)


        #create a log panel
        fgs6 = wx.FlexGridSizer(1,0,0,0)
        self.log = wx.TextCtrl(self, -1, size=(800,600),style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        fgs6.Add(self.log,0,wx.CENTER|wx.ALL,5)
        redir=RedirectText(self.log)
        os.sys.stdout=redir
        print 'test'

        ###
        self.topBox.AddSpacer(10)
        self.topBox.Add(fgs, flag= wx.EXPAND |wx.TOP |wx.RIGHT|wx.LEFT, border=25)
        self.topBox.Add(fgs2, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.topBox.Add(fgs3, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.topBox.Add(self.fgs4, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.topBox.Add(fgs5, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.topBox.Add(fgs6, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.SetSizer(self.topBox)
        self.topBox.Fit(self)

        ####


        self.Layout()
        ####
    def genome_faa(self, fgs):

        ###Genome faa file ###
        genome = wx.StaticText(self, wx.NewId(), "Genome")
        fgs.Add(genome, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)

        self.GenomeTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        fgs.Add(self.GenomeTextCtrl, proportion = 1, flag = wx.CENTER, border = 7)

        self.buttonFile1 = wx.Button(self, id = 10, label = "Select File") #Add Open File Button
        self.Bind(wx.EVT_BUTTON, self.OpenFile, self.buttonFile1) #Add click event
        fgs.Add(self.buttonFile1, proportion = 1, flag = wx.CENTER, border = -1)
        self.setlst.append(self.GenomeTextCtrl)


    def OpenFile(self, event):
        dlg = wx.FileDialog(self, "Open File",
                            os.getcwd(), style = wx.OPEN)
        button_id = event.GetId()

        optionDict = self.ButtonOptions()

        for k,v in optionDict.items():
            if button_id == k:
                if dlg.ShowModal() == wx.ID_OK:
                    self.filename = dlg.GetPath()
                    v.SetValue(self.filename)
    def ButtonOptions(self):
        return {10: self.GenomeTextCtrl,
                11: self.pttTextCtrl,
                12: self.rntTextCtrl}
    def TrimValue(self, event):
        sender = event.GetEventObject()
        isChecked = sender.GetValue()
        if isChecked:
            print "Yes"
        else:
            print "No"
    def pairedChoice(self, event):
        sender = event.GetEventObject()
        isChecked = sender.GetValue()
    def picardChoice(self, event):
        sender = event.GetEventObject()
        isChecked = sender.GetValue()

    def OnAddWidget(self, event):
        self.samplenumber += 1
        temp_lst = []
        all_info_lst = []
        # Head
        sample_text = "Sample " + str(self.samplenumber)

         # keep order

        self.fgs4.Add((0,0))
        self.sampleTextNumber = wx.StaticText(self, wx.NewId(), sample_text)
        self.fgs4.Add(self.sampleTextNumber, flag = wx.CENTER, border = 5)
        self.fgs4.Add((0,0))
        all_info_lst.append(self.sampleTextNumber)



        #Sample Name
        text = "Sample name"
        self.Stext = wx.StaticText(self, wx.NewId(), text)
        self.fgs4.Add(self.Stext, flag = wx.CENTER, border = 5)

        self.sampleTxtCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        self.fgs4.Add(self.sampleTxtCtrl, proportion = 1, flag = wx.CENTER, border = 9)
        self.fgs4.Add((0,0))

        temp_lst.append(self.sampleTxtCtrl) # sampleName
        all_info_lst.append(self.Stext)
        all_info_lst.append(self.sampleTxtCtrl)


        ###Condition
        self.conditionText = wx.StaticText(self, wx.NewId(), "Condition")
        self.fgs4.Add(self.conditionText, flag = wx.CENTER, border = 5)

        self.conditionTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        self.fgs4.Add(self.conditionTextCtrl, proportion = 1, flag = wx.CENTER, border = -1)

        self.fgs4.Add((0,0))
        all_info_lst.append(self.conditionText)
        all_info_lst.append(self.conditionTextCtrl)
        temp_lst.append(self.conditionTextCtrl)

        ###Trim
        if self.trimCheckBox.IsChecked():

            self.trim5 = wx.StaticText(self, wx.NewId(), "5' Trim")
            self.fgs4.Add(self.trim5, flag = wx.CENTER, border = 5)

            self.trim5TextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
            self.fgs4.Add(self.trim5TextCtrl, proportion = 1, flag = wx.CENTER, border = -1)
            self.space = self.fgs4.Add((0,0))

            temp_lst.append(self.trim5TextCtrl)
            all_info_lst.append(self.trim5)
            all_info_lst.append(self.trim5TextCtrl)
            all_info_lst.append(self.space)

            if self.pairedCheckBox.IsChecked(): #trim read2
                self.trim3 = wx.StaticText(self, wx.NewId(), "3' Trim")
                self.fgs4.Add(self.trim3, flag = wx.CENTER, border = 5)

                self.trim3TextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
                self.fgs4.Add(self.trim3TextCtrl, proportion = 1, flag = wx.CENTER, border = -1)

                self.space2 = self.fgs4.Add((0,0))
                temp_lst.append(self.trim3TextCtrl)
                all_info_lst.append(self.trim3)
                all_info_lst.append(self.trim3TextCtrl)
                all_info_lst.append(self.space2)

        #Read1
        self.Text = wx.StaticText(self, wx.NewId(), "Read 1")
        self.fgs4.Add(self.Text, flag = wx.CENTER, border = 5)

        self.read1TextCtrl = wx.TextCtrl(self, wx.NewId(), "", size = (200,-1))
        sampletext1 = self.read1TextCtrl
        self.fgs4.Add(self.read1TextCtrl, flag = wx.CENTER | wx.RIGHT, border = 5)

        id_buttonF = wx.NewId()
        self.ReadsDict[id_buttonF] = sampletext1
        self.buttonF = wx.Button(self, id_buttonF, label = "Select File") #Add Open File Button
        self.Bind(wx.EVT_BUTTON, self.OpenReadFile, self.buttonF) #Add click event
        self.fgs4.Add(self.buttonF, proportion = 1, flag = wx.CENTER, border = -1)

        temp_lst.append(self.read1TextCtrl)
        all_info_lst.append(self.Text)
        all_info_lst.append(self.buttonF)
        all_info_lst.append(self.read1TextCtrl)

        if self.pairedCheckBox.IsChecked(): #Get Read2!
            self.Text2 = wx.StaticText(self, wx.NewId(), "Read 2")
            self.fgs4.Add(self.Text2, flag = wx.CENTER, border = 5)

            self.read2TextCtrl = wx.TextCtrl(self, wx.NewId() , "", size = (200,-1))
            sampletext2 = self.read2TextCtrl
            self.fgs4.Add(self.read2TextCtrl, flag = wx.CENTER, border = 5)

            id_buttonF2 = wx.NewId()
            self.ReadsDict[id_buttonF2] = sampletext2
            self.buttonF2 = wx.Button(self, id_buttonF2, label = "Select File") #Add Open File Button
            self.Bind(wx.EVT_BUTTON, self.OpenReadFile, self.buttonF2) #Add click event
            self.fgs4.Add(self.buttonF2, proportion = 1, flag = wx.CENTER, border = -1)

            temp_lst.append(self.read2TextCtrl)
            all_info_lst.append(self.Text2)
            all_info_lst.append(self.buttonF2)
            all_info_lst.append(self.read2TextCtrl)

        self.SetupScrolling()
        self.Layout()
        self.fgs4.Layout()
        self.sampleList.append(self.sampleTxtCtrl)
        self.AllDict[self.sampleTxtCtrl] = temp_lst
        self.toRemoveDict[self.sampleTxtCtrl] = all_info_lst

    def OnRemove(self, event):
        print self.sampleList
        self.samplenumber -=1
        to_remove = self.sampleList[-1]
        for val in self.toRemoveDict[to_remove]:
            self.fgs4.Hide(val)
            self.fgs4.Remove(val)
        del self.sampleList[-1]
        self.SetupScrolling()
        self.Layout()
        self.fgs4.Layout()

    def StartAnalysis(self, event):
        """
        if button:
        Get values from AllDict:
        -sample name
        -Condition
        -Read1
        -Read2 (if paired-end checked)

        Get values from setlst:
        - Project name
        - Genome path and file
        - ppt path and file
        - rnt path and file
        """
        #Common features:
        project = self.setlst[0].GetValue()
        genome = self.setlst[1].GetValue()
        ppt = self.setlst[2].GetValue()
        rnt = self.setlst[3].GetValue()

        for k, v in self.AllDict.items():
            if self.pairedCheckBox.IsChecked(): #for paired-end
                info = self.AllDict[k]
                sample_name, condition, read_1, read_2 = info[0].GetValue(), info[1].GetValue(), info[2].GetValue(), info[3].GetValue()
            else:
                info = self.AllDict[k]
                sample_name, condition, read_1 = info[0].GetValue(), info[1].GetValue(), info[2].GetValue()

            print "Sample", sample_name
            print "Cond", condition
            print "read_1", read_1
            try:
                print "read_2", read_2
            except:
                pass
            print "Proj", project
            print "genome", genome
            print "ptt", ppt
            print "rnt", rnt

            path = os.getcwd()
            project_dir = os.path.join(path, project)
            self.MakeDir(project_dir)
            self.Edge_call2(genome, ppt, rnt, read_1, read_2, project_dir)



    def OpenReadFile(self,event):
        dlg = wx.FileDialog(self, "Open File",
                    os.getcwd(), style = wx.OPEN)
        button_number = event.GetId()
        print button_number
        print self.ReadsDict.keys()
        for k,v in self.ReadsDict.items():
            if k == button_number:
                if dlg.ShowModal() == wx.ID_OK:
                    self.filename = dlg.GetPath()
                    v.SetValue(self.filename)

    def Edge_call2(self, Reference_genome, ptt, rnt, R1_file, R2_file, OUTPUT_PATH):
        os.system("/home/kaihami/EDGE_pro_v1.3.1/edge.pl -g " + Reference_genome +
              " -p "+ ptt +
              " -r " + rnt +
              " -u " + R1_file +
              " -v " + R2_file +
              " -o " + OUTPUT_PATH)
    def MakeDir(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
class RedirectText:
    #Print log class
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        self.out.WriteText(string)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent = None, title = "iBRA", size = (800,600))
        self.createMenuBar()
        panel = wx.Panel(self)
        nb = wx.Notebook(panel)

        tab1 = Align_Anal(nb)
        #tab2 = Align(nb)
        #tab3 = Anal(nb)

        nb.AddPage(tab1, "iBRA")
        #nb.AddPage(tab2, "Alignment")
        #nb.AddPage(tab3, "Statistics")

        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        panel.SetSizer(sizer)


        self.Show()


    def menuData(self):
        return [
            ("&File", (("&New", "New file", self.OnNew),
                         ("&Open", "Open file", self.OnOpen),
                         ("","",""),
                         ("&Quit", "Quit", self.OnCloseWindow))),

            ("Tools", (("&Align", "Alignment", self.OnAlign),
                        ("DEG", "Differential Expressed Genes", self.OnDeg)))
            ]
    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)
    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachItem in menuData:
            if len(eachItem) == 2:
                label = eachItem[0]
                subMenu = self.createMenu(eachItem[1])
                menu.AppendMenu(wx.NewId(), label, subMenu)
            else:
                self.createMenuItem(menu, *eachItem)
        return menu
    def createMenuItem(self, menu, label, status, handler,
                       kind = wx.ITEM_NORMAL):
        if not label:
            menu.AppendSeparator()
            return
        menuItem = menu.Append(-1, label, status, kind)
        self.Bind(wx.EVT_MENU, handler, menuItem)

    def OnNew(self,event):
        pass
    def OnOpen(self, event):
        dlg = wx.FileDialog(self, "Open File",
                            os.getcwd(), style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.ReadFile()
            print self.filename
    def ReadFile(self):
        print "File read"

    def OnSave(self, event):
        pass
    def OnCloseWindow(self,event):
        self.Destroy()
    def OnAlign(self, event):
        pass
    def OnDeg(self, evetn):
        pass
if __name__ == "__main__":
    app = wx.App(redirect=False)
    frame = MyFrame()
    app.MainLoop()