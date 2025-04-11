// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export const BUTTON_LEFT = {
    button: 0,
    buttons: 1,
};

export const BUTTON_RIGHT = {
    button: 2,
    buttons: 2,
};

const BUTTON_WHEEL = {
    button: 1,
    buttons: 4,
};

const BUTTON_ERASER = {
    button: 5,
    buttons: 32,
};

export interface MouseButton {
    button: number;
    buttons: number;
}

const isButton = (button: MouseButton, buttonToCompare: MouseButton): boolean =>
    button.button === buttonToCompare.button || button.buttons === buttonToCompare.buttons;

export const isLeftButton = (button: MouseButton): boolean => {
    return isButton(button, BUTTON_LEFT);
};

export const isRightButton = (button: MouseButton): boolean => {
    return isButton(button, BUTTON_RIGHT);
};

export const isWheelButton = (button: MouseButton): boolean => {
    return isButton(button, BUTTON_WHEEL);
};

export const isEraserButton = (button: MouseButton): boolean => {
    return isButton(button, BUTTON_ERASER);
};

export const isEraserOrRightButton = (button: MouseButton): boolean => {
    return isButton(button, BUTTON_ERASER) || isButton(button, BUTTON_RIGHT);
};
