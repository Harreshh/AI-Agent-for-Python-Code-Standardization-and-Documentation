import numpy as np
 
def compute_parameters(pixels, mm):
    pixels = np.array(pixels, dtype=int)
    mm     = np.array(mm, dtype=float)
    x = pixels[:, 0]
    y = pixels[:, 1]
    X = mm[:, 0]
    Y = mm[:, 1]
    # X
    A_x = np.vstack([x, np.ones_like(x)]).T
    sx, tx = np.linalg.lstsq(A_x, X, rcond=None)[0]
    print(A_x)
    A_y = np.vstack([y, np.ones_like(y)]).T
    sy, ty = np.linalg.lstsq(A_y, Y, rcond=None)[0]
    print(A_y)
    return sx, tx, sy, ty
 
def pixel_to_mm(x, y, params):
    sx, tx, sy, ty = params
    X = sx * x + tx
    Y = sy * y + ty
    return X, Y
#-----------------------------
 
pixels = [[730, 540],[785, 1277],[241, 548],[230, 1277]]
mm = [[268.8905, -275.3674],[272.0310, -321.4426],[240.7092, -275.6674],[240.1387, -319.6548]]
 
params = compute_parameters(pixels, mm)
print("sx, tx, sy, ty =", params)
 
print(pixel_to_mm(730, 540, params))
 
