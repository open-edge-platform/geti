// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0

/* eslint-disable max-len */

declare module 'mat' {
    import { EmClassHandle } from 'emscripten';
    import { int, double } from 'scalars';
    import { RectLike, ScalarLike, SizeLike, RangeLike } from 'valueObjects';

    class Mat extends EmClassHandle {
        // .constructor<>()
        constructor();
        // .constructor<const Mat&>()
        constructor(mat: Mat);
        // .constructor<Size, int>()
        constructor(size: SizeLike, type: int);
        // .constructor<int, int, int>()
        constructor(rows: int, cols: int, type: int);
        // .constructor<int, int, int, const Scalar&>()
        constructor(rows: int, cols: int, type: int, scalar: ScalarLike);
        // .constructor(&binding_utils::createMat, allow_raw_pointers())
        constructor(rows: int, cols: int, type: int, data: unknown, step: number);
        // .class_function("eye", select_overload<Mat(Size, int)>(&binding_utils::matEye))
        static eye(size: SizeLike, type: int): Mat;
        // .class_function("eye", select_overload<Mat(int, int, int)>(&binding_utils::matEye))
        static eye(rows: int, cols: int, type: int): Mat;
        // .class_function("ones", select_overload<Mat(Size, int)>(&binding_utils::matOnes))
        static ones(size: SizeLike, type: int): Mat;
        // .class_function("ones", select_overload<Mat(int, int, int)>(&binding_utils::matOnes))
        static ones(rows: int, cols: int, type: int): Mat;
        // .class_function("zeros", select_overload<Mat(Size, int)>(&binding_utils::matZeros))
        static zeros(size: SizeLike, type: int): Mat;
        // .class_function("zeros", select_overload<Mat(int, int, int)>(&binding_utils::matZeros))
        static zeros(rows: int, cols: int, type: int): Mat;
        // .property("rows", &cv::Mat::rows)
        readonly rows: int;
        // .property("cols", &cv::Mat::cols)
        readonly cols: int;
        // .property("matSize", &binding_utils::getMatSize)
        readonly matSize: int[];
        // .property("step", &binding_utils::getMatStep)
        readonly step: int[];
        // .property("data", &binding_utils::matData<unsigned char>)
        readonly data: Uint8Array;
        // .property("data8S", &binding_utils::matData<char>)
        readonly data8S: Int8Array;
        // .property("data16U", &binding_utils::matData<unsigned short>)
        readonly data16U: Uint16Array;
        // .property("data16S", &binding_utils::matData<short>)
        readonly data16S: Int16Array;
        // .property("data32S", &binding_utils::matData<int>)
        readonly data32S: Int32Array;
        // .property("data32F", &binding_utils::matData<float>)
        readonly data32F: Float32Array;
        // .property("data64F", &binding_utils::matData<double>)
        readonly data64F: Float64Array;

        // .function("elemSize", select_overload<size_t()const>(&cv::Mat::elemSize))
        elemSize(): int;
        // .function("elemSize1", select_overload<size_t()const>(&cv::Mat::elemSize1))
        elemSize1(): int;
        // .function("channels", select_overload<int()const>(&cv::Mat::channels))
        channels(): int;
        // .function("convertTo", select_overload<void(const Mat&, Mat&, int, double, double)>(&binding_utils::convertTo))
        convertTo(m: Mat, rtype: int, alpha: double, beta: double): void;
        // .function("convertTo", select_overload<void(const Mat&, Mat&, int)>(&binding_utils::convertTo))
        convertTo(m: Mat, rtype: int): void;
        // .function("convertTo", select_overload<void(const Mat&, Mat&, int, double)>(&binding_utils::convertTo))
        convertTo(m: Mat, rtype: int, alpha: double): void;
        // .function("total", select_overload<size_t()const>(&cv::Mat::total))
        total(): int;
        // .function("row", select_overload<Mat(int)const>(&cv::Mat::row))
        row(y: int): Mat;
        // .function("create", select_overload<void(int, int, int)>(&cv::Mat::create))
        create(rows: int, cols: int, type: int): Mat;
        // .function("create", select_overload<void(Size, int)>(&cv::Mat::create))
        create(size: SizeLike, type: int): Mat;
        // .function("rowRange", select_overload<Mat(int, int)const>(&cv::Mat::rowRange))
        rowRange(startrow: int, endrow: int): Mat;
        // .function("rowRange", select_overload<Mat(const Range&)const>(&cv::Mat::rowRange))
        rowRange(r: RangeLike): Mat;
        // .function("copyTo", select_overload<void(const Mat&, Mat&)>(&binding_utils::matCopyTo))
        copyTo(mat: Mat): void;
        // .function("copyTo", select_overload<void(const Mat&, Mat&, const Mat&)>(&binding_utils::matCopyTo))
        copyTo(mat: Mat, mask: Mat): void;
        // .function("type", select_overload<int()const>(&cv::Mat::type)
        type(): int;
        // .function("empty", select_overload<bool()const>(&cv::Mat::empty))
        empty(): boolean;
        // .function("colRange", select_overload<Mat(int, int)const>(&cv::Mat::colRange))
        colRange(startcol: int, endcol: int): Mat;
        // .function("colRange", select_overload<Mat(const Range&)const>(&cv::Mat::colRange))
        colRange(r: RangeLike): Mat;
        // .function("step1", select_overload<size_t(int)const>(&cv::Mat::step1))
        step1(i: int): int;
        // .function("clone", select_overload<Mat()const>(&cv::Mat::clone))
        clone(): Mat;
        // .function("depth", select_overload<int()const>(&cv::Mat::depth))
        depth(): int;
        // .function("col", select_overload<Mat(int)const>(&cv::Mat::col))
        col(x: int): Mat;
        // .function("dot", select_overload<double(const Mat&, const Mat&)>(&binding_utils::matDot))
        dot(mat: Mat): double;
        // .function("mul", select_overload<Mat(const Mat&, const Mat&, double)>(&binding_utils::matMul))
        mul(mat: Mat, scale: double): Mat;
        // .function("inv", select_overload<Mat(const Mat&, int)>(&binding_utils::matInv))
        inv(type: int): Mat;
        // .function("t", select_overload<Mat(const Mat&)>(&binding_utils::matT))
        t(): Mat;
        // .function("roi", select_overload<Mat(const Rect&)const>(&cv::Mat::operator()))
        roi(rect: RectLike): Mat;
        // .function("diag", select_overload<Mat(const Mat&, int)>(&binding_utils::matDiag))
        diag(d: int): Mat;
        // .function("diag", select_overload<Mat(const Mat&)>(&binding_utils::matDiag))
        diag(): Mat;
        // .function("isContinuous", select_overload<bool()const>(&cv::Mat::isContinuous))
        isContinuous(): boolean;
        // .function("setTo", select_overload<void(Mat&, const Scalar&)>(&binding_utils::matSetTo))
        setTo(scalar: ScalarLike): void;
        // .function("setTo", select_overload<void(Mat&, const Scalar&, const Mat&)>(&binding_utils::matSetTo))
        setTo(scalar: ScalarLike, mask: Mat): void;
        // .function("size", select_overload<Size(const Mat&)>(&binding_utils::matSize))
        size(): SizeLike;

        // .function("ptr", select_overload<val(const Mat&, int)>(&binding_utils::matPtr<unsigned char>))
        ptr(row: int): Uint8Array;
        ptr(row: int, col: int): Uint8Array;
        ucharPtr(row: int): Uint8Array;
        ucharPtr(row: int, col: int): Uint8Array;
        charPtr(row: int): Int8Array;
        charPtr(row: int, col: int): Int8Array;
        shortPtr(row: int): Int16Array;
        shortPtr(row: int, col: int): Int16Array;
        ushortPtr(row: int): Uint16Array;
        ushortPtr(row: int, col: int): Uint16Array;
        intPtr(row: int): Int32Array;
        intPtr(row: int, col: int): Int32Array;
        floatPtr(row: int): Float32Array;
        floatPtr(row: int, col: int): Float32Array;
        doublePtr(row: int): Float64Array;
        doublePtr(row: int, col: int): Float64Array;

        // .function("charAt", select_overload<char&(int)>(&cv::Mat::at<char>))
        charAt(row: int): number;
        charAt(row: int, col: int): number;
        charAt(i0: int, i1: int, i2: int): number;
        ucharAt(row: int): number;
        ucharAt(row: int, col: int): number;
        ucharAt(i0: int, i1: int, i2: int): number;
        shortAt(row: int): number;
        shortAt(row: int, col: int): number;
        shortAt(i0: int, i1: int, i2: int): number;
        ushortAt(row: int): number;
        ushortAt(row: int, col: int): number;
        ushortAt(i0: int, i1: int, i2: int): number;
        intAt(row: int): number;
        intAt(row: int, col: int): number;
        intAt(i0: int, i1: int, i2: int): number;
        floatAt(row: int): number;
        floatAt(row: int, col: int): number;
        floatAt(i0: int, i1: int, i2: int): number;
        doubleAt(row: int): number;
        doubleAt(row: int, col: int): number;
        doubleAt(i0: int, i1: int, i2: int): number;
    }
}
