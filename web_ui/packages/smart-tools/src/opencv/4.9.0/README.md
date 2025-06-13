# OpenCV Readme

We're only using some of the modules from OpenCV so the goal is to have an opencv file with just the used code, making it a lot smaller.
Specifically the watershed, polygon optimization, grabcut and intelligent scissors tools.

In order to improve the performance of the application we build OpenCV with only the functionality we use.

## Install

Following instructions below, but make sure you install and activate emscripten 2.0.10 (`./emsdk install 2.0.10 & ./emsdk activate 2.0.10`). The new version of emscripten is not compatible with opencv at the moment of writing.

1. [install emscripten](https://emscripten.org/docs/getting_started/downloads.html)
2. follow further [instructions](https://docs.opencv.org/4.x/d4/da1/tutorial_js_setup.html) for downloading and building OpenCV.

## Build

Execute `emcmake python ./opencv/platforms/js/build_js.py build_js` to build OpenCV.
You can then copy over `./build_js/bin/opencv.js` to `opencv` folder.

In order to select the features that openCV is built with you need to edit `./opencv/platforms/js/opencv_js.config.py`.
There you can append the following and replace the `white_list` variable. When adding features do _not_ forget to update this list below so we can keep track of the used functionality.

```
web_gui = {
    '': [
        'rectangle',
        'resize',
        'findContours',
        'contourArea',
        'approxPolyDP',
        'cvtColor',
        'polylines',
        'threshold',
        'watershed',
        'grabCut',
        'bitwise_or',
        'flip',
        'circle',
        'add',
        'subtract',
        'divide',
        'exp',
        'split',
        'boundingRect',
        'contourArea',
        'normalize',
        'matchTemplate',
        'pointPolygonTest',
        'applyColorMap',
        'copyMakeBorder',
        'blobFromImage',
        'minAreaRect'
    ],
    'segmentation_IntelligentScissorsMB': [
        'IntelligentScissorsMB',
        'setGradientMagnitudeMaxLimit',
        'setEdgeFeatureCannyParameters',
        'applyImage',
        'buildMap',
        'getContour'
    ],
    'DescriptorMatcher': [
        'clone'
    ]
}

white_list = makeWhiteList([web_gui])
```
