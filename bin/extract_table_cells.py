#!/usr/bin/env python3 
# ---------------------------------------------------------------------------- #
#
#  Copyright (c) 2019 Edson Borin <edson@ic.unicamp.br>
#
#  This file is part of the signing-sheets-tools toolset.
# 
#  The signing-sheets-tools toolset is free software: you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License 3, as published by the Free Software Foundation.
# 
#  The signing-sheets-tools toolset is distributed in the hope that
#  it will be useful, but WITHOUT ANY WARRANTY; without even the
#  implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with the signing-sheets-tools toolset.
#  If not, see <https://www.gnu.org/licenses/>.
# 
# ---------------------------------------------------------------------------- #
 
import argparse
import cv2
import os
import numpy as np

def extract(image, boxedImage=False, boxesTemplate=None, outputDir="./cells/", minWidth=15, maxWidth=1000, minHeight=15, 
    maxHeight=1000, widenFactor=0, norm1=False):

        #Check output dir
        output_dir = outputDir
        if output_dir[-1] != "/": output_dir += "/"
        if not os.path.exists(output_dir):
                print("Output dir \""+output_dir+"\"does not exist. Creating it.")
                try:
                        os.mkdir(output_dir)
                except:
                        print("Error when trying to create output dir \""+output_dir+"\". Giving up.")
                        exit(1)
        
        print("Loading image from file ", image)
        img = cv2.imread(image)

        if norm1:
                print("Normalizing image...") 
                img = normalize_img(img)
                cv2.imwrite("NormalizedTable.jpg", img)
                
        print("Extracting table cells...")
        cells = extract_table_cells(img,boxesTemplate)

        print("Filtering out cells, grouping them by row, and sorting from left to right...") 
        non_small_cells = filter_out_cells(cells, int(minWidth), int(minHeight), \
                                           int(maxWidth), int(maxHeight), \
                                           int(widenFactor))

        if boxedImage:
                print("Generating boxed image. File:", boxedImage)
                boxed_img = img.copy()
                for x,y,w,h in non_small_cells:
                        cv2.rectangle(boxed_img, (x,y), (x+w,y+h), (255,0,0), 2)
                        cv2.line(boxed_img, (x,y), (x+w,y+h), (0,0,255), 2)
                        cv2.line(boxed_img, (x,y+h), (x+w,y), (0,0,255), 2)
                cv2.imwrite(boxedImage, boxed_img)
        
        print("Group cells by row and sort by column order...")
        sorted_cells = group_by_row_and_sort_by_column(non_small_cells)

        print("Extracting cell images and output do directory:"+outputDir)
        row = 0
        stats = {} # Map number of cols => Number of rows 
        for k, l in sorted_cells.items():
                row += 1
                col = 0
                for x,y,w,h in l:
                        col += 1
                        new_img = img[y:y+h, x:x+w]
                        new_img = removeMargins(new_img)
                        generate_img(row,col,new_img,output_dir,image)
                if col in stats: stats[col] += 1
                else: stats[col] = 1
                if col != 6: print("Warning: row",row,"has",col,"columns")
        print("Stats")
        for k, v in stats.items():
                print(v,"row(s) with",k,"column(s).")

def str2bool(v):
        if isinstance(v, bool):
                return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
                return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
                return False
        else:
                raise argparse.ArgumentTypeError('Boolean value expected.')

def extract_table_cells(img,boxes_template_fn):
        # Thresholding the image
        (thresh, img_bin) = cv2.threshold(img, 128, 255,cv2.THRESH_BINARY, cv2.THRESH_OTSU)
        # Invert the image
        img_bin = 255-img_bin 

        # Defining a kernel length
        hori_kernel_length = np.array(img).shape[1]//100
        vert_kernel_length = np.array(img).shape[0]//100
        print("image shape =", np.array(img).shape)
        print("Hori kernel length = {}, Vert kernel length = {}".format(hori_kernel_length, vert_kernel_length))
        # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
        verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vert_kernel_length))
        # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
        hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hori_kernel_length, 1))
        # A kernel of (3 X 3) ones.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        #img_temp11 = img_bin
        #img_temp11 = cv2.dilate(img_temp11, verticle_kernel, iterations=1)
        #img_temp11 = cv2.erode(img_temp11, verticle_kernel, iterations=1)
        img_temp1 = cv2.erode(img_bin, verticle_kernel, iterations=3)
        vertical_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=3)
        vertical_lines_img = cv2.dilate(vertical_lines_img, np.ones((3,3), np.uint8))
        # Morphological operation to detect horizontal lines from an image
        img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=3)
        horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=3)
        horizontal_lines_img = cv2.dilate(horizontal_lines_img, np.ones((3,3), np.uint8))

        # Clear headline
        gray_vertical_lines = cv2.cvtColor(vertical_lines_img, cv2.COLOR_RGB2GRAY)
        gray_horizontal_lines = cv2.cvtColor(horizontal_lines_img, cv2.COLOR_RGB2GRAY)
        vertical_contours, tmp_hierarchy = cv2.findContours(gray_vertical_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        horizontal_contours, tmp_hierarchy2 = cv2.findContours(gray_horizontal_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        top_most_position = img.shape[0]
        for cnt in vertical_contours:
            contour_top_most_y = tuple(cnt[cnt[:,:,1].argmin()][0])[1]
            if contour_top_most_y < top_most_position:
                top_most_position = contour_top_most_y
        for y in range(horizontal_lines_img.shape[1]):
            for x in range(0, top_most_position):
                for z in range(horizontal_lines_img.shape[2]):
                    horizontal_lines_img[x, y, z] = 0

        positions_matrix = []
        blank = np.zeros(img.shape)
        gray_horizontal_lines = cv2.cvtColor(horizontal_lines_img, cv2.COLOR_RGB2GRAY)
        horizontal_edged = cv2.Canny(gray_horizontal_lines, 75, 200)
        horizontal_contours, horizontal_hierarchy = cv2.findContours(horizontal_edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in horizontal_contours:
            cv2.drawContours(img, cnt, -1, (255, 0, 0), 1)

        for cnt in horizontal_contours:
            position_vector = []


        img1 = cv2.drawContours(blank.copy(), vertical_contours, -1, (255, 255, 255), 3)
        img2 = cv2.drawContours(blank.copy(), horizontal_contours, -1, (255, 255, 255), 3)

        intersection = np.logical_and(img1, img2)
        # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
        alpha = 0.5
        beta = 1.0 - alpha
        # This function helps to add two image with specific weight parameter to get a third image as summation of two image.
        img_final_bin = cv2.addWeighted(vertical_lines_img, alpha, horizontal_lines_img, beta, 0.0)

        img_final_bin = cv2.erode(~img_final_bin, kernel, iterations=2)
        (thresh, img_final_bin) = cv2.threshold(img_final_bin, 128,255, cv2.THRESH_BINARY, cv2.THRESH_OTSU)

        if boxes_template_fn:
                cv2.imwrite(boxes_template_fn, img_final_bin)

        # Find contours for image, which will detect all the boxes
        img_final_bin = cv2.cvtColor(img_final_bin, cv2.COLOR_RGB2GRAY)
        contours, hierarchy = cv2.findContours(img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Format boxes as tuples of (x,y,w,h), where x,y is the position of
        # the top-left corner, w = width and h = height
        cells = []
        for c in contours:
                # Returns the location and width,height for every contour
                x, y, w, h = cv2.boundingRect(c)
                cells.append((x, y, w, h))
        return cells

def search_row_set(rs,yi,hi):
    m1 = yi + hi/2
    for k, v in rs.items():
        l = v[-1]
        x, y, h = l[0], l[1], l[3]
        m2 = y + h/2
        if m1 >= y-h/2 and m1 <= y+(3*h/4): #and xi > x:
            return k
        #y, h = k
        #if m >= y and m <= y+h:
        #    return k
    return None

def group_by_row_and_sort_by_column(cells):
    print("Number of cells: ", len(cells))
    # Sort by y (tup[1])
    cells.sort(key=lambda tup: tup[1])
    row_sets = {}
    for x,y,w,h in cells:
            # Filter out small cells
            k = search_row_set(row_sets,y,h)
            if k == None:
                    row_sets[(y,h)] = [(x,y,w,h)]
            else:
                    row_sets[k].append((x,y,w,h))
    
    #Sort sets by x
    for k, v in row_sets.items():
            v.sort(key=lambda tup: tup[0])

    return row_sets

def filter_out_cells(cells, min_w, min_h, max_w, max_h, wf):
        filtered_list = []
        for x,y,w,h in cells:
                # Filter out small cells
                if (w >= min_w and h >= min_h and w <= max_w and h <= max_h):
                        filtered_list.append((x-wf,y-wf,w+2*wf,h+2*wf))
        return filtered_list

def generate_img(row,col,img,base_dir,image):
        cv2.imwrite(base_dir+image[:-4]+"-cell-"+"{0:0=2d}-".format(row)+"{0:0=2d}".format(col)+'.png', img)

def removeMargins(image):
    horizontalKernel = np.uint8(np.array([[0,0,0],[1,1,1],[0,0,0]]))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = (255 - gray)

    eroded = cv2.erode(gray, horizontalKernel, iterations=20)
    restored = cv2.dilate(eroded, horizontalKernel, iterations=20)

    cleansed = gray - restored

    return (255 - cleansed)

try:
        import imutils
        
        def stretch_img(image, pts):
	        rect = np.zeros((4, 2), dtype = "float32")
	        s = pts.sum(axis = 1)
	        rect[0] = pts[np.argmin(s)]
	        rect[2] = pts[np.argmax(s)]
	        diff = np.diff(pts, axis = 1)
	        rect[1] = pts[np.argmin(diff)]
	        rect[3] = pts[np.argmax(diff)]
	        (tl, tr, br, bl) = rect
	        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
	        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
	        maxWidth = max(int(widthA), int(widthB))
	        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
	        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
	        maxHeight = max(int(heightA), int(heightB))
	        dst = np.array([[0, 0],[maxWidth - 1, 0],[maxWidth - 1, maxHeight - 1],[0, maxHeight - 1]], dtype = "float32")
	        M = cv2.getPerspectiveTransform(rect, dst)
	        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
	        return warped

        def normalize_img(img):
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                edged = cv2.Canny(gray, 75, 200)
                cv2.imwrite("TestCanny.jpg", edged)
                cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
                for c in cnts:
	                # approximate the contour
	                peri = cv2.arcLength(c, True)
	                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
	                if len(approx) == 4:
		                screenCnt = approx
		                break
                warped = stretch_img(img, screenCnt.reshape(4, 2))
                return warped
        
except:
        def normalize_img(img):
                print("WARNING: could not import imutils.")
                print("WARNING: option -norm1 disabled.")
                return img

