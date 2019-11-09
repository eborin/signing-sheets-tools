from PIL import Image
from Preprocessing import convert_to_image_tensor, invert_image
import torch
from Model import SiameseConvNet, distance_metric
from io import BytesIO

def load_model():
    device = torch.device('cpu')
    model = SiameseConvNet().eval()
    model.load_state_dict(torch.load('Models/model_epoch_2', map_location=device))
    return model

def is_signature_equal(groundTruthPath, croppedImagePath):
    groundTruth = Image.open(groundTruthPath)
    croppedImage = Image.open(croppedImagePath)

    groundTruth = convert_to_image_tensor(invert_image(groundTruth)).view(1, 1, 220, 155)
    croppedImage = convert_to_image_tensor(invert_image(croppedImage)).view(1, 1, 220, 155)

    model = load_model()
    f_groundTruth, f_croppedImage = model.forward(groundTruth, croppedImage)
    dist = distance_metric(f_groundTruth, f_croppedImage).detach().numpy()
    print('Dist={}'.format(dist))
    if dist <= 0.145139:
        print ("signatures are the same")
        return 1
    else:
        print ("signatures are different")
        return 0