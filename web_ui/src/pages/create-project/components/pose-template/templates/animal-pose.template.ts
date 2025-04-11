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

export const animalPose = {
    points: [
        { label: 'nose', x: 0.1882, y: 0.3792 },
        { label: 'top head', x: 0.2497, y: 0.1792 },
        { label: 'withers', x: 0.4263, y: 0.4981 },
        { label: 'right front elbow', x: 0.3582, y: 0.7142 },
        { label: 'right front wrist', x: 0.3455, y: 0.8028 },
        { label: 'right front paw', x: 0.2961, y: 0.8943 },
        { label: 'left front elbow', x: 0.4532, y: 0.7028 },
        { label: 'left front wrist', x: 0.4374, y: 0.8102 },
        { label: 'left front paw', x: 0.3829, y: 0.9226 },
        { label: 'tail set', x: 0.6763, y: 0.5264 },
        { label: 'tail tip', x: 0.7237, y: 0.3962 },
        { label: 'left back elbow', x: 0.6416, y: 0.6726 },
        { label: 'left back wrist', x: 0.7158, y: 0.7943 },
        { label: 'left back paw', x: 0.6868, y: 0.915 },
        { label: 'right back elbow', x: 0.5618, y: 0.6811 },
        { label: 'right back wrist', x: 0.5776, y: 0.7766 },
        { label: 'right back paw', x: 0.5337, y: 0.8736 },
    ],
    edges: [
        { to: 'top head', from: 'nose' },
        { to: 'withers', from: 'top head' },
        { to: 'right front elbow', from: 'withers' },
        { to: 'right front wrist', from: 'right front elbow' },
        { to: 'right front paw', from: 'right front wrist' },
        { to: 'left front elbow', from: 'withers' },
        { to: 'left front wrist', from: 'left front elbow' },
        { to: 'left front paw', from: 'left front wrist' },
        { to: 'tail set', from: 'withers' },
        { to: 'tail tip', from: 'tail set' },
        { to: 'left back elbow', from: 'tail set' },
        { to: 'left back wrist', from: 'left back elbow' },
        { to: 'left back paw', from: 'left back wrist' },
        { to: 'right back elbow', from: 'tail set' },
        { to: 'right back wrist', from: 'right back elbow' },
        { to: 'right back paw', from: 'right back wrist' },
    ],
};
