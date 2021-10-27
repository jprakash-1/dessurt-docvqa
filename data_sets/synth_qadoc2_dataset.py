import json
import timeit
import torch
from torch.utils.data import Dataset
from torch.autograd import Variable

from collections import defaultdict
from glob import iglob
import os
import utils.img_f as img_f
import numpy as np
import math, time
import random, string

from utils import grid_distortion

from utils import string_utils, augmentation
from utils.util import ensure_dir
from utils.yolo_tools import allIOU
from .form_qa import FormQA, collate, Entity, Line, Table
from .gen_daemon import GenDaemon

from multiprocessing import Pool, TimeoutError

import random, pickle
PADDING_CONSTANT = -1



class SynthQADoc2Dataset(FormQA):
    def __init__(self, dirPath, split, config):
        super(SynthQADoc2Dataset, self).__init__(dirPath,split,config)
        self.color=False
        self.ocr = False
        self.min_text_height = config['min_text_height'] if 'min_text_height' in config else   8
        self.max_text_height = config['max_text_height'] if 'max_text_height' in config else   32
        self.image_size = config['image_size'] if 'image_size' in config else None
        if type(self.image_size) is int:
            self.image_size = (self.image_size,self.image_size)
        self.max_entries = config['max_entries'] if 'max_entries' in config else self.questions
        self.wider = config['wider'] if 'wider' in config else 200
        self.min_start_read = 7
        self.tables = False
        
        self.generator = GenDaemon(dirPath)
        
        self.images=[]
        for i in range(config['batch_size']*100): #we just randomly generate instances on the fly
            self.images.append({'id':'{}'.format(i), 'imagePath':None, 'annotationPath':0, 'rescaled':1.0, 'imageName':'0'})

        self.try_pos_count = 20
        self.try_value_count = 5




    def __len__(self):
        return len(self.images)

    def max_len(self):
        return self.text_max_len

    def parseAnn(self,annotations,s):
        #This defines the creation of the image with its GT entities, boxes etc.
        #Questions are generated by parent class with maskQuestions()

        #select Text instances
        num_entries = self.max_entries

        all_entities=[]
        entity_link=[]

        wider = round(random.triangular(0,self.wider,0))


        label_value_pairs = self.generator.generateLabelValuePairs(num_entries)
        image = np.full((self.image_size[0],self.image_size[1]),255,np.uint8)
        used_space = np.zeros((self.image_size[0],self.image_size[1]),np.bool)
        #for (label_img_idx,label_text,label_dir,resize_l),(value_img_idx,value_text,value_dir,resize_v) in zip(labels,values):
        for label,value in label_value_pairs:
            label_height = random.randrange(self.min_text_height,self.max_text_height)
            value_height = random.randrange(round(label_height*0.7),round(label_height*1.3))
            est_width=0
            for text,label_img in label[:4]:
                label_width = round(label_img.shape[1]*label_height/label_img.shape[0])
                est_width+=label_width
            est_height =  max(label_height,value_height) * round(len(value)/4)
            em_approx = label_height*1.6 #https://en.wikipedia.org/wiki/Em_(typography)
            min_space_label = 0.2*em_approx #https://docs.microsoft.com/en-us/typography/develop/chara  cter-design-standards/whitespace
            max_space_label = 0.5*em_approx

            em_approx = value_height*1.6 
            min_space_value = 0.2*em_approx 
            max_space_value = 0.5*em_approx
            success=False
            for i in range(self.try_pos_count):
                space_width_label = round(random.random()*(max_space_label-min_space_label) + min_space_label)
                newline_height_label = random.randrange(1,label_height) + label_height
                space_width_value = round(random.random()*(max_space_value-min_space_value) + min_space_value)
                newline_height_value = random.randrange(1,value_height) + value_height
                if self.image_size[1]-est_width>0:
                    start_x = random.randrange(int(self.image_size[1]-est_width))
                else:
                    start_x =0

                if self.image_size[0]-est_height>0:
                    start_y = random.randrange(int(self.image_size[0]-est_height))
                else:
                    start_y =0 
                if used_space[start_y:start_y+est_height,start_x:start_x+est_width].sum()<4:

                    new_label_lines = []
                    line=[]
                    #new_label_text = ''
                    x=start_x
                    y=start_y
                    toss_out=False

                    for label_text,label_img in label:
                        label_width = round(label_img.shape[1]*label_height/label_img.shape[0])
                        #try:
                        #    label_img = img_f.resize(label_img,(label_height,label_width))
                        #except OverflowError as e:
                        #    print(e)
                        #    print('image {} to {}  min={} max={}'.format(label_img.shape,(label_height,label_width),label_img.min(),label_img.max()))
                        if used_space[y:y+label_height,x:x+label_width].sum()<4 and y+label_height<self.image_size[0] and x+label_width<self.image_size[1]:
                            line.append((label_text,label_img,label_width,x,y))
                            #new_label_text+=' '+label_text
                            x+=label_width+space_width_label
                        elif len(new_label_lines)>0:
                            #start newline:
                            x=start_x+ random.randrange(-space_width_label//2,space_width_label//2)
                            x=max(x,0)
                            y+=newline_height_label + label_height + random.randrange(-2,2)
                            if used_space[y:y+label_height,x:x+label_width].sum()<4 and y+label_height<self.image_size[0] and x+label_width<self.image_size[1]:
                                new_label_lines.append(line)
                                line=[(label_text,label_img,label_width,x,y)]
                                #new_label_text+='\n'+label_text
                                x+=label_width+space_width_label
                            else:
                                #this doesn't fit
                                toss_out=True
                                break
                        else:
                            #this doesn't fit
                            toss_out=True
                            break
                    if toss_out:
                        continue
                    new_label_lines.append(line)

                    for i in range(self.try_value_count):
                        #where should the value start?
                        if random.random()<0.05:
                            #below
                            start_x += random.randrange(-label_width,label_width)
                            start_y += round(label_height + 2*newline_height_label*random.random())
                        else:
                            #to the left
                            start_x = y + random.randrange(-label_height,label_height)
                            start_y = x + wider + random.randrange(-10,10)

                        start_x=max(start_x,0)
                        start_y=max(start_y,0)

                        new_value_lines = []
                        line=[]
                        #new_value_text=''
                        x=start_x
                        y=start_y
                        toss_out=False
                        for value_text,value_img in value:
                            value_width = round(value_img.shape[1]*value_height/value_img.shape[0])
                            if used_space[y:y+value_height,x:x+value_width].sum()<4 and y+value_height<self.image_size[0] and x+value_width<self.image_size[1]:
                                line.append((value_text,value_img,value_width,x,y))
                                #new_value_text+=' '+value_text
                                x+=value_width+space_width_value
                            elif len(new_value_lines)>0:
                                #start newline:
                                x=start_x+ random.randrange(-space_width_value//2,space_width_value//2)
                                x=max(x,0)
                                y+=newline_height_value + value_height + random.randrange(-2,2)
                                if used_space[y:y+value_height,x:x+value_width].sum()<4 and y+value_height<self.image_size[0] and x+value_width<self.image_size[1]:
                                    new_value_lines.append(line)
                                    line=[(value_text,value_img,value_width,x,y)]
                                    #new_value_text+='\n'+value_text
                                    x+=value_width+space_width_value
                                else:
                                    #this doesn't fit
                                    toss_out=True
                                    break
                            else:
                                #this doesn't fit
                                toss_out=True
                                break

                        if toss_out and len(new_value_lines)<1:
                            continue
                        else:
                            new_value_lines.append(line)
                            #just leave the incomplete value
                            success=True
                            break
                    if success:
                        break
            if not success:
                continue
            
            #lets actually draw these in and mark them (and resize!)
            
            final_label_lines=[]
            for line in new_label_lines:
                if len(line)==0:
                    continue
                text=[]
                for label_text,label_img,label_width,x,y in line:
                    label_img = img_f.resize(label_img,(label_height,label_width))
                    image[y:y+label_height,x:x+label_width] = label_img
                    used_space[y:y+label_height,x:x+label_width] = 1
                    text.append(label_text)
                final_label_lines.append(Line(' '.join(text),[line[0][3],line[0][4],x+label_width,y+label_height]))

            last_label_x=x
            last_label_y=y

            first_value_x = new_value_lines[0][0][3]+new_value_lines[0][0][2]
            first_value_y = new_value_lines[0][0][3]+value_height
            used_space[last_label_y:first_value_y,last_label_x:first_value_x]=1

            final_value_lines=[]
            for line in new_value_lines:
                if len(line)==0:
                    continue
                text=[]
                for value_text,value_img,value_width,x,y in line:
                   value_img = img_f.resize(value_img,(value_height,value_width))
                   image[y:y+value_height,x:x+value_width] = value_img
                   used_space[y:y+value_height,x:x+value_width] = 1
                   text.append(value_text)
                final_value_lines.append(Line(' '.join(text),[line[0][3],line[0][4],x+value_width,y+value_height]))



            if len(final_label_lines)>0:
                label_id = len(all_entities)
                all_entities.append(Entity('question',final_label_lines))

                if len(final_value_lines)>0:
                    value_id = len(all_entities)
                    all_entities.append(Entity('answer',final_value_lines))
                else:
                    value_id=None

                entity_link.append((label_id,value_id))

        #run through all entites to build bbs, assign bbid, and find ambiguity
        boxes = []
        text_line_counts = defaultdict(list)
        for ei,entity in enumerate(all_entities):
            for li,line in enumerate(entity.lines):
                text = self.punc_regex.sub('',line.text.lower())
                text_line_counts[text].append((ei,li))
                bbid = len(boxes)
                boxes.append(self.convertBB(s,line.box))
                line.bbid = bbid

        bbs = np.array(boxes)

        #assign ambiguity
        for line_ids in text_line_counts.values():
            if len(line_ids)>1:
                for ei,li in line_ids:
                    all_entities[ei].lines[li].ambiguous = True

        #now set up a full linking dictionary
        link_dict=defaultdict(list)
        for e1,e2s in entity_link:
            if e2s is not None:
                if isinstance(e2s,int):
                    e2s=[e2s]
                link_dict[e1]+=e2s
                for e2 in e2s:
                    link_dict[e2].append(e1)

        tables = []
        link_dict = self.sortLinkDict(all_entities,link_dict)

        qa = self.makeQuestions(s,all_entities,entity_link,tables,all_entities,link_dict)

        return bbs, list(range(bbs.shape[0])), None, {'image':image}, {}, qa

    
