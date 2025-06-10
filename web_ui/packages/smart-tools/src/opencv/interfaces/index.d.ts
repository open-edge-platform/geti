// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/// <reference lib="webworker" />
/// <reference path="scalars.d.ts" />
/// <reference path="constants.d.ts" />
/// <reference path="Mat.d.ts" />
/// <reference path="valueObjects.d.ts" />
/// <reference path="enums.d.ts" />
/// <reference path="vectors.d.ts" />
/// <reference path="emscripten.d.ts" />
/// <reference path="functions.d.ts" />
/// <reference path="helpers.d.ts" />

declare module 'opencv-types' {
    export * from 'mat';
    export * from 'cv_constants';
    export * from 'valueObjects';
    export * from 'scalars';
    export * from 'enums';
    export * from 'functions';
    export * from 'vectors';
    export * from 'emscripten';
    export * from 'helpers';
}

declare module 'OpenCVTypes' {
    import * as OpenCVTypes from '.';

    export = OpenCVTypes;
}

declare const cv: Promise<OpenCVTypes.cv>;
