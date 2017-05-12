import wx
import os
import wx.lib.scrolledpanel as scrolled
from bs4 import BeautifulSoup
from urllib2 import urlopen
from threading import *
from multiprocessing import cpu_count, Pool
import datetime
from Bio.KEGG.REST import kegg_get
from Bio.Blast import NCBIXML
from numpy import std
from scipy.stats import linregress
from math import log
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from collections import Counter
import collections
import itertools


##########################
class ACTextControl(wx.TextCtrl):
    """
    A Textcontrol that accepts a list of choices at the beginning.
    Choices are presented to the user based on string being entered.
    If a string outside the choices list is entered, option may
    be given for user to add it to list of choices.
    match_at_start - Should only choices beginning with text be shown ?
    add_option - Should user be able to add new choices
    case_sensitive - Only case sensitive matches
    https://github.com/RajaS/ACTextCtrl/blob/master/actextcontrol.py
    """

    def __init__(self, parent, candidates=[], match_at_start=False,
                 add_option=False, case_sensitive=False, size=(600,-1)):

        wx.TextCtrl.__init__(self, parent,wx.NewId(), style=wx.TE_PROCESS_ENTER, size = size)

        self.all_candidates = candidates
        self.match_at_start = match_at_start
        self.add_option = add_option
        self.case_sensitive = case_sensitive
        self.max_candidates = 5  # maximum no. of candidates to show
        self.select_candidates = []
        self.popup = ACPopup(self)

        self._set_bindings()

        self._screenheight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        self._popdown = True  # Does the popup go down from the textctrl ?

    def _set_bindings(self):
        """
        One place to setup all the bindings
        """
        # text entry triggers update of the popup window
        self.Bind(wx.EVT_TEXT, self._on_text, self)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down, self)

        # loss of focus should hide the popup
        self.Bind(wx.EVT_KILL_FOCUS, self._on_focus_loss)
        self.Bind(wx.EVT_SET_FOCUS, self._on_focus)

    def _SetValue(self, value):
        """
        Directly calling setvalue triggers textevent
        which results in popup appearing.
        To avoid this, call changevalue
        """
        super(ACTextControl, self).ChangeValue(value)

    def _on_text(self, event):
        """
        On text entry in the textctrl,
        Pop up the popup,
        or update candidates if its already visible
        """
        txt = self.GetValue()

        # if txt is empty (after backspace), hide popup
        if not txt:
            if self.popup.IsShown:
                self.popup.Show(False)
                event.Skip()
                return

        # select candidates

        if self.match_at_start and self.case_sensitive:
            self.select_candidates = [ch for ch in self.all_candidates
                                      if ch.startswith(txt)]
        if self.match_at_start and not self.case_sensitive:
            self.select_candidates = [ch for ch in self.all_candidates
                                      if ch.lower().startswith(txt.lower())]
        elif self.case_sensitive and not self.match_at_start:
            self.select_candidates = [ch for ch in self.all_candidates if txt in ch]
        else:
            self.select_candidates = [ch for ch in self.all_candidates if txt.lower() in ch.lower()]

        if len(self.select_candidates) == 0:
            if not self.add_option:
                if self.popup.IsShown():
                    self.popup.Show(False)

            else:
                display = ['Add ' + txt]
                self.popup._set_candidates(display, 'Add')
                self._resize_popup(display, txt)
                self._position_popup()
                if not self.popup.IsShown():
                    self.popup.Show()

        else:
            self._show_popup(self.select_candidates, txt)

    def _show_popup(self, candidates, txt):
        # set up the popup and bring it on
        self._resize_popup(candidates, txt)
        self._position_popup()

        candidates.sort()

        if self._popdown:
            # TODO: Allow custom ordering
            self.popup._set_candidates(candidates, txt)
            self.popup.candidatebox.SetSelection(0)

        else:
            candidates.reverse()
            self.popup._set_candidates(candidates, txt)
            self.popup.candidatebox.SetSelection(len(candidates) - 1)

        if not self.popup.IsShown():
            self.popup.Show()

    def _on_focus_loss(self, event):
        """Close the popup when focus is lost"""
        if self.popup.IsShown():
            self.popup.Show(False)

    def _on_focus(self, event):
        """
        When focus is gained,
        if empty, show all candidates,
        else, show matches
        """
        txt = self.GetValue()
        if txt == '':
            self.select_candidates = self.all_candidates
            self._show_popup(self.all_candidates, '')
        else:
            self._on_text(event)

    def _position_popup(self):
        """Calculate position for popup and
        display it"""
        left_x, upper_y = self.GetScreenPositionTuple()
        _, height = self.GetSizeTuple()
        popup_width, popup_height = self.popupsize

        if upper_y + height + popup_height > self._screenheight:
            self._popdown = False
            self.popup.SetPosition((left_x, upper_y - popup_height))
        else:
            self._popdown = True
            self.popup.SetPosition((left_x, upper_y + height))

    def _resize_popup(self, candidates, entered_txt):
        """Calculate the size for the popup to
        accomodate the selected candidates"""
        # Handle empty list (no matching candidates)
        if len(candidates) == 0:
            candidate_count = 3.5  # one line
            longest = len(entered_txt) + 4 + 4  # 4 for 'Add '

        else:
            # additional 3 lines needed to show all candidates without scrollbar
            candidate_count = min(self.max_candidates, len(candidates)) + 2.5
            longest = max([len(candidate) for candidate in candidates]) + 4

        charheight = self.popup.candidatebox.GetCharHeight()
        #charwidth = self.popup.candidatebox.GetCharWidth()

        self.popupsize = wx.Size(400, charheight * candidate_count)

        self.popup.candidatebox.SetSize(self.popupsize)
        self.popup.SetClientSize(self.popupsize)

    def _on_key_down(self, event):
        """Handle key presses.
        Special keys are handled appropriately.
        For other keys, the event is skipped and allowed
        to be caught by ontext event"""
        skip = True
        visible = self.popup.IsShown()
        sel = self.popup.candidatebox.GetSelection()

        # Escape key closes the popup if it is visible
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            if visible:
                self.popup.Show(False)

        # Down key for navigation in list of candidates
        elif event.GetKeyCode() == wx.WXK_DOWN:
            if not visible:
                skip = False
                pass
            #
            if sel + 1 < self.popup.candidatebox.GetItemCount():
                self.popup.candidatebox.SetSelection(sel + 1)
            else:
                skip = False

        # Up key for navigation in list of candidates
        elif event.GetKeyCode() == wx.WXK_UP:
            if not visible:
                skip = False
                pass
            if sel > -1:
                self.popup.candidatebox.SetSelection(sel - 1)
            else:
                skip = False

        # Enter - use current selection for text
        elif event.GetKeyCode() == wx.WXK_RETURN:
            if not visible:
                # TODO: trigger event?
                pass
            # Add option is only displayed
            elif len(self.select_candidates) == 0:
                if self.popup.candidatebox.GetSelection() == 0:
                    self.all_candidates.append(self.GetValue())
                self.popup.Show(False)

            elif self.popup.candidatebox.GetSelection() == -1:
                self.popup.Show(False)

            elif self.popup.candidatebox.GetSelection() > -1:
                self.SetValue(self.select_candidates[self.popup.candidatebox.GetSelection()])
                self.SetInsertionPointEnd()
                self.popup.Show(False)

        # Tab  - set selected choice as text
        elif event.GetKeyCode() == wx.WXK_TAB:
            if visible:
                self._SetValue(self.select_candidates[self.popup.candidatebox.GetSelection()])
                # set cursor at end of text
                self.SetInsertionPointEnd()
                skip = False

        if skip:
            event.Skip()

    def get_choices(self):
        """Return the current choices.
        Useful if choices have been added by the user"""
        return self.all_candidates

class ACPopup(wx.PopupWindow):
    """
    The popup that displays the candidates for
    autocompleting the current text in the textctrl
    """

    def __init__(self, parent):
        wx.PopupWindow.__init__(self, parent)
        self.candidatebox = wx.SimpleHtmlListBox(self, -1, choices=[])

        self.SetSize((100, 100))

        self.displayed_candidates = []

    def _set_candidates(self, candidates, txt):
        """
        Clear existing candidates and use the supplied candidates
        Candidates is a list of strings.
        """
        # if there is no change, do not update
        if candidates == sorted(self.displayed_candidates):
            pass

        # Remove the current candidates
        self.candidatebox.Clear()

        # self.candidatebox.Append(['te<b>st</b>', 'te<b>st</b>'])
        for ch in candidates:
            self.candidatebox.Append(self._htmlformat(ch, txt))

        self.displayed_candidates = candidates

    def _htmlformat(self, text, substring):
        """
        For displaying in the popup, format the text
        to highlight the substring in html
        """
        # empty substring
        if len(substring) == 0:
            return text

        else:
            return text.replace(substring, '<b>' + substring + '</b>', 1)

def threaded(fn):
    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper

##########################

class GREPy(scrolled.ScrolledPanel):
    def __init__(self, parent):

        scrolled.ScrolledPanel.__init__(self, parent, size = (800,600))
        self.SetBackgroundColour((175,224,230))

        #setDict (a dict containing all information but no samples)
        self.setlst = []

        ###HEAD###
        self.topBox = wx.BoxSizer(wx.VERTICAL)
        ##1st sizer##
        fgs = wx.FlexGridSizer(1, 2, 10,0)

        ###Project Name###
        projectName = wx.StaticText(self, wx.NewId(), "Project Name")
        fgs.Add(projectName, flag =  wx.ALIGN_CENTER_HORIZONTAL, border = 7)

        self.projectTextCtrl = wx.TextCtrl(self, wx.NewId(), "My_project", size = (200,-1))
        fgs.Add(self.projectTextCtrl, flag = wx.ALIGN_CENTER_HORIZONTAL, border = 7)
        fgs.Add((-1,-1))

        self.setlst.append(self.projectTextCtrl)

            ###Genome faa file ###
        fgs6 = wx.FlexGridSizer(2,0,0,0)
        info = self.strains().keys()

        label1 = wx.StaticText(self, -1, 'Matches anywhere in string')
        ctrl1 = ACTextControl(self, candidates=info, add_option=False)

        fgs6.Add(label1,0, wx.CENTER|wx.ALL)
        fgs6.Add(ctrl1,0,wx.CENTER)

        # keg_code = self.strains()[ctrl1]
        self.setlst.append(ctrl1)

        fgs2 = wx.FlexGridSizer(6,2,10,0)

        self.protein_label = wx.StaticText(self, -1, 'Protein 1')
        self.proteinTextCtrl = wx.TextCtrl(self, wx.NewId(), "", size=(200, -1))
        fgs2.Add(self.protein_label, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)
        fgs2.Add(self.proteinTextCtrl, flag = wx.CENTER, border = -1)

        self.protein_label2 = wx.StaticText(self, -1, 'Protein 2')
        self.proteinTextCtrl2 = wx.TextCtrl(self, wx.NewId(), "", size=(200, -1))
        fgs2.Add(self.protein_label2, flag = wx.ALIGN_CENTRE_HORIZONTAL, border = 7)
        fgs2.Add(self.proteinTextCtrl2, flag = wx.CENTER, border = -1)

        self.setlst.append(self.proteinTextCtrl)
        self.setlst.append(self.proteinTextCtrl2)
        #fgs3 = wx.FlexGridSizer(2, 0, 0, 0)
        #self.protein_fasta_label = wx.StaticText(self, -1, "or Protein Fasta 1")
        #self.proteinTextCtrlFasta = wx.TextCtrl(self, wx.NewId(), "", size=(250, 100))
        #fgs3.Add(self.proteinTextCtrlFasta, flag=wx.CENTER, border=-1)

        #self.setlst.append(self.proteinTextCtrlFasta)
        ####
        #Start Button
        fgs5 = wx.FlexGridSizer(1,3,0,0)
        fgs5.Add((100,-1))
        self.startButton = wx.Button(self, label = "Start")
        self.Bind(wx.EVT_BUTTON, self.StartAnalysis, self.startButton)

        fgs5.Add(self.startButton, 0, wx.CENTER|wx.ALL, 5)


        #create a log panel
        fgs20 = wx.FlexGridSizer(1, 3, 0, 0)
        self.log = wx.TextCtrl(self, -1, size=(600,200),style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        fgs20.Add(self.log,0,wx.CENTER|wx.ALL,5)
        redir=RedirectText(self.log)
        os.sys.stdout=redir

        ###
        self.topBox.AddSpacer(10)

        self.topBox.Add(fgs, flag= wx.EXPAND |wx.TOP |wx.RIGHT|wx.LEFT, border=25)

        self.topBox.Add(fgs6, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.CENTER, border=25)
        self.topBox.Add(fgs2, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.CENTER, border=25)
        #self.topBox.Add(fgs3, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.CENTER, border=25)
        #self.topBox.Add(fgs2, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        #self.topBox.Add(fgs3, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        #self.topBox.Add(self.fgs4, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.topBox.Add(fgs5, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)

        self.topBox.Add(fgs20, flag= wx.EXPAND|wx.LEFT|wx.TOP| wx.CENTER, border=25)
        self.SetSizer(self.topBox)
        self.topBox.Fit(self)

        ####


        self.Layout()
        ####

    def strains(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.join(dir_path,'Organism_DB.txt')

        database = open(base_dir,'r').read().split('\n')
        Database_hash = defaultdict(list)

        for line in database:
            if "#" not in line:
                if len(line.split("\t")) >1:
                    organim_id = line.split("\t")[0]
                    strain = line.split("\t")[1]
                    Database_hash[strain] = organim_id

        return Database_hash

    @threaded
    def StartAnalysis(self, event):
        '''
        NarL = PA3879
        NarX = PA3878
        AtpC = b3731
        AtpG = b3733
        '''
        self.startButton.Disable()
        #Get values from setlst
        #TODO: max gap (10%), min identity (default 20), max identity (default 90)
        #TODO: min entropy (5%)

        dir_path = os.path.dirname(os.path.realpath(__file__))

        project = self.setlst[0].GetValue()
        strain = self.setlst[1].GetValue()
        protein1 = self.setlst[2].GetValue()
        protein2 = self.setlst[3].GetValue()

        KEGG_id = self.strains()[strain]

        ######################
        ###Starting Project###
        ######################

        #Make project dir
        project_directory = os.path.join(dir_path, project)
        try:
            os.mkdir(project_directory)
        except:
            print "Dir already exist"

        #Count Time
        start_mid = datetime.datetime.now().replace(microsecond=0)

        #To find is the protein to find in KEGG DB, formart org:locus e.g. pau:PA14_26570
        to_find1 = KEGG_id + ":" + protein1
        to_find2 = KEGG_id + ":" + protein2


        print "Project: " + project
        print "Strain: " + strain
        print "Protein1:", protein1
        print "Protein2:", protein2
        print to_find1
        print to_find2
        print "-"*30

        #Find best hit of protein1
        print "Find best hit of", to_find1
        query1 = self.KEGG_best_hit(to_find1)
        print "Done"
        end_time_query1 = datetime.datetime.now().replace(microsecond=0)
        print "Parcial time: %s" % (end_time_query1 - start_mid)
        print "-"*30

        #Find best hit of protein2
        print "Find best hit of", to_find2
        query2 = self.KEGG_best_hit(to_find2)
        print "Done"
        end_time_query2 = datetime.datetime.now().replace(microsecond=0)
        print "Parcial time: %s" % (end_time_query2 - start_mid)
        print "-" * 30

        ########################
        ###Find best-best hit###
        ########################

        #query1 = ['pau:PA14_26570', 'pau:PA14_00800','pau:PA14_72420','pae:PA2899' ]
        #query2 = ['pau:PA14_26570', 'pau:PA14_00800', 'pau:PA14_72420','pae:PA2899']

        #Multiprocess now is (max number of Threads -1) * 12 = 36

        print "Multiprocess"
        time_1 = str(datetime.timedelta(seconds=(len(query1)/30)*30))
        time_2 = str(datetime.timedelta(seconds=(len(query2)/30)*30))
        time_3 = str(datetime.timedelta(seconds=( (len(query1) + len(query2) ) / 30) * 30) )
        print "Estimated time for protein 1:", str(time_1)
        print "Estimated time for protein 2:", str(time_2)
        print "Worst case time:", str(time_3)
        print "Getting best-best of", protein1

        #Stupid class initialization for parallel computing; Windows problem(?)
        start_best_best1 = datetime.datetime.now().replace(microsecond=0)

        query_1_class = someClass()

        #Get best-best of query1, will return a list of best-best (org:locus)
        #Note will return empty elements as well
        go_best_best_1 = query_1_class.go(protein1,query1)

        #Time for Best-best of protein 1
        end_best_best1 = datetime.datetime.now().replace(microsecond=0)
        print "Total time best-best hit of", protein1 + str(" %s") %(end_best_best1 - start_best_best1)
        print "Parcial time: %s" % (end_best_best1 - start_mid)

        end_mid = datetime.datetime.now().replace(microsecond=0)

        print "Writing info"
        path_to_log = os.path.join(project_directory, "log.txt")

        with open(path_to_log, "a") as f:
            f.write(str(end_mid - start_mid))
            f.write("\n")
            f.write(str(len(query1)))
            f.write("\n")
        print "Saving Best-best", protein1

        ###########
        #list of best-best orgs in protein 1
        filter_protein_2 = []

        locus_protein1_path = os.path.join(project_directory,"locus_"+protein1+".txt")

        for ele in go_best_best_1:
            if ele != "":
                filter_protein_2.append(ele.split(":")[0])
                with open(locus_protein1_path ,"a") as f:
                    f.write(str(ele))
                    f.write("\n")

        ###############
        #We don't need to pick all best-best for protein 2, only the same orgs in query2
        query2_hash = {}

        for ele in query2:
            keg_org = ele.split(":")[0]
            query2_hash[keg_org] = ele
        filtered_query2 = []
        for org in filter_protein_2:
            if org in query2_hash.keys():
                filtered_query2.append(query2_hash[org])
        print len(filtered_query2)

        ###########################

        start_best_best2 = datetime.datetime.now().replace(microsecond=0)

        query_2_class = someClass()

        go_best_best_2 = query_2_class.go(protein2,filtered_query2)

        end_best_best2 = datetime.datetime.now().replace(microsecond=0)
        print "Total time best-best hit of", protein2 + str(" %s") %(end_best_best2 - start_best_best2)
        with open(path_to_log, "a") as f:
            f.write("Found Best-best hit of "+ str(protein2)+" in ")
            f.write(str(end_best_best2 - start_best_best2))
            f.write("\n")
            f.write("Elapsed time: ")
            f.write(str((end_best_best2 - start_mid)))
            f.write("\n")
        print "Parcial time: %s" % (end_best_best2 - start_mid)

        ############################################
        end_mid2 = datetime.datetime.now().replace(microsecond=0)
        locus_protein2_path = os.path.join(project_directory,"locus_"+protein2+".txt")

        for ele in go_best_best_1:
            if ele != "":
                with open(locus_protein2_path, "a") as f:
                    f.write(str(ele))
                    f.write("\n")

        #############################
        best_best_hash_1 = {}
        best_best_hash_2 = {}


        #Build a Function
        for e in go_best_best_1:
            if ":" in e:
                kegg_symbol = e.split(":")[0]
                if e in best_best_hash_1.keys():
                    print "Already found"
                if e not in best_best_hash_1.keys():
                    best_best_hash_1[kegg_symbol] = e
        for e in go_best_best_2:
            if ":" in e:
                kegg_symbol = e.split(":")[0]
                if e in best_best_hash_2.keys():
                    print "Already found"
                if e not in best_best_hash_2.keys():
                    best_best_hash_2[kegg_symbol] = e
        first_common_hash = {}
        for k in best_best_hash_1.keys():
            if k in best_best_hash_2.keys():
                first_common_hash[k]= [best_best_hash_1[k], best_best_hash_2[k]]
        end_x = datetime.datetime.now().replace(microsecond=0)
        path_common_1 = os.path.join(project_directory,"Co-occurrence_first_filter.txt")
        for k,v in first_common_hash.items():
            with open(path_common_1, "a") as f:
                f.write(str(k))
                f.write("\t")
                f.write("\t".join(v))
                f.write("\n")
        print "Parcial time: %s" % (end_x - start_mid)
        #Write Log
        with open(path_to_log, "a") as f:
            f.write(str(end_x - start_mid))
            f.write("\t")
            f.write("Writing Common files ")
            f.write("\n")


        #############################################
        #Fasta files

        ####Super slow parallel search (!) later: 40 min!!!! 1st try

        #build a list of query
        fasta_protein_1_lst = []
        fasta_protein_2_lst = []

        for v in first_common_hash.values():
            fasta_protein_1_lst.append(v[0])
            fasta_protein_2_lst.append(v[1])

        #find fasta in this list of query
        print "Find fasta for", protein1
        start_fasta_1 = datetime.datetime.now().replace(microsecond=0)
        fasta_protein_class1 = AnotherStupidClass()
        go_fasta_protein1 = fasta_protein_class1.go(fasta_protein_1_lst)
        end_fasta_1 = datetime.datetime.now().replace(microsecond=0)
        with open(path_to_log, "a") as f:
            f.write("Found fasta " +protein1)
            f.write(" in ")
            f.write(str(end_fasta_1- start_fasta_1))
            f.write("\n")

        print "Find fasta for", protein2
        start_fasta_2 = datetime.datetime.now().replace(microsecond=0)
        fasta_protein_class2 = AnotherStupidClass()
        go_fasta_protein2 = fasta_protein_class2.go(fasta_protein_2_lst)
        end_fasta_2 = datetime.datetime.now().replace(microsecond=0)
        with open(path_to_log, "a") as f:
            f.write("Found fasta " +protein2)
            f.write(" in ")
            f.write(str(end_fasta_2- start_fasta_2))
            f.write("\n")
        fasta_hash_protein_1 = {}
        fasta_hash_protein_2 = {}

        for ele in go_fasta_protein1:
            locus = ele[0]
            fasta = ele[1]
            fasta_hash_protein_1[locus] = fasta

        for ele in go_fasta_protein2:
            locus = ele[0]
            fasta = ele[1]
            fasta_hash_protein_2[locus] = fasta


        #make fasta files and then DB
        print "Creating Fasta files"
        fasta_path_protein1 = os.path.join(project_directory,"Fasta_list_"+protein1+".txt")
        for k,v in fasta_hash_protein_1.items():
            with open(fasta_path_protein1, "a") as f:
                f.write(">")
                f.write(k)
                f.write("\n")
                f.write(v)
                f.write("\n")

        fasta_path_protein2 = os.path.join(project_directory, "Fasta_list_" + protein2 + ".txt")
        for k,v in fasta_hash_protein_2.items():
            with open(fasta_path_protein2, "a") as f:
                f.write(">")
                f.write(k)
                f.write("\n")
                f.write(v)
                f.write("\n")
        print "Writing info"

        end_fasta = datetime.datetime.now().replace(microsecond=0)
        with open(path_to_log, "a") as f:
            f.write(str(end_fasta - start_mid))
            f.write("\n")
            f.write(str(len(fasta_hash_protein_1.values())+len(fasta_hash_protein_2.values())))
            f.write("\n")
        print "Saving Best-best", protein1

        #DB
        print "Making Databases"

        DB_protein1 = os.path.join(project_directory, protein1 + "_DB")

        self.NCBI_DB(fasta_path_protein1, DB_protein1)

        DB_protein2 = os.path.join(project_directory, protein2 + "_DB")

        self.NCBI_DB(fasta_path_protein2, DB_protein2)

        #Get protein 1 fasta
        fasta_protein_1 = kegg_get(to_find1, "aaseq")
        fasta_format_protein1 = fasta_protein_1.read()
        split_fasta_format1 = fasta_format_protein1.split("\n")
        fasta_without_space_protein1 = ''.join(split_fasta_format1[1:len(split_fasta_format1)])
        fasta_only_protein_1 = os.path.join(project_directory, "Fasta_" + protein1 + ".fasta")

        with open(fasta_only_protein_1, 'a') as f:
            f.write(fasta_format_protein1)

        #TODO salvar protein fasta 1 e 2


        length_protein1 = float(len(fasta_without_space_protein1))

        fasta_protein_2 = kegg_get(to_find2, "aaseq")
        fasta_format_protein2 = fasta_protein_2.read()
        split_fasta_format2 = fasta_format_protein2.split("\n")
        fasta_without_space_protein2 = ''.join(split_fasta_format2[1:len(split_fasta_format2)])
        fasta_only_protein_2 = os.path.join(project_directory, "Fasta_" + protein2 + ".fasta")
        with open(fasta_only_protein_2, 'a') as f:
            f.write(fasta_format_protein2)

        length_protein2 = float(len(fasta_without_space_protein2))



        output_protein1_xml = os.path.join(project_directory, "BLAST_" + protein1 + ".txt")
        output_protein2_xml = os.path.join(project_directory, "BLAST_" + protein2 + ".txt")

        self.BLAST(fasta_only_protein_1, DB_protein1, output_protein1_xml)
        self.BLAST(fasta_only_protein_2, DB_protein2, output_protein2_xml)

        #Parse Fasta

        records1 = NCBIXML.parse(open(output_protein1_xml, 'r'))
        rec1 = {}

        for item in records1:

            for aln in item.alignments:
                for hsp in aln.hsps:
                    l = aln.title.split(" ")[1]
                    iden = (hsp.identities/length_protein1)*100
                    if l in rec1.keys():
                        rec1[l] += iden
                    if l not in rec1.keys():

                        rec1[l] = iden
        records1_filtered = {}

        for k,v in rec1.items():
            protein_locus = k
            if v >= 20.0 and v <= 90.0:
                records1_filtered[protein_locus] = fasta_hash_protein_1[protein_locus]
        with open(path_to_log, "a") as f:
            f.write("Total protein ")
            f.write(protein1)
            f.write(": ")
            f.write(str(len(fasta_hash_protein_1.keys())))
            f.write("\n")
            f.write("Total after identity filtering: ")
            f.write(str(len(records1_filtered.keys())))
            f.write("\n")

        records2 = NCBIXML.parse(open(output_protein2_xml, 'r'))
        rec2 = {}
        for item in records2:
            for aln in item.alignments:
                for hsp in aln.hsps:
                    l = aln.title.split(" ")[1]
                    iden = (hsp.identities/length_protein2)*100
                    if l in rec2.keys():
                        rec2[l] += iden
                    if l not in rec2.keys():
                        rec2[l] = iden


        records2_filtered = {}
        for k,v in rec2.items():
            protein_locus = k
            if v >= 20.0 and v <= 90.0:
                records2_filtered[protein_locus] = fasta_hash_protein_2[protein_locus]
        with open(path_to_log, "a") as f:
            f.write("Total protein ")
            f.write(protein2)
            f.write(": ")
            f.write(str(len(fasta_hash_protein_2.keys())))
            f.write("\n")
            f.write("Total after identity filtering: ")
            f.write(str(len(records2_filtered.keys())))
            f.write("\n")

        Fasta_filtered_identity_protein_1 = os.path.join(project_directory, "Fasta_filtered_identity_" + protein1 + ".txt")
        for k,v in records1_filtered.items():
            with open(Fasta_filtered_identity_protein_1, 'a') as f:
                f.write(">")
                f.write(str(k))
                f.write("\n")
                f.write(str(v))
                f.write("\n")
        Fasta_filtered_identity_protein_2 = os.path.join(project_directory, "Fasta_filtered_identity_" + protein2 + ".txt")
        for k,v in records2_filtered.items():
            with open(Fasta_filtered_identity_protein_2, 'a') as f:
                f.write(">")
                f.write(str(k))
                f.write("\n")
                f.write(str(v))
                f.write("\n")

        common_org_list_filtered_final = defaultdict(list)

        for k in records1_filtered.keys():
            org = k.split(":")[0].replace(">","")
            for k2 in records2_filtered.keys():
                org2 = k2.split(":")[0].replace(">","")
                if org == org2:
                    common_org_list_filtered_final[org].append(k)
                    common_org_list_filtered_final[org].append(k2)

        ################################################################
        #//testing
        test = os.path.join(project_directory, "test_filter_common.txt")
        with open(test, 'a') as f:
            for k,v in common_org_list_filtered_final.items():
                f.write(k)
                f.write("\t")
                f.write("\t".join(v))
                f.write("\n")

        #############################################################

        #Get only common genes after filtering by identity
        print "Writting some Muscle input file"
        MAFFT_input_protein1 = os.path.join(project_directory, "Muscle_input_" + protein1 + ".txt")
        MAFFT_input_protein2 = os.path.join(project_directory, "Muscle_input_" + protein2 + ".txt")

        with open(MAFFT_input_protein1, "a") as f:
            f.write(">")
            f.write(protein1)
            f.write("\n")
            f.write(fasta_without_space_protein1)
            f.write("\n")
        with open(MAFFT_input_protein2, "a") as f:
            f.write(">")
            f.write(protein2)
            f.write("\n")
            f.write(fasta_without_space_protein2)
            f.write("\n")

        for val in common_org_list_filtered_final.values():
            locus_hom_protein1 = val[0]
            locus_hom_protein2 = val[1]
            with open(MAFFT_input_protein1, 'a') as f:
                f.write(">")
                f.write(locus_hom_protein1)
                f.write("\n")
                f.write(records1_filtered[locus_hom_protein1])
                f.write("\n")
            with open(MAFFT_input_protein2, 'a') as f:
                f.write(">")
                f.write(locus_hom_protein2)
                f.write("\n")
                f.write(records2_filtered[locus_hom_protein2])
                f.write("\n")

        print "Calling Muscle"
        #MAFFT_input_protein1
        Muscle_output_protein1 = os.path.join(project_directory, "Muscle_output_" + protein1 + ".txt")
        Muscle_output_protein2 = os.path.join(project_directory, "Muscle_output_" + protein2 + ".txt")
        log_muscle1 = os.path.join(project_directory, "log_muscle_" + protein1 + ".txt")
        log_muscle2 = os.path.join(project_directory, "log_muscle_" + protein2 + ".txt")


        muscle_stime1 = datetime.datetime.now().replace(microsecond=0)

        self.Muscle(MAFFT_input_protein1,Muscle_output_protein1,log_muscle1)
        muscle_etime1 = datetime.datetime.now().replace(microsecond=0)

        print "Total MUSCLE time", protein1
        print muscle_etime1-muscle_stime1
        with open(path_to_log, "a") as f:
            f.write("Total Muscle Time ")
            f.write(protein1)
            f.write(str(muscle_etime1-muscle_stime1))
            f.write(" ")
            f.write("\n")


        muscle_stime2 = datetime.datetime.now().replace(microsecond=0)
        self.Muscle(MAFFT_input_protein2, Muscle_output_protein2, log_muscle2)
        muscle_etime2 = datetime.datetime.now().replace(microsecond=0)
        print "Total MUSCLE time", protein1
        print muscle_etime2-muscle_stime2
        print muscle_etime1-muscle_stime1
        with open(path_to_log, "a") as f:
            f.write("Total Muscle Time ")
            f.write(protein2)
            f.write(" ")
            f.write(str(muscle_etime2-muscle_stime2))
            f.write("\n")

        #Deal with Muscle

        muscle_out1 = open(Muscle_output_protein1, 'r').read().split("\n")
        final_out_dict1 = defaultdict(list)

        for line in muscle_out1:
            if ">" in line:
                org = line.replace(">", "")
            else:
                final_out_dict1[org].append(line)

        seq_protein1_muscle = "".join(final_out_dict1[protein1])

        #List of valid positions

        pos_lst1 = []
        for x in xrange(0, len(seq_protein1_muscle)):
            if "-" not in seq_protein1_muscle[x]:
                pos_lst1.append(x)
        muscle_out2 = open(Muscle_output_protein2, 'r').read().split("\n")
        final_out_dict2 = defaultdict(list)

        for line in muscle_out2:
            if ">" in line:
                org = line.replace(">", "")
            else:
                final_out_dict2[org].append(line)

        seq_protein2_muscle = "".join(final_out_dict2[protein2])

        # List of valid positions
        pos_lst2 = []
        for x in xrange(0, len(seq_protein2_muscle)):
            if "-" not in seq_protein2_muscle[x]:
                pos_lst2.append(x)

        formated_muscle_out1 = defaultdict(list)
        for k, v in final_out_dict1.items():
            org = k.replace(">","")
            pivot = "".join(v)
            final_seq = ""
            for aa_pos in pos_lst1:
                final_seq += pivot[aa_pos]
            formated_muscle_out1[org] = final_seq

        formated_muscle_out2 = defaultdict(list)
        for k, v in final_out_dict2.items():
            org = k.replace(">","")
            pivot = "".join(v)
            final_seq = ""
            for aa_pos in pos_lst2:
                final_seq += pivot[aa_pos]
            formated_muscle_out2[org] = final_seq

        #Put sequences with no gap (based on original sequence)
        #It must be in the same taxID
        ordered_list_protein1_Zres = []
        ordered_list_protein1_Zres.append(fasta_without_space_protein1)
        ordered_list_protein2_Zres = []
        ordered_list_protein2_Zres.append(fasta_without_space_protein2)

        for v in common_org_list_filtered_final.values():
            common_protein1 = v[0]
            ordered_list_protein1_Zres.append(formated_muscle_out1[common_protein1])

            common_protein2 = v[1]
            ordered_list_protein2_Zres.append(formated_muscle_out2[common_protein2])

        #Ok! Sequences are in order let's filter by gap

        print "Filter by gap"
        seq_filtered_protein1 = self.filter_by_gap(ordered_list_protein1_Zres)
        seq_filtered_protein2 = self.filter_by_gap(ordered_list_protein2_Zres)
        only_seq_protein1 = seq_filtered_protein1[1].values()
        only_seq_protein2 = seq_filtered_protein2[1].values()

        aa_info1 = os.path.join(project_directory, protein1 + "info_aa_zres.txt")
        aa_info2 = os.path.join(project_directory, protein2 + "info_aa_zres.txt")


        for k, v in seq_filtered_protein1[0].items():
            with open(aa_info1, 'a') as f:
                f.write(str(k))
                f.write("\t")
                f.write(str(v))
                f.write("\n")
                f.close()

        for k, v in seq_filtered_protein2[0].items():
            with open(aa_info2, 'a') as f:
                f.write(str(k))
                f.write("\t")
                f.write(str(v))
                f.write("\n")
                f.close()
        print "Concatenating Sequences"
        protein1_protein2 = self.concatenate_sequences(only_seq_protein1, only_seq_protein2)
        print "Calculating MI_array"
        arr = self.MI_array(protein1_protein2)
        start_MI = datetime.datetime.now().replace(microsecond=0)
        MI_array_path = os.path.join(project_directory, protein1 + "MI_gap_filtered.txt")
        end_MI = datetime.datetime.now().replace(microsecond=0)

        with open(path_to_log,'a') as f:
            f.write("MI array time: ")
            f.write(str(end_MI - start_MI))
            f.write("\n")
        np.savetxt(MI_array_path, arr)
        print "Calculating Zres"
        start_Zres = datetime.datetime.now().replace(microsecond=0)
        b = self.calculate_Zres(arr)
        end_Zres = datetime.datetime.now().replace(microsecond=0)

        with open(path_to_log,'a') as f:
            f.write("Zres array time: ")
            f.write(str(end_Zres - start_Zres))
            f.write("\n")
        residual = b[0]
        Z_res = b[1]
        residual_path = os.path.join(project_directory, "Residual_gap_filtered.txt")
        Zres_path = os.path.join(project_directory, "Zres_gap_filtered.txt")
        np.savetxt(residual_path, residual)
        np.savetxt(Zres_path, Z_res)

        x_ax = []
        y_ax = []

        for x in xrange(0, Z_res.shape[0]):
            for y in xrange(0, Z_res.shape[0]):
                x_ax.append(Z_res[x, y])
        for x in xrange(0, residual.shape[0]):
            for y in xrange(0, residual.shape[0]):
                y_ax.append(residual[x, y])

        tot = 0
        for x in xrange(0, Z_res.shape[0]):
            print x
            for y in xrange(0, Z_res.shape[0]):
                if Z_res[x, y] > abs(np.amin(Z_res)):
                    tot += 1
        with open(path_to_log,'a') as f:
            f.write("Zmin: ")
            f.write(str(np.amin(Z_res)))
            f.write("\n")
            f.write("Total interaction: ")
            f.write(str(tot))
            f.write("\n")
        fin = datetime.datetime.now().replace(microsecond=0)
        print "Total time: %s" % (fin-start_mid)
        with open(path_to_log, "a") as f:
            f.write("Total Analysis Time ")
            f.write(str(fin-start_mid))
        print """
           /) /)
          ( ^.^ )
         C(") (")
        """

        plt.ioff()
        Zres_fig_total = os.path.join(project_directory, "Z_res_Res_total.png")
        fig = plt.figure()
        plt.scatter(x_ax, y_ax, s=30, alpha=0.15, marker='o')

        plt.xlim(np.amin(Z_res), np.amax(Z_res))
        plt.axvline(x=abs(np.amin(Z_res)))

        plt.savefig(Zres_fig_total)
        plt.close(fig)

        fig2 = plt.figure()
        Zres_fig_total2 = os.path.join(project_directory, "Z_res_Res_max20.png")
        plt.scatter(x_ax, y_ax, s=30, alpha=0.15, marker='o')
        plt.xlim(np.amin(Z_res), 20)
        plt.axvline(x=abs(np.amin(Z_res)))
        plt.savefig(Zres_fig_total2)
        plt.close(fig2)




    def MakeDir(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def KEGG_best_hit(self,locus):
        # Save best_genes herewhile True:

        # Open page
        open_kegg = urlopen('http://www.kegg.jp/ssdb-bin/ssdb_best?org_gene=' + locus)
        best_list = []
        page = open_kegg.read()

        # make soup
        soup = BeautifulSoup(page)

        # find best genes
        tt = soup.find_all("input", {'type': 'checkbox'})
        for elem in tt:
            value = elem.get('value')
            if value:
                best_list.append(value)
        return best_list
    def NCBI_DB(self,Fasta_file, output_file):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        makeblastdb_path = os.path.join(dir_path, 'makeblastdb.exe')
        os.system(makeblastdb_path+" -in " + Fasta_file + " -dbtype prot -out " + output_file)

    def BLAST(self,q, DB, output):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        command_path = os.path.join(dir_path,'blastp.exe' )
        os.system(command_path+' -db ' + DB + " -query " + q + " -outfmt 5 -num_alignments 2000" + " -out " + output)

    def Muscle(self, fasta_file, output,logoutput):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        command_path = os.path.join(dir_path, 'muscle.exe')
        os.system(command_path + " -in " +fasta_file+ " -out "+ output+ " -log "+ logoutput)

    def filter_by_gap(self,Sequences, max_gap=20,
                      min_entropy=((-5 / 100.0) * log(5 / 100.0)) - ((1 - 5 / 100.0) * log(1 - 5 / 100.0))):
        Seq_pos = collections.OrderedDict()
        Seq_filtered = collections.OrderedDict()
        total_col = float(len(Sequences))
        now_pos = 0
        for i in xrange(0, len(Sequences[0])):
            Pi = Counter(sequence[i] for sequence in Sequences)
            if (Pi['-'] / total_col) * 100 <= max_gap:
                Pi = Counter(sequence[i] for sequence in Sequences)
                number_seq = float(len(Sequences))
                entropy_Pi = -sum((Pi[x] / number_seq) * (log(Pi[x] / number_seq)) for x in Pi)

                if entropy_Pi > min_entropy:
                    Seq_pos[now_pos] = i
                    now_pos += 1
                    for x in xrange(0, len(Sequences)):

                        if x in Seq_filtered.keys():
                            Seq_filtered[x] += Sequences[x][i]
                        if x not in Seq_filtered.keys():
                            Seq_filtered[x] = Sequences[x][i]
        return [Seq_pos, Seq_filtered]

    def concatenate_sequences(self,SeqList1, SeqList2):
        conc_list = []
        for x in xrange(0, len(SeqList1)):
            s = SeqList1[x] + SeqList2[x]
            conc_list.append(s)
        return conc_list

    def MI(self,sequences, i, j, min_entropy=((-5 / 100.0) * log(5 / 100.0)) - ((1 - 5 / 100.0) * log(1 - 5 / 100.0))):
        '''
        Return MI(i,j)
        #############
        #####OK######
        #############
        :param sequences:
        :param i:
        :param j:
        :return:
        '''
        Pi = Counter(sequence[i] for sequence in sequences)
        Pj = Counter(sequence[j] for sequence in sequences)
        Pij = Counter((sequence[i], sequence[j]) for sequence in sequences)
        number_seq = float(len(sequences))
        entropy_Pi = -sum((Pi[x] / number_seq) * (log(Pi[x] / number_seq)) for x, y in Pij)
        entropy_Pj = -sum((Pj[y] / number_seq) * (log(Pj[y] / number_seq)) for x, y in Pij)

        if entropy_Pi < min_entropy or entropy_Pj < min_entropy:
            return 0.0
        else:

            return round(sum((Pij[(x, y)] / number_seq) *
                             log(
                                 ((Pij[(x, y)] / number_seq)) /
                                 (((Pi[x] / number_seq) *
                                   (Pj[y] / number_seq))
                                  )
                             )
                             for x, y in Pij), 20)

    def MI_array(self,Sequences):
            print "Starting Analysis"
            sequence_shape = len(Sequences[0])
            np_array = np.zeros(shape=(sequence_shape, sequence_shape))
            for x in xrange(0, len(Sequences[0])):
                for y in xrange(0, len(Sequences[0])):
                    s = self.MI(Sequences, x, y)
                    np_array[x, y] = s

            return np_array

    def calculate_Zres(self,MI_array):
        """Calculate the z-scored residual mutual information [Little & Chen (2009) PLoS One] (natural log base) for reducedColumns"""
        # read column1 as i and column2 as j
        # make lists of MI and the column MI mean products
        listMI = []
        listProduct = []
        Zres_array = np.zeros(shape=(MI_array.shape[0], MI_array.shape[1]))

        MI_hash = {}
        print 'calculatin MI hash'
        for x in xrange(0, MI_array.shape[0]):
            for y in xrange(0, MI_array.shape[0]):
                if x != y:
                    if x in MI_hash.keys():
                        MI_hash[x] += MI_array[x, y]
                    if x not in MI_hash.keys():
                        MI_hash[x] = MI_array[x, y]

        n = float(MI_array.shape[0])
        print 'Getting MI and product'
        for i in xrange(0, MI_array.shape[0]):
            for j in xrange(0, MI_array.shape[1]):
                listMI.append(MI_array[i, j])
                mean_product = (MI_hash[i] * MI_hash[j]) / n
                listProduct.append(mean_product)

        # linearly regress out the correlation
        # x = listProduct, y = listMI
        print 'Calcilating linear regression'
        slope, intercept, corr, pvalue, sterr = linregress(listProduct, listMI)
        # Best fit linear regression yfit values for best fit
        # yfit = [ intercept+ slope * xi for xi in listProduct]
        # plt.scatter(listProduct, listMI, s=30, alpha=0.15, marker='o')
        # plt.plot(listProduct, yfit)


        residuals = np.zeros(shape=(MI_array.shape[0], MI_array.shape[1]))

        print 'Calculating residuals'
        colRes = defaultdict(list)
        for i in xrange(0, MI_array.shape[0]):
            for j in xrange(0, MI_array.shape[1]):
                mean_product = (MI_hash[i] * MI_hash[j]) / n
                appr = slope * (mean_product) + intercept
                residuals[i, j] = MI_array[i, j] - appr

                colRes[i].append((MI_array[i, j] - appr))

        # calculate zres
        # Rever calculo
        print 'Calcilating Zres'
        for i in xrange(0, residuals.shape[0]):
            for j in xrange(0, residuals.shape[1]):
                mean1 = sum(colRes[i]) / (float(len(colRes.keys())))
                mean2 = sum(colRes[j]) / (float(len(colRes.keys())))
                std1 = std(colRes[i])
                std2 = std(colRes[j])
                zres1 = (residuals[i, j] - mean1) / std1
                zres2 = (residuals[i, j] - mean2) / std2
                if zres1 > 0 and zres2 > 0:
                    Zres_array[i, j] = zres1 * zres2
                else:
                    Zres_array[i, j] = -abs(zres1 * zres2)
        ls_r = [residuals, Zres_array]
        return ls_r
class someClass():
    def __init__(self):
        self.haha = "haha"
        pass

    def is_best_best(self,args):


        (locus, gene) = args
        c = ""

        while True:
            try:

                start_mid = datetime.datetime.now().replace(microsecond=0)
                # Open page
                open_kegg = urlopen('http://www.kegg.jp/ssdb-bin/ssdb_best?org_gene=' + gene)
                page = open_kegg.read()

                # make soup
                soup = BeautifulSoup(page)

                tt = soup.find_all("input", {'type': 'checkbox'})
                for elem in tt:
                    value = elem.get('value')
                    if value:
                        if locus in value:
                            c = gene

                end_mid = datetime.datetime.now().replace(microsecond=0)
                print "Parcial time: %s" % (end_mid - start_mid)

            except:
                continue
            break
        return c

    def go(self,to_find,query1):
        #a = n+m
        #p = Pool(4)
        #sc = p.map(self, range(a))
        #print sc
        #self.is_best_best((to_find,query1))
        self.number_processes = (cpu_count() - 1)*12
        self.pool = Pool(self.number_processes)

        results = self.pool.map(self, itertools.izip(itertools.repeat(to_find), query1))
        self.pool.close()
        self.pool.join()
        return results

    def __call__(self, args):
        return self.is_best_best(args)
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict
    def __setstate__(self, state):
        self.__dict__.update(state)

class AnotherStupidClass():
    def __init__(self):
        self.haha = "haha"
        pass

    def find_kegg_fasta(self,args):
        (locus) = args

        c = []
        get_fasta_protein1 = kegg_get(locus, "aaseq")

        fasta_locus_protein1 = get_fasta_protein1.read()
        fasta_formatted_protein1 = fasta_locus_protein1.split('\n')
        without_space_protein1 = ''.join(fasta_formatted_protein1[1:len(fasta_formatted_protein1)])
        c.append(locus)
        c.append(without_space_protein1)

        return c

    def go(self,locus):
        #a = n+m
        #p = Pool(4)
        #sc = p.map(self, range(a))
        #print sc
        #self.is_best_best((to_find,query1))
        self.number_processes = (cpu_count() - 1)*12
        self.pool = Pool(self.number_processes)

        results = self.pool.map(self, locus)
        self.pool.close()
        self.pool.join()
        return results

    def __call__(self, args):
        return self.find_kegg_fasta(args)
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict
    def __setstate__(self, state):
        self.__dict__.update(state)
class RedirectText:
    #Print log class
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        self.out.WriteText(string)


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent = None, title = "GREPy", size = (800,600))
        self.createMenuBar()
        panel = wx.Panel(self)
        nb = wx.Notebook(panel)

        tab1 = GREPy(nb)
        #tab2 = Align(nb)
        #tab3 = Anal(nb)

        nb.AddPage(tab1, "GREPy")
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
