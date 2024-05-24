from ctypes import Structure, POINTER

class NCCAMHANDLE(Structure):
    pass

NCCAM = POINTER(NCCAMHANDLE)

class NCIMAGEHANDLE(Structure):
    pass

NCIMAGE = POINTER(NCIMAGEHANDLE)