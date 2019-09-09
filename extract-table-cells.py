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

def main():

        ap = argparse.ArgumentParser()

        ap.add_argument("-i", "--image", required=True,
                        help="input image's path")
        ap.add_argument("-bi", "--boxed_image", required=False,
                        help="Filename to write the image marked with cell boxes. Usefull for debugging.")
        ap.add_argument("-bt", "--boxes_template", required=False,
                        help="Filename to write the boxes template. Usefull for debugging.")
        ap.add_argument("-od", "--output_dir", required=False, default = "./",
                        help="Output directory to write cells")
        ap.add_argument("-min_width", default=15, required=False,
                        help="Filter out cells with width smaller than min_width. Default = 15.")
        ap.add_argument("-max_width", default=1000, required=False,
                        help="Filter out cells with width larger than max_width. Default = 1000.")
        ap.add_argument("-min_height", default=15, required=False,
                        help="Filter out cells with height smaller than min_height. Default = 15.")
        ap.add_argument("-max_height", default=1000, required=False,
                        help="Filter out cells with height larger than max_height. Default = 1000.")
        ap.add_argument("-widen_factor", default=0, required=False,
                        help="Factor used to widen cells.")
        ap.add_argument("-norm1", type=str2bool, nargs='?',
                        const=True, default=False, required=False,
                        help="Detect outer box and normalize image")

        args = vars(ap.parse_args())

        #Check output dir
        output_dir=args["output_dir"]
        if output_dir[-1] != "/": output_dir += "/"
        if not os.path.exists(output_dir):
                print("Output dir \""+output_dir+"\"does not exist. Creating it.")
                try:
                        os.mkdir(output_dir)
                except:
                        print("Error when trying to create output dir \""+output_dir+"\". Giving up.")
                        exit(1)
        
        print("Loading image from file ", args["image"])
        img = cv2.imread(args["image"])

        if args["norm1"]:
                print("Normalizing image...") 
                img = normalize_img(img)
                
        print("Extracting table cells...")
        cells = extract_table_cells(img,args["boxes_template"])

        print("Filtering out cells, grouping them by row, and sorting from left to right...") 
        non_small_cells = filter_out_cells(cells, int(args["min_width"]), int(args["min_height"]), \
                                           int(args["max_width"]), int(args["max_height"]), \
                                           int(args["widen_factor"]))

        if args["boxed_image"]:
                print("Generating boxed image. File:", args["boxed_image"])
                boxed_img = img.copy()
                for x,y,w,h in non_small_cells:
                        cv2.rectangle(boxed_img, (x,y), (x+w,y+h), (255,0,0), 2)
                        cv2.line(boxed_img, (x,y), (x+w,y+h), (0,0,255), 2)
                        cv2.line(boxed_img, (x,y+h), (x+w,y), (0,0,255), 2)
                cv2.imwrite(args["boxed_image"], boxed_img)
        
        print("Group cells by row and sort by column order...")
        sorted_cells = group_by_row_and_sort_by_column(non_small_cells)

        print("Extracting cell images and output do directory:"+args["output_dir"])
        row = 0
        stats = {} # Map number of cols => Number of rows 
        for k, l in sorted_cells.items():
                row += 1
                col = 0
                for x,y,w,h in l:
                        col += 1
                        new_img = img[y:y+h, x:x+w]
                        generate_img(row,col,new_img,output_dir)
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
        kernel_length = np.array(img).shape[1]//100
        #print("kernel length =",kernel_length)
        # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
        verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
        # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
        hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
        # A kernel of (3 X 3) ones.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        # Morphological operation to detect vertical lines from an image
        #img_temp11 = img_bin
        #img_temp11 = cv2.dilate(img_temp11, verticle_kernel, iterations=1)
        #img_temp11 = cv2.erode(img_temp11, verticle_kernel, iterations=1)
        img_temp1 = cv2.erode(img_bin, verticle_kernel, iterations=3)
        verticle_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=3)
        # Morphological operation to detect horizontal lines from an image
        img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=3)
        horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=3)

        # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
        alpha = 0.5
        beta = 1.0 - alpha
        # This function helps to add two image with specific weight parameter to get a third image as summation of two image.
        img_final_bin = cv2.addWeighted(verticle_lines_img, alpha, horizontal_lines_img, beta, 0.0)
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
    m = yi + hi/2
    for k, v in rs.items():
        y, h = k
        if m >= y and m <= y+h:
            return k
    return None

def group_by_row_and_sort_by_column(cells):
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

def generate_img(row,col,img,base_dir):
        cv2.imwrite(base_dir+"cell-"+"{0:0=2d}-".format(row)+"{0:0=2d}".format(col)+'.png', img)

                        
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

# ------- #

main()
