import cv2
import numpy as np
from scipy import ndimage

from PyQt5 import QtGui

def bbox_iou(b1, b2):
    '''
    b: (x1,y1,x2,y2)
    '''
    lx = max(b1[0], b2[0])
    rx = min(b1[2], b2[2])
    uy = max(b1[1], b2[1])
    dy = min(b1[3], b2[3])
    if rx <= lx or dy <= uy:
        return 0.
    else:
        interArea = (rx-lx)*(dy-uy)
        a1 = float((b1[2] - b1[0]) * (b1[3] - b1[1]))
        a2 = float((b2[2] - b2[0]) * (b2[3] - b2[1]))
        return interArea / (a1 + a2 - interArea)

def crop_padding(img, roi, pad_value):
    '''
    img: HxW or HxWxC np.ndarray
    roi: (x,y,w,h)
    pad_value: [b,g,r, (a)]
    '''
    need_squeeze = False
    if len(img.shape) == 2:
        img = img[:,:,np.newaxis]
        need_squeeze = True
    assert len(pad_value) == img.shape[2]
    x,y,w,h = roi
    x,y,w,h = int(x),int(y),int(w),int(h)
    H, W = img.shape[:2]
    output = np.tile(np.array(pad_value), (h, w, 1)).astype(img.dtype)
    if bbox_iou((x,y,x+w,y+h), (0,0,W,H)) > 0:
        output[max(-y,0):min(H-y,h), max(-x,0):min(W-x,w), :] = img[max(y,0):min(y+h,H), max(x,0):min(x+w,W), :]
    if need_squeeze:
        output = np.squeeze(output)
    return output

def resize_with_center(img, center, ratio):
    cx, cy = center
    h, w = img.shape[:2]
    nh, nw = int(h * ratio), int(w * ratio)
    center_move_x = cx * (ratio - 1)
    center_move_y = cy * (ratio - 1)
    newimg = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    #newimg[:,:,3][newimg[:,:,3] < 255] = 0
    bbox = [center_move_x, center_move_y, w, h]
    newimg = crop_padding(newimg, bbox, pad_value=tuple([0] * img.shape[2]))
    return newimg

def rotate_with_center(img, center, degree):
    cx, cy = map(int, center)
    h, w, ch = img.shape
    bbox_centered = [0, 0, 2 * cx, 2 * cy]
    img_c = crop_padding(img, bbox_centered, pad_value=tuple([0] * ch))
    img_r = ndimage.rotate(img_c, degree, reshape=False)
    bbox_recover = [0, 0, w, h]
    return crop_padding(img_r, bbox_recover, pad_value=tuple([0] * ch))

def mask_to_bbox(mask):
    mask = (mask == 1)
    if np.all(~mask):
        return [0, 0, 0, 0]
    assert len(mask.shape) == 2
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return [cmin.item(), rmin.item(), cmax.item() + 1 - cmin.item(), rmax.item() + 1 - rmin.item()] # xywh

def compute_center(img):
    assert img.shape[2] == 4
    mask = img[:,:,3] > 128
    bbox = mask_to_bbox(mask)
    center_x = bbox[0] + bbox[2] // 2
    center_y = bbox[1] + bbox[3] // 2
    return [center_x, center_y]
