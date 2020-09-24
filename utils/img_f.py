import skimage
import numpy as np

#These are all based on the OpenCV functions, to make the conversion to scikit image easier (also should make future changes easier as well)

def line(img,p1,p2,color,thickness=1):
    y1 = max(0,min(img.shape[0]-1,p1[1]))
    y2 = max(0,min(img.shape[0]-1,p2[1]))
    x1 = max(0,min(img.shape[1]-1,p1[0]))
    x2 = max(0,min(img.shape[1]-1,p2[0]))
    rr,cc = skimage.draw.line(y1,x1,y2,x2)
    img[rr,cc]=color
    if thickness>1:
        if x1<img.shape[1]-2 and y1<img.shape[0]-2 and x2<img.shape[1]-2 and y2<img.shape[0]-2:
            rr,cc = skimage.draw.line(y1+1,x1+1,y2+1,x2+1)
            img[rr,cc]=color
        if x1<img.shape[1]-2 and x2<img.shape[1]-2:
            rr,cc = skimage.draw.line(y1,x1+1,y2,x2+1)
            img[rr,cc]=color
        if y1<img.shape[0]-2 and y2<img.shape[0]-2:
            rr,cc = skimage.draw.line(y1+1,x1,y2+1,x2)
            img[rr,cc]=color
    if thickness>2:
        rr,cc = skimage.draw.line(y1-1,x1-1,y2-1,x2-1)
        img[rr,cc]=color
        rr,cc = skimage.draw.line(y1,x1-1,y2,x2-1)
        img[rr,cc]=color
        rr,cc = skimage.draw.line(y1-1,x1,y2-1,x2)
        img[rr,cc]=color
        if y1<img.shape[0]-2 and y2<img.shape[0]-2:
            rr,cc = skimage.draw.line(y1+1,x1-1,y2+1,x2-1)
            img[rr,cc]=color
        if x1<img.shape[1]-2 and x2<img.shape[1]-2:
            rr,cc = skimage.draw.line(y1-1,x1+1,y2-1,x2+1)
            img[rr,cc]=color
        assert(thickness<4)


def imread(path,color=True):
    return skimage.io.imread(path,not color)

def imwrite(path,img):
    return skimage.io.imsave(path,img)

def imshow(name,img):
    return skimage.io.imshow(img)

def show(): #replaces cv2.waitKey()
    return skimage.io.imshow(img)

def resize(img,dim,fx=None,fy=None): #remove ",interpolation = cv2.INTER_CUBIC"
    hasColor = len(img.shape)==3
    if dim[0]==0:
        downsize = fx<1 and fy<1
        
        return skimage.transform.rescale(img,(fy,fx),3,multichannel=hasColor,anti_aliasing=downsize)
    else:
        downsize = dim[0]<img.shape[0] and dim[1]<img.shape[1]
        return skimage.transform.resize(img,dim,3,multichannel=hasColor,anti_aliasing=downsize)

def otsuThreshold(img):
    #if len(img.shape)==3 and img.shape[2]==1:
    #    img=img[:,:,0]
    t = skimage.filters.threshold_otsu(img)
    return  t,(img>t)*255

def rgb2hsv(img):
    return skimage.color.rgb2hsv(img)
def hsv2rgb(img):
    return skimage.color.hsv2rgb(img)
def rgb2gray(img):
    return skimage.color.rgb2gray(img)
def gray2rgb(img):
    if len(img.shape) == 3:
        img=img[:,:,0]
    return skimage.color.gray2rgb(img)

def polylines(img,points,isClosed,color,thickness=1):
    if len(points.shape)==3:
        assert(points.shape[1]==1)
        points=points[:,0]
    if isClosed:
        rr,cc = skimage.draw.polygon(points[:,1],points[:,0],shape=img.shape)
    else:
        rr,cc = skimage.draw.polygon_perimeter(points[:,1],points[:,0],shape=img.shape)
    img[rr,cc]=color

def warpAffine(img,M,shape=None):
    if shape is None:
        shape=img.shape
    if M.shape[0]==2: #OpenCV takes 2x3 instead of 3x3
        M = np.concatenate((M,np.array([[0.0,0.0,1.0]])),axis=0)
    T = skimage.transform.AffineTransform(M)
    return skimage.transform.warp(img,T,output_shape=shape)
