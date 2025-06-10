// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0
declare module 'helpers' {
    import { Mat } from 'mat';
    import { int } from 'scalars';

    function matFromArray<T>(rows: int, cols: int, type: int, array: ArrayLike<T>): Mat;

    function matFromImageData(imageData: ImageData): Mat;
}
