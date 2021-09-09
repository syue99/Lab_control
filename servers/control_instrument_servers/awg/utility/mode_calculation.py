from scipy.optimize import newton
import numpy as np


def Eqposition3(N):
    def func(u): #the equations
        p=np.empty(shape=(N))
        for m in range(N):
            p[m]=u[m]-np.sum(1/(u[m]-u[:m])**2)+np.sum(1/(u[m]-u[m+1:])**2)
        return p
    
    def dfunc(u): # first order derivative
        p=np.empty(shape=(N))
        for m in range(N):
            p[m]=1+2*np.sum(1/(u[m]-u[:m])**3)-2*np.sum(1/(u[m]-u[m+1:])**3)
        return p
    
    def ddfunc(u): # second order derivative
        p=np.empty(shape=(N))
        for m in range(N):
            p[m]=np.sum(1/(u[m]-u[:m])**4) - np.sum(1/(u[m]-u[m+1:])**4)
        return p
    
    ni = np.arange(0,N)
    guess = 3.94*(N**0.387)*np.sin(1/3*np.arcsin(1.75*N**(-0.982)*((ni+1)-(N+1)/2)))
    
    x0=newton(func,guess,fprime=dfunc,maxiter=100000) # newton method
    
    return(np.round(x0,5))
def Axialfull(N, wz): # N is the ion number, wz is the axial frequency, in MHz
    u=Eqposition3(N)
    u_1=np.empty(shape=(N))
    for i in range(N):
        u_1[i]= np.sum(1/np.absolute(u[i]-u[:i])**3) + np.sum(1/np.absolute(u[i]-u[i+1:])**3)
    A=np.empty((N,N))
    for i in range(N):
        for j in range(N):
            if j==i:
                A[i,j]=1+2*u_1[i] # A_mn, m==n
            else:
                A[i,j]=-2/np.absolute(u[i]-u[j])**3 #A_mn, m!=n
    w,v = np.linalg.eig(A)
    idx = np.argsort(w)
    w = w[idx]
    v = v[:,idx]
    return ([w,v])
    
def Axialmodes(N, wz):
    return(np.sqrt(Axialfull(N, wz)[0])*wz)