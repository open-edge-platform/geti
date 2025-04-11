// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export const humanPose = {
    points: [
        { label: 'head', x: 0.5172, y: 0.1 },
        { label: 'spine shoulder', x: 0.5172, y: 0.2235 },
        { label: 'left shoulder', x: 0.4543, y: 0.2328 },
        { label: 'right shoulder', x: 0.5762, y: 0.2328 },
        { label: 'left elbow', x: 0.3648, y: 0.3626 },
        { label: 'right elbow', x: 0.6486, y: 0.3626 },
        { label: 'right wrist', x: 0.7, y: 0.4954 },
        { label: 'left wrist', x: 0.3, y: 0.4954 },
        { label: 'spine base', x: 0.5172, y: 0.4645 },
        { label: 'left hip', x: 0.46, y: 0.4954 },
        { label: 'right hip', x: 0.5743, y: 0.4954 },
        { label: 'right knee', x: 0.5972, y: 0.693 },
        { label: 'left knee', x: 0.4467, y: 0.693 },
        { label: 'left ankle', x: 0.4372, y: 0.8907 },
        { label: 'right ankle', x: 0.6048, y: 0.8907 },
    ],
    edges: [
        { to: 'left shoulder', from: 'spine shoulder' },
        { to: 'left ankle', from: 'left knee' },
        { to: 'left elbow', from: 'left shoulder' },
        { to: 'right elbow', from: 'right shoulder' },
        { to: 'spine shoulder', from: 'right shoulder' },
        { to: 'left hip', from: 'left knee' },
        { to: 'right knee', from: 'right hip' },
        { to: 'right ankle', from: 'right knee' },
        { to: 'head', from: 'spine shoulder' },
        { to: 'right wrist', from: 'right elbow' },
        { to: 'left wrist', from: 'left elbow' },
        { to: 'spine base', from: 'spine shoulder' },
        { from: 'spine base', to: 'left hip' },
        { from: 'spine base', to: 'right hip' },
    ],
};
