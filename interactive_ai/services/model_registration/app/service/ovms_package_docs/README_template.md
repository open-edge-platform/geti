# OpenVINO™ Model Server deployment package

This package contains a Intel® Geti™ Model ready to deploy on OpenVINO™ Model Server.
After deploying the model on OpenVINO™ Model Server, inference on the model can be performed with easy to use HTTP interface.

## Prerequisites

1. Docker - if you do not have Docker installed locally, please follow official installation guide: https://docs.docker.com/engine/install/

## Starting OpenVINO™ Model Server Docker container

```bash
docker run -v $(pwd):/opt/ml:ro \
 -p 9001:9001 \ 
 -p 8001:8001 \
 OVMS_IMAGE_PLACEHOLDER \
  --config_path /opt/ml/config.json \
  --port 9001 --rest_port 8001
```

## Inference using HTTP API

### cURL

```bash
$ echo "{\"model\": \"GRAPH_NAME_PLACEHOLDER\", \"input\": {\"image\": \"$(base64 -w0 <path to your image>)\"}}" > request.json
$ curl -H 'Content-Type: application/json' -d @request.json localhost:8001/v3/geti
```

### Python

```python
import base64

import requests

def infer(image_path: str) -> dict:
    with open(image_path, "rb") as image:
        encoded_image = base64.b64encode(image.read())

    request_body = {
        "model": "GRAPH_NAME_PLACEHOLDER",
        "input": {
            "image": encoded_image.decode("utf-8")
        }
    }

    response = requests.post("http://localhost:8001/v3/geti", json=request_body)
    return response.json()


print(infer("image.jpg"))
```

### JavaScript

Example for NodeJS 22.11.0:

```javascript
const fs = require('fs');

async function infer(imagePath) {
  const encodedImage = Buffer.from(fs.readFileSync(imagePath)).toString('base64');
  const body = {
     "model": "GRAPH_NAME_PLACEHOLDER",
     "input": {
        "image": encodedImage
      }
  };
	const response = await fetch(
		"http://localhost:8001/v3/geti",
		{
			headers: {
				"Content-Type": "application/json"
			},
			method: "POST",
			body: JSON.stringify(body)
    }
	);
	const result = await response.json();
	return result;
}

infer("image.jpg").then((response) => {
	console.log(JSON.stringify(response));
});
```


## API Endpoint details

### Request

Request payload:
```json
{
  "model": <str; name of the Intel® Geti™ model graph>,
  "input": {
    "image": <str; input image encoded in base64>
  }
}
```

Request payload example:
```json
{
    "model": "671f94e385939c29370657c5-graph",
    "input": {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"
    }

}
```

### Response

Response schema:
```json
{
    "predictions": [
        {
            "labels": [
                {
                    "id": <str; label_id>,
                    "name": <str; label_name>,
                    "probability": <float; prediction probability for this label>
                }
            ],
            "shape": {
                <shape object, see section below for more details>
            }
        }
    ]
}
```

Depending on model that you are using, predictions can return one of the following shapes:
- Rectangle
- RotatedRectangle
- Ellipse
- Polygon
- Keypoint

Rectangle shape object:
```json
{
    "type": "RECTANGLE",
    "x": <int; X coordinate of the left side of the rectangle>,
    "y": <int; Y coordinate of the top of the rectangle>,
    "width": <int; Width of the rectangle>,
    "height": <int; Height of the rectangle>
}
```

RotatedRectangle shape object:
```json
{
    "type": "ROTATED_RECTANGLE",
    "angle": <float; angle, in degrees, under which the rectangle is defined>,
    "x": <int; X coordinate of the left side of the rectangle>,
    "y": <int; Y coordinate of the top of the rectangle>,
    "width": <int; Width of the rectangle>,
    "height": <int; Height of the rectangle>
}
```

Ellipse shape object:
```json
{
    "type": "ELLIPSE",
    "x": <int; Lowest x coordinate of the ellipse>,
    "y": <int; Lowest y coordinate of the ellipse>,
    "width": <int; Width of the ellipse>,
    "height": <int; Height of the ellipse>
}
```

Polygon shape object:
```json
{
    "type": "POLYGON",
    "points": [
        {
            "x": <int; x coordinate of polygon point>,
            "y": <int; y coordinate of polygon point>,
        }
    ]
}
```

Keypoint shape object:
```json
{
    "type": "KEYPOINT",
    "x": <int; x coordinate of the keypoint>,
    "y": <int; y coordinate of the keypoint>,
    "is_visible": <bool; if the keypoint is visible or not, always set to true>,
}
```

Response example:
```json
{
  "predictions": [
    {
      "labels": [
        {
          "id": "67220b00f511ff450090c925",
          "name": "person",
          "probability": 0.7808193564414978
        }
      ],
      "shape": {
        "height": 207,
        "type": "RECTANGLE",
        "width": 86,
        "x": 1447,
        "y": 173
      }
    },
    {
      "labels": [
        {
          "id": "67220b00f511ff450090c925",
          "name": "person",
          "probability": 0.761854887008667
        }
      ],
      "shape": {
        "height": 389,
        "type": "RECTANGLE",
        "width": 105,
        "x": 267,
        "y": 159
      }
    },
    {
      "labels": [
        {
          "id": "67220b00f511ff450090c925",
          "name": "person",
          "probability": 0.6493890881538391
        }
      ],
      "shape": {
        "height": 218,
        "type": "RECTANGLE",
        "width": 89,
        "x": 1326,
        "y": 157
      }
    }
  ]
}
```
