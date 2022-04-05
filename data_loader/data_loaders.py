import torch
import torch.utils.data
import numpy as np
from data_sets import multiple_dataset
from data_sets import synth_qa_dataset
from data_sets import synth_form_dataset
from data_sets import squad
from data_sets import hw_squad
from data_sets import docvqa
from data_sets import rvl_cdip_class
from data_sets import sroie
from data_sets import funsd_qa
from data_sets import naf_qa
from data_sets import naf_read
from data_sets import cdip_qa
from data_sets import cdip_cloud_qa
from data_sets import iam_qa
from data_sets import iam_mixed
from data_sets import iam_ner
from data_sets import census_qa
from data_sets import distil_bart
from data_sets import forms_graph_pair
from data_sets import funsd_graph_pair
from base import BaseDataLoader




def getDataLoader(config,split,rank=None,world_size=None):
        data_set_name = config['data_loader']['data_set_name']
        data_dir = config['data_loader']['data_dir']
        batch_size = config['data_loader']['batch_size']
        valid_batch_size = config['validation']['batch_size'] if 'batch_size' in config['validation'] else batch_size

        #copy info from main dataloader to validation (but don't overwrite)
        #helps insure same data
        for k,v in config['data_loader'].items():
            if k not in config['validation']:
                config['validation'][k]=v

        if 'augmentation_params' in config['data_loader']:
            aug_param = config['data_loader']['augmentation_params']
        else:
            aug_param = None
        if rank is None:
            shuffle = config['data_loader']['shuffle']
        else:
            shuffle = False
        if 'num_workers' in config['data_loader']:
            numDataWorkers = config['data_loader']['num_workers']
        else:
            numDataWorkers = 1
        shuffleValid = config['validation']['shuffle']

        if data_set_name=='MultipleDataset':
            config['data_loader']['super_computer']=config['super_computer']
            config['validation']['super_computer']=config['super_computer']
            return withCollate(multiple_dataset.MultipleDataset,multiple_dataset.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='SynthParaQA':
            return withCollate(synth_para_qa.SynthParaQA,synth_para_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='SynthFormDataset':
            return withCollate(synth_form_dataset.SynthFormDataset,synth_form_dataset.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='SQuAD':
            return withCollate(squad.SQuAD,squad.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='HWSQuAD':
            return withCollate(hw_squad.HWSQuAD,hw_squad.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='DocVQA':
            return withCollate(docvqa.DocVQA,docvqa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='RVLCDIPClass':
            return withCollate(rvl_cdip_class.RVLCDIPClass,rvl_cdip_class.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='FormsGraphPair':
            return withCollate(forms_graph_pair.FormsGraphPair,forms_graph_pair.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='FUNSDGraphPair':
            return withCollate(funsd_graph_pair.FUNSDGraphPair,funsd_graph_pair.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='FUNSDQA':
            return withCollate(funsd_qa.FUNSDQA,funsd_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='NAFQA':
            return withCollate(naf_qa.NAFQA,naf_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='NAFRead':
            return withCollate(naf_read.NAFRead,naf_read.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='SROIE':
            return withCollate(sroie.SROIE,sroie.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='CDIPQA':
            return withCollate(cdip_qa.CDIPQA,cdip_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='CDIPCloudQA':
            config['data_loader']['super_computer']=config['super_computer']
            config['validation']['super_computer']=config['super_computer']
            return withCollate(cdip_cloud_qa.CDIPCloudQA,cdip_cloud_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='IAMQA':
            return withCollate(iam_qa.IAMQA,iam_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='IAMMixed':
            return withCollate(iam_mixed.IAMMixed,iam_mixed.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='IAMNER':
            return withCollate(iam_ner.IAMNER,iam_ner.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='CensusQA':
            return withCollate(census_qa.CensusQA,census_qa.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        elif data_set_name=='DistilBartDataset':
            return withCollate(distil_bart.DistilBartDataset,distil_bart.collate,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config)
        else:
            print('Error, dataloader has no set for {}'.format(data_set_name))
            exit()



def basic(setObj,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config):
    if split=='train':
        trainData = setObj(dirPath=data_dir, split='train', config=config['data_loader'])
        trainLoader = torch.utils.data.DataLoader(trainData, batch_size=batch_size, shuffle=shuffle, num_workers=numDataWorkers)
        validData = setObj(dirPath=data_dir, split='valid', config=config['validation'])
        validLoader = torch.utils.data.DataLoader(validData, batch_size=valid_batch_size, shuffle=shuffleValid, num_workers=numDataWorkers)
        return trainLoader, validLoader
    elif split=='test':
        testData = setObj(dirPath=data_dir, split='test', config=config['validation'])
        testLoader = torch.utils.data.DataLoader(testData, batch_size=valid_batch_size, shuffle=False, num_workers=numDataWorkers)
    elif split=='merge' or split=='merged' or split=='train-valid' or split=='train+valid':
        trainData = setObj(dirPath=data_dir, split=['train','valid'], config=config['data_loader'])
        trainLoader = torch.utils.data.DataLoader(trainData, batch_size=batch_size, shuffle=shuffle, num_workers=numDataWorkers)
        validData = setObj(dirPath=data_dir, split=['train','valid'], config=config['validation'])
        validLoader = torch.utils.data.DataLoader(validData, batch_size=valid_batch_size, shuffle=shuffleValid, num_workers=numDataWorkers)
        return trainLoader, validLoader

def withCollate(setObj,collateFunc,batch_size,valid_batch_size,shuffle,shuffleValid,numDataWorkers,split,data_dir,config,rank=None,world_size=None):
    prefetch_factor = config['data_loader']['prefetch_factor'] if 'prefetch_factor' in config else 2
    persistent_workers = config['data_loader']['persistent_workers'] if 'persistent_workers' in config else False
    if split=='train':
        trainData = setObj(dirPath=data_dir, split='train', config=config['data_loader'])
        if rank is not None:
            train_sampler = torch.utils.data.distributed.DistributedSampler(
                    trainData,
                    num_replicas=world_size,
                    rank=rank )
        else:
            train_sampler = None

        trainLoader = torch.utils.data.DataLoader(trainData, batch_size=batch_size, shuffle=shuffle, num_workers=numDataWorkers, collate_fn=collateFunc, sampler=train_sampler, prefetch_factor=prefetch_factor, persistent_workers=persistent_workers)
        if rank is None or rank==0:
            validData = setObj(dirPath=data_dir, split='valid', config=config['validation'])
            validLoader = torch.utils.data.DataLoader(validData, batch_size=valid_batch_size, shuffle=shuffleValid, num_workers=numDataWorkers, collate_fn=collateFunc)
        else:
            validLoads = None #For now, just have the master do the validation loop
        return trainLoader, validLoader
    elif split=='test':
        testData = setObj(dirPath=data_dir, split='test', config=config['validation'])
        testLoader = torch.utils.data.DataLoader(testData, batch_size=valid_batch_size, shuffle=False, num_workers=numDataWorkers, collate_fn=collateFunc)
        return testLoader, None
    elif split=='merge' or split=='merged' or split=='train-valid' or split=='train+valid':
        trainData = setObj(dirPath=data_dir, split=['train','valid'], config=config['data_loader'])
        trainLoader = torch.utils.data.DataLoader(trainData, batch_size=batch_size, shuffle=shuffle, num_workers=numDataWorkers, collate_fn=collateFunc)
        validData = setObj(dirPath=data_dir, split=['train','valid'], config=config['validation'])
        validLoader = torch.utils.data.DataLoader(validData, batch_size=valid_batch_size, shuffle=shuffleValid, num_workers=numDataWorkers, collate_fn=collateFunc)
        return trainLoader, validLoader
    

