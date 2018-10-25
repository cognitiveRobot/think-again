from flask import Flask, request, jsonify
import io
import numpy as np
import tensorflow as tf
from PIL import Image
from keras.applications import ResNet50, imagenet_utils
from keras.preprocessing.image import img_to_array

# initialize the Flask app
app = Flask(__name__)
app.debug = True

# initialize the model
model = None
graph = None

def load_model(model, graph):
    # load the pre-trained Keras model (here we are using a model
	# pre-trained on ImageNet and provided by Keras, but you can
	# substitute in your own networks just as easily)
	# global model, graph
	model = ResNet50(weights="imagenet")
	graph = tf.get_default_graph()

	return model, graph

def prepare_image(image, target):
	# if the image mode is not RGB, convert it
	if image.mode != "RGB":
		image = image.convert("RGB")

	# resize the input image and preprocess it
	image = image.resize(target)
	image = img_to_array(image)
	image = np.expand_dims(image, axis=0)
	image = imagenet_utils.preprocess_input(image)

	print("Image is ready for prediction")
	# return the processed image
	return image


@app.route("/api/predict_dog_breed", methods=['POST'])
def predict_dog_breed():
    # initialize the data dictionary that will be returned from the
	# view
	data = {"success": False}

	# ensure an image was properly uploaded to our endpoint
	if request.method == "POST":
		if request.files.get("image"):
			# read the image in PIL format
			image = request.files["image"].read()
			image = Image.open(io.BytesIO(image))

			# preprocess the image and prepare it for classification
			image = prepare_image(image, target=(224, 224))

			# classify the input image and then initialize the list
			# of predictions to return to the client
			with graph.as_default():
				preds = model.predict(image)
			results = imagenet_utils.decode_predictions(preds)
			data["predictions"] = []

			# loop over the results and add them to the list of
			# returned predictions
			for (imagenetID, label, prob) in results[0]:
				r = {"label": label, "probability": float(prob)}
				data["predictions"].append(r)

			# indicate that the request was a success
			data["success"] = True

	# return the data dictionary as a JSON response
	return jsonify(data)


# The main function
if __name__ == "__main__":
    print("Loading Keras model, afterwords Flask server will start.."
    "Please wait")

    # call to load
    model, graph = load_model(model, graph)
    # Run the app
    app.run()
