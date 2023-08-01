import torch
import torch.nn as nn
import torch.nn.functional as F

from models.FEDformer import Model as FEDformer
from models import Autoformer 
import copy 
dict_membre={
    "buste":[0,1,2,3,20],
    "bras_gauche":[4,5,6,7,21,22],
    "bras_droit":[8,9,10,11,23,24],
    "jambe_gauche":[12,13,14,15],
    "jambe_droite":[16,17,18,19],
    
}
liste_membre=[dict_membre["buste"],dict_membre["bras_gauche"],dict_membre["bras_droit"],dict_membre["jambe_gauche"],dict_membre["jambe_droite"]]
def transfo_inverse_NTU(x,liste_membre):
    if x is None:
        return None
    xprime=torch.reshape(x,(x.shape[0],x.shape[1],25,3)) # Reshape de la bonne manière
    xprime=xprime[:,:,liste_membre,:] 
    xprime=torch.reshape(xprime,(xprime.shape[0],xprime.shape[1],xprime.shape[2]*xprime.shape[3]))
    return xprime

class Model(nn.Module):
 

    def __init__(self, configs,liste_membre:list=liste_membre):
        """
        MON PREMIER NN MODULE
        """
        super(Model, self).__init__()
        self.task_name = configs.task_name
        self.seq_len = configs.seq_len
        self.label_len = configs.label_len
        self.pred_len = configs.pred_len
        self.liste_membre=liste_membre
        self.modelmembre= FEDformer
        self.liste_modele_partie=nn.ModuleList()
        self.c_out=configs.c_out   
        configprime=copy.deepcopy(configs)
        
        for k in range(len(self.liste_membre)):
            configprime.enc_in=len(liste_membre[k])*3 # A CHHANGER
            configprime.dec_in=len(liste_membre[k])*3 #A CHANGER
            configprime.dec_out=len(liste_membre[k])*3
            configprime.c_out=len(liste_membre[k])*3
                
            print( " dec_out de cprime",configprime.dec_out,"enc_out de cprime",configprime.enc_in,"c_out de cprime",configprime.c_out)
        
            ajouter=self.modelmembre(configprime)
            self.liste_modele_partie.append(ajouter)
        print("fin initialisation du modèle, nombre de partie",len(self.liste_modele_partie),"nombre de membre",len(self.liste_membre))
        

    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None):
        y=torch.zeros(x_enc.shape[0],self.pred_len,25,3)

        for k in range(len(self.liste_membre)):
            print("on s'occupe de: k ")
            #* Transforme la série temporelle en ne gardant que celle qui nous intéresse 
            xprime=transfo_inverse_NTU(x_enc,liste_membre[k])
            x_mark_enc_prime=transfo_inverse_NTU(x_mark_enc,liste_membre[k])
            x_dec_prime=transfo_inverse_NTU(x_dec,liste_membre[k])
            x_mark_dec_prime=transfo_inverse_NTU(x_mark_dec,liste_membre[k])
            #* On fait tourner le modèle sur la partie qui nous intéresse
            print("les shapes sont",xprime.shape,x_mark_enc_prime.shape,None,x_mark_dec_prime.shape)
            yprime=self.liste_modele_partie[k](xprime,x_mark_enc_prime,x_dec_prime,x_mark_dec_prime)
            print(yprime.shape)
            #* On remet la série temporelle à la bonne taille
            yprime=yprime.reshape(yprime.shape[0],yprime.shape[1],len(liste_membre[k]),3)
            y[:,:,liste_membre[k],:]=yprime
        y=y.reshape(y.shape[0],y.shape[1],self.c_out)
        return y 