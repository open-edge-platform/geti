// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0

/* eslint-disable max-len */

declare module 'functions' {
    import { DrawMatchesFlags } from 'enums';
    import { Mat } from 'mat';
    import { int, float, double } from 'scalars';
    import {
        SizeLike,
        PointLike,
        Point2fLike,
        RectLike,
        TermCriteriaLike,
        ScalarLike,
        RotatedRectLike,
        MomentsLike,
    } from 'valueObjects';
    import {
        IntVector,
        FloatVector,
        PointVector,
        MatVector,
        RectVector,
        KeyPointVector,
        DMatchVector,
        DMatchVectorVector,
    } from 'vectors';

    /**
     * @brief Finds edges in an image using the Canny algorithm @cite Canny86 .
     *
     * The function finds edges in the input image and marks them in the output map edges using the
     * Canny algorithm. The smallest value between threshold1 and threshold2 is used for edge linking. The
     * largest value is used to find initial segments of strong edges. See
     * <http://en.wikipedia.org/wiki/Canny_edge_detector>
     *
     * @param image 8-bit input image.
     * @param edges output edge map; single channels 8-bit image, which has the same size as image .
     * @param threshold1 first threshold for the hysteresis procedure.
     * @param threshold2 second threshold for the hysteresis procedure.
     * @param apertureSize aperture size for the Sobel operator.
     * @param L2gradient a flag, indicating whether a more accurate \f$L_2\f$ norm
     * \f$=\sqrt{(dI/dx)^2 + (dI/dy)^2}\f$ should be used to calculate the image gradient magnitude (
     * L2gradient=true ), or whether the default \f$L_1\f$ norm \f$=|dI/dx|+|dI/dy|\f$ is enough (
     * L2gradient=false ).
     */
    function Canny(
        image: Mat,
        edges: Mat,
        threshold1: double,
        threshold2: double,
        apertureSize?: int,
        L2gradient?: boolean
    ): void;

    /**
     * \overload
     *
     * Finds edges in an image using the Canny algorithm with custom image gradient.
     *
     * @param dx 16-bit x derivative of input image (CV_16SC1 or CV_16SC3).
     * @param dy 16-bit y derivative of input image (same type as dx).
     * @param edges output edge map; single channels 8-bit image, which has the same size as image .
     * @param threshold1 first threshold for the hysteresis procedure.
     * @param threshold2 second threshold for the hysteresis procedure.
     * @param L2gradient a flag, indicating whether a more accurate \f$L_2\f$ norm
     * \f$=\sqrt{(dI/dx)^2 + (dI/dy)^2}\f$ should be used to calculate the image gradient magnitude (
     * L2gradient=true ), or whether the default \f$L_1\f$ norm \f$=|dI/dx|+|dI/dy|\f$ is enough (
     * L2gradient=false ).
     */
    function Canny(dx: Mat, dy: Mat, edges: Mat, threshold1: double, threshold2: double, L2gradient?: boolean): void;

    /**
     * @brief Blurs an image using a Gaussian filter.
     *
     * The function convolves the source image with the specified Gaussian kernel. In-place filtering is
     * supported.
     *
     * @param src input image; the image can have any number of channels, which are processed
     * independently, but the depth should be CV_8U, CV_16U, CV_16S, CV_32F or CV_64F.
     * @param dst output image of the same size and type as src.
     * @param ksize Gaussian kernel size. ksize.width and ksize.height can differ but they both must be
     * positive and odd. Or, they can be zero's and then they are computed from sigma.
     * @param sigmaX Gaussian kernel standard deviation in X direction.
     * @param sigmaY Gaussian kernel standard deviation in Y direction; if sigmaY is zero, it is set to be
     * equal to sigmaX, if both sigmas are zeros, they are computed from ksize.width and ksize.height,
     * respectively (see #getGaussianKernel for details); to fully control the result regardless of
     * possible future modifications of all this semantics, it is recommended to specify all of ksize,
     * sigmaX, and sigmaY.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     *
     * @sa  sepFilter2D, filter2D, blur, boxFilter, bilateralFilter, medianBlur
     */
    function GaussianBlur(src: Mat, dst: Mat, ksize: SizeLike, sigmaX: double, sigmaY?: double, borderType?: int): void;

    /**
     * @brief Finds circles in a grayscale image using the Hough transform.
     *
     * The function finds circles in a grayscale image using a modification of the Hough transform.
     *
     * Example: :
     * @include snippets/imgproc_HoughLinesCircles.cpp
     *
     * @note Usually the function detects the centers of circles well. However, it may fail to find correct
     * radii. You can assist to the function by specifying the radius range ( minRadius and maxRadius ) if
     * you know it. Or, in the case of #HOUGH_GRADIENT method you may set maxRadius to a negative number
     * to return centers only without radius search, and find the correct radius using an additional procedure.
     *
     * It also helps to smooth image a bit unless it's already soft. For example,
     * GaussianBlur() with 7x7 kernel and 1.5x1.5 sigma or similar blurring may help.
     *
     * @param image 8-bit, single-channel, grayscale input image.
     * @param circles Output vector of found circles. Each vector is encoded as  3 or 4 element
     * floating-point vector \f$(x, y, radius)\f$ or \f$(x, y, radius, votes)\f$ .
     * @param method Detection method, see #HoughModes. The available methods are #HOUGH_GRADIENT and #HOUGH_GRADIENT_ALT.
     * @param dp Inverse ratio of the accumulator resolution to the image resolution. For example, if
     * dp=1 , the accumulator has the same resolution as the input image. If dp=2 , the accumulator has
     * half as big width and height. For #HOUGH_GRADIENT_ALT the recommended value is dp=1.5,
     * unless some small very circles need to be detected.
     * @param minDist Minimum distance between the centers of the detected circles. If the parameter is
     * too small, multiple neighbor circles may be falsely detected in addition to a true one. If it is
     * too large, some circles may be missed.
     * @param param1 First method-specific parameter. In case of #HOUGH_GRADIENT and #HOUGH_GRADIENT_ALT,
     * it is the higher threshold of the two passed to the Canny edge detector (the lower one is twice smaller).
     * Note that #HOUGH_GRADIENT_ALT uses #Scharr algorithm to compute image derivatives, so the threshold value
     * shough normally be higher, such as 300 or normally exposed and contrasty images.
     * @param param2 Second method-specific parameter. In case of #HOUGH_GRADIENT, it is the
     * accumulator threshold for the circle centers at the detection stage. The smaller it is, the more
     * false circles may be detected. Circles, corresponding to the larger accumulator values, will be
     * returned first. In the case of #HOUGH_GRADIENT_ALT algorithm, this is the circle "perfectness" measure.
     * The closer it to 1, the better shaped circles algorithm selects. In most cases 0.9 should be fine.
     * If you want get better detection of small circles, you may decrease it to 0.85, 0.8 or even less.
     * But then also try to limit the search range [minRadius, maxRadius] to avoid many false circles.
     * @param minRadius Minimum circle radius.
     * @param maxRadius Maximum circle radius. If <= 0, uses the maximum image dimension. If < 0, #HOUGH_GRADIENT returns
     * centers without finding the radius. #HOUGH_GRADIENT_ALT always computes circle radiuses.
     *
     * @sa fitEllipse, minEnclosingCircle
     */
    function HoughCircles(
        image: Mat,
        circles: Mat,
        method: int,
        dp: double,
        minDist: double,
        param1?: double,
        param2?: double,
        minRadius?: int,
        maxRadius?: int
    ): void;

    /**
     * @brief Finds lines in a binary image using the standard Hough transform.
     *
     * The function implements the standard or standard multi-scale Hough transform algorithm for line
     * detection. See <http://homepages.inf.ed.ac.uk/rbf/HIPR2/hough.htm> for a good explanation of Hough
     * transform.
     *
     * @param image 8-bit, single-channel binary source image. The image may be modified by the function.
     * @param lines Output vector of lines. Each line is represented by a 2 or 3 element vector
     * \f$(\rho, \theta)\f$ or \f$(\rho, \theta, \textrm{votes})\f$ . \f$\rho\f$ is the distance from the coordinate origin \f$(0,0)\f$ (top-left corner of
     * the image). \f$\theta\f$ is the line rotation angle in radians (
     * \f$0 \sim \textrm{vertical line}, \pi/2 \sim \textrm{horizontal line}\f$ ).
     * \f$\textrm{votes}\f$ is the value of accumulator.
     * @param rho Distance resolution of the accumulator in pixels.
     * @param theta Angle resolution of the accumulator in radians.
     * @param threshold Accumulator threshold parameter. Only those lines are returned that get enough
     * votes ( \f$>\texttt{threshold}\f$ ).
     * @param srn For the multi-scale Hough transform, it is a divisor for the distance resolution rho .
     * The coarse accumulator distance resolution is rho and the accurate accumulator resolution is
     * rho/srn . If both srn=0 and stn=0 , the classical Hough transform is used. Otherwise, both these
     * parameters should be positive.
     * @param stn For the multi-scale Hough transform, it is a divisor for the distance resolution theta.
     * @param min_theta For standard and multi-scale Hough transform, minimum angle to check for lines.
     * Must fall between 0 and max_theta.
     * @param max_theta For standard and multi-scale Hough transform, maximum angle to check for lines.
     * Must fall between min_theta and CV_PI.
     */
    function HoughLines(
        image: Mat,
        lines: Mat,
        rho: double,
        theta: double,
        threshold: int,
        srn?: double,
        stn?: double,
        min_theta?: double,
        max_theta?: double
    ): void;

    /**
     * @brief Finds line segments in a binary image using the probabilistic Hough transform.
     *
     * The function implements the probabilistic Hough transform algorithm for line detection, described
     * in @cite Matas00
     *
     * See the line detection example below:
     * @include snippets/imgproc_HoughLinesP.cpp
     * This is a sample picture the function parameters have been tuned for:
     *
     * ![image](pics/building.jpg)
     *
     * And this is the output of the above program in case of the probabilistic Hough transform:
     *
     * ![image](pics/houghp.png)
     *
     * @param image 8-bit, single-channel binary source image. The image may be modified by the function.
     * @param lines Output vector of lines. Each line is represented by a 4-element vector
     * \f$(x_1, y_1, x_2, y_2)\f$ , where \f$(x_1,y_1)\f$ and \f$(x_2, y_2)\f$ are the ending points of each detected
     * line segment.
     * @param rho Distance resolution of the accumulator in pixels.
     * @param theta Angle resolution of the accumulator in radians.
     * @param threshold Accumulator threshold parameter. Only those lines are returned that get enough
     * votes ( \f$>\texttt{threshold}\f$ ).
     * @param minLineLength Minimum line length. Line segments shorter than that are rejected.
     * @param maxLineGap Maximum allowed gap between points on the same line to link them.
     *
     * @sa LineSegmentDetector
     */
    function HoughLinesP(
        image: Mat,
        lines: Mat,
        rho: double,
        theta: double,
        threshold: int,
        minLineLength?: double,
        maxLineGap?: double
    ): void;

    /**
     * @brief Calculates the Laplacian of an image.
     *
     * The function calculates the Laplacian of the source image by adding up the second x and y
     * derivatives calculated using the Sobel operator:
     *
     * \f[\texttt{dst} =  \Delta \texttt{src} =  \frac{\partial^2 \texttt{src}}{\partial x^2} +  \frac{\partial^2 \texttt{src}}{\partial y^2}\f]
     *
     * This is done when `ksize > 1`. When `ksize == 1`, the Laplacian is computed by filtering the image
     * with the following \f$3 \times 3\f$ aperture:
     *
     * \f[\vecthreethree {0}{1}{0}{1}{-4}{1}{0}{1}{0}\f]
     *
     * @param src Source image.
     * @param dst Destination image of the same size and the same number of channels as src .
     * @param ddepth Desired depth of the destination image.
     * @param ksize Aperture size used to compute the second-derivative filters. See #getDerivKernels for
     * details. The size must be positive and odd.
     * @param scale Optional scale factor for the computed Laplacian values. By default, no scaling is
     * applied. See #getDerivKernels for details.
     * @param delta Optional delta value that is added to the results prior to storing them in dst .
     * @param borderType Pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  Sobel, Scharr
     */
    function Laplacian(
        src: Mat,
        dst: Mat,
        ddepth: int,
        ksize?: int,
        scale?: double,
        delta?: double,
        borderType?: int
    ): void;

    /**
     * @brief Converts a rotation matrix to a rotation vector or vice versa.
     *
     * @param src Input rotation vector (3x1 or 1x3) or rotation matrix (3x3).
     * @param dst Output rotation matrix (3x3) or rotation vector (3x1 or 1x3), respectively.
     * @param jacobian Optional output Jacobian matrix, 3x9 or 9x3, which is a matrix of partial
     * derivatives of the output array components with respect to the input array components.
     *
     * \f[\begin{array}{l} \theta \leftarrow norm(r) \\ r  \leftarrow r/ \theta \\ R =  \cos(\theta) I + (1- \cos{\theta} ) r r^T +  \sin(\theta) \vecthreethree{0}{-r_z}{r_y}{r_z}{0}{-r_x}{-r_y}{r_x}{0} \end{array}\f]
     *
     * Inverse transformation can be also done easily, since
     *
     * \f[\sin ( \theta ) \vecthreethree{0}{-r_z}{r_y}{r_z}{0}{-r_x}{-r_y}{r_x}{0} = \frac{R - R^T}{2}\f]
     *
     * A rotation vector is a convenient and most compact representation of a rotation matrix (since any
     * rotation matrix has just 3 degrees of freedom). The representation is used in the global 3D geometry
     * optimization procedures like @ref calibrateCamera, @ref stereoCalibrate, or @ref solvePnP .
     *
     * @note More information about the computation of the derivative of a 3D rotation matrix with respect to its exponential coordinate
     * can be found in:
     * - A Compact Formula for the Derivative of a 3-D Rotation in Exponential Coordinates, Guillermo Gallego, Anthony J. Yezzi @cite Gallego2014ACF
     *
     * @note Useful information on SE(3) and Lie Groups can be found in:
     * - A tutorial on SE(3) transformation parameterizations and on-manifold optimization, Jose-Luis Blanco @cite blanco2010tutorial
     * - Lie Groups for 2D and 3D Transformation, Ethan Eade @cite Eade17
     * - A micro Lie theory for state estimation in robotics, Joan Solà, Jérémie Deray, Dinesh Atchuthan @cite Sol2018AML
     */
    function Rodrigues(src: Mat, dst: Mat, jacobian?: Mat): void;

    /**
     * @brief Calculates the first x- or y- image derivative using Scharr operator.
     *
     * The function computes the first x- or y- spatial image derivative using the Scharr operator. The
     * call
     *
     * \f[\texttt{Scharr(src, dst, ddepth, dx, dy, scale, delta, borderType)}\f]
     *
     * is equivalent to
     *
     * \f[\texttt{Sobel(src, dst, ddepth, dx, dy, FILTER_SCHARR, scale, delta, borderType)} .\f]
     *
     * @param src input image.
     * @param dst output image of the same size and the same number of channels as src.
     * @param ddepth output image depth, see @ref filter_depths "combinations"
     * @param dx order of the derivative x.
     * @param dy order of the derivative y.
     * @param scale optional scale factor for the computed derivative values; by default, no scaling is
     * applied (see #getDerivKernels for details).
     * @param delta optional delta value that is added to the results prior to storing them in dst.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  cartToPolar
     */
    function Scharr(
        src: Mat,
        dst: Mat,
        ddepth: int,
        dx: int,
        dy: int,
        scale?: double,
        delta?: double,
        borderType?: int
    ): void;

    /**
     * @brief Calculates the first, second, third, or mixed image derivatives using an extended Sobel operator.
     *
     * In all cases except one, the \f$\texttt{ksize} \times \texttt{ksize}\f$ separable kernel is used to
     * calculate the derivative. When \f$\texttt{ksize = 1}\f$, the \f$3 \times 1\f$ or \f$1 \times 3\f$
     * kernel is used (that is, no Gaussian smoothing is done). `ksize = 1` can only be used for the first
     * or the second x- or y- derivatives.
     *
     * There is also the special value `ksize = #FILTER_SCHARR (-1)` that corresponds to the \f$3\times3\f$ Scharr
     * filter that may give more accurate results than the \f$3\times3\f$ Sobel. The Scharr aperture is
     *
     * \f[\vecthreethree{-3}{0}{3}{-10}{0}{10}{-3}{0}{3}\f]
     *
     * for the x-derivative, or transposed for the y-derivative.
     *
     * The function calculates an image derivative by convolving the image with the appropriate kernel:
     *
     * \f[\texttt{dst} =  \frac{\partial^{xorder+yorder} \texttt{src}}{\partial x^{xorder} \partial y^{yorder}}\f]
     *
     * The Sobel operators combine Gaussian smoothing and differentiation, so the result is more or less
     * resistant to the noise. Most often, the function is called with ( xorder = 1, yorder = 0, ksize = 3)
     * or ( xorder = 0, yorder = 1, ksize = 3) to calculate the first x- or y- image derivative. The first
     * case corresponds to a kernel of:
     *
     * \f[\vecthreethree{-1}{0}{1}{-2}{0}{2}{-1}{0}{1}\f]
     *
     * The second case corresponds to a kernel of:
     *
     * \f[\vecthreethree{-1}{-2}{-1}{0}{0}{0}{1}{2}{1}\f]
     *
     * @param src input image.
     * @param dst output image of the same size and the same number of channels as src .
     * @param ddepth output image depth, see @ref filter_depths "combinations"; in the case of
     * 8-bit input images it will result in truncated derivatives.
     * @param dx order of the derivative x.
     * @param dy order of the derivative y.
     * @param ksize size of the extended Sobel kernel; it must be 1, 3, 5, or 7.
     * @param scale optional scale factor for the computed derivative values; by default, no scaling is
     * applied (see #getDerivKernels for details).
     * @param delta optional delta value that is added to the results prior to storing them in dst.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  Scharr, Laplacian, sepFilter2D, filter2D, GaussianBlur, cartToPolar
     */
    function Sobel(
        src: Mat,
        dst: Mat,
        ddepth: int,
        dx: int,
        dy: int,
        ksize?: int,
        scale?: double,
        delta?: double,
        borderType?: int
    ): void;

    /**
     * @brief Calculates the per-element absolute difference between two arrays or between an array and a scalar.
     *
     * The function cv::absdiff calculates:
     * Absolute difference between two arrays when they have the same
     * size and type:
     * \f[\texttt{dst}(I) =  \texttt{saturate} (| \texttt{src1}(I) -  \texttt{src2}(I)|)\f]
     * Absolute difference between an array and a scalar when the second
     * array is constructed from Scalar or has as many elements as the
     * number of channels in `src1`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} (| \texttt{src1}(I) -  \texttt{src2} |)\f]
     * Absolute difference between a scalar and an array when the first
     * array is constructed from Scalar or has as many elements as the
     * number of channels in `src2`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} (| \texttt{src1} -  \texttt{src2}(I) |)\f]
     * where I is a multi-dimensional index of array elements. In case of
     * multi-channel arrays, each channel is processed independently.
     * @note Saturation is not applied when the arrays have the depth CV_32S.
     * You may even get a negative value in the case of overflow.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array that has the same size and type as input arrays.
     * @sa cv::abs(const Mat&)
     */
    function absdiff(src1: Mat, src2: Mat, dst: Mat): void;

    /**
     * @brief Applies an adaptive threshold to an array.
     *
     * The function transforms a grayscale image to a binary image according to the formulae:
     * -   **THRESH_BINARY**
     * \f[dst(x,y) =  \fork{\texttt{maxValue}}{if \(src(x,y) > T(x,y)\)}{0}{otherwise}\f]
     * -   **THRESH_BINARY_INV**
     * \f[dst(x,y) =  \fork{0}{if \(src(x,y) > T(x,y)\)}{\texttt{maxValue}}{otherwise}\f]
     * where \f$T(x,y)\f$ is a threshold calculated individually for each pixel (see adaptiveMethod parameter).
     *
     * The function can process the image in-place.
     *
     * @param src Source 8-bit single-channel image.
     * @param dst Destination image of the same size and the same type as src.
     * @param maxValue Non-zero value assigned to the pixels for which the condition is satisfied
     * @param adaptiveMethod Adaptive thresholding algorithm to use, see #AdaptiveThresholdTypes.
     * The #BORDER_REPLICATE | #BORDER_ISOLATED is used to process boundaries.
     * @param thresholdType Thresholding type that must be either #THRESH_BINARY or #THRESH_BINARY_INV,
     * see #ThresholdTypes.
     * @param blockSize Size of a pixel neighborhood that is used to calculate a threshold value for the
     * pixel: 3, 5, 7, and so on.
     * @param C Constant subtracted from the mean or weighted mean (see the details below). Normally, it
     * is positive but may be zero or negative as well.
     *
     * @sa  threshold, blur, GaussianBlur
     */
    function adaptiveThreshold(
        src: Mat,
        dst: Mat,
        maxValue: double,
        adaptiveMethod: int,
        thresholdType: int,
        blockSize: int,
        C: double
    ): void;

    /**
     * @brief Calculates the per-element sum of two arrays or an array and a scalar.
     *
     * The function add calculates:
     * - Sum of two arrays when both input arrays have the same size and the same number of channels:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1}(I) +  \texttt{src2}(I)) \quad \texttt{if mask}(I) \ne0\f]
     * - Sum of an array and a scalar when src2 is constructed from Scalar or has the same number of
     * elements as `src1.channels()`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1}(I) +  \texttt{src2} ) \quad \texttt{if mask}(I) \ne0\f]
     * - Sum of a scalar and an array when src1 is constructed from Scalar or has the same number of
     * elements as `src2.channels()`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1} +  \texttt{src2}(I) ) \quad \texttt{if mask}(I) \ne0\f]
     * where `I` is a multi-dimensional index of array elements. In case of multi-channel arrays, each
     * channel is processed independently.
     *
     * The first function in the list above can be replaced with matrix expressions:
     * @code{.cpp}
     * dst = src1 + src2;
     * dst += src1; // equivalent to add(dst, src1, dst);
     * @endcode
     * The input arrays and the output array can all have the same or different depths. For example, you
     * can add a 16-bit unsigned array to a 8-bit signed array and store the sum as a 32-bit
     * floating-point array. Depth of the output array is determined by the dtype parameter. In the second
     * and third cases above, as well as in the first case, when src1.depth() == src2.depth(), dtype can
     * be set to the default -1. In this case, the output array will have the same depth as the input
     * array, be it src1, src2 or both.
     * @note Saturation is not applied when the output array has the depth CV_32S. You may even get
     * result of an incorrect sign in the case of overflow.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array that has the same size and number of channels as the input array(s); the
     * depth is defined by dtype or src1/src2.
     * @param mask optional operation mask - 8-bit single channel array, that specifies elements of the
     * output array to be changed.
     * @param dtype optional depth of the output array (see the discussion below).
     * @sa subtract, addWeighted, scaleAdd, Mat::convertTo
     */
    function add(src1: Mat, src2: Mat, dst: Mat, mask?: Mat, dtype?: int): void;

    /**
     * @brief Calculates the weighted sum of two arrays.
     *
     * The function addWeighted calculates the weighted sum of two arrays as follows:
     * \f[\texttt{dst} (I)= \texttt{saturate} ( \texttt{src1} (I)* \texttt{alpha} +  \texttt{src2} (I)* \texttt{beta} +  \texttt{gamma} )\f]
     * where I is a multi-dimensional index of array elements. In case of multi-channel arrays, each
     * channel is processed independently.
     * The function can be replaced with a matrix expression:
     * @code{.cpp}
     * dst = src1*alpha + src2*beta + gamma;
     * @endcode
     * @note Saturation is not applied when the output array has the depth CV_32S. You may even get
     * result of an incorrect sign in the case of overflow.
     * @param src1 first input array.
     * @param alpha weight of the first array elements.
     * @param src2 second input array of the same size and channel number as src1.
     * @param beta weight of the second array elements.
     * @param gamma scalar added to each sum.
     * @param dst output array that has the same size and number of channels as the input arrays.
     * @param dtype optional depth of the output array; when both input arrays have the same depth, dtype
     * can be set to -1, which will be equivalent to src1.depth().
     * @sa  add, subtract, scaleAdd, Mat::convertTo
     */
    function addWeighted(src1: Mat, alpha: double, src2: Mat, beta: double, gamma: double, dst: Mat, dtype?: int): void;

    /**
     * @brief Approximates a polygonal curve(s) with the specified precision.
     *
     * The function cv::approxPolyDP approximates a curve or a polygon with another curve/polygon with less
     * vertices so that the distance between them is less or equal to the specified precision. It uses the
     * Douglas-Peucker algorithm <http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm>
     *
     * @param curve Input vector of a 2D point stored in std::vector or Mat
     * @param approxCurve Result of the approximation. The type should match the type of the input curve.
     * @param epsilon Parameter specifying the approximation accuracy. This is the maximum distance
     * between the original curve and its approximation.
     * @param closed If true, the approximated curve is closed (its first and last vertices are
     * connected). Otherwise, it is not closed.
     */
    function approxPolyDP(curve: Mat, approxCurve: Mat, epsilon: double, closed: boolean): void;

    /**
     * @brief Calculates a contour perimeter or a curve length.
     *
     * The function computes a curve length or a closed contour perimeter.
     *
     * @param curve Input vector of 2D points, stored in std::vector or Mat.
     * @param closed Flag indicating whether the curve is closed or not.
     */
    function arcLength(curve: Mat, closed: boolean): double;

    /**
     * @brief Applies the bilateral filter to an image.
     *
     * The function applies bilateral filtering to the input image, as described in
     * http://www.dai.ed.ac.uk/CVonline/LOCAL_COPIES/MANDUCHI1/Bilateral_Filtering.html
     * bilateralFilter can reduce unwanted noise very well while keeping edges fairly sharp. However, it is
     * very slow compared to most filters.
     *
     * _Sigma values_: For simplicity, you can set the 2 sigma values to be the same. If they are small (\<
     * 10), the filter will not have much effect, whereas if they are large (\> 150), they will have a very
     * strong effect, making the image look "cartoonish".
     *
     * _Filter size_: Large filters (d \> 5) are very slow, so it is recommended to use d=5 for real-time
     * applications, and perhaps d=9 for offline applications that need heavy noise filtering.
     *
     * This filter does not work inplace.
     * @param src Source 8-bit or floating-point, 1-channel or 3-channel image.
     * @param dst Destination image of the same size and type as src .
     * @param d Diameter of each pixel neighborhood that is used during filtering. If it is non-positive,
     * it is computed from sigmaSpace.
     * @param sigmaColor Filter sigma in the color space. A larger value of the parameter means that
     * farther colors within the pixel neighborhood (see sigmaSpace) will be mixed together, resulting
     * in larger areas of semi-equal color.
     * @param sigmaSpace Filter sigma in the coordinate space. A larger value of the parameter means that
     * farther pixels will influence each other as long as their colors are close enough (see sigmaColor
     * ). When d\>0, it specifies the neighborhood size regardless of sigmaSpace. Otherwise, d is
     * proportional to sigmaSpace.
     * @param borderType border mode used to extrapolate pixels outside of the image, see #BorderTypes
     */
    function bilateralFilter(
        src: Mat,
        dst: Mat,
        d: int,
        sigmaColor: double,
        sigmaSpace: double,
        borderType?: int
    ): void;

    /**
     * @brief computes bitwise conjunction of the two arrays (dst = src1 & src2)
     * Calculates the per-element bit-wise conjunction of two arrays or an
     * array and a scalar.
     *
     * The function cv::bitwise_and calculates the per-element bit-wise logical conjunction for:
     * Two arrays when src1 and src2 have the same size:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \wedge \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * An array and a scalar when src2 is constructed from Scalar or has
     * the same number of elements as `src1.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \wedge \texttt{src2} \quad \texttt{if mask} (I) \ne0\f]
     * A scalar and an array when src1 is constructed from Scalar or has
     * the same number of elements as `src2.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1}  \wedge \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * In case of floating-point arrays, their machine-specific bit
     * representations (usually IEEE754-compliant) are used for the operation.
     * In case of multi-channel arrays, each channel is processed
     * independently. In the second and third cases above, the scalar is first
     * converted to the array type.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array that has the same size and type as the input
     * arrays.
     * @param mask optional operation mask, 8-bit single channel array, that
     * specifies elements of the output array to be changed.
     */
    function bitwise_and(src1: Mat, src2: Mat, dst: Mat, mask?: Mat): void;

    /**
     * @brief  Inverts every bit of an array.
     *
     * The function cv::bitwise_not calculates per-element bit-wise inversion of the input
     * array:
     * \f[\texttt{dst} (I) =  \neg \texttt{src} (I)\f]
     * In case of a floating-point input array, its machine-specific bit
     * representation (usually IEEE754-compliant) is used for the operation. In
     * case of multi-channel arrays, each channel is processed independently.
     * @param src input array.
     * @param dst output array that has the same size and type as the input
     * array.
     * @param mask optional operation mask, 8-bit single channel array, that
     * specifies elements of the output array to be changed.
     */
    function bitwise_not(src: Mat, dst: Mat, mask?: Mat): void;

    /**
     * @brief Calculates the per-element bit-wise disjunction of two arrays or an
     * array and a scalar.
     *
     * The function cv::bitwise_or calculates the per-element bit-wise logical disjunction for:
     * Two arrays when src1 and src2 have the same size:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \vee \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * An array and a scalar when src2 is constructed from Scalar or has
     * the same number of elements as `src1.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \vee \texttt{src2} \quad \texttt{if mask} (I) \ne0\f]
     * A scalar and an array when src1 is constructed from Scalar or has
     * the same number of elements as `src2.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1}  \vee \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * In case of floating-point arrays, their machine-specific bit
     * representations (usually IEEE754-compliant) are used for the operation.
     * In case of multi-channel arrays, each channel is processed
     * independently. In the second and third cases above, the scalar is first
     * converted to the array type.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array that has the same size and type as the input
     * arrays.
     * @param mask optional operation mask, 8-bit single channel array, that
     * specifies elements of the output array to be changed.
     */
    function bitwise_or(src1: Mat, src2: Mat, dst: Mat, mask?: Mat): void;

    /**
     * @brief Calculates the per-element bit-wise "exclusive or" operation on two
     * arrays or an array and a scalar.
     *
     * The function cv::bitwise_xor calculates the per-element bit-wise logical "exclusive-or"
     * operation for:
     * Two arrays when src1 and src2 have the same size:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \oplus \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * An array and a scalar when src2 is constructed from Scalar or has
     * the same number of elements as `src1.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \oplus \texttt{src2} \quad \texttt{if mask} (I) \ne0\f]
     * A scalar and an array when src1 is constructed from Scalar or has
     * the same number of elements as `src2.channels()`:
     * \f[\texttt{dst} (I) =  \texttt{src1}  \oplus \texttt{src2} (I) \quad \texttt{if mask} (I) \ne0\f]
     * In case of floating-point arrays, their machine-specific bit
     * representations (usually IEEE754-compliant) are used for the operation.
     * In case of multi-channel arrays, each channel is processed
     * independently. In the 2nd and 3rd cases above, the scalar is first
     * converted to the array type.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array that has the same size and type as the input
     * arrays.
     * @param mask optional operation mask, 8-bit single channel array, that
     * specifies elements of the output array to be changed.
     */
    function bitwise_xor(src1: Mat, src2: Mat, dst: Mat, mask?: Mat): void;

    /**
     * @brief Blurs an image using the normalized box filter.
     *
     * The function smooths an image using the kernel:
     *
     * \f[\texttt{K} =  \frac{1}{\texttt{ksize.width*ksize.height}} \begin{bmatrix} 1 & 1 & 1 &  \cdots & 1 & 1  \\ 1 & 1 & 1 &  \cdots & 1 & 1  \\ \hdotsfor{6} \\ 1 & 1 & 1 &  \cdots & 1 & 1  \\ \end{bmatrix}\f]
     *
     * The call `blur(src, dst, ksize, anchor, borderType)` is equivalent to `boxFilter(src, dst, src.type(), ksize,
     * anchor, true, borderType)`.
     *
     * @param src input image; it can have any number of channels, which are processed independently, but
     * the depth should be CV_8U, CV_16U, CV_16S, CV_32F or CV_64F.
     * @param dst output image of the same size and type as src.
     * @param ksize blurring kernel size.
     * @param anchor anchor point; default value Point(-1,-1) means that the anchor is at the kernel
     * center.
     * @param borderType border mode used to extrapolate pixels outside of the image, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  boxFilter, bilateralFilter, GaussianBlur, medianBlur
     */
    function blur(src: Mat, dst: Mat, ksize: SizeLike, anchor?: PointLike, borderType?: int): void;

    /**
     * @brief Calculates the up-right bounding rectangle of a point set or non-zero pixels of gray-scale image.
     *
     * The function calculates and returns the minimal up-right bounding rectangle for the specified point set or
     * non-zero pixels of gray-scale image.
     *
     * @param array Input gray-scale image or 2D point set, stored in std::vector or Mat.
     */
    function boundingRect(array: Mat): RectLike;

    /**
     * @brief Blurs an image using the box filter.
     *
     * The function smooths an image using the kernel:
     *
     * \f[\texttt{K} =  \alpha \begin{bmatrix} 1 & 1 & 1 &  \cdots & 1 & 1  \\ 1 & 1 & 1 &  \cdots & 1 & 1  \\ \hdotsfor{6} \\ 1 & 1 & 1 &  \cdots & 1 & 1 \end{bmatrix}\f]
     *
     * where
     *
     * \f[\alpha = \begin{cases} \frac{1}{\texttt{ksize.width*ksize.height}} & \texttt{when } \texttt{normalize=true}  \\1 & \texttt{otherwise}\end{cases}\f]
     *
     * Unnormalized box filter is useful for computing various integral characteristics over each pixel
     * neighborhood, such as covariance matrices of image derivatives (used in dense optical flow
     * algorithms, and so on). If you need to compute pixel sums over variable-size windows, use #integral.
     *
     * @param src input image.
     * @param dst output image of the same size and type as src.
     * @param ddepth the output image depth (-1 to use src.depth()).
     * @param ksize blurring kernel size.
     * @param anchor anchor point; default value Point(-1,-1) means that the anchor is at the kernel
     * center.
     * @param normalize flag, specifying whether the kernel is normalized by its area or not.
     * @param borderType border mode used to extrapolate pixels outside of the image, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  blur, bilateralFilter, GaussianBlur, medianBlur, integral
     */
    function boxFilter(
        src: Mat,
        dst: Mat,
        ddepth: int,
        ksize: SizeLike,
        anchor?: PointLike,
        normalize?: boolean,
        borderType?: int
    ): void;

    /**
     * @overload
     */
    function calcBackProject(
        images: MatVector,
        channels: IntVector | int[],
        hist: Mat,
        dst: Mat,
        ranges: FloatVector | float[],
        scale: double
    ): void;

    /**
     * @overload
     */
    function calcHist(
        images: MatVector,
        channels: IntVector | int[],
        mask: Mat,
        hist: Mat,
        histSize: IntVector | int[],
        ranges: FloatVector | float[],
        accumulate?: boolean
    ): void;

    /**
     * @brief Computes a dense optical flow using the Gunnar Farneback's algorithm.
     *
     * @param prev first 8-bit single-channel input image.
     * @param next second input image of the same size and the same type as prev.
     * @param flow computed flow image that has the same size as prev and type CV_32FC2.
     * @param pyr_scale parameter, specifying the image scale (\<1) to build pyramids for each image;
     * pyr_scale=0.5 means a classical pyramid, where each next layer is twice smaller than the previous
     * one.
     * @param levels number of pyramid layers including the initial image; levels=1 means that no extra
     * layers are created and only the original images are used.
     * @param winsize averaging window size; larger values increase the algorithm robustness to image
     * noise and give more chances for fast motion detection, but yield more blurred motion field.
     * @param iterations number of iterations the algorithm does at each pyramid level.
     * @param poly_n size of the pixel neighborhood used to find polynomial expansion in each pixel;
     * larger values mean that the image will be approximated with smoother surfaces, yielding more
     * robust algorithm and more blurred motion field, typically poly_n =5 or 7.
     * @param poly_sigma standard deviation of the Gaussian that is used to smooth derivatives used as a
     * basis for the polynomial expansion; for poly_n=5, you can set poly_sigma=1.1, for poly_n=7, a
     * good value would be poly_sigma=1.5.
     * @param flags operation flags that can be a combination of the following:
     * -   **OPTFLOW_USE_INITIAL_FLOW** uses the input flow as an initial flow approximation.
     * -   **OPTFLOW_FARNEBACK_GAUSSIAN** uses the Gaussian \f$\texttt{winsize}\times\texttt{winsize}\f$
     * filter instead of a box filter of the same size for optical flow estimation; usually, this
     * option gives z more accurate flow than with a box filter, at the cost of lower speed;
     * normally, winsize for a Gaussian window should be set to a larger value to achieve the same
     * level of robustness.
     *
     * The function finds an optical flow for each prev pixel using the @cite Farneback2003 algorithm so that
     *
     * \f[\texttt{prev} (y,x)  \sim \texttt{next} ( y + \texttt{flow} (y,x)[1],  x + \texttt{flow} (y,x)[0])\f]
     *
     * @note
     *
     * -   An example using the optical flow algorithm described by Gunnar Farneback can be found at
     * opencv_source_code/samples/cpp/fback.cpp
     * -   (Python) An example using the optical flow algorithm described by Gunnar Farneback can be
     * found at opencv_source_code/samples/python/opt_flow.py
     */
    function calcOpticalFlowFarneback(
        prev: Mat,
        next: Mat,
        flow: Mat,
        pyr_scale: double,
        levels: int,
        winsize: int,
        iterations: int,
        poly_n: int,
        poly_sigma: double,
        flags: int
    ): void;

    /**
     * @brief Calculates an optical flow for a sparse feature set using the iterative Lucas-Kanade method with
     * pyramids.
     *
     * @param prevImg first 8-bit input image or pyramid constructed by buildOpticalFlowPyramid.
     * @param nextImg second input image or pyramid of the same size and the same type as prevImg.
     * @param prevPts vector of 2D points for which the flow needs to be found; point coordinates must be
     * single-precision floating-point numbers.
     * @param nextPts output vector of 2D points (with single-precision floating-point coordinates)
     * containing the calculated new positions of input features in the second image; when
     * OPTFLOW_USE_INITIAL_FLOW flag is passed, the vector must have the same size as in the input.
     * @param status output status vector (of unsigned chars); each element of the vector is set to 1 if
     * the flow for the corresponding features has been found, otherwise, it is set to 0.
     * @param err output vector of errors; each element of the vector is set to an error for the
     * corresponding feature, type of the error measure can be set in flags parameter; if the flow wasn't
     * found then the error is not defined (use the status parameter to find such cases).
     * @param winSize size of the search window at each pyramid level.
     * @param maxLevel 0-based maximal pyramid level number; if set to 0, pyramids are not used (single
     * level), if set to 1, two levels are used, and so on; if pyramids are passed to input then
     * algorithm will use as many levels as pyramids have but no more than maxLevel.
     * @param criteria parameter, specifying the termination criteria of the iterative search algorithm
     * (after the specified maximum number of iterations criteria.maxCount or when the search window
     * moves by less than criteria.epsilon.
     * @param flags operation flags:
     * -   **OPTFLOW_USE_INITIAL_FLOW** uses initial estimations, stored in nextPts; if the flag is
     * not set, then prevPts is copied to nextPts and is considered the initial estimate.
     * -   **OPTFLOW_LK_GET_MIN_EIGENVALS** use minimum eigen values as an error measure (see
     * minEigThreshold description); if the flag is not set, then L1 distance between patches
     * around the original and a moved point, divided by number of pixels in a window, is used as a
     * error measure.
     * @param minEigThreshold the algorithm calculates the minimum eigen value of a 2x2 normal matrix of
     * optical flow equations (this matrix is called a spatial gradient matrix in @cite Bouguet00), divided
     * by number of pixels in a window; if this value is less than minEigThreshold, then a corresponding
     * feature is filtered out and its flow is not processed, so it allows to remove bad points and get a
     * performance boost.
     *
     * The function implements a sparse iterative version of the Lucas-Kanade optical flow in pyramids. See
     * @cite Bouguet00 . The function is parallelized with the TBB library.
     *
     * @note
     *
     * -   An example using the Lucas-Kanade optical flow algorithm can be found at
     * opencv_source_code/samples/cpp/lkdemo.cpp
     * -   (Python) An example using the Lucas-Kanade optical flow algorithm can be found at
     * opencv_source_code/samples/python/lk_track.py
     * -   (Python) An example using the Lucas-Kanade tracker for homography matching can be found at
     * opencv_source_code/samples/python/lk_homography.py
     */
    function calcOpticalFlowPyrLK(
        prevImg: Mat,
        nextImg: Mat,
        prevPts: Mat,
        nextPts: Mat,
        status: Mat,
        err: Mat,
        winSize?: SizeLike,
        maxLevel?: int,
        criteria?: TermCriteriaLike,
        flags?: int,
        minEigThreshold?: double
    ): void;

    /**
     * @brief Finds the camera intrinsic and extrinsic parameters from several views of a calibration
     * pattern.
     *
     * @param objectPoints In the new interface it is a vector of vectors of calibration pattern points in
     * the calibration pattern coordinate space (e.g. std::vector<std::vector<cv::Vec3f>>). The outer
     * vector contains as many elements as the number of pattern views. If the same calibration pattern
     * is shown in each view and it is fully visible, all the vectors will be the same. Although, it is
     * possible to use partially occluded patterns or even different patterns in different views. Then,
     * the vectors will be different. Although the points are 3D, they all lie in the calibration pattern's
     * XY coordinate plane (thus 0 in the Z-coordinate), if the used calibration pattern is a planar rig.
     * In the old interface all the vectors of object points from different views are concatenated
     * together.
     * @param imagePoints In the new interface it is a vector of vectors of the projections of calibration
     * pattern points (e.g. std::vector<std::vector<cv::Vec2f>>). imagePoints.size() and
     * objectPoints.size(), and imagePoints[i].size() and objectPoints[i].size() for each i, must be equal,
     * respectively. In the old interface all the vectors of object points from different views are
     * concatenated together.
     * @param imageSize Size of the image used only to initialize the camera intrinsic matrix.
     * @param cameraMatrix Input/output 3x3 floating-point camera intrinsic matrix
     * \f$\cameramatrix{A}\f$ . If @ref CALIB_USE_INTRINSIC_GUESS
     * and/or @ref CALIB_FIX_ASPECT_RATIO are specified, some or all of fx, fy, cx, cy must be
     * initialized before calling the function.
     * @param distCoeffs Input/output vector of distortion coefficients
     * \f$\distcoeffs\f$.
     * @param rvecs Output vector of rotation vectors (@ref Rodrigues ) estimated for each pattern view
     * (e.g. std::vector<cv::Mat>>). That is, each i-th rotation vector together with the corresponding
     * i-th translation vector (see the next output parameter description) brings the calibration pattern
     * from the object coordinate space (in which object points are specified) to the camera coordinate
     * space. In more technical terms, the tuple of the i-th rotation and translation vector performs
     * a change of basis from object coordinate space to camera coordinate space. Due to its duality, this
     * tuple is equivalent to the position of the calibration pattern with respect to the camera coordinate
     * space.
     * @param tvecs Output vector of translation vectors estimated for each pattern view, see parameter
     * describtion above.
     * @param stdDeviationsIntrinsics Output vector of standard deviations estimated for intrinsic
     * parameters. Order of deviations values:
     * \f$(f_x, f_y, c_x, c_y, k_1, k_2, p_1, p_2, k_3, k_4, k_5, k_6 , s_1, s_2, s_3,
     * s_4, \tau_x, \tau_y)\f$ If one of parameters is not estimated, it's deviation is equals to zero.
     * @param stdDeviationsExtrinsics Output vector of standard deviations estimated for extrinsic
     * parameters. Order of deviations values: \f$(R_0, T_0, \dotsc , R_{M - 1}, T_{M - 1})\f$ where M is
     * the number of pattern views. \f$R_i, T_i\f$ are concatenated 1x3 vectors.
     * @param perViewErrors Output vector of the RMS re-projection error estimated for each pattern view.
     * @param flags Different flags that may be zero or a combination of the following values:
     * -   @ref CALIB_USE_INTRINSIC_GUESS cameraMatrix contains valid initial values of
     * fx, fy, cx, cy that are optimized further. Otherwise, (cx, cy) is initially set to the image
     * center ( imageSize is used), and focal distances are computed in a least-squares fashion.
     * Note, that if intrinsic parameters are known, there is no need to use this function just to
     * estimate extrinsic parameters. Use solvePnP instead.
     * -   @ref CALIB_FIX_PRINCIPAL_POINT The principal point is not changed during the global
     * optimization. It stays at the center or at a different location specified when
     * @ref CALIB_USE_INTRINSIC_GUESS is set too.
     * -   @ref CALIB_FIX_ASPECT_RATIO The functions consider only fy as a free parameter. The
     * ratio fx/fy stays the same as in the input cameraMatrix . When
     * @ref CALIB_USE_INTRINSIC_GUESS is not set, the actual input values of fx and fy are
     * ignored, only their ratio is computed and used further.
     * -   @ref CALIB_ZERO_TANGENT_DIST Tangential distortion coefficients \f$(p_1, p_2)\f$ are set
     * to zeros and stay zero.
     * -   @ref CALIB_FIX_K1,..., @ref CALIB_FIX_K6 The corresponding radial distortion
     * coefficient is not changed during the optimization. If @ref CALIB_USE_INTRINSIC_GUESS is
     * set, the coefficient from the supplied distCoeffs matrix is used. Otherwise, it is set to 0.
     * -   @ref CALIB_RATIONAL_MODEL Coefficients k4, k5, and k6 are enabled. To provide the
     * backward compatibility, this extra flag should be explicitly specified to make the
     * calibration function use the rational model and return 8 coefficients. If the flag is not
     * set, the function computes and returns only 5 distortion coefficients.
     * -   @ref CALIB_THIN_PRISM_MODEL Coefficients s1, s2, s3 and s4 are enabled. To provide the
     * backward compatibility, this extra flag should be explicitly specified to make the
     * calibration function use the thin prism model and return 12 coefficients. If the flag is not
     * set, the function computes and returns only 5 distortion coefficients.
     * -   @ref CALIB_FIX_S1_S2_S3_S4 The thin prism distortion coefficients are not changed during
     * the optimization. If @ref CALIB_USE_INTRINSIC_GUESS is set, the coefficient from the
     * supplied distCoeffs matrix is used. Otherwise, it is set to 0.
     * -   @ref CALIB_TILTED_MODEL Coefficients tauX and tauY are enabled. To provide the
     * backward compatibility, this extra flag should be explicitly specified to make the
     * calibration function use the tilted sensor model and return 14 coefficients. If the flag is not
     * set, the function computes and returns only 5 distortion coefficients.
     * -   @ref CALIB_FIX_TAUX_TAUY The coefficients of the tilted sensor model are not changed during
     * the optimization. If @ref CALIB_USE_INTRINSIC_GUESS is set, the coefficient from the
     * supplied distCoeffs matrix is used. Otherwise, it is set to 0.
     * @param criteria Termination criteria for the iterative optimization algorithm.
     *
     * @return the overall RMS re-projection error.
     *
     * The function estimates the intrinsic camera parameters and extrinsic parameters for each of the
     * views. The algorithm is based on @cite Zhang2000 and @cite BouguetMCT . The coordinates of 3D object
     * points and their corresponding 2D projections in each view must be specified. That may be achieved
     * by using an object with known geometry and easily detectable feature points. Such an object is
     * called a calibration rig or calibration pattern, and OpenCV has built-in support for a chessboard as
     * a calibration rig (see @ref findChessboardCorners). Currently, initialization of intrinsic
     * parameters (when @ref CALIB_USE_INTRINSIC_GUESS is not set) is only implemented for planar calibration
     * patterns (where Z-coordinates of the object points must be all zeros). 3D calibration rigs can also
     * be used as long as initial cameraMatrix is provided.
     *
     * The algorithm performs the following steps:
     *
     * -   Compute the initial intrinsic parameters (the option only available for planar calibration
     * patterns) or read them from the input parameters. The distortion coefficients are all set to
     * zeros initially unless some of CALIB_FIX_K? are specified.
     *
     * -   Estimate the initial camera pose as if the intrinsic parameters have been already known. This is
     * done using solvePnP .
     *
     * -   Run the global Levenberg-Marquardt optimization algorithm to minimize the reprojection error,
     * that is, the total sum of squared distances between the observed feature points imagePoints and
     * the projected (using the current estimates for camera parameters and the poses) object points
     * objectPoints. See projectPoints for details.
     *
     * @note
     * If you use a non-square (i.e. non-N-by-N) grid and @ref findChessboardCorners for calibration,
     * and @ref calibrateCamera returns bad values (zero distortion coefficients, \f$c_x\f$ and
     * \f$c_y\f$ very far from the image center, and/or large differences between \f$f_x\f$ and
     * \f$f_y\f$ (ratios of 10:1 or more)), then you are probably using patternSize=cvSize(rows,cols)
     * instead of using patternSize=cvSize(cols,rows) in @ref findChessboardCorners.
     *
     * @sa
     * calibrateCameraRO, findChessboardCorners, solvePnP, initCameraMatrix2D, stereoCalibrate,
     * undistort
     */
    function calibrateCameraExtended(
        objectPoints: MatVector,
        imagePoints: MatVector,
        imageSize: SizeLike,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvecs: MatVector,
        tvecs: MatVector,
        stdDeviationsIntrinsics: Mat,
        stdDeviationsExtrinsics: Mat,
        perViewErrors: Mat,
        flags?: int,
        criteria?: TermCriteriaLike
    ): double;

    /**
     * @brief Calculates the magnitude and angle of 2D vectors.
     *
     * The function cv::cartToPolar calculates either the magnitude, angle, or both
     * for every 2D vector (x(I),y(I)):
     * \f[\begin{array}{l} \texttt{magnitude} (I)= \sqrt{\texttt{x}(I)^2+\texttt{y}(I)^2} , \\ \texttt{angle} (I)= \texttt{atan2} ( \texttt{y} (I), \texttt{x} (I))[ \cdot180 / \pi ] \end{array}\f]
     *
     * The angles are calculated with accuracy about 0.3 degrees. For the point
     * (0,0), the angle is set to 0.
     * @param x array of x-coordinates; this must be a single-precision or
     * double-precision floating-point array.
     * @param y array of y-coordinates, that must have the same size and same type as x.
     * @param magnitude output array of magnitudes of the same size and type as x.
     * @param angle output array of angles that has the same size and type as
     * x; the angles are measured in radians (from 0 to 2\*Pi) or in degrees (0 to 360 degrees).
     * @param angleInDegrees a flag, indicating whether the angles are measured
     * in radians (which is by default), or in degrees.
     * @sa Sobel, Scharr
     */
    function cartToPolar(x: Mat, y: Mat, magnitude: Mat, angle: Mat, angleInDegrees?: boolean): void;

    /**
     * @brief Draws a circle.
     *
     * The function cv::circle draws a simple or filled circle with a given center and radius.
     * @param img Image where the circle is drawn.
     * @param center Center of the circle.
     * @param radius Radius of the circle.
     * @param color Circle color.
     * @param thickness Thickness of the circle outline, if positive. Negative values, like #FILLED,
     * mean that a filled circle is to be drawn.
     * @param lineType Type of the circle boundary. See #LineTypes
     * @param shift Number of fractional bits in the coordinates of the center and in the radius value.
     */
    function circle(
        img: Mat,
        center: PointLike,
        radius: int,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        shift?: int
    ): void;

    /**
     * @brief Performs the per-element comparison of two arrays or an array and scalar value.
     *
     * The function compares:
     * Elements of two arrays when src1 and src2 have the same size:
     * \f[\texttt{dst} (I) =  \texttt{src1} (I)  \,\texttt{cmpop}\, \texttt{src2} (I)\f]
     * Elements of src1 with a scalar src2 when src2 is constructed from
     * Scalar or has a single element:
     * \f[\texttt{dst} (I) =  \texttt{src1}(I) \,\texttt{cmpop}\,  \texttt{src2}\f]
     * src1 with elements of src2 when src1 is constructed from Scalar or
     * has a single element:
     * \f[\texttt{dst} (I) =  \texttt{src1}  \,\texttt{cmpop}\, \texttt{src2} (I)\f]
     * When the comparison result is true, the corresponding element of output
     * array is set to 255. The comparison operations can be replaced with the
     * equivalent matrix expressions:
     * @code{.cpp}
     * Mat dst1 = src1 >= src2;
     * Mat dst2 = src1 < 8;
     * ...
     * @endcode
     * @param src1 first input array or a scalar; when it is an array, it must have a single channel.
     * @param src2 second input array or a scalar; when it is an array, it must have a single channel.
     * @param dst output array of type ref CV_8U that has the same size and the same number of channels as
     * the input arrays.
     * @param cmpop a flag, that specifies correspondence between the arrays (cv::CmpTypes)
     * @sa checkRange, min, max, threshold
     */
    function compare(src1: Mat, src2: Mat, dst: Mat, cmpop: int): void;

    /**
     * @brief Compares two histograms.
     *
     * The function cv::compareHist compares two dense or two sparse histograms using the specified method.
     *
     * The function returns \f$d(H_1, H_2)\f$ .
     *
     * While the function works well with 1-, 2-, 3-dimensional dense histograms, it may not be suitable
     * for high-dimensional sparse histograms. In such histograms, because of aliasing and sampling
     * problems, the coordinates of non-zero histogram bins can slightly shift. To compare such histograms
     * or more general sparse configurations of weighted points, consider using the #EMD function.
     *
     * @param H1 First compared histogram.
     * @param H2 Second compared histogram of the same size as H1 .
     * @param method Comparison method, see #HistCompMethods
     */
    function compareHist(H1: Mat, H2: Mat, method: int): double;

    /**
     * @overload
     *
     * @param image the 8-bit single-channel image to be labeled
     * @param labels destination labeled image
     * @param connectivity 8 or 4 for 8-way or 4-way connectivity respectively
     * @param ltype output image label type. Currently CV_32S and CV_16U are supported.
     */
    function connectedComponents(image: Mat, labels: Mat, connectivity?: int, ltype?: int): int;

    /**
     * @overload
     * @param image the 8-bit single-channel image to be labeled
     * @param labels destination labeled image
     * @param stats statistics output for each label, including the background label.
     * Statistics are accessed via stats(label, COLUMN) where COLUMN is one of
     * #ConnectedComponentsTypes, selecting the statistic. The data type is CV_32S.
     * @param centroids centroid output for each label, including the background label. Centroids are
     * accessed via centroids(label, 0) for x and centroids(label, 1) for y. The data type CV_64F.
     * @param connectivity 8 or 4 for 8-way or 4-way connectivity respectively
     * @param ltype output image label type. Currently CV_32S and CV_16U are supported.
     */
    function connectedComponentsWithStats(
        image: Mat,
        labels: Mat,
        stats: Mat,
        centroids: Mat,
        connectivity?: int,
        ltype?: int
    ): int;

    /**
     * @brief Calculates a contour area.
     *
     * The function computes a contour area. Similarly to moments , the area is computed using the Green
     * formula. Thus, the returned area and the number of non-zero pixels, if you draw the contour using
     * #drawContours or #fillPoly , can be different. Also, the function will most certainly give a wrong
     * results for contours with self-intersections.
     *
     * Example:
     * @code
     * vector<Point> contour;
     * contour.push_back(Point2f(0, 0));
     * contour.push_back(Point2f(10, 0));
     * contour.push_back(Point2f(10, 10));
     * contour.push_back(Point2f(5, 4));
     *
     * double area0 = contourArea(contour);
     * vector<Point> approx;
     * approxPolyDP(contour, approx, 5, true);
     * double area1 = contourArea(approx);
     *
     * cout << "area0 =" << area0 << endl <<
     * "area1 =" << area1 << endl <<
     * "approx poly vertices" << approx.size() << endl;
     * @endcode
     * @param contour Input vector of 2D points (contour vertices), stored in std::vector or Mat.
     * @param oriented Oriented area flag. If it is true, the function returns a signed area value,
     * depending on the contour orientation (clockwise or counter-clockwise). Using this feature you can
     * determine orientation of a contour by taking the sign of an area. By default, the parameter is
     * false, which means that the absolute value is returned.
     */
    function contourArea(contour: Mat, oriented?: boolean): double;

    /**
     * @brief Scales, calculates absolute values, and converts the result to 8-bit.
     *
     * On each element of the input array, the function convertScaleAbs
     * performs three operations sequentially: scaling, taking an absolute
     * value, conversion to an unsigned 8-bit type:
     * \f[\texttt{dst} (I)= \texttt{saturate\_cast<uchar>} (| \texttt{src} (I)* \texttt{alpha} +  \texttt{beta} |)\f]
     * In case of multi-channel arrays, the function processes each channel
     * independently. When the output is not 8-bit, the operation can be
     * emulated by calling the Mat::convertTo method (or by using matrix
     * expressions) and then by calculating an absolute value of the result.
     * For example:
     * @code{.cpp}
     * Mat_<float> A(30,30);
     * randu(A, Scalar(-100), Scalar(100));
     * Mat_<float> B = A*5 + 3;
     * B = abs(B);
     * // Mat_<float> B = abs(A*5+3) will also do the job,
     * // but it will allocate a temporary matrix
     * @endcode
     * @param src input array.
     * @param dst output array.
     * @param alpha optional scale factor.
     * @param beta optional delta added to the scaled values.
     * @sa  Mat::convertTo, cv::abs(const Mat&)
     */
    function convertScaleAbs(src: Mat, dst: Mat, alpha?: double, beta?: double): void;

    /**
     * @brief Finds the convex hull of a point set.
     *
     * The function cv::convexHull finds the convex hull of a 2D point set using the Sklansky's algorithm @cite Sklansky82
     * that has *O(N logN)* complexity in the current implementation.
     *
     * @param points Input 2D point set, stored in std::vector or Mat.
     * @param hull Output convex hull. It is either an integer vector of indices or vector of points. In
     * the first case, the hull elements are 0-based indices of the convex hull points in the original
     * array (since the set of convex hull points is a subset of the original point set). In the second
     * case, hull elements are the convex hull points themselves.
     * @param clockwise Orientation flag. If it is true, the output convex hull is oriented clockwise.
     * Otherwise, it is oriented counter-clockwise. The assumed coordinate system has its X axis pointing
     * to the right, and its Y axis pointing upwards.
     * @param returnPoints Operation flag. In case of a matrix, when the flag is true, the function
     * returns convex hull points. Otherwise, it returns indices of the convex hull points. When the
     * output array is std::vector, the flag is ignored, and the output depends on the type of the
     * vector: std::vector\<int\> implies returnPoints=false, std::vector\<Point\> implies
     * returnPoints=true.
     *
     * @note `points` and `hull` should be different arrays, inplace processing isn't supported.
     *
     * Check @ref tutorial_hull "the corresponding tutorial" for more details.
     *
     * useful links:
     *
     * https://www.learnopencv.com/convex-hull-using-opencv-in-python-and-c/
     */
    function convexHull(points: Mat, hull: Mat, clockwise?: boolean, returnPoints?: boolean): void;

    /**
     * @brief Finds the convexity defects of a contour.
     *
     * The figure below displays convexity defects of a hand contour:
     *
     * ![image](pics/defects.png)
     *
     * @param contour Input contour.
     * @param convexhull Convex hull obtained using convexHull that should contain indices of the contour
     * points that make the hull.
     * @param convexityDefects The output vector of convexity defects. In C++ and the new Python/Java
     * interface each convexity defect is represented as 4-element integer vector (a.k.a. #Vec4i):
     * (start_index, end_index, farthest_pt_index, fixpt_depth), where indices are 0-based indices
     * in the original contour of the convexity defect beginning, end and the farthest point, and
     * fixpt_depth is fixed-point approximation (with 8 fractional bits) of the distance between the
     * farthest contour point and the hull. That is, to get the floating-point value of the depth will be
     * fixpt_depth/256.0.
     */
    function convexityDefects(contour: Mat, convexhull: Mat, convexityDefects: Mat): void;

    /**
     * @brief Forms a border around an image.
     *
     * The function copies the source image into the middle of the destination image. The areas to the
     * left, to the right, above and below the copied source image will be filled with extrapolated
     * pixels. This is not what filtering functions based on it do (they extrapolate pixels on-fly), but
     * what other more complex functions, including your own, may do to simplify image boundary handling.
     *
     * The function supports the mode when src is already in the middle of dst . In this case, the
     * function does not copy src itself but simply constructs the border, for example:
     *
     * @code{.cpp}
     * // let border be the same in all directions
     * int border=2;
     * // constructs a larger image to fit both the image and the border
     * Mat gray_buf(rgb.rows + border*2, rgb.cols + border*2, rgb.depth());
     * // select the middle part of it w/o copying data
     * Mat gray(gray_canvas, Rect(border, border, rgb.cols, rgb.rows));
     * // convert image from RGB to grayscale
     * cvtColor(rgb, gray, COLOR_RGB2GRAY);
     * // form a border in-place
     * copyMakeBorder(gray, gray_buf, border, border,
     * border, border, BORDER_REPLICATE);
     * // now do some custom filtering ...
     * ...
     * @endcode
     * @note When the source image is a part (ROI) of a bigger image, the function will try to use the
     * pixels outside of the ROI to form a border. To disable this feature and always do extrapolation, as
     * if src was not a ROI, use borderType | #BORDER_ISOLATED.
     *
     * @param src Source image.
     * @param dst Destination image of the same type as src and the size Size(src.cols+left+right,
     * src.rows+top+bottom) .
     * @param top the top pixels
     * @param bottom the bottom pixels
     * @param left the left pixels
     * @param right Parameter specifying how many pixels in each direction from the source image rectangle
     * to extrapolate. For example, top=1, bottom=1, left=1, right=1 mean that 1 pixel-wide border needs
     * to be built.
     * @param borderType Border type. See borderInterpolate for details.
     * @param value Border value if borderType==BORDER_CONSTANT .
     *
     * @sa  borderInterpolate
     */
    function copyMakeBorder(
        src: Mat,
        dst: Mat,
        top: int,
        bottom: int,
        left: int,
        right: int,
        borderType: int,
        value?: ScalarLike
    ): void;

    /**
     * @brief Harris corner detector.
     *
     * The function runs the Harris corner detector on the image. Similarly to cornerMinEigenVal and
     * cornerEigenValsAndVecs , for each pixel \f$(x, y)\f$ it calculates a \f$2\times2\f$ gradient covariance
     * matrix \f$M^{(x,y)}\f$ over a \f$\texttt{blockSize} \times \texttt{blockSize}\f$ neighborhood. Then, it
     * computes the following characteristic:
     *
     * \f[\texttt{dst} (x,y) =  \mathrm{det} M^{(x,y)} - k  \cdot \left ( \mathrm{tr} M^{(x,y)} \right )^2\f]
     *
     * Corners in the image can be found as the local maxima of this response map.
     *
     * @param src Input single-channel 8-bit or floating-point image.
     * @param dst Image to store the Harris detector responses. It has the type CV_32FC1 and the same
     * size as src .
     * @param blockSize Neighborhood size (see the details on #cornerEigenValsAndVecs ).
     * @param ksize Aperture parameter for the Sobel operator.
     * @param k Harris detector free parameter. See the formula above.
     * @param borderType Pixel extrapolation method. See #BorderTypes. #BORDER_WRAP is not supported.
     */
    function cornerHarris(src: Mat, dst: Mat, blockSize: int, ksize: int, k: double, borderType?: int): void;

    /**
     * @brief Calculates the minimal eigenvalue of gradient matrices for corner detection.
     *
     * The function is similar to cornerEigenValsAndVecs but it calculates and stores only the minimal
     * eigenvalue of the covariance matrix of derivatives, that is, \f$\min(\lambda_1, \lambda_2)\f$ in terms
     * of the formulae in the cornerEigenValsAndVecs description.
     *
     * @param src Input single-channel 8-bit or floating-point image.
     * @param dst Image to store the minimal eigenvalues. It has the type CV_32FC1 and the same size as
     * src .
     * @param blockSize Neighborhood size (see the details on #cornerEigenValsAndVecs ).
     * @param ksize Aperture parameter for the Sobel operator.
     * @param borderType Pixel extrapolation method. See #BorderTypes. #BORDER_WRAP is not supported.
     */
    function cornerMinEigenVal(src: Mat, dst: Mat, blockSize: int, ksize?: int, borderType?: int): void;

    /**
     * @brief Counts non-zero array elements.
     *
     * The function returns the number of non-zero elements in src :
     * \f[\sum _{I: \; \texttt{src} (I) \ne0 } 1\f]
     * @param src single-channel array.
     * @sa  mean, meanStdDev, norm, minMaxLoc, calcCovarMatrix
     */
    function countNonZero(src: Mat): int;

    /**
     * @brief Converts an image from one color space to another.
     *
     * The function converts an input image from one color space to another. In case of a transformation
     * to-from RGB color space, the order of the channels should be specified explicitly (RGB or BGR). Note
     * that the default color format in OpenCV is often referred to as RGB but it is actually BGR (the
     * bytes are reversed). So the first byte in a standard (24-bit) color image will be an 8-bit Blue
     * component, the second byte will be Green, and the third byte will be Red. The fourth, fifth, and
     * sixth bytes would then be the second pixel (Blue, then Green, then Red), and so on.
     *
     * The conventional ranges for R, G, and B channel values are:
     * -   0 to 255 for CV_8U images
     * -   0 to 65535 for CV_16U images
     * -   0 to 1 for CV_32F images
     *
     * In case of linear transformations, the range does not matter. But in case of a non-linear
     * transformation, an input RGB image should be normalized to the proper value range to get the correct
     * results, for example, for RGB \f$\rightarrow\f$ L\*u\*v\* transformation. For example, if you have a
     * 32-bit floating-point image directly converted from an 8-bit image without any scaling, then it will
     * have the 0..255 value range instead of 0..1 assumed by the function. So, before calling #cvtColor ,
     * you need first to scale the image down:
     * @code
     * img *= 1./255;
     * cvtColor(img, img, COLOR_BGR2Luv);
     * @endcode
     * If you use #cvtColor with 8-bit images, the conversion will have some information lost. For many
     * applications, this will not be noticeable but it is recommended to use 32-bit images in applications
     * that need the full range of colors or that convert an image before an operation and then convert
     * back.
     *
     * If conversion adds the alpha channel, its value will set to the maximum of corresponding channel
     * range: 255 for CV_8U, 65535 for CV_16U, 1 for CV_32F.
     *
     * @param src input image: 8-bit unsigned, 16-bit unsigned ( CV_16UC... ), or single-precision
     * floating-point.
     * @param dst output image of the same size and depth as src.
     * @param code color space conversion code (see #ColorConversionCodes).
     * @param dstCn number of channels in the destination image; if the parameter is 0, the number of the
     * channels is derived automatically from src and code.
     *
     * @see @ref imgproc_color_conversions
     */
    function cvtColor(src: Mat, dst: Mat, code: int, dstCn?: int): void;

    /**
     * @brief main function for all demosaicing processes
     *
     * @param src input image: 8-bit unsigned or 16-bit unsigned.
     * @param dst output image of the same size and depth as src.
     * @param code Color space conversion code (see the description below).
     * @param dstCn number of channels in the destination image; if the parameter is 0, the number of the
     * channels is derived automatically from src and code.
     *
     * The function can do the following transformations:
     *
     * -   Demosaicing using bilinear interpolation
     *
     * #COLOR_BayerBG2BGR , #COLOR_BayerGB2BGR , #COLOR_BayerRG2BGR , #COLOR_BayerGR2BGR
     *
     * #COLOR_BayerBG2GRAY , #COLOR_BayerGB2GRAY , #COLOR_BayerRG2GRAY , #COLOR_BayerGR2GRAY
     *
     * -   Demosaicing using Variable Number of Gradients.
     *
     * #COLOR_BayerBG2BGR_VNG , #COLOR_BayerGB2BGR_VNG , #COLOR_BayerRG2BGR_VNG , #COLOR_BayerGR2BGR_VNG
     *
     * -   Edge-Aware Demosaicing.
     *
     * #COLOR_BayerBG2BGR_EA , #COLOR_BayerGB2BGR_EA , #COLOR_BayerRG2BGR_EA , #COLOR_BayerGR2BGR_EA
     *
     * -   Demosaicing with alpha channel
     *
     * #COLOR_BayerBG2BGRA , #COLOR_BayerGB2BGRA , #COLOR_BayerRG2BGRA , #COLOR_BayerGR2BGRA
     *
     * @sa cvtColor
     */
    function demosaicing(src: Mat, dst: Mat, code: int, dstCn?: int): void;

    /**
     * @brief Returns the determinant of a square floating-point matrix.
     *
     * The function cv::determinant calculates and returns the determinant of the
     * specified matrix. For small matrices ( mtx.cols=mtx.rows\<=3 ), the
     * direct method is used. For larger matrices, the function uses LU
     * factorization with partial pivoting.
     *
     * For symmetric positively-determined matrices, it is also possible to use
     * eigen decomposition to calculate the determinant.
     * @param mtx input matrix that must have CV_32FC1 or CV_64FC1 type and
     * square size.
     * @sa trace, invert, solve, eigen, @ref MatrixExpressions
     */
    function determinant(mtx: Mat): double;

    /**
     * @brief Performs a forward or inverse Discrete Fourier transform of a 1D or 2D floating-point array.
     *
     * The function cv::dft performs one of the following:
     * -   Forward the Fourier transform of a 1D vector of N elements:
     * \f[Y = F^{(N)}  \cdot X,\f]
     * where \f$F^{(N)}_{jk}=\exp(-2\pi i j k/N)\f$ and \f$i=\sqrt{-1}\f$
     * -   Inverse the Fourier transform of a 1D vector of N elements:
     * \f[\begin{array}{l} X'=  \left (F^{(N)} \right )^{-1}  \cdot Y =  \left (F^{(N)} \right )^*  \cdot y  \\ X = (1/N)  \cdot X, \end{array}\f]
     * where \f$F^*=\left(\textrm{Re}(F^{(N)})-\textrm{Im}(F^{(N)})\right)^T\f$
     * -   Forward the 2D Fourier transform of a M x N matrix:
     * \f[Y = F^{(M)}  \cdot X  \cdot F^{(N)}\f]
     * -   Inverse the 2D Fourier transform of a M x N matrix:
     * \f[\begin{array}{l} X'=  \left (F^{(M)} \right )^*  \cdot Y  \cdot \left (F^{(N)} \right )^* \\ X =  \frac{1}{M \cdot N} \cdot X' \end{array}\f]
     *
     * In case of real (single-channel) data, the output spectrum of the forward Fourier transform or input
     * spectrum of the inverse Fourier transform can be represented in a packed format called *CCS*
     * (complex-conjugate-symmetrical). It was borrowed from IPL (Intel\* Image Processing Library). Here
     * is how 2D *CCS* spectrum looks:
     * \f[\begin{bmatrix} Re Y_{0,0} & Re Y_{0,1} & Im Y_{0,1} & Re Y_{0,2} & Im Y_{0,2} &  \cdots & Re Y_{0,N/2-1} & Im Y_{0,N/2-1} & Re Y_{0,N/2}  \\ Re Y_{1,0} & Re Y_{1,1} & Im Y_{1,1} & Re Y_{1,2} & Im Y_{1,2} &  \cdots & Re Y_{1,N/2-1} & Im Y_{1,N/2-1} & Re Y_{1,N/2}  \\ Im Y_{1,0} & Re Y_{2,1} & Im Y_{2,1} & Re Y_{2,2} & Im Y_{2,2} &  \cdots & Re Y_{2,N/2-1} & Im Y_{2,N/2-1} & Im Y_{1,N/2}  \\ \hdotsfor{9} \\ Re Y_{M/2-1,0} &  Re Y_{M-3,1}  & Im Y_{M-3,1} &  \hdotsfor{3} & Re Y_{M-3,N/2-1} & Im Y_{M-3,N/2-1}& Re Y_{M/2-1,N/2}  \\ Im Y_{M/2-1,0} &  Re Y_{M-2,1}  & Im Y_{M-2,1} &  \hdotsfor{3} & Re Y_{M-2,N/2-1} & Im Y_{M-2,N/2-1}& Im Y_{M/2-1,N/2}  \\ Re Y_{M/2,0}  &  Re Y_{M-1,1} &  Im Y_{M-1,1} &  \hdotsfor{3} & Re Y_{M-1,N/2-1} & Im Y_{M-1,N/2-1}& Re Y_{M/2,N/2} \end{bmatrix}\f]
     *
     * In case of 1D transform of a real vector, the output looks like the first row of the matrix above.
     *
     * So, the function chooses an operation mode depending on the flags and size of the input array:
     * -   If #DFT_ROWS is set or the input array has a single row or single column, the function
     * performs a 1D forward or inverse transform of each row of a matrix when #DFT_ROWS is set.
     * Otherwise, it performs a 2D transform.
     * -   If the input array is real and #DFT_INVERSE is not set, the function performs a forward 1D or
     * 2D transform:
     * -   When #DFT_COMPLEX_OUTPUT is set, the output is a complex matrix of the same size as
     * input.
     * -   When #DFT_COMPLEX_OUTPUT is not set, the output is a real matrix of the same size as
     * input. In case of 2D transform, it uses the packed format as shown above. In case of a
     * single 1D transform, it looks like the first row of the matrix above. In case of
     * multiple 1D transforms (when using the #DFT_ROWS flag), each row of the output matrix
     * looks like the first row of the matrix above.
     * -   If the input array is complex and either #DFT_INVERSE or #DFT_REAL_OUTPUT are not set, the
     * output is a complex array of the same size as input. The function performs a forward or
     * inverse 1D or 2D transform of the whole input array or each row of the input array
     * independently, depending on the flags DFT_INVERSE and DFT_ROWS.
     * -   When #DFT_INVERSE is set and the input array is real, or it is complex but #DFT_REAL_OUTPUT
     * is set, the output is a real array of the same size as input. The function performs a 1D or 2D
     * inverse transformation of the whole input array or each individual row, depending on the flags
     * #DFT_INVERSE and #DFT_ROWS.
     *
     * If #DFT_SCALE is set, the scaling is done after the transformation.
     *
     * Unlike dct , the function supports arrays of arbitrary size. But only those arrays are processed
     * efficiently, whose sizes can be factorized in a product of small prime numbers (2, 3, and 5 in the
     * current implementation). Such an efficient DFT size can be calculated using the getOptimalDFTSize
     * method.
     *
     * The sample below illustrates how to calculate a DFT-based convolution of two 2D real arrays:
     * @code
     * void convolveDFT(InputArray A, InputArray B, OutputArray C)
     * {
     * // reallocate the output array if needed
     * C.create(abs(A.rows - B.rows)+1, abs(A.cols - B.cols)+1, A.type());
     * Size dftSize;
     * // calculate the size of DFT transform
     * dftSize.width = getOptimalDFTSize(A.cols + B.cols - 1);
     * dftSize.height = getOptimalDFTSize(A.rows + B.rows - 1);
     *
     * // allocate temporary buffers and initialize them with 0's
     * Mat tempA(dftSize, A.type(), Scalar::all(0));
     * Mat tempB(dftSize, B.type(), Scalar::all(0));
     *
     * // copy A and B to the top-left corners of tempA and tempB, respectively
     * Mat roiA(tempA, Rect(0,0,A.cols,A.rows));
     * A.copyTo(roiA);
     * Mat roiB(tempB, Rect(0,0,B.cols,B.rows));
     * B.copyTo(roiB);
     *
     * // now transform the padded A & B in-place;
     * // use "nonzeroRows" hint for faster processing
     * dft(tempA, tempA, 0, A.rows);
     * dft(tempB, tempB, 0, B.rows);
     *
     * // multiply the spectrums;
     * // the function handles packed spectrum representations well
     * mulSpectrums(tempA, tempB, tempA);
     *
     * // transform the product back from the frequency domain.
     * // Even though all the result rows will be non-zero,
     * // you need only the first C.rows of them, and thus you
     * // pass nonzeroRows == C.rows
     * dft(tempA, tempA, DFT_INVERSE + DFT_SCALE, C.rows);
     *
     * // now copy the result back to C.
     * tempA(Rect(0, 0, C.cols, C.rows)).copyTo(C);
     *
     * // all the temporary buffers will be deallocated automatically
     * }
     * @endcode
     * To optimize this sample, consider the following approaches:
     * -   Since nonzeroRows != 0 is passed to the forward transform calls and since A and B are copied to
     * the top-left corners of tempA and tempB, respectively, it is not necessary to clear the whole
     * tempA and tempB. It is only necessary to clear the tempA.cols - A.cols ( tempB.cols - B.cols)
     * rightmost columns of the matrices.
     * -   This DFT-based convolution does not have to be applied to the whole big arrays, especially if B
     * is significantly smaller than A or vice versa. Instead, you can calculate convolution by parts.
     * To do this, you need to split the output array C into multiple tiles. For each tile, estimate
     * which parts of A and B are required to calculate convolution in this tile. If the tiles in C are
     * too small, the speed will decrease a lot because of repeated work. In the ultimate case, when
     * each tile in C is a single pixel, the algorithm becomes equivalent to the naive convolution
     * algorithm. If the tiles are too big, the temporary arrays tempA and tempB become too big and
     * there is also a slowdown because of bad cache locality. So, there is an optimal tile size
     * somewhere in the middle.
     * -   If different tiles in C can be calculated in parallel and, thus, the convolution is done by
     * parts, the loop can be threaded.
     *
     * All of the above improvements have been implemented in #matchTemplate and #filter2D . Therefore, by
     * using them, you can get the performance even better than with the above theoretically optimal
     * implementation. Though, those two functions actually calculate cross-correlation, not convolution,
     * so you need to "flip" the second convolution operand B vertically and horizontally using flip .
     * @note
     * -   An example using the discrete fourier transform can be found at
     * opencv_source_code/samples/cpp/dft.cpp
     * -   (Python) An example using the dft functionality to perform Wiener deconvolution can be found
     * at opencv_source/samples/python/deconvolution.py
     * -   (Python) An example rearranging the quadrants of a Fourier image can be found at
     * opencv_source/samples/python/dft.py
     * @param src input array that could be real or complex.
     * @param dst output array whose size and type depends on the flags .
     * @param flags transformation flags, representing a combination of the #DftFlags
     * @param nonzeroRows when the parameter is not zero, the function assumes that only the first
     * nonzeroRows rows of the input array (#DFT_INVERSE is not set) or only the first nonzeroRows of the
     * output array (#DFT_INVERSE is set) contain non-zeros, thus, the function can handle the rest of the
     * rows more efficiently and save some time; this technique is very useful for calculating array
     * cross-correlation or convolution using DFT.
     * @sa dct , getOptimalDFTSize , mulSpectrums, filter2D , matchTemplate , flip , cartToPolar ,
     * magnitude , phase
     */
    function dft(src: Mat, dst: Mat, flags?: int, nonzeroRows?: int): void;

    /**
     * @brief Dilates an image by using a specific structuring element.
     *
     * The function dilates the source image using the specified structuring element that determines the
     * shape of a pixel neighborhood over which the maximum is taken:
     * \f[\texttt{dst} (x,y) =  \max _{(x',y'):  \, \texttt{element} (x',y') \ne0 } \texttt{src} (x+x',y+y')\f]
     *
     * The function supports the in-place mode. Dilation can be applied several ( iterations ) times. In
     * case of multi-channel images, each channel is processed independently.
     *
     * @param src input image; the number of channels can be arbitrary, but the depth should be one of
     * CV_8U, CV_16U, CV_16S, CV_32F or CV_64F.
     * @param dst output image of the same size and type as src.
     * @param kernel structuring element used for dilation; if elemenat=Mat(), a 3 x 3 rectangular
     * structuring element is used. Kernel can be created using #getStructuringElement
     * @param anchor position of the anchor within the element; default value (-1, -1) means that the
     * anchor is at the element center.
     * @param iterations number of times dilation is applied.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not suported.
     * @param borderValue border value in case of a constant border
     * @sa  erode, morphologyEx, getStructuringElement
     */
    function dilate(
        src: Mat,
        dst: Mat,
        kernel: Mat,
        anchor?: PointLike,
        iterations?: int,
        borderType?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * @overload
     * @param src 8-bit, single-channel (binary) source image.
     * @param dst Output image with calculated distances. It is a 8-bit or 32-bit floating-point,
     * single-channel image of the same size as src .
     * @param distanceType Type of distance, see #DistanceTypes
     * @param maskSize Size of the distance transform mask, see #DistanceTransformMasks. In case of the
     * #DIST_L1 or #DIST_C distance type, the parameter is forced to 3 because a \f$3\times 3\f$ mask gives
     * the same result as \f$5\times 5\f$ or any larger aperture.
     * @param dstType Type of output image. It can be CV_8U or CV_32F. Type CV_8U can be used only for
     * the first variant of the function and distanceType == #DIST_L1.
     */
    function distanceTransform(src: Mat, dst: Mat, distanceType: int, maskSize: int, dstType?: int): void;

    /**
     * @brief Calculates the distance to the closest zero pixel for each pixel of the source image.
     *
     * The function cv::distanceTransform calculates the approximate or precise distance from every binary
     * image pixel to the nearest zero pixel. For zero image pixels, the distance will obviously be zero.
     *
     * When maskSize == #DIST_MASK_PRECISE and distanceType == #DIST_L2 , the function runs the
     * algorithm described in @cite Felzenszwalb04 . This algorithm is parallelized with the TBB library.
     *
     * In other cases, the algorithm @cite Borgefors86 is used. This means that for a pixel the function
     * finds the shortest path to the nearest zero pixel consisting of basic shifts: horizontal, vertical,
     * diagonal, or knight's move (the latest is available for a \f$5\times 5\f$ mask). The overall
     * distance is calculated as a sum of these basic distances. Since the distance function should be
     * symmetric, all of the horizontal and vertical shifts must have the same cost (denoted as a ), all
     * the diagonal shifts must have the same cost (denoted as `b`), and all knight's moves must have the
     * same cost (denoted as `c`). For the #DIST_C and #DIST_L1 types, the distance is calculated
     * precisely, whereas for #DIST_L2 (Euclidean distance) the distance can be calculated only with a
     * relative error (a \f$5\times 5\f$ mask gives more accurate results). For `a`,`b`, and `c`, OpenCV
     * uses the values suggested in the original paper:
     * - DIST_L1: `a = 1, b = 2`
     * - DIST_L2:
     * - `3 x 3`: `a=0.955, b=1.3693`
     * - `5 x 5`: `a=1, b=1.4, c=2.1969`
     * - DIST_C: `a = 1, b = 1`
     *
     * Typically, for a fast, coarse distance estimation #DIST_L2, a \f$3\times 3\f$ mask is used. For a
     * more accurate distance estimation #DIST_L2, a \f$5\times 5\f$ mask or the precise algorithm is used.
     * Note that both the precise and the approximate algorithms are linear on the number of pixels.
     *
     * This variant of the function does not only compute the minimum distance for each pixel \f$(x, y)\f$
     * but also identifies the nearest connected component consisting of zero pixels
     * (labelType==#DIST_LABEL_CCOMP) or the nearest zero pixel (labelType==#DIST_LABEL_PIXEL). Index of the
     * component/pixel is stored in `labels(x, y)`. When labelType==#DIST_LABEL_CCOMP, the function
     * automatically finds connected components of zero pixels in the input image and marks them with
     * distinct labels. When labelType==#DIST_LABEL_PIXEL, the function scans through the input image and
     * marks all the zero pixels with distinct labels.
     *
     * In this mode, the complexity is still linear. That is, the function provides a very fast way to
     * compute the Voronoi diagram for a binary image. Currently, the second variant can use only the
     * approximate distance transform algorithm, i.e. maskSize=#DIST_MASK_PRECISE is not supported
     * yet.
     *
     * @param src 8-bit, single-channel (binary) source image.
     * @param dst Output image with calculated distances. It is a 8-bit or 32-bit floating-point,
     * single-channel image of the same size as src.
     * @param labels Output 2D array of labels (the discrete Voronoi diagram). It has the type
     * CV_32SC1 and the same size as src.
     * @param distanceType Type of distance, see #DistanceTypes
     * @param maskSize Size of the distance transform mask, see #DistanceTransformMasks.
     * #DIST_MASK_PRECISE is not supported by this variant. In case of the #DIST_L1 or #DIST_C distance type,
     * the parameter is forced to 3 because a \f$3\times 3\f$ mask gives the same result as \f$5\times
     * 5\f$ or any larger aperture.
     * @param labelType Type of the label array to build, see #DistanceTransformLabelTypes.
     */
    function distanceTransformWithLabels(
        src: Mat,
        dst: Mat,
        labels: Mat,
        distanceType: int,
        maskSize: int,
        labelType?: int
    ): void;

    /**
     * @brief Performs per-element division of two arrays or a scalar by an array.
     *
     * The function cv::divide divides one array by another:
     * \f[\texttt{dst(I) = saturate(src1(I)*scale/src2(I))}\f]
     * or a scalar by an array when there is no src1 :
     * \f[\texttt{dst(I) = saturate(scale/src2(I))}\f]
     *
     * Different channels of multi-channel arrays are processed independently.
     *
     * For integer types when src2(I) is zero, dst(I) will also be zero.
     *
     * @note In case of floating point data there is no special defined behavior for zero src2(I) values.
     * Regular floating-point division is used.
     * Expect correct IEEE-754 behaviour for floating-point data (with NaN, Inf result values).
     *
     * @note Saturation is not applied when the output array has the depth CV_32S. You may even get
     * result of an incorrect sign in the case of overflow.
     * @param src1 first input array.
     * @param src2 second input array of the same size and type as src1.
     * @param scale scalar factor.
     * @param dst output array of the same size and type as src2.
     * @param dtype optional depth of the output array; if -1, dst will have depth src2.depth(), but in
     * case of an array-by-array division, you can only pass -1 when src1.depth()==src2.depth().
     * @sa  multiply, add, subtract
     */
    function divide(src1: Mat, src2: Mat, dst: Mat, scale?: double, dtype?: int): void;

    /**
     * @overload
     */
    function divide(scale: double, src2: Mat, dst: Mat, dtype?: int): void;

    /**
     * @brief Draws contours outlines or filled contours.
     *
     * The function draws contour outlines in the image if \f$\texttt{thickness} \ge 0\f$ or fills the area
     * bounded by the contours if \f$\texttt{thickness}<0\f$ . The example below shows how to retrieve
     * connected components from the binary image and label them: :
     * @include snippets/imgproc_drawContours.cpp
     *
     * @param image Destination image.
     * @param contours All the input contours. Each contour is stored as a point vector.
     * @param contourIdx Parameter indicating a contour to draw. If it is negative, all the contours are drawn.
     * @param color Color of the contours.
     * @param thickness Thickness of lines the contours are drawn with. If it is negative (for example,
     * thickness=#FILLED ), the contour interiors are drawn.
     * @param lineType Line connectivity. See #LineTypes
     * @param hierarchy Optional information about hierarchy. It is only needed if you want to draw only
     * some of the contours (see maxLevel ).
     * @param maxLevel Maximal level for drawn contours. If it is 0, only the specified contour is drawn.
     * If it is 1, the function draws the contour(s) and all the nested contours. If it is 2, the function
     * draws the contours, all the nested contours, all the nested-to-nested contours, and so on. This
     * parameter is only taken into account when there is hierarchy available.
     * @param offset Optional contour shift parameter. Shift all the drawn contours by the specified
     * \f$\texttt{offset}=(dx,dy)\f$ .
     * @note When thickness=#FILLED, the function is designed to handle connected components with holes correctly
     * even when no hierarchy date is provided. This is done by analyzing all the outlines together
     * using even-odd rule. This may give incorrect results if you have a joint collection of separately retrieved
     * contours. In order to solve this problem, you need to call #drawContours separately for each sub-group
     * of contours, or iterate over the collection using contourIdx parameter.
     */
    function drawContours(
        image: Mat,
        contours: MatVector,
        contourIdx: int,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        hierarchy?: Mat,
        maxLevel?: int,
        offset?: PointLike
    ): void;

    /**
     * @brief Draw axes of the world/object coordinate system from pose estimation. @sa solvePnP
     *
     * @param image Input/output image. It must have 1 or 3 channels. The number of channels is not altered.
     * @param cameraMatrix Input 3x3 floating-point matrix of camera intrinsic parameters.
     * \f$\cameramatrix{A}\f$
     * @param distCoeffs Input vector of distortion coefficients
     * \f$\distcoeffs\f$. If the vector is empty, the zero distortion coefficients are assumed.
     * @param rvec Rotation vector (see @ref Rodrigues ) that, together with tvec, brings points from
     * the model coordinate system to the camera coordinate system.
     * @param tvec Translation vector.
     * @param length Length of the painted axes in the same unit than tvec (usually in meters).
     * @param thickness Line thickness of the painted axes.
     *
     * This function draws the axes of the world/object coordinate system w.r.t. to the camera frame.
     * OX is drawn in red, OY in green and OZ in blue.
     */
    function drawFrameAxes(
        image: Mat,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvec: Mat,
        tvec: Mat,
        length: float,
        thickness?: int
    ): void;

    /**
     * @brief Draws keypoints.
     *
     * @param image Source image.
     * @param keypoints Keypoints from the source image.
     * @param outImage Output image. Its content depends on the flags value defining what is drawn in the
     * output image. See possible flags bit values below.
     * @param color Color of keypoints.
     * @param flags Flags setting drawing features. Possible flags bit values are defined by
     * DrawMatchesFlags. See details above in drawMatches .
     *
     * @note
     * For Python API, flags are modified as cv.DRAW_MATCHES_FLAGS_DEFAULT,
     * cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS, cv.DRAW_MATCHES_FLAGS_DRAW_OVER_OUTIMG,
     * cv.DRAW_MATCHES_FLAGS_NOT_DRAW_SINGLE_POINTS
     */
    function drawKeypoints(
        image: Mat,
        keypoints: KeyPointVector,
        outImage: Mat,
        color?: ScalarLike,
        flags?: DrawMatchesFlags
    ): void;

    /**
     * @brief Draws the found matches of keypoints from two images.
     *
     * @param img1 First source image.
     * @param keypoints1 Keypoints from the first source image.
     * @param img2 Second source image.
     * @param keypoints2 Keypoints from the second source image.
     * @param matches1to2 Matches from the first image to the second one, which means that keypoints1[i]
     * has a corresponding point in keypoints2[matches[i]] .
     * @param outImg Output image. Its content depends on the flags value defining what is drawn in the
     * output image. See possible flags bit values below.
     * @param matchColor Color of matches (lines and connected keypoints). If matchColor==Scalar::all(-1)
     * , the color is generated randomly.
     * @param singlePointColor Color of single keypoints (circles), which means that keypoints do not
     * have the matches. If singlePointColor==Scalar::all(-1) , the color is generated randomly.
     * @param matchesMask Mask determining which matches are drawn. If the mask is empty, all matches are
     * drawn.
     * @param flags Flags setting drawing features. Possible flags bit values are defined by
     * DrawMatchesFlags.
     *
     * This function draws matches of keypoints from two images in the output image. Match is a line
     * connecting two keypoints (circles). See cv::DrawMatchesFlags.
     */
    function drawMatches(
        img1: Mat,
        keypoints1: KeyPointVector,
        img2: Mat,
        keypoints2: KeyPointVector,
        matches1to2: DMatchVector,
        outImg: Mat,
        matchColor?: ScalarLike,
        singlePointColor?: ScalarLike,
        matchesMask?: unknown,
        flags?: DrawMatchesFlags
    ): void;

    /**
     * @overload
     */
    function drawMatchesKnn(
        img1: Mat,
        keypoints1: KeyPointVector,
        img2: Mat,
        keypoints2: KeyPointVector,
        matches1to2: DMatchVectorVector,
        outImg: Mat,
        matchColor?: ScalarLike,
        singlePointColor?: ScalarLike,
        matchesMask?: unknown,
        flags?: DrawMatchesFlags
    ): void;

    /**
     * @brief Calculates eigenvalues and eigenvectors of a symmetric matrix.
     *
     * The function cv::eigen calculates just eigenvalues, or eigenvalues and eigenvectors of the symmetric
     * matrix src:
     * @code
     * src*eigenvectors.row(i).t() = eigenvalues.at<srcType>(i)*eigenvectors.row(i).t()
     * @endcode
     *
     * @note Use cv::eigenNonSymmetric for calculation of real eigenvalues and eigenvectors of non-symmetric matrix.
     *
     * @param src input matrix that must have CV_32FC1 or CV_64FC1 type, square size and be symmetrical
     * (src ^T^ == src).
     * @param eigenvalues output vector of eigenvalues of the same type as src; the eigenvalues are stored
     * in the descending order.
     * @param eigenvectors output matrix of eigenvectors; it has the same size and type as src; the
     * eigenvectors are stored as subsequent matrix rows, in the same order as the corresponding
     * eigenvalues.
     * @sa eigenNonSymmetric, completeSymm , PCA
     */
    function eigen(src: Mat, eigenvalues: Mat, eigenvectors?: Mat): boolean;

    /**
     * @brief Draws a simple or thick elliptic arc or fills an ellipse sector.
     *
     * The function cv::ellipse with more parameters draws an ellipse outline, a filled ellipse, an elliptic
     * arc, or a filled ellipse sector. The drawing code uses general parametric form.
     * A piecewise-linear curve is used to approximate the elliptic arc
     * boundary. If you need more control of the ellipse rendering, you can retrieve the curve using
     * #ellipse2Poly and then render it with #polylines or fill it with #fillPoly. If you use the first
     * variant of the function and want to draw the whole ellipse, not an arc, pass `startAngle=0` and
     * `endAngle=360`. If `startAngle` is greater than `endAngle`, they are swapped. The figure below explains
     * the meaning of the parameters to draw the blue arc.
     *
     * ![Parameters of Elliptic Arc](pics/ellipse.svg)
     *
     * @param img Image.
     * @param center Center of the ellipse.
     * @param axes Half of the size of the ellipse main axes.
     * @param angle Ellipse rotation angle in degrees.
     * @param startAngle Starting angle of the elliptic arc in degrees.
     * @param endAngle Ending angle of the elliptic arc in degrees.
     * @param color Ellipse color.
     * @param thickness Thickness of the ellipse arc outline, if positive. Otherwise, this indicates that
     * a filled ellipse sector is to be drawn.
     * @param lineType Type of the ellipse boundary. See #LineTypes
     * @param shift Number of fractional bits in the coordinates of the center and values of axes.
     */
    function ellipse(
        img: Mat,
        center: PointLike,
        axes: SizeLike,
        angle: double,
        startAngle: double,
        endAngle: double,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        shift?: int
    ): void;

    /**
     * @overload
     * @param img Image.
     * @param box Alternative ellipse representation via RotatedRect. This means that the function draws
     * an ellipse inscribed in the rotated rectangle.
     * @param color Ellipse color.
     * @param thickness Thickness of the ellipse arc outline, if positive. Otherwise, this indicates that
     * a filled ellipse sector is to be drawn.
     * @param lineType Type of the ellipse boundary. See #LineTypes
     */
    function ellipse(img: Mat, box: RotatedRectLike, color: ScalarLike, thickness?: int, lineType?: int): void;

    /**
     * @brief Approximates an elliptic arc with a polyline.
     *
     * The function ellipse2Poly computes the vertices of a polyline that approximates the specified
     * elliptic arc. It is used by #ellipse. If `arcStart` is greater than `arcEnd`, they are swapped.
     *
     * @param center Center of the arc.
     * @param axes Half of the size of the ellipse main axes. See #ellipse for details.
     * @param angle Rotation angle of the ellipse in degrees. See #ellipse for details.
     * @param arcStart Starting angle of the elliptic arc in degrees.
     * @param arcEnd Ending angle of the elliptic arc in degrees.
     * @param delta Angle between the subsequent polyline vertices. It defines the approximation
     * accuracy.
     * @param pts Output vector of polyline vertices.
     */
    function ellipse2Poly(
        center: PointLike,
        axes: SizeLike,
        angle: int,
        arcStart: int,
        arcEnd: int,
        delta: int,
        pts: PointVector
    ): void;

    /**
     * @brief Equalizes the histogram of a grayscale image.
     *
     * The function equalizes the histogram of the input image using the following algorithm:
     *
     * - Calculate the histogram \f$H\f$ for src .
     * - Normalize the histogram so that the sum of histogram bins is 255.
     * - Compute the integral of the histogram:
     * \f[H'_i =  \sum _{0  \le j < i} H(j)\f]
     * - Transform the image using \f$H'\f$ as a look-up table: \f$\texttt{dst}(x,y) = H'(\texttt{src}(x,y))\f$
     *
     * The algorithm normalizes the brightness and increases the contrast of the image.
     *
     * @param src Source 8-bit single channel image.
     * @param dst Destination image of the same size and type as src .
     */
    function equalizeHist(src: Mat, dst: Mat): void;

    /**
     * @brief Erodes an image by using a specific structuring element.
     *
     * The function erodes the source image using the specified structuring element that determines the
     * shape of a pixel neighborhood over which the minimum is taken:
     *
     * \f[\texttt{dst} (x,y) =  \min _{(x',y'):  \, \texttt{element} (x',y') \ne0 } \texttt{src} (x+x',y+y')\f]
     *
     * The function supports the in-place mode. Erosion can be applied several ( iterations ) times. In
     * case of multi-channel images, each channel is processed independently.
     *
     * @param src input image; the number of channels can be arbitrary, but the depth should be one of
     * CV_8U, CV_16U, CV_16S, CV_32F or CV_64F.
     * @param dst output image of the same size and type as src.
     * @param kernel structuring element used for erosion; if `element=Mat()`, a `3 x 3` rectangular
     * structuring element is used. Kernel can be created using #getStructuringElement.
     * @param anchor position of the anchor within the element; default value (-1, -1) means that the
     * anchor is at the element center.
     * @param iterations number of times erosion is applied.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @param borderValue border value in case of a constant border
     * @sa  dilate, morphologyEx, getStructuringElement
     */
    function erode(
        src: Mat,
        dst: Mat,
        kernel: Mat,
        anchor?: PointLike,
        iterations?: int,
        borderType?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * @brief Computes an optimal affine transformation between two 2D point sets.
     *
     * It computes
     * \f[
     * \begin{bmatrix}
     * x\\
     * y\\
     * \end{bmatrix}
     * =
     * \begin{bmatrix}
     * a_{11} & a_{12}\\
     * a_{21} & a_{22}\\
     * \end{bmatrix}
     * \begin{bmatrix}
     * X\\
     * Y\\
     * \end{bmatrix}
     * +
     * \begin{bmatrix}
     * b_1\\
     * b_2\\
     * \end{bmatrix}
     * \f]
     *
     * @param from First input 2D point set containing \f$(X,Y)\f$.
     * @param to Second input 2D point set containing \f$(x,y)\f$.
     * @param inliers Output vector indicating which points are inliers (1-inlier, 0-outlier).
     * @param method Robust method used to compute transformation. The following methods are possible:
     * -   @ref RANSAC - RANSAC-based robust method
     * -   @ref LMEDS - Least-Median robust method
     * RANSAC is the default method.
     * @param ransacReprojThreshold Maximum reprojection error in the RANSAC algorithm to consider
     * a point as an inlier. Applies only to RANSAC.
     * @param maxIters The maximum number of robust method iterations.
     * @param confidence Confidence level, between 0 and 1, for the estimated transformation. Anything
     * between 0.95 and 0.99 is usually good enough. Values too close to 1 can slow down the estimation
     * significantly. Values lower than 0.8-0.9 can result in an incorrectly estimated transformation.
     * @param refineIters Maximum number of iterations of refining algorithm (Levenberg-Marquardt).
     * Passing 0 will disable refining, so the output matrix will be output of robust method.
     *
     * @return Output 2D affine transformation matrix \f$2 \times 3\f$ or empty matrix if transformation
     * could not be estimated. The returned matrix has the following form:
     * \f[
     * \begin{bmatrix}
     * a_{11} & a_{12} & b_1\\
     * a_{21} & a_{22} & b_2\\
     * \end{bmatrix}
     * \f]
     *
     * The function estimates an optimal 2D affine transformation between two 2D point sets using the
     * selected robust algorithm.
     *
     * The computed transformation is then refined further (using only inliers) with the
     * Levenberg-Marquardt method to reduce the re-projection error even more.
     *
     * @note
     * The RANSAC method can handle practically any ratio of outliers but needs a threshold to
     * distinguish inliers from outliers. The method LMeDS does not need any threshold but it works
     * correctly only when there are more than 50% of inliers.
     *
     * @sa estimateAffinePartial2D, getAffineTransform
     */
    function estimateAffine2D(
        from: Mat,
        to: Mat,
        inliers?: Mat,
        method?: int,
        ransacReprojThreshold?: double,
        maxIters?: number,
        confidence?: double,
        refineIters?: number
    ): Mat;

    /**
     *
     */
    function estimateAffine2D(pts1: Mat, pts2: Mat, inliers: Mat, params: unknown): Mat;

    /**
     * @brief Calculates the exponent of every array element.
     *
     * The function cv::exp calculates the exponent of every element of the input
     * array:
     * \f[\texttt{dst} [I] = e^{ src(I) }\f]
     *
     * The maximum relative error is about 7e-6 for single-precision input and
     * less than 1e-10 for double-precision input. Currently, the function
     * converts denormalized values to zeros on output. Special values (NaN,
     * Inf) are not handled.
     * @param src input array.
     * @param dst output array of the same size and type as src.
     * @sa log , cartToPolar , polarToCart , phase , pow , sqrt , magnitude
     */
    function exp(src: Mat, dst: Mat): void;

    /**
     * @brief Fills a convex polygon.
     *
     * The function cv::fillConvexPoly draws a filled convex polygon. This function is much faster than the
     * function #fillPoly . It can fill not only convex polygons but any monotonic polygon without
     * self-intersections, that is, a polygon whose contour intersects every horizontal line (scan line)
     * twice at the most (though, its top-most and/or the bottom edge could be horizontal).
     *
     * @param img Image.
     * @param points Polygon vertices.
     * @param color Polygon color.
     * @param lineType Type of the polygon boundaries. See #LineTypes
     * @param shift Number of fractional bits in the vertex coordinates.
     */
    function fillConvexPoly(img: Mat, points: Mat, color: ScalarLike, lineType?: int, shift?: int): void;

    /**
     * @brief Fills the area bounded by one or more polygons.
     *
     * The function cv::fillPoly fills an area bounded by several polygonal contours. The function can fill
     * complex areas, for example, areas with holes, contours with self-intersections (some of their
     * parts), and so forth.
     *
     * @param img Image.
     * @param pts Array of polygons where each polygon is represented as an array of points.
     * @param color Polygon color.
     * @param lineType Type of the polygon boundaries. See #LineTypes
     * @param shift Number of fractional bits in the vertex coordinates.
     * @param offset Optional offset of all points of the contours.
     */
    function fillPoly(
        img: Mat,
        pts: MatVector,
        color: ScalarLike,
        lineType?: int,
        shift?: int,
        offset?: PointLike
    ): void;

    /**
     * @brief Convolves an image with the kernel.
     *
     * The function applies an arbitrary linear filter to an image. In-place operation is supported. When
     * the aperture is partially outside the image, the function interpolates outlier pixel values
     * according to the specified border mode.
     *
     * The function does actually compute correlation, not the convolution:
     *
     * \f[\texttt{dst} (x,y) =  \sum _{ \substack{0\leq x' < \texttt{kernel.cols}\\{0\leq y' < \texttt{kernel.rows}}}}  \texttt{kernel} (x',y')* \texttt{src} (x+x'- \texttt{anchor.x} ,y+y'- \texttt{anchor.y} )\f]
     *
     * That is, the kernel is not mirrored around the anchor point. If you need a real convolution, flip
     * the kernel using #flip and set the new anchor to `(kernel.cols - anchor.x - 1, kernel.rows -
     * anchor.y - 1)`.
     *
     * The function uses the DFT-based algorithm in case of sufficiently large kernels (~`11 x 11` or
     * larger) and the direct algorithm for small kernels.
     *
     * @param src input image.
     * @param dst output image of the same size and the same number of channels as src.
     * @param ddepth desired depth of the destination image, see @ref filter_depths "combinations"
     * @param kernel convolution kernel (or rather a correlation kernel), a single-channel floating point
     * matrix; if you want to apply different kernels to different channels, split the image into
     * separate color planes using split and process them individually.
     * @param anchor anchor of the kernel that indicates the relative position of a filtered point within
     * the kernel; the anchor should lie within the kernel; default value (-1,-1) means that the anchor
     * is at the kernel center.
     * @param delta optional value added to the filtered pixels before storing them in dst.
     * @param borderType pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  sepFilter2D, dft, matchTemplate
     */
    function filter2D(
        src: Mat,
        dst: Mat,
        ddepth: int,
        kernel: Mat,
        anchor?: PointLike,
        delta?: double,
        borderType?: int
    ): void;

    /**
     * @brief Finds contours in a binary image.
     *
     * The function retrieves contours from the binary image using the algorithm @cite Suzuki85 . The contours
     * are a useful tool for shape analysis and object detection and recognition. See squares.cpp in the
     * OpenCV sample directory.
     * @note Since opencv 3.2 source image is not modified by this function.
     *
     * @param image Source, an 8-bit single-channel image. Non-zero pixels are treated as 1's. Zero
     * pixels remain 0's, so the image is treated as binary . You can use #compare, #inRange, #threshold ,
     * #adaptiveThreshold, #Canny, and others to create a binary image out of a grayscale or color one.
     * If mode equals to #RETR_CCOMP or #RETR_FLOODFILL, the input can also be a 32-bit integer image of labels (CV_32SC1).
     * @param contours Detected contours. Each contour is stored as a vector of points (e.g.
     * std::vector<std::vector<cv::Point> >).
     * @param hierarchy Optional output vector (e.g. std::vector<cv::Vec4i>), containing information about the image topology. It has
     * as many elements as the number of contours. For each i-th contour contours[i], the elements
     * hierarchy[i][0] , hierarchy[i][1] , hierarchy[i][2] , and hierarchy[i][3] are set to 0-based indices
     * in contours of the next and previous contours at the same hierarchical level, the first child
     * contour and the parent contour, respectively. If for the contour i there are no next, previous,
     * parent, or nested contours, the corresponding elements of hierarchy[i] will be negative.
     * @param mode Contour retrieval mode, see #RetrievalModes
     * @param method Contour approximation method, see #ContourApproximationModes
     * @param offset Optional offset by which every contour point is shifted. This is useful if the
     * contours are extracted from the image ROI and then they should be analyzed in the whole image
     * context.
     */
    function findContours(
        image: Mat,
        contours: MatVector,
        hierarchy: Mat,
        mode: int,
        method: int,
        offset?: PointLike
    ): void;

    /**
     * @brief Finds a perspective transformation between two planes.
     *
     * @param srcPoints Coordinates of the points in the original plane, a matrix of the type CV_32FC2
     * or vector\<Point2f\> .
     * @param dstPoints Coordinates of the points in the target plane, a matrix of the type CV_32FC2 or
     * a vector\<Point2f\> .
     * @param method Method used to compute a homography matrix. The following methods are possible:
     * -   **0** - a regular method using all the points, i.e., the least squares method
     * -   @ref RANSAC - RANSAC-based robust method
     * -   @ref LMEDS - Least-Median robust method
     * -   @ref RHO - PROSAC-based robust method
     * @param ransacReprojThreshold Maximum allowed reprojection error to treat a point pair as an inlier
     * (used in the RANSAC and RHO methods only). That is, if
     * \f[\| \texttt{dstPoints} _i -  \texttt{convertPointsHomogeneous} ( \texttt{H} * \texttt{srcPoints} _i) \|_2  >  \texttt{ransacReprojThreshold}\f]
     * then the point \f$i\f$ is considered as an outlier. If srcPoints and dstPoints are measured in pixels,
     * it usually makes sense to set this parameter somewhere in the range of 1 to 10.
     * @param mask Optional output mask set by a robust method ( RANSAC or LMeDS ). Note that the input
     * mask values are ignored.
     * @param maxIters The maximum number of RANSAC iterations.
     * @param confidence Confidence level, between 0 and 1.
     *
     * The function finds and returns the perspective transformation \f$H\f$ between the source and the
     * destination planes:
     *
     * \f[s_i  \vecthree{x'_i}{y'_i}{1} \sim H  \vecthree{x_i}{y_i}{1}\f]
     *
     * so that the back-projection error
     *
     * \f[\sum _i \left ( x'_i- \frac{h_{11} x_i + h_{12} y_i + h_{13}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2+ \left ( y'_i- \frac{h_{21} x_i + h_{22} y_i + h_{23}}{h_{31} x_i + h_{32} y_i + h_{33}} \right )^2\f]
     *
     * is minimized. If the parameter method is set to the default value 0, the function uses all the point
     * pairs to compute an initial homography estimate with a simple least-squares scheme.
     *
     * However, if not all of the point pairs ( \f$srcPoints_i\f$, \f$dstPoints_i\f$ ) fit the rigid perspective
     * transformation (that is, there are some outliers), this initial estimate will be poor. In this case,
     * you can use one of the three robust methods. The methods RANSAC, LMeDS and RHO try many different
     * random subsets of the corresponding point pairs (of four pairs each, collinear pairs are discarded), estimate the homography matrix
     * using this subset and a simple least-squares algorithm, and then compute the quality/goodness of the
     * computed homography (which is the number of inliers for RANSAC or the least median re-projection error for
     * LMeDS). The best subset is then used to produce the initial estimate of the homography matrix and
     * the mask of inliers/outliers.
     *
     * Regardless of the method, robust or not, the computed homography matrix is refined further (using
     * inliers only in case of a robust method) with the Levenberg-Marquardt method to reduce the
     * re-projection error even more.
     *
     * The methods RANSAC and RHO can handle practically any ratio of outliers but need a threshold to
     * distinguish inliers from outliers. The method LMeDS does not need any threshold but it works
     * correctly only when there are more than 50% of inliers. Finally, if there are no outliers and the
     * noise is rather small, use the default method (method=0).
     *
     * The function is used to find initial intrinsic and extrinsic matrices. Homography matrix is
     * determined up to a scale. Thus, it is normalized so that \f$h_{33}=1\f$. Note that whenever an \f$H\f$ matrix
     * cannot be estimated, an empty one will be returned.
     *
     * @sa
     * getAffineTransform, estimateAffine2D, estimateAffinePartial2D, getPerspectiveTransform, warpPerspective,
     * perspectiveTransform
     */
    function findHomography(
        srcPoints: Mat,
        dstPoints: Mat,
        method?: int,
        ransacReprojThreshold?: double,
        mask?: Mat,
        maxIters?: int,
        confidence?: double
    ): Mat;

    /**
     * @overload
     */
    function findHomography(srcPoints: Mat, dstPoints: Mat, mask: Mat, params: unknown): Mat;

    /**
     * @brief Finds the geometric transform (warp) between two images in terms of the ECC criterion @cite EP08 .
     *
     * @param templateImage single-channel template image; CV_8U or CV_32F array.
     * @param inputImage single-channel input image which should be warped with the final warpMatrix in
     * order to provide an image similar to templateImage, same type as templateImage.
     * @param warpMatrix floating-point \f$2\times 3\f$ or \f$3\times 3\f$ mapping matrix (warp).
     * @param motionType parameter, specifying the type of motion:
     * -   **MOTION_TRANSLATION** sets a translational motion model; warpMatrix is \f$2\times 3\f$ with
     * the first \f$2\times 2\f$ part being the unity matrix and the rest two parameters being
     * estimated.
     * -   **MOTION_EUCLIDEAN** sets a Euclidean (rigid) transformation as motion model; three
     * parameters are estimated; warpMatrix is \f$2\times 3\f$.
     * -   **MOTION_AFFINE** sets an affine motion model (DEFAULT); six parameters are estimated;
     * warpMatrix is \f$2\times 3\f$.
     * -   **MOTION_HOMOGRAPHY** sets a homography as a motion model; eight parameters are
     * estimated;\`warpMatrix\` is \f$3\times 3\f$.
     * @param criteria parameter, specifying the termination criteria of the ECC algorithm;
     * criteria.epsilon defines the threshold of the increment in the correlation coefficient between two
     * iterations (a negative criteria.epsilon makes criteria.maxcount the only termination criterion).
     * Default values are shown in the declaration above.
     * @param inputMask An optional mask to indicate valid values of inputImage.
     * @param gaussFiltSize An optional value indicating size of gaussian blur filter; (DEFAULT: 5)
     *
     * The function estimates the optimum transformation (warpMatrix) with respect to ECC criterion
     * (@cite EP08), that is
     *
     * \f[\texttt{warpMatrix} = \arg\max_{W} \texttt{ECC}(\texttt{templateImage}(x,y),\texttt{inputImage}(x',y'))\f]
     *
     * where
     *
     * \f[\begin{bmatrix} x' \\ y' \end{bmatrix} = W \cdot \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}\f]
     *
     * (the equation holds with homogeneous coordinates for homography). It returns the final enhanced
     * correlation coefficient, that is the correlation coefficient between the template image and the
     * final warped input image. When a \f$3\times 3\f$ matrix is given with motionType =0, 1 or 2, the third
     * row is ignored.
     *
     * Unlike findHomography and estimateRigidTransform, the function findTransformECC implements an
     * area-based alignment that builds on intensity similarities. In essence, the function updates the
     * initial transformation that roughly aligns the images. If this information is missing, the identity
     * warp (unity matrix) is used as an initialization. Note that if images undergo strong
     * displacements/rotations, an initial transformation that roughly aligns the images is necessary
     * (e.g., a simple euclidean/similarity transform that allows for the images showing the same image
     * content approximately). Use inverse warping in the second image to take an image close to the first
     * one, i.e. use the flag WARP_INVERSE_MAP with warpAffine or warpPerspective. See also the OpenCV
     * sample image_alignment.cpp that demonstrates the use of the function. Note that the function throws
     * an exception if algorithm does not converges.
     *
     * @sa
     * computeECC, estimateAffine2D, estimateAffinePartial2D, findHomography
     */
    function findTransformECC(
        templateImage: Mat,
        inputImage: Mat,
        warpMatrix: Mat,
        motionType: int,
        criteria: TermCriteriaLike,
        inputMask: Mat,
        gaussFiltSize: int
    ): double;

    /**
     * @brief Fits an ellipse around a set of 2D points.
     *
     * The function calculates the ellipse that fits (in a least-squares sense) a set of 2D points best of
     * all. It returns the rotated rectangle in which the ellipse is inscribed. The first algorithm described by @cite Fitzgibbon95
     * is used. Developer should keep in mind that it is possible that the returned
     * ellipse/rotatedRect data contains negative indices, due to the data points being close to the
     * border of the containing Mat element.
     *
     * @param points Input 2D point set, stored in std::vector\<\> or Mat
     */
    function fitEllipse(points: Mat): RotatedRectLike;

    /**
     * @brief Fits a line to a 2D or 3D point set.
     *
     * The function fitLine fits a line to a 2D or 3D point set by minimizing \f$\sum_i \rho(r_i)\f$ where
     * \f$r_i\f$ is a distance between the \f$i^{th}\f$ point, the line and \f$\rho(r)\f$ is a distance function, one
     * of the following:
     * -  DIST_L2
     * \f[\rho (r) = r^2/2  \quad \text{(the simplest and the fastest least-squares method)}\f]
     * - DIST_L1
     * \f[\rho (r) = r\f]
     * - DIST_L12
     * \f[\rho (r) = 2  \cdot ( \sqrt{1 + \frac{r^2}{2}} - 1)\f]
     * - DIST_FAIR
     * \f[\rho \left (r \right ) = C^2  \cdot \left (  \frac{r}{C} -  \log{\left(1 + \frac{r}{C}\right)} \right )  \quad \text{where} \quad C=1.3998\f]
     * - DIST_WELSCH
     * \f[\rho \left (r \right ) =  \frac{C^2}{2} \cdot \left ( 1 -  \exp{\left(-\left(\frac{r}{C}\right)^2\right)} \right )  \quad \text{where} \quad C=2.9846\f]
     * - DIST_HUBER
     * \f[\rho (r) =  \fork{r^2/2}{if \(r < C\)}{C \cdot (r-C/2)}{otherwise} \quad \text{where} \quad C=1.345\f]
     *
     * The algorithm is based on the M-estimator ( <http://en.wikipedia.org/wiki/M-estimator> ) technique
     * that iteratively fits the line using the weighted least-squares algorithm. After each iteration the
     * weights \f$w_i\f$ are adjusted to be inversely proportional to \f$\rho(r_i)\f$ .
     *
     * @param points Input vector of 2D or 3D points, stored in std::vector\<\> or Mat.
     * @param line Output line parameters. In case of 2D fitting, it should be a vector of 4 elements
     * (like Vec4f) - (vx, vy, x0, y0), where (vx, vy) is a normalized vector collinear to the line and
     * (x0, y0) is a point on the line. In case of 3D fitting, it should be a vector of 6 elements (like
     * Vec6f) - (vx, vy, vz, x0, y0, z0), where (vx, vy, vz) is a normalized vector collinear to the line
     * and (x0, y0, z0) is a point on the line.
     * @param distType Distance used by the M-estimator, see #DistanceTypes
     * @param param Numerical parameter ( C ) for some types of distances. If it is 0, an optimal value
     * is chosen.
     * @param reps Sufficient accuracy for the radius (distance between the coordinate origin and the line).
     * @param aeps Sufficient accuracy for the angle. 0.01 would be a good default value for reps and aeps.
     */
    function fitLine(points: Mat, line: Mat, distType: int, param: double, reps: double, aeps: double): void;

    /**
     * @brief Flips a 2D array around vertical, horizontal, or both axes.
     *
     * The function cv::flip flips the array in one of three different ways (row
     * and column indices are 0-based):
     * \f[\texttt{dst} _{ij} =
     * \left\{
     * \begin{array}{l l}
     * \texttt{src} _{\texttt{src.rows}-i-1,j} & if\;  \texttt{flipCode} = 0 \\
     * \texttt{src} _{i, \texttt{src.cols} -j-1} & if\;  \texttt{flipCode} > 0 \\
     * \texttt{src} _{ \texttt{src.rows} -i-1, \texttt{src.cols} -j-1} & if\; \texttt{flipCode} < 0 \\
     * \end{array}
     * \right.\f]
     * The example scenarios of using the function are the following:
     * Vertical flipping of the image (flipCode == 0) to switch between
     * top-left and bottom-left image origin. This is a typical operation
     * in video processing on Microsoft Windows\* OS.
     * Horizontal flipping of the image with the subsequent horizontal
     * shift and absolute difference calculation to check for a
     * vertical-axis symmetry (flipCode \> 0).
     * Simultaneous horizontal and vertical flipping of the image with
     * the subsequent shift and absolute difference calculation to check
     * for a central symmetry (flipCode \< 0).
     * Reversing the order of point arrays (flipCode \> 0 or
     * flipCode == 0).
     * @param src input array.
     * @param dst output array of the same size and type as src.
     * @param flipCode a flag to specify how to flip the array; 0 means
     * flipping around the x-axis and positive value (for example, 1) means
     * flipping around y-axis. Negative value (for example, -1) means flipping
     * around both axes.
     * @sa transpose , repeat , completeSymm
     */
    function flip(src: Mat, dst: Mat, flipCode: int): void;

    /**
     * @brief Performs generalized matrix multiplication.
     *
     * The function cv::gemm performs generalized matrix multiplication similar to the
     * gemm functions in BLAS level 3. For example,
     * `gemm(src1, src2, alpha, src3, beta, dst, GEMM_1_T + GEMM_3_T)`
     * corresponds to
     * \f[\texttt{dst} =  \texttt{alpha} \cdot \texttt{src1} ^T  \cdot \texttt{src2} +  \texttt{beta} \cdot \texttt{src3} ^T\f]
     *
     * In case of complex (two-channel) data, performed a complex matrix
     * multiplication.
     *
     * The function can be replaced with a matrix expression. For example, the
     * above call can be replaced with:
     * @code{.cpp}
     * dst = alpha*src1.t()*src2 + beta*src3.t();
     * @endcode
     * @param src1 first multiplied input matrix that could be real(CV_32FC1,
     * CV_64FC1) or complex(CV_32FC2, CV_64FC2).
     * @param src2 second multiplied input matrix of the same type as src1.
     * @param alpha weight of the matrix product.
     * @param src3 third optional delta matrix added to the matrix product; it
     * should have the same type as src1 and src2.
     * @param beta weight of src3.
     * @param dst output matrix; it has the proper size and the same type as
     * input matrices.
     * @param flags operation flags (cv::GemmFlags)
     * @sa mulTransposed , transform
     */
    function gemm(src1: Mat, src2: Mat, alpha: double, src3: Mat, beta: double, dst: Mat, flags?: int): void;

    /**
     * @overload
     */
    function getAffineTransform(src: Mat, dst: Mat): Mat;

    /**
     * @brief Returns the default new camera matrix.
     *
     * The function returns the camera matrix that is either an exact copy of the input cameraMatrix (when
     * centerPrinicipalPoint=false ), or the modified one (when centerPrincipalPoint=true).
     *
     * In the latter case, the new camera matrix will be:
     *
     * \f[\begin{bmatrix} f_x && 0 && ( \texttt{imgSize.width} -1)*0.5  \\ 0 && f_y && ( \texttt{imgSize.height} -1)*0.5  \\ 0 && 0 && 1 \end{bmatrix} ,\f]
     *
     * where \f$f_x\f$ and \f$f_y\f$ are \f$(0,0)\f$ and \f$(1,1)\f$ elements of cameraMatrix, respectively.
     *
     * By default, the undistortion functions in OpenCV (see #initUndistortRectifyMap, #undistort) do not
     * move the principal point. However, when you work with stereo, it is important to move the principal
     * points in both views to the same y-coordinate (which is required by most of stereo correspondence
     * algorithms), and may be to the same x-coordinate too. So, you can form the new camera matrix for
     * each view where the principal points are located at the center.
     *
     * @param cameraMatrix Input camera matrix.
     * @param imgsize Camera view image size in pixels.
     * @param centerPrincipalPoint Location of the principal point in the new camera matrix. The
     * parameter indicates whether this location should be at the image center or not.
     */
    function getDefaultNewCameraMatrix(cameraMatrix: Mat, imgsize?: SizeLike, centerPrincipalPoint?: boolean): Mat;

    /**
     * @brief Returns the optimal DFT size for a given vector size.
     *
     * DFT performance is not a monotonic function of a vector size. Therefore, when you calculate
     * convolution of two arrays or perform the spectral analysis of an array, it usually makes sense to
     * pad the input data with zeros to get a bit larger array that can be transformed much faster than the
     * original one. Arrays whose size is a power-of-two (2, 4, 8, 16, 32, ...) are the fastest to process.
     * Though, the arrays whose size is a product of 2's, 3's, and 5's (for example, 300 = 5\*5\*3\*2\*2)
     * are also processed quite efficiently.
     *
     * The function cv::getOptimalDFTSize returns the minimum number N that is greater than or equal to vecsize
     * so that the DFT of a vector of size N can be processed efficiently. In the current implementation N
     * = 2 ^p^ \* 3 ^q^ \* 5 ^r^ for some integer p, q, r.
     *
     * The function returns a negative number if vecsize is too large (very close to INT_MAX ).
     *
     * While the function cannot be used directly to estimate the optimal vector size for DCT transform
     * (since the current DCT implementation supports only even-size vectors), it can be easily processed
     * as getOptimalDFTSize((vecsize+1)/2)\*2.
     * @param vecsize vector size.
     * @sa dft , dct , idft , idct , mulSpectrums
     */
    function getOptimalDFTSize(vecsize: int): int;

    /**
     * @brief Calculates a perspective transform from four pairs of the corresponding points.
     *
     * The function calculates the \f$3 \times 3\f$ matrix of a perspective transform so that:
     *
     * \f[\begin{bmatrix} t_i x'_i \\ t_i y'_i \\ t_i \end{bmatrix} = \texttt{map_matrix} \cdot \begin{bmatrix} x_i \\ y_i \\ 1 \end{bmatrix}\f]
     *
     * where
     *
     * \f[dst(i)=(x'_i,y'_i), src(i)=(x_i, y_i), i=0,1,2,3\f]
     *
     * @param src Coordinates of quadrangle vertices in the source image.
     * @param dst Coordinates of the corresponding quadrangle vertices in the destination image.
     * @param solveMethod method passed to cv::solve (#DecompTypes)
     *
     * @sa  findHomography, warpPerspective, perspectiveTransform
     */
    function getPerspectiveTransform(src: Mat, dst: Mat, solveMethod?: int): Mat;

    /**
     * @brief Calculates an affine matrix of 2D rotation.
     *
     * The function calculates the following matrix:
     *
     * \f[\begin{bmatrix} \alpha &  \beta & (1- \alpha )  \cdot \texttt{center.x} -  \beta \cdot \texttt{center.y} \\ - \beta &  \alpha &  \beta \cdot \texttt{center.x} + (1- \alpha )  \cdot \texttt{center.y} \end{bmatrix}\f]
     *
     * where
     *
     * \f[\begin{array}{l} \alpha =  \texttt{scale} \cdot \cos \texttt{angle} , \\ \beta =  \texttt{scale} \cdot \sin \texttt{angle} \end{array}\f]
     *
     * The transformation maps the rotation center to itself. If this is not the target, adjust the shift.
     *
     * @param center Center of the rotation in the source image.
     * @param angle Rotation angle in degrees. Positive values mean counter-clockwise rotation (the
     * coordinate origin is assumed to be the top-left corner).
     * @param scale Isotropic scale factor.
     *
     * @sa  getAffineTransform, warpAffine, transform
     */
    function getRotationMatrix2D(center: Point2fLike, angle: double, scale: double): Mat;

    /**
     * @brief Returns a structuring element of the specified size and shape for morphological operations.
     *
     * The function constructs and returns the structuring element that can be further passed to #erode,
     * #dilate or #morphologyEx. But you can also construct an arbitrary binary mask yourself and use it as
     * the structuring element.
     *
     * @param shape Element shape that could be one of #MorphShapes
     * @param ksize Size of the structuring element.
     * @param anchor Anchor position within the element. The default value \f$(-1, -1)\f$ means that the
     * anchor is at the center. Note that only the shape of a cross-shaped element depends on the anchor
     * position. In other cases the anchor just regulates how much the result of the morphological
     * operation is shifted.
     */
    function getStructuringElement(shape: int, ksize: SizeLike, anchor?: PointLike): Mat;

    /**
     * @brief Determines strong corners on an image.
     *
     * The function finds the most prominent corners in the image or in the specified image region, as
     * described in @cite Shi94
     *
     * -   Function calculates the corner quality measure at every source image pixel using the
     * #cornerMinEigenVal or #cornerHarris .
     * -   Function performs a non-maximum suppression (the local maximums in *3 x 3* neighborhood are
     * retained).
     * -   The corners with the minimal eigenvalue less than
     * \f$\texttt{qualityLevel} \cdot \max_{x,y} qualityMeasureMap(x,y)\f$ are rejected.
     * -   The remaining corners are sorted by the quality measure in the descending order.
     * -   Function throws away each corner for which there is a stronger corner at a distance less than
     * maxDistance.
     *
     * The function can be used to initialize a point-based tracker of an object.
     *
     * @note If the function is called with different values A and B of the parameter qualityLevel , and
     * A \> B, the vector of returned corners with qualityLevel=A will be the prefix of the output vector
     * with qualityLevel=B .
     *
     * @param image Input 8-bit or floating-point 32-bit, single-channel image.
     * @param corners Output vector of detected corners.
     * @param maxCorners Maximum number of corners to return. If there are more corners than are found,
     * the strongest of them is returned. `maxCorners <= 0` implies that no limit on the maximum is set
     * and all detected corners are returned.
     * @param qualityLevel Parameter characterizing the minimal accepted quality of image corners. The
     * parameter value is multiplied by the best corner quality measure, which is the minimal eigenvalue
     * (see #cornerMinEigenVal ) or the Harris function response (see #cornerHarris ). The corners with the
     * quality measure less than the product are rejected. For example, if the best corner has the
     * quality measure = 1500, and the qualityLevel=0.01 , then all the corners with the quality measure
     * less than 15 are rejected.
     * @param minDistance Minimum possible Euclidean distance between the returned corners.
     * @param mask Optional region of interest. If the image is not empty (it needs to have the type
     * CV_8UC1 and the same size as image ), it specifies the region in which the corners are detected.
     * @param blockSize Size of an average block for computing a derivative covariation matrix over each
     * pixel neighborhood. See cornerEigenValsAndVecs .
     * @param useHarrisDetector Parameter indicating whether to use a Harris detector (see #cornerHarris)
     * or #cornerMinEigenVal.
     * @param k Free parameter of the Harris detector.
     *
     * @sa  cornerMinEigenVal, cornerHarris, calcOpticalFlowPyrLK, estimateRigidTransform,
     */
    function goodFeaturesToTrack(
        image: Mat,
        corners: Mat,
        maxCorners: int,
        qualityLevel: double,
        minDistance: double,
        mask?: Mat,
        blockSize?: int,
        useHarrisDetector?: boolean,
        k?: double
    ): void;

    /**
     *
     */
    function goodFeaturesToTrack(
        image: Mat,
        corners: Mat,
        maxCorners: int,
        qualityLevel: double,
        minDistance: double,
        mask: Mat,
        blockSize: int,
        gradientSize: int,
        useHarrisDetector?: boolean,
        k?: double
    ): void;

    /**
     * @brief Runs the GrabCut algorithm.
     *
     * The function implements the [GrabCut image segmentation algorithm](http://en.wikipedia.org/wiki/GrabCut).
     *
     * @param img Input 8-bit 3-channel image.
     * @param mask Input/output 8-bit single-channel mask. The mask is initialized by the function when
     * mode is set to #GC_INIT_WITH_RECT. Its elements may have one of the #GrabCutClasses.
     * @param rect ROI containing a segmented object. The pixels outside of the ROI are marked as
     * "obvious background". The parameter is only used when mode==#GC_INIT_WITH_RECT .
     * @param bgdModel Temporary array for the background model. Do not modify it while you are
     * processing the same image.
     * @param fgdModel Temporary arrays for the foreground model. Do not modify it while you are
     * processing the same image.
     * @param iterCount Number of iterations the algorithm should make before returning the result. Note
     * that the result can be refined with further calls with mode==#GC_INIT_WITH_MASK or
     * mode==GC_EVAL .
     * @param mode Operation mode that could be one of the #GrabCutModes
     */
    function grabCut(
        img: Mat,
        mask: Mat,
        rect: RectLike,
        bgdModel: Mat,
        fgdModel: Mat,
        iterCount: int,
        mode?: int
    ): void;

    /**
     * @overload
     */
    function groupRectangles(rectList: RectVector, weights: IntVector | int[], groupThreshold: int, eps?: double): void;

    /**
     * @overload
     * @code{.cpp}
     * std::vector<cv::Mat> matrices = { cv::Mat(4, 1, CV_8UC1, cv::Scalar(1)),
     * cv::Mat(4, 1, CV_8UC1, cv::Scalar(2)),
     * cv::Mat(4, 1, CV_8UC1, cv::Scalar(3)),};
     *
     * cv::Mat out;
     * cv::hconcat( matrices, out );
     * //out:
     * //[1, 2, 3;
     * // 1, 2, 3;
     * // 1, 2, 3;
     * // 1, 2, 3]
     * @endcode
     * @param src input array or vector of matrices. all of the matrices must have the same number of rows and the same depth.
     * @param dst output array. It has the same number of rows and depth as the src, and the sum of cols of the src.
     * same depth.
     */
    function hconcat(src: MatVector, dst: Mat): void;

    /**
     * @brief  Checks if array elements lie between the elements of two other arrays.
     *
     * The function checks the range as follows:
     * -   For every element of a single-channel input array:
     * \f[\texttt{dst} (I)= \texttt{lowerb} (I)_0  \leq \texttt{src} (I)_0 \leq  \texttt{upperb} (I)_0\f]
     * -   For two-channel arrays:
     * \f[\texttt{dst} (I)= \texttt{lowerb} (I)_0  \leq \texttt{src} (I)_0 \leq  \texttt{upperb} (I)_0  \land \texttt{lowerb} (I)_1  \leq \texttt{src} (I)_1 \leq  \texttt{upperb} (I)_1\f]
     * -   and so forth.
     *
     * That is, dst (I) is set to 255 (all 1 -bits) if src (I) is within the
     * specified 1D, 2D, 3D, ... box and 0 otherwise.
     *
     * When the lower and/or upper boundary parameters are scalars, the indexes
     * (I) at lowerb and upperb in the above formulas should be omitted.
     * @param src first input array.
     * @param lowerb inclusive lower boundary array or a scalar.
     * @param upperb inclusive upper boundary array or a scalar.
     * @param dst output array of the same size as src and CV_8U type.
     */
    function inRange(
        src: Mat,
        lowerb: Mat | ScalarLike | number[],
        upperb: Mat | ScalarLike | number[],
        dst: Mat
    ): void;

    /**
     * @brief Computes the undistortion and rectification transformation map.
     *
     * The function computes the joint undistortion and rectification transformation and represents the
     * result in the form of maps for remap. The undistorted image looks like original, as if it is
     * captured with a camera using the camera matrix =newCameraMatrix and zero distortion. In case of a
     * monocular camera, newCameraMatrix is usually equal to cameraMatrix, or it can be computed by
     * #getOptimalNewCameraMatrix for a better control over scaling. In case of a stereo camera,
     * newCameraMatrix is normally set to P1 or P2 computed by #stereoRectify .
     *
     * Also, this new camera is oriented differently in the coordinate space, according to R. That, for
     * example, helps to align two heads of a stereo camera so that the epipolar lines on both images
     * become horizontal and have the same y- coordinate (in case of a horizontally aligned stereo camera).
     *
     * The function actually builds the maps for the inverse mapping algorithm that is used by remap. That
     * is, for each pixel \f$(u, v)\f$ in the destination (corrected and rectified) image, the function
     * computes the corresponding coordinates in the source image (that is, in the original image from
     * camera). The following process is applied:
     * \f[
     * \begin{array}{l}
     * x  \leftarrow (u - {c'}_x)/{f'}_x  \\
     * y  \leftarrow (v - {c'}_y)/{f'}_y  \\
     * {[X\,Y\,W]} ^T  \leftarrow R^{-1}*[x \, y \, 1]^T  \\
     * x'  \leftarrow X/W  \\
     * y'  \leftarrow Y/W  \\
     * r^2  \leftarrow x'^2 + y'^2 \\
     * x''  \leftarrow x' \frac{1 + k_1 r^2 + k_2 r^4 + k_3 r^6}{1 + k_4 r^2 + k_5 r^4 + k_6 r^6}
     * + 2p_1 x' y' + p_2(r^2 + 2 x'^2)  + s_1 r^2 + s_2 r^4\\
     * y''  \leftarrow y' \frac{1 + k_1 r^2 + k_2 r^4 + k_3 r^6}{1 + k_4 r^2 + k_5 r^4 + k_6 r^6}
     * + p_1 (r^2 + 2 y'^2) + 2 p_2 x' y' + s_3 r^2 + s_4 r^4 \\
     * s\vecthree{x'''}{y'''}{1} =
     * \vecthreethree{R_{33}(\tau_x, \tau_y)}{0}{-R_{13}((\tau_x, \tau_y)}
     * {0}{R_{33}(\tau_x, \tau_y)}{-R_{23}(\tau_x, \tau_y)}
     * {0}{0}{1} R(\tau_x, \tau_y) \vecthree{x''}{y''}{1}\\
     * map_x(u,v)  \leftarrow x''' f_x + c_x  \\
     * map_y(u,v)  \leftarrow y''' f_y + c_y
     * \end{array}
     * \f]
     * where \f$(k_1, k_2, p_1, p_2[, k_3[, k_4, k_5, k_6[, s_1, s_2, s_3, s_4[, \tau_x, \tau_y]]]])\f$
     * are the distortion coefficients.
     *
     * In case of a stereo camera, this function is called twice: once for each camera head, after
     * stereoRectify, which in its turn is called after #stereoCalibrate. But if the stereo camera
     * was not calibrated, it is still possible to compute the rectification transformations directly from
     * the fundamental matrix using #stereoRectifyUncalibrated. For each camera, the function computes
     * homography H as the rectification transformation in a pixel domain, not a rotation matrix R in 3D
     * space. R can be computed from H as
     * \f[\texttt{R} = \texttt{cameraMatrix} ^{-1} \cdot \texttt{H} \cdot \texttt{cameraMatrix}\f]
     * where cameraMatrix can be chosen arbitrarily.
     *
     * @param cameraMatrix Input camera matrix \f$A=\vecthreethree{f_x}{0}{c_x}{0}{f_y}{c_y}{0}{0}{1}\f$ .
     * @param distCoeffs Input vector of distortion coefficients
     * \f$(k_1, k_2, p_1, p_2[, k_3[, k_4, k_5, k_6[, s_1, s_2, s_3, s_4[, \tau_x, \tau_y]]]])\f$
     * of 4, 5, 8, 12 or 14 elements. If the vector is NULL/empty, the zero distortion coefficients are assumed.
     * @param R Optional rectification transformation in the object space (3x3 matrix). R1 or R2 ,
     * computed by #stereoRectify can be passed here. If the matrix is empty, the identity transformation
     * is assumed. In cvInitUndistortMap R assumed to be an identity matrix.
     * @param newCameraMatrix New camera matrix \f$A'=\vecthreethree{f_x'}{0}{c_x'}{0}{f_y'}{c_y'}{0}{0}{1}\f$.
     * @param size Undistorted image size.
     * @param m1type Type of the first output map that can be CV_32FC1, CV_32FC2 or CV_16SC2, see #convertMaps
     * @param map1 The first output map.
     * @param map2 The second output map.
     */
    function initUndistortRectifyMap(
        cameraMatrix: Mat,
        distCoeffs: Mat,
        R: Mat,
        newCameraMatrix: Mat,
        size: SizeLike,
        m1type: int,
        map1: Mat,
        map2: Mat
    ): void;

    /**
     * @brief Restores the selected region in an image using the region neighborhood.
     *
     * @param src Input 8-bit, 16-bit unsigned or 32-bit float 1-channel or 8-bit 3-channel image.
     * @param inpaintMask Inpainting mask, 8-bit 1-channel image. Non-zero pixels indicate the area that
     * needs to be inpainted.
     * @param dst Output image with the same size and type as src .
     * @param inpaintRadius Radius of a circular neighborhood of each point inpainted that is considered
     * by the algorithm.
     * @param flags Inpainting method that could be cv::INPAINT_NS or cv::INPAINT_TELEA
     *
     * The function reconstructs the selected image area from the pixel near the area boundary. The
     * function may be used to remove dust and scratches from a scanned photo, or to remove undesirable
     * objects from still images or video. See <http://en.wikipedia.org/wiki/Inpainting> for more details.
     *
     * @note
     * -   An example using the inpainting technique can be found at
     * opencv_source_code/samples/cpp/inpaint.cpp
     * -   (Python) An example using the inpainting technique can be found at
     * opencv_source_code/samples/python/inpaint.py
     */
    function inpaint(src: Mat, inpaintMask: Mat, dst: Mat, inpaintRadius: double, flags: int): void;

    /**
     * @overload
     */
    function integral(src: Mat, sum: Mat, sdepth?: int): void;

    /**
     * @overload
     */
    function integral2(src: Mat, sum: Mat, sqsum: Mat, sdepth?: int, sqdepth?: int): void;

    /**
     * @brief Finds the inverse or pseudo-inverse of a matrix.
     *
     * The function cv::invert inverts the matrix src and stores the result in dst
     * . When the matrix src is singular or non-square, the function calculates
     * the pseudo-inverse matrix (the dst matrix) so that norm(src\*dst - I) is
     * minimal, where I is an identity matrix.
     *
     * In case of the #DECOMP_LU method, the function returns non-zero value if
     * the inverse has been successfully calculated and 0 if src is singular.
     *
     * In case of the #DECOMP_SVD method, the function returns the inverse
     * condition number of src (the ratio of the smallest singular value to the
     * largest singular value) and 0 if src is singular. The SVD method
     * calculates a pseudo-inverse matrix if src is singular.
     *
     * Similarly to #DECOMP_LU, the method #DECOMP_CHOLESKY works only with
     * non-singular square matrices that should also be symmetrical and
     * positively defined. In this case, the function stores the inverted
     * matrix in dst and returns non-zero. Otherwise, it returns 0.
     *
     * @param src input floating-point M x N matrix.
     * @param dst output matrix of N x M size and the same type as src.
     * @param flags inversion method (cv::DecompTypes)
     * @sa solve, SVD
     */
    function invert(src: Mat, dst: Mat, flags?: int): double;

    /**
     * @brief Tests a contour convexity.
     *
     * The function tests whether the input contour is convex or not. The contour must be simple, that is,
     * without self-intersections. Otherwise, the function output is undefined.
     *
     * @param contour Input vector of 2D points, stored in std::vector\<\> or Mat
     */
    function isContourConvex(contour: Mat): boolean;

    /**
     * @brief Finds centers of clusters and groups input samples around the clusters.
     *
     * The function kmeans implements a k-means algorithm that finds the centers of cluster_count clusters
     * and groups the input samples around the clusters. As an output, \f$\texttt{bestLabels}_i\f$ contains a
     * 0-based cluster index for the sample stored in the \f$i^{th}\f$ row of the samples matrix.
     *
     * @note
     * -   (Python) An example on K-means clustering can be found at
     * opencv_source_code/samples/python/kmeans.py
     * @param data Data for clustering. An array of N-Dimensional points with float coordinates is needed.
     * Examples of this array can be:
     * -   Mat points(count, 2, CV_32F);
     * -   Mat points(count, 1, CV_32FC2);
     * -   Mat points(1, count, CV_32FC2);
     * -   std::vector\<cv::Point2f\> points(sampleCount);
     * @param K Number of clusters to split the set by.
     * @param bestLabels Input/output integer array that stores the cluster indices for every sample.
     * @param criteria The algorithm termination criteria, that is, the maximum number of iterations and/or
     * the desired accuracy. The accuracy is specified as criteria.epsilon. As soon as each of the cluster
     * centers moves by less than criteria.epsilon on some iteration, the algorithm stops.
     * @param attempts Flag to specify the number of times the algorithm is executed using different
     * initial labellings. The algorithm returns the labels that yield the best compactness (see the last
     * function parameter).
     * @param flags Flag that can take values of cv::KmeansFlags
     * @param centers Output matrix of the cluster centers, one row per each cluster center.
     * @return The function returns the compactness measure that is computed as
     * \f[\sum _i  \| \texttt{samples} _i -  \texttt{centers} _{ \texttt{labels} _i} \| ^2\f]
     * after every attempt. The best (minimum) value is chosen and the corresponding labels and the
     * compactness value are returned by the function. Basically, you can use only the core of the
     * function, set the number of attempts to 1, initialize labels each time using a custom algorithm,
     * pass them with the ( flags = #KMEANS_USE_INITIAL_LABELS ) flag, and then choose the best
     * (most-compact) clustering.
     */
    function kmeans(
        data: Mat,
        K: int,
        bestLabels: Mat,
        criteria: TermCriteriaLike,
        attempts: int,
        flags: int,
        centers?: Mat
    ): double;

    /**
     * @brief Draws a line segment connecting two points.
     *
     * The function line draws the line segment between pt1 and pt2 points in the image. The line is
     * clipped by the image boundaries. For non-antialiased lines with integer coordinates, the 8-connected
     * or 4-connected Bresenham algorithm is used. Thick lines are drawn with rounding endings. Antialiased
     * lines are drawn using Gaussian filtering.
     *
     * @param img Image.
     * @param pt1 First point of the line segment.
     * @param pt2 Second point of the line segment.
     * @param color Line color.
     * @param thickness Line thickness.
     * @param lineType Type of the line. See #LineTypes.
     * @param shift Number of fractional bits in the point coordinates.
     */
    function line(
        img: Mat,
        pt1: PointLike,
        pt2: PointLike,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        shift?: int
    ): void;

    /**
     * @brief Calculates the natural logarithm of every array element.
     *
     * The function cv::log calculates the natural logarithm of every element of the input array:
     * \f[\texttt{dst} (I) =  \log (\texttt{src}(I)) \f]
     *
     * Output on zero, negative and special (NaN, Inf) values is undefined.
     *
     * @param src input array.
     * @param dst output array of the same size and type as src .
     * @sa exp, cartToPolar, polarToCart, phase, pow, sqrt, magnitude
     */
    function log(src: Mat, dst: Mat): void;

    /**
     * @brief Calculates the magnitude of 2D vectors.
     *
     * The function cv::magnitude calculates the magnitude of 2D vectors formed
     * from the corresponding elements of x and y arrays:
     * \f[\texttt{dst} (I) =  \sqrt{\texttt{x}(I)^2 + \texttt{y}(I)^2}\f]
     * @param x floating-point array of x-coordinates of the vectors.
     * @param y floating-point array of y-coordinates of the vectors; it must
     * have the same size as x.
     * @param magnitude output array of the same size and type as x.
     * @sa cartToPolar, polarToCart, phase, sqrt
     */
    function magnitude(x: Mat, y: Mat, magnitude: Mat): void;

    /**
     * @brief Compares two shapes.
     *
     * The function compares two shapes. All three implemented methods use the Hu invariants (see #HuMoments)
     *
     * @param contour1 First contour or grayscale image.
     * @param contour2 Second contour or grayscale image.
     * @param method Comparison method, see #ShapeMatchModes
     * @param parameter Method-specific parameter (not supported now).
     */
    function matchShapes(contour1: Mat, contour2: Mat, method: int, parameter: double): double;

    /**
     * @brief Compares a template against overlapped image regions.
     *
     * The function slides through image , compares the overlapped patches of size \f$w \times h\f$ against
     * templ using the specified method and stores the comparison results in result . #TemplateMatchModes
     * describes the formulae for the available comparison methods ( \f$I\f$ denotes image, \f$T\f$
     * template, \f$R\f$ result, \f$M\f$ the optional mask ). The summation is done over template and/or
     * the image patch: \f$x' = 0...w-1, y' = 0...h-1\f$
     *
     * After the function finishes the comparison, the best matches can be found as global minimums (when
     * #TM_SQDIFF was used) or maximums (when #TM_CCORR or #TM_CCOEFF was used) using the
     * #minMaxLoc function. In case of a color image, template summation in the numerator and each sum in
     * the denominator is done over all of the channels and separate mean values are used for each channel.
     * That is, the function can take a color template and a color image. The result will still be a
     * single-channel image, which is easier to analyze.
     *
     * @param image Image where the search is running. It must be 8-bit or 32-bit floating-point.
     * @param templ Searched template. It must be not greater than the source image and have the same
     * data type.
     * @param result Map of comparison results. It must be single-channel 32-bit floating-point. If image
     * is \f$W \times H\f$ and templ is \f$w \times h\f$ , then result is \f$(W-w+1) \times (H-h+1)\f$ .
     * @param method Parameter specifying the comparison method, see #TemplateMatchModes
     * @param mask Optional mask. It must have the same size as templ. It must either have the same number
     * of channels as template or only one channel, which is then used for all template and
     * image channels. If the data type is #CV_8U, the mask is interpreted as a binary mask,
     * meaning only elements where mask is nonzero are used and are kept unchanged independent
     * of the actual mask value (weight equals 1). For data tpye #CV_32F, the mask values are
     * used as weights. The exact formulas are documented in #TemplateMatchModes.
     */
    function matchTemplate(image: Mat, templ: Mat, result: Mat, method: int, mask?: Mat): void;

    /**
     * @brief Calculates per-element maximum of two arrays or an array and a scalar.
     *
     * The function cv::max calculates the per-element maximum of two arrays:
     * \f[\texttt{dst} (I)= \max ( \texttt{src1} (I), \texttt{src2} (I))\f]
     * or array and a scalar:
     * \f[\texttt{dst} (I)= \max ( \texttt{src1} (I), \texttt{value} )\f]
     * @param src1 first input array.
     * @param src2 second input array of the same size and type as src1 .
     * @param dst output array of the same size and type as src1.
     * @sa  min, compare, inRange, minMaxLoc, @ref MatrixExpressions
     */
    function max(src1: Mat, src2: Mat, dst: Mat): void;

    /**
     * @brief Calculates an average (mean) of array elements.
     *
     * The function cv::mean calculates the mean value M of array elements,
     * independently for each channel, and return it:
     * \f[\begin{array}{l} N =  \sum _{I: \; \texttt{mask} (I) \ne 0} 1 \\ M_c =  \left ( \sum _{I: \; \texttt{mask} (I) \ne 0}{ \texttt{mtx} (I)_c} \right )/N \end{array}\f]
     * When all the mask elements are 0's, the function returns Scalar::all(0)
     * @param src input array that should have from 1 to 4 channels so that the result can be stored in
     * Scalar_ .
     * @param mask optional operation mask.
     * @sa  countNonZero, meanStdDev, norm, minMaxLoc
     */
    function mean(src: Mat, mask?: Mat): ScalarLike;

    /**
     * Calculates a mean and standard deviation of array elements.
     *
     * The function cv::meanStdDev calculates the mean and the standard deviation M
     * of array elements independently for each channel and returns it via the
     * output parameters:
     * \f[\begin{array}{l} N =  \sum _{I, \texttt{mask} (I)  \ne 0} 1 \\ \texttt{mean} _c =  \frac{\sum_{ I: \; \texttt{mask}(I) \ne 0} \texttt{src} (I)_c}{N} \\ \texttt{stddev} _c =  \sqrt{\frac{\sum_{ I: \; \texttt{mask}(I) \ne 0} \left ( \texttt{src} (I)_c -  \texttt{mean} _c \right )^2}{N}} \end{array}\f]
     * When all the mask elements are 0's, the function returns
     * mean=stddev=Scalar::all(0).
     * @note The calculated standard deviation is only the diagonal of the
     * complete normalized covariance matrix. If the full matrix is needed, you
     * can reshape the multi-channel array M x N to the single-channel array
     * M\*N x mtx.channels() (only possible when the matrix is continuous) and
     * then pass the matrix to calcCovarMatrix .
     * @param src input array that should have from 1 to 4 channels so that the results can be stored in
     * Scalar_ 's.
     * @param mean output parameter: calculated mean value.
     * @param stddev output parameter: calculated standard deviation.
     * @param mask optional operation mask.
     * @sa  countNonZero, mean, norm, minMaxLoc, calcCovarMatrix
     */
    function meanStdDev(src: Mat, mean: Mat, stddev: Mat, mask?: Mat): void;

    /**
     * @brief Blurs an image using the median filter.
     *
     * The function smoothes an image using the median filter with the \f$\texttt{ksize} \times
     * \texttt{ksize}\f$ aperture. Each channel of a multi-channel image is processed independently.
     * In-place operation is supported.
     *
     * @note The median filter uses #BORDER_REPLICATE internally to cope with border pixels, see #BorderTypes
     *
     * @param src input 1-, 3-, or 4-channel image; when ksize is 3 or 5, the image depth should be
     * CV_8U, CV_16U, or CV_32F, for larger aperture sizes, it can only be CV_8U.
     * @param dst destination array of the same size and type as src.
     * @param ksize aperture linear size; it must be odd and greater than 1, for example: 3, 5, 7 ...
     * @sa  bilateralFilter, blur, boxFilter, GaussianBlur
     */
    function medianBlur(src: Mat, dst: Mat, ksize: int): void;

    /**
     * @overload
     * @param mv input vector of matrices to be merged; all the matrices in mv must have the same
     * size and the same depth.
     * @param dst output array of the same size and the same depth as mv[0]; The number of channels will
     * be the total number of channels in the matrix array.
     */
    function merge(mv: MatVector, dst: Mat): void;

    /**
     * @brief Calculates per-element minimum of two arrays or an array and a scalar.
     *
     * The function cv::min calculates the per-element minimum of two arrays:
     * \f[\texttt{dst} (I)= \min ( \texttt{src1} (I), \texttt{src2} (I))\f]
     * or array and a scalar:
     * \f[\texttt{dst} (I)= \min ( \texttt{src1} (I), \texttt{value} )\f]
     * @param src1 first input array.
     * @param src2 second input array of the same size and type as src1.
     * @param dst output array of the same size and type as src1.
     * @sa max, compare, inRange, minMaxLoc
     */
    function min(src1: Mat, src2: Mat, dst: Mat): void;

    /**
     * @brief Finds a rotated rectangle of the minimum area enclosing the input 2D point set.
     *
     * The function calculates and returns the minimum-area bounding rectangle (possibly rotated) for a
     * specified point set. Developer should keep in mind that the returned RotatedRect can contain negative
     * indices when data is close to the containing Mat element boundary.
     *
     * @param points Input vector of 2D points, stored in std::vector\<\> or Mat
     */
    function minAreaRect(points: Mat): RotatedRectLike;

    /**
     * @overload
     * @param src input array or vector of matrices; all of the matrices must have the same size and the
     * same depth.
     * @param dst output array or vector of matrices; all the matrices **must be allocated**; their size and
     * depth must be the same as in src[0].
     * @param fromTo array of index pairs specifying which channels are copied and where; fromTo[k\*2] is
     * a 0-based index of the input channel in src, fromTo[k\*2+1] is an index of the output channel in
     * dst; the continuous channel numbering is used: the first input image channels are indexed from 0 to
     * src[0].channels()-1, the second input image channels are indexed from src[0].channels() to
     * src[0].channels() + src[1].channels()-1, and so on, the same scheme is used for the output image
     * channels; as a special case, when fromTo[k\*2] is negative, the corresponding output channel is
     * filled with zero .
     */
    function mixChannels(src: MatVector, dst: MatVector, fromTo: IntVector | int[]): void;

    /**
     * @brief Calculates all of the moments up to the third order of a polygon or rasterized shape.
     *
     * The function computes moments, up to the 3rd order, of a vector shape or a rasterized shape. The
     * results are returned in the structure cv::Moments.
     *
     * @param array Raster image (single-channel, 8-bit or floating-point 2D array) or an array (
     * \f$1 \times N\f$ or \f$N \times 1\f$ ) of 2D points (Point or Point2f ).
     * @param binaryImage If it is true, all non-zero image pixels are treated as 1's. The parameter is
     * used for images only.
     * @returns moments.
     *
     * @note Only applicable to contour moments calculations from Python bindings: Note that the numpy
     * type for the input array should be either np.int32 or np.float32.
     *
     * @sa  contourArea, arcLength
     */
    function moments(array: Mat, binaryImage?: boolean): MomentsLike;

    /**
     * @brief Performs advanced morphological transformations.
     *
     * The function cv::morphologyEx can perform advanced morphological transformations using an erosion and dilation as
     * basic operations.
     *
     * Any of the operations can be done in-place. In case of multi-channel images, each channel is
     * processed independently.
     *
     * @param src Source image. The number of channels can be arbitrary. The depth should be one of
     * CV_8U, CV_16U, CV_16S, CV_32F or CV_64F.
     * @param dst Destination image of the same size and type as source image.
     * @param op Type of a morphological operation, see #MorphTypes
     * @param kernel Structuring element. It can be created using #getStructuringElement.
     * @param anchor Anchor position with the kernel. Negative values mean that the anchor is at the
     * kernel center.
     * @param iterations Number of times erosion and dilation are applied.
     * @param borderType Pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @param borderValue Border value in case of a constant border. The default value has a special
     * meaning.
     * @sa  dilate, erode, getStructuringElement
     * @note The number of iterations is the number of times erosion or dilatation operation will be applied.
     * For instance, an opening operation (#MORPH_OPEN) with two iterations is equivalent to apply
     * successively: erode -> erode -> dilate -> dilate (and not erode -> dilate -> erode -> dilate).
     */
    function morphologyEx(
        src: Mat,
        dst: Mat,
        op: int,
        kernel: Mat,
        anchor?: PointLike,
        iterations?: int,
        borderType?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * @brief Calculates the per-element scaled product of two arrays.
     *
     * The function multiply calculates the per-element product of two arrays:
     *
     * \f[\texttt{dst} (I)= \texttt{saturate} ( \texttt{scale} \cdot \texttt{src1} (I)  \cdot \texttt{src2} (I))\f]
     *
     * There is also a @ref MatrixExpressions -friendly variant of the first function. See Mat::mul .
     *
     * For a not-per-element matrix product, see gemm .
     *
     * @note Saturation is not applied when the output array has the depth
     * CV_32S. You may even get result of an incorrect sign in the case of
     * overflow.
     * @param src1 first input array.
     * @param src2 second input array of the same size and the same type as src1.
     * @param dst output array of the same size and type as src1.
     * @param scale optional scale factor.
     * @param dtype optional depth of the output array
     * @sa add, subtract, divide, scaleAdd, addWeighted, accumulate, accumulateProduct, accumulateSquare,
     * Mat::convertTo
     */
    function multiply(src1: Mat, src2: Mat, dst: Mat, scale?: double, dtype?: int): void;

    /**
     * @brief Calculates the  absolute norm of an array.
     *
     * This version of #norm calculates the absolute norm of src1. The type of norm to calculate is specified using #NormTypes.
     *
     * As example for one array consider the function \f$r(x)= \begin{pmatrix} x \\ 1-x \end{pmatrix}, x \in [-1;1]\f$.
     * The \f$ L_{1}, L_{2} \f$ and \f$ L_{\infty} \f$ norm for the sample value \f$r(-1) = \begin{pmatrix} -1 \\ 2 \end{pmatrix}\f$
     * is calculated as follows
     * \f{align*}
     * \| r(-1) \|_{L_1} &= |-1| + |2| = 3 \\
     * \| r(-1) \|_{L_2} &= \sqrt{(-1)^{2} + (2)^{2}} = \sqrt{5} \\
     * \| r(-1) \|_{L_\infty} &= \max(|-1|,|2|) = 2
     * \f}
     * and for \f$r(0.5) = \begin{pmatrix} 0.5 \\ 0.5 \end{pmatrix}\f$ the calculation is
     * \f{align*}
     * \| r(0.5) \|_{L_1} &= |0.5| + |0.5| = 1 \\
     * \| r(0.5) \|_{L_2} &= \sqrt{(0.5)^{2} + (0.5)^{2}} = \sqrt{0.5} \\
     * \| r(0.5) \|_{L_\infty} &= \max(|0.5|,|0.5|) = 0.5.
     * \f}
     * The following graphic shows all values for the three norm functions \f$\| r(x) \|_{L_1}, \| r(x) \|_{L_2}\f$ and \f$\| r(x) \|_{L_\infty}\f$.
     * It is notable that the \f$ L_{1} \f$ norm forms the upper and the \f$ L_{\infty} \f$ norm forms the lower border for the example function \f$ r(x) \f$.
     * ![Graphs for the different norm functions from the above example](pics/NormTypes_OneArray_1-2-INF.png)
     *
     * When the mask parameter is specified and it is not empty, the norm is
     *
     * If normType is not specified, #NORM_L2 is used.
     * calculated only over the region specified by the mask.
     *
     * Multi-channel input arrays are treated as single-channel arrays, that is,
     * the results for all channels are combined.
     *
     * Hamming norms can only be calculated with CV_8U depth arrays.
     *
     * @param src1 first input array.
     * @param normType type of the norm (see #NormTypes).
     * @param mask optional operation mask; it must have the same size as src1 and CV_8UC1 type.
     */
    function norm(src1: Mat, normType?: int, mask?: Mat): double;

    /**
     * @brief Calculates an absolute difference norm or a relative difference norm.
     *
     * This version of cv::norm calculates the absolute difference norm
     * or the relative difference norm of arrays src1 and src2.
     * The type of norm to calculate is specified using #NormTypes.
     *
     * @param src1 first input array.
     * @param src2 second input array of the same size and the same type as src1.
     * @param normType type of the norm (see #NormTypes).
     * @param mask optional operation mask; it must have the same size as src1 and CV_8UC1 type.
     */
    function norm(src1: Mat, src2: Mat, normType?: int, mask?: Mat): double;

    /**
     * @brief Normalizes the norm or value range of an array.
     *
     * The function cv::normalize normalizes scale and shift the input array elements so that
     * \f[\| \texttt{dst} \| _{L_p}= \texttt{alpha}\f]
     * (where p=Inf, 1 or 2) when normType=NORM_INF, NORM_L1, or NORM_L2, respectively; or so that
     * \f[\min _I  \texttt{dst} (I)= \texttt{alpha} , \, \, \max _I  \texttt{dst} (I)= \texttt{beta}\f]
     *
     * when normType=NORM_MINMAX (for dense arrays only). The optional mask specifies a sub-array to be
     * normalized. This means that the norm or min-n-max are calculated over the sub-array, and then this
     * sub-array is modified to be normalized. If you want to only use the mask to calculate the norm or
     * min-max but modify the whole array, you can use norm and Mat::convertTo.
     *
     * In case of sparse matrices, only the non-zero values are analyzed and transformed. Because of this,
     * the range transformation for sparse matrices is not allowed since it can shift the zero level.
     *
     * Possible usage with some positive example data:
     * @code{.cpp}
     * vector<double> positiveData = { 2.0, 8.0, 10.0 };
     * vector<double> normalizedData_l1, normalizedData_l2, normalizedData_inf, normalizedData_minmax;
     *
     * // Norm to probability (total count)
     * // sum(numbers) = 20.0
     * // 2.0      0.1     (2.0/20.0)
     * // 8.0      0.4     (8.0/20.0)
     * // 10.0     0.5     (10.0/20.0)
     * normalize(positiveData, normalizedData_l1, 1.0, 0.0, NORM_L1);
     *
     * // Norm to unit vector: ||positiveData|| = 1.0
     * // 2.0      0.15
     * // 8.0      0.62
     * // 10.0     0.77
     * normalize(positiveData, normalizedData_l2, 1.0, 0.0, NORM_L2);
     *
     * // Norm to max element
     * // 2.0      0.2     (2.0/10.0)
     * // 8.0      0.8     (8.0/10.0)
     * // 10.0     1.0     (10.0/10.0)
     * normalize(positiveData, normalizedData_inf, 1.0, 0.0, NORM_INF);
     *
     * // Norm to range [0.0;1.0]
     * // 2.0      0.0     (shift to left border)
     * // 8.0      0.75    (6.0/8.0)
     * // 10.0     1.0     (shift to right border)
     * normalize(positiveData, normalizedData_minmax, 1.0, 0.0, NORM_MINMAX);
     * @endcode
     *
     * @param src input array.
     * @param dst output array of the same size as src .
     * @param alpha norm value to normalize to or the lower range boundary in case of the range
     * normalization.
     * @param beta upper range boundary in case of the range normalization; it is not used for the norm
     * normalization.
     * @param norm_type normalization type (see cv::NormTypes).
     * @param dtype when negative, the output array has the same type as src; otherwise, it has the same
     * number of channels as src and the depth =CV_MAT_DEPTH(dtype).
     * @param mask optional operation mask.
     * @sa norm, Mat::convertTo, SparseMat::convertTo
     */
    function normalize(
        src: Mat,
        dst: Mat,
        alpha?: double,
        beta?: double,
        norm_type?: int,
        dtype?: int,
        mask?: Mat
    ): void;

    /**
     * @brief Performs the perspective matrix transformation of vectors.
     *
     * The function cv::perspectiveTransform transforms every element of src by
     * treating it as a 2D or 3D vector, in the following way:
     * \f[(x, y, z)  \rightarrow (x'/w, y'/w, z'/w)\f]
     * where
     * \f[(x', y', z', w') =  \texttt{mat} \cdot \begin{bmatrix} x & y & z & 1  \end{bmatrix}\f]
     * and
     * \f[w =  \fork{w'}{if \(w' \ne 0\)}{\infty}{otherwise}\f]
     *
     * Here a 3D vector transformation is shown. In case of a 2D vector
     * transformation, the z component is omitted.
     *
     * @note The function transforms a sparse set of 2D or 3D vectors. If you
     * want to transform an image using perspective transformation, use
     * warpPerspective . If you have an inverse problem, that is, you want to
     * compute the most probable perspective transformation out of several
     * pairs of corresponding points, you can use getPerspectiveTransform or
     * findHomography .
     * @param src input two-channel or three-channel floating-point array; each
     * element is a 2D/3D vector to be transformed.
     * @param dst output array of the same size and type as src.
     * @param m 3x3 or 4x4 floating-point transformation matrix.
     * @sa  transform, warpPerspective, getPerspectiveTransform, findHomography
     */
    function perspectiveTransform(src: Mat, dst: Mat, m: Mat): void;

    /**
     * @brief Performs a point-in-contour test.
     *
     * The function determines whether the point is inside a contour, outside, or lies on an edge (or
     * coincides with a vertex). It returns positive (inside), negative (outside), or zero (on an edge)
     * value, correspondingly. When measureDist=false , the return value is +1, -1, and 0, respectively.
     * Otherwise, the return value is a signed distance between the point and the nearest contour edge.
     *
     * See below a sample output of the function where each image pixel is tested against the contour:
     *
     * ![sample output](pics/pointpolygon.png)
     *
     * @param contour Input contour.
     * @param pt Point tested against the contour.
     * @param measureDist If true, the function estimates the signed distance from the point to the
     * nearest contour edge. Otherwise, the function only checks if the point is inside a contour or not.
     */
    function pointPolygonTest(contour: Mat, pt: Point2fLike, measureDist: boolean): double;

    /**
     * @brief Calculates x and y coordinates of 2D vectors from their magnitude and angle.
     *
     * The function cv::polarToCart calculates the Cartesian coordinates of each 2D
     * vector represented by the corresponding elements of magnitude and angle:
     * \f[\begin{array}{l} \texttt{x} (I) =  \texttt{magnitude} (I) \cos ( \texttt{angle} (I)) \\ \texttt{y} (I) =  \texttt{magnitude} (I) \sin ( \texttt{angle} (I)) \\ \end{array}\f]
     *
     * The relative accuracy of the estimated coordinates is about 1e-6.
     * @param magnitude input floating-point array of magnitudes of 2D vectors;
     * it can be an empty matrix (=Mat()), in this case, the function assumes
     * that all the magnitudes are =1; if it is not empty, it must have the
     * same size and type as angle.
     * @param angle input floating-point array of angles of 2D vectors.
     * @param x output array of x-coordinates of 2D vectors; it has the same
     * size and type as angle.
     * @param y output array of y-coordinates of 2D vectors; it has the same
     * size and type as angle.
     * @param angleInDegrees when true, the input angles are measured in
     * degrees, otherwise, they are measured in radians.
     * @sa cartToPolar, magnitude, phase, exp, log, pow, sqrt
     */
    function polarToCart(magnitude: Mat, angle: Mat, x: Mat, y: Mat, angleInDegrees?: boolean): void;

    /**
     * @brief Draws several polygonal curves.
     *
     * @param img Image.
     * @param pts Array of polygonal curves.
     * @param isClosed Flag indicating whether the drawn polylines are closed or not. If they are closed,
     * the function draws a line from the last vertex of each curve to its first vertex.
     * @param color Polyline color.
     * @param thickness Thickness of the polyline edges.
     * @param lineType Type of the line segments. See #LineTypes
     * @param shift Number of fractional bits in the vertex coordinates.
     *
     * The function cv::polylines draws one or more polygonal curves.
     */
    function polylines(
        img: Mat,
        pts: MatVector,
        isClosed: boolean,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        shift?: int
    ): void;

    /**
     * @brief Raises every array element to a power.
     *
     * The function cv::pow raises every element of the input array to power :
     * \f[\texttt{dst} (I) =  \fork{\texttt{src}(I)^{power}}{if \(\texttt{power}\) is integer}{|\texttt{src}(I)|^{power}}{otherwise}\f]
     *
     * So, for a non-integer power exponent, the absolute values of input array
     * elements are used. However, it is possible to get true values for
     * negative values using some extra operations. In the example below,
     * computing the 5th root of array src shows:
     * @code{.cpp}
     * Mat mask = src < 0;
     * pow(src, 1./5, dst);
     * subtract(Scalar::all(0), dst, dst, mask);
     * @endcode
     * For some values of power, such as integer values, 0.5 and -0.5,
     * specialized faster algorithms are used.
     *
     * Special values (NaN, Inf) are not handled.
     * @param src input array.
     * @param power exponent of power.
     * @param dst output array of the same size and type as src.
     * @sa sqrt, exp, log, cartToPolar, polarToCart
     */
    function pow(src: Mat, power: double, dst: Mat): void;

    /**
     * @brief Draws a text string.
     *
     * The function cv::putText renders the specified text string in the image. Symbols that cannot be rendered
     * using the specified font are replaced by question marks. See #getTextSize for a text rendering code
     * example.
     *
     * @param img Image.
     * @param text Text string to be drawn.
     * @param org Bottom-left corner of the text string in the image.
     * @param fontFace Font type, see #HersheyFonts.
     * @param fontScale Font scale factor that is multiplied by the font-specific base size.
     * @param color Text color.
     * @param thickness Thickness of the lines used to draw a text.
     * @param lineType Line type. See #LineTypes
     * @param bottomLeftOrigin When true, the image data origin is at the bottom-left corner. Otherwise,
     * it is at the top-left corner.
     */
    function putText(
        img: Mat,
        text: string,
        org: PointLike,
        fontFace: int,
        fontScale: double,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        bottomLeftOrigin?: boolean
    ): void;

    /**
     * @brief Blurs an image and downsamples it.
     *
     * By default, size of the output image is computed as `Size((src.cols+1)/2, (src.rows+1)/2)`, but in
     * any case, the following conditions should be satisfied:
     *
     * \f[\begin{array}{l} | \texttt{dstsize.width} *2-src.cols| \leq 2 \\ | \texttt{dstsize.height} *2-src.rows| \leq 2 \end{array}\f]
     *
     * The function performs the downsampling step of the Gaussian pyramid construction. First, it
     * convolves the source image with the kernel:
     *
     * \f[\frac{1}{256} \begin{bmatrix} 1 & 4 & 6 & 4 & 1  \\ 4 & 16 & 24 & 16 & 4  \\ 6 & 24 & 36 & 24 & 6  \\ 4 & 16 & 24 & 16 & 4  \\ 1 & 4 & 6 & 4 & 1 \end{bmatrix}\f]
     *
     * Then, it downsamples the image by rejecting even rows and columns.
     *
     * @param src input image.
     * @param dst output image; it has the specified size and the same type as src.
     * @param dstsize size of the output image.
     * @param borderType Pixel extrapolation method, see #BorderTypes (#BORDER_CONSTANT isn't supported)
     */
    function pyrDown(src: Mat, dst: Mat, dstsize?: SizeLike, borderType?: int): void;

    /**
     * @brief Upsamples an image and then blurs it.
     *
     * By default, size of the output image is computed as `Size(src.cols\*2, (src.rows\*2)`, but in any
     * case, the following conditions should be satisfied:
     *
     * \f[\begin{array}{l} | \texttt{dstsize.width} -src.cols*2| \leq  ( \texttt{dstsize.width}   \mod  2)  \\ | \texttt{dstsize.height} -src.rows*2| \leq  ( \texttt{dstsize.height}   \mod  2) \end{array}\f]
     *
     * The function performs the upsampling step of the Gaussian pyramid construction, though it can
     * actually be used to construct the Laplacian pyramid. First, it upsamples the source image by
     * injecting even zero rows and columns and then convolves the result with the same kernel as in
     * pyrDown multiplied by 4.
     *
     * @param src input image.
     * @param dst output image. It has the specified size and the same type as src .
     * @param dstsize size of the output image.
     * @param borderType Pixel extrapolation method, see #BorderTypes (only #BORDER_DEFAULT is supported)
     */
    function pyrUp(src: Mat, dst: Mat, dstsize?: SizeLike, borderType?: int): void;

    /**
     * @brief Fills the array with normally distributed random numbers.
     *
     * The function cv::randn fills the matrix dst with normally distributed random numbers with the specified
     * mean vector and the standard deviation matrix. The generated random numbers are clipped to fit the
     * value range of the output array data type.
     * @param dst output array of random numbers; the array must be pre-allocated and have 1 to 4 channels.
     * @param mean mean value (expectation) of the generated random numbers.
     * @param stddev standard deviation of the generated random numbers; it can be either a vector (in
     * which case a diagonal standard deviation matrix is assumed) or a square matrix.
     * @sa RNG, randu
     */
    function randn(dst: Mat, mean: Mat, stddev: Mat): void;

    /**
     * @brief Generates a single uniformly-distributed random number or an array of random numbers.
     *
     * Non-template variant of the function fills the matrix dst with uniformly-distributed
     * random numbers from the specified range:
     * \f[\texttt{low} _c  \leq \texttt{dst} (I)_c <  \texttt{high} _c\f]
     * @param dst output array of random numbers; the array must be pre-allocated.
     * @param low inclusive lower boundary of the generated random numbers.
     * @param high exclusive upper boundary of the generated random numbers.
     * @sa RNG, randn, theRNG
     */
    function randu(dst: Mat, low: Mat, high: Mat): void;

    /**
     * @brief Draws a simple, thick, or filled up-right rectangle.
     *
     * The function cv::rectangle draws a rectangle outline or a filled rectangle whose two opposite corners
     * are pt1 and pt2.
     *
     * @param img Image.
     * @param pt1 Vertex of the rectangle.
     * @param pt2 Vertex of the rectangle opposite to pt1 .
     * @param color Rectangle color or brightness (grayscale image).
     * @param thickness Thickness of lines that make up the rectangle. Negative values, like #FILLED,
     * mean that the function has to draw a filled rectangle.
     * @param lineType Type of the line. See #LineTypes
     * @param shift Number of fractional bits in the point coordinates.
     */
    function rectangle(
        img: Mat,
        pt1: PointLike,
        pt2: PointLike,
        color: ScalarLike,
        thickness?: int,
        lineType?: int,
        shift?: int
    ): void;

    /**
     * @overload
     *
     * use `rec` parameter as alternative specification of the drawn rectangle: `r.tl() and
     * r.br()-Point(1,1)` are opposite corners
     */
    function rectangle(img: Mat, rec: RectLike, color: ScalarLike, thickness?: int, lineType?: int, shift?: int): void;

    /**
     * @brief Reduces a matrix to a vector.
     *
     * The function #reduce reduces the matrix to a vector by treating the matrix rows/columns as a set of
     * 1D vectors and performing the specified operation on the vectors until a single row/column is
     * obtained. For example, the function can be used to compute horizontal and vertical projections of a
     * raster image. In case of #REDUCE_MAX and #REDUCE_MIN , the output image should have the same type as the source one.
     * In case of #REDUCE_SUM and #REDUCE_AVG , the output may have a larger element bit-depth to preserve accuracy.
     * And multi-channel arrays are also supported in these two reduction modes.
     *
     * The following code demonstrates its usage for a single channel matrix.
     * @snippet snippets/core_reduce.cpp example
     *
     * And the following code demonstrates its usage for a two-channel matrix.
     * @snippet snippets/core_reduce.cpp example2
     *
     * @param src input 2D matrix.
     * @param dst output vector. Its size and type is defined by dim and dtype parameters.
     * @param dim dimension index along which the matrix is reduced. 0 means that the matrix is reduced to
     * a single row. 1 means that the matrix is reduced to a single column.
     * @param rtype reduction operation that could be one of #ReduceTypes
     * @param dtype when negative, the output vector will have the same type as the input matrix,
     * otherwise, its type will be CV_MAKE_TYPE(CV_MAT_DEPTH(dtype), src.channels()).
     * @sa repeat
     */
    function reduce(src: Mat, dst: Mat, dim: int, rtype: int, dtype?: int): void;

    /**
     * @brief Applies a generic geometrical transformation to an image.
     *
     * The function remap transforms the source image using the specified map:
     *
     * \f[\texttt{dst} (x,y) =  \texttt{src} (map_x(x,y),map_y(x,y))\f]
     *
     * where values of pixels with non-integer coordinates are computed using one of available
     * interpolation methods. \f$map_x\f$ and \f$map_y\f$ can be encoded as separate floating-point maps
     * in \f$map_1\f$ and \f$map_2\f$ respectively, or interleaved floating-point maps of \f$(x,y)\f$ in
     * \f$map_1\f$, or fixed-point maps created by using convertMaps. The reason you might want to
     * convert from floating to fixed-point representations of a map is that they can yield much faster
     * (\~2x) remapping operations. In the converted case, \f$map_1\f$ contains pairs (cvFloor(x),
     * cvFloor(y)) and \f$map_2\f$ contains indices in a table of interpolation coefficients.
     *
     * This function cannot operate in-place.
     *
     * @param src Source image.
     * @param dst Destination image. It has the same size as map1 and the same type as src .
     * @param map1 The first map of either (x,y) points or just x values having the type CV_16SC2 ,
     * CV_32FC1, or CV_32FC2. See convertMaps for details on converting a floating point
     * representation to fixed-point for speed.
     * @param map2 The second map of y values having the type CV_16UC1, CV_32FC1, or none (empty map
     * if map1 is (x,y) points), respectively.
     * @param interpolation Interpolation method (see #InterpolationFlags). The methods #INTER_AREA
     * and #INTER_LINEAR_EXACT are not supported by this function.
     * @param borderMode Pixel extrapolation method (see #BorderTypes). When
     * borderMode=#BORDER_TRANSPARENT, it means that the pixels in the destination image that
     * corresponds to the "outliers" in the source image are not modified by the function.
     * @param borderValue Value used in case of a constant border. By default, it is 0.
     * @note
     * Due to current implementation limitations the size of an input and output images should be less than 32767x32767.
     */
    function remap(
        src: Mat,
        dst: Mat,
        map1: Mat,
        map2: Mat,
        interpolation: int,
        borderMode?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * @brief Fills the output array with repeated copies of the input array.
     *
     * The function cv::repeat duplicates the input array one or more times along each of the two axes:
     * \f[\texttt{dst} _{ij}= \texttt{src} _{i\mod src.rows, \; j\mod src.cols }\f]
     * The second variant of the function is more convenient to use with @ref MatrixExpressions.
     * @param src input array to replicate.
     * @param ny Flag to specify how many times the `src` is repeated along the
     * vertical axis.
     * @param nx Flag to specify how many times the `src` is repeated along the
     * horizontal axis.
     * @param dst output array of the same type as `src`.
     * @sa cv::reduce
     */
    function repeat(src: Mat, ny: int, nx: int, dst: Mat): void;

    /**
     * @brief Resizes an image.
     *
     * The function resize resizes the image src down to or up to the specified size. Note that the
     * initial dst type or size are not taken into account. Instead, the size and type are derived from
     * the `src`,`dsize`,`fx`, and `fy`. If you want to resize src so that it fits the pre-created dst,
     * you may call the function as follows:
     * @code
     * // explicitly specify dsize=dst.size(); fx and fy will be computed from that.
     * resize(src, dst, dst.size(), 0, 0, interpolation);
     * @endcode
     * If you want to decimate the image by factor of 2 in each direction, you can call the function this
     * way:
     * @code
     * // specify fx and fy and let the function compute the destination image size.
     * resize(src, dst, Size(), 0.5, 0.5, interpolation);
     * @endcode
     * To shrink an image, it will generally look best with #INTER_AREA interpolation, whereas to
     * enlarge an image, it will generally look best with c#INTER_CUBIC (slow) or #INTER_LINEAR
     * (faster but still looks OK).
     *
     * @param src input image.
     * @param dst output image; it has the size dsize (when it is non-zero) or the size computed from
     * src.size(), fx, and fy; the type of dst is the same as of src.
     * @param dsize output image size; if it equals zero, it is computed as:
     * \f[\texttt{dsize = Size(round(fx*src.cols), round(fy*src.rows))}\f]
     * Either dsize or both fx and fy must be non-zero.
     * @param fx scale factor along the horizontal axis; when it equals 0, it is computed as
     * \f[\texttt{(double)dsize.width/src.cols}\f]
     * @param fy scale factor along the vertical axis; when it equals 0, it is computed as
     * \f[\texttt{(double)dsize.height/src.rows}\f]
     * @param interpolation interpolation method, see #InterpolationFlags
     *
     * @sa  warpAffine, warpPerspective, remap
     */
    function resize(src: Mat, dst: Mat, dsize: SizeLike, fx?: double, fy?: double, interpolation?: int): void;

    /**
     * @brief Rotates a 2D array in multiples of 90 degrees.
     * The function cv::rotate rotates the array in one of three different ways:
     * Rotate by 90 degrees clockwise (rotateCode = ROTATE_90_CLOCKWISE).
     * Rotate by 180 degrees clockwise (rotateCode = ROTATE_180).
     * Rotate by 270 degrees clockwise (rotateCode = ROTATE_90_COUNTERCLOCKWISE).
     * @param src input array.
     * @param dst output array of the same type as src.  The size is the same with ROTATE_180,
     * and the rows and cols are switched for ROTATE_90_CLOCKWISE and ROTATE_90_COUNTERCLOCKWISE.
     * @param rotateCode an enum to specify how to rotate the array; see the enum #RotateFlags
     * @sa transpose , repeat , completeSymm, flip, RotateFlags
     */
    function rotate(src: Mat, dst: Mat, rotateCode: int): void;

    /**
     * @brief Applies a separable linear filter to an image.
     *
     * The function applies a separable linear filter to the image. That is, first, every row of src is
     * filtered with the 1D kernel kernelX. Then, every column of the result is filtered with the 1D
     * kernel kernelY. The final result shifted by delta is stored in dst .
     *
     * @param src Source image.
     * @param dst Destination image of the same size and the same number of channels as src .
     * @param ddepth Destination image depth, see @ref filter_depths "combinations"
     * @param kernelX Coefficients for filtering each row.
     * @param kernelY Coefficients for filtering each column.
     * @param anchor Anchor position within the kernel. The default value \f$(-1,-1)\f$ means that the anchor
     * is at the kernel center.
     * @param delta Value added to the filtered results before storing them.
     * @param borderType Pixel extrapolation method, see #BorderTypes. #BORDER_WRAP is not supported.
     * @sa  filter2D, Sobel, GaussianBlur, boxFilter, blur
     */
    function sepFilter2D(
        src: Mat,
        dst: Mat,
        ddepth: int,
        kernelX: Mat,
        kernelY: Mat,
        anchor?: PointLike,
        delta?: double,
        borderType?: int
    ): void;

    /**
     * @brief Initializes a scaled identity matrix.
     *
     * The function cv::setIdentity initializes a scaled identity matrix:
     * \f[\texttt{mtx} (i,j)= \fork{\texttt{value}}{ if \(i=j\)}{0}{otherwise}\f]
     *
     * The function can also be emulated using the matrix initializers and the
     * matrix expressions:
     * @code
     * Mat A = Mat::eye(4, 3, CV_32F)*5;
     * // A will be set to [[5, 0, 0], [0, 5, 0], [0, 0, 5], [0, 0, 0]]
     * @endcode
     * @param mtx matrix to initialize (not necessarily square).
     * @param s value to assign to diagonal elements.
     * @sa Mat::zeros, Mat::ones, Mat::setTo, Mat::operator=
     */
    function setIdentity(mtx: Mat, s?: ScalarLike): void;

    /**
     * @brief Sets state of default random number generator.
     *
     * The function cv::setRNGSeed sets state of default random number generator to custom value.
     * @param seed new state for default random number generator
     * @sa RNG, randu, randn
     */
    function setRNGSeed(seed: int): void;

    /**
     * @brief Solves one or more linear systems or least-squares problems.
     *
     * The function cv::solve solves a linear system or least-squares problem (the
     * latter is possible with SVD or QR methods, or by specifying the flag
     * #DECOMP_NORMAL ):
     * \f[\texttt{dst} =  \arg \min _X \| \texttt{src1} \cdot \texttt{X} -  \texttt{src2} \|\f]
     *
     * If #DECOMP_LU or #DECOMP_CHOLESKY method is used, the function returns 1
     * if src1 (or \f$\texttt{src1}^T\texttt{src1}\f$ ) is non-singular. Otherwise,
     * it returns 0. In the latter case, dst is not valid. Other methods find a
     * pseudo-solution in case of a singular left-hand side part.
     *
     * @note If you want to find a unity-norm solution of an under-defined
     * singular system \f$\texttt{src1}\cdot\texttt{dst}=0\f$ , the function solve
     * will not do the work. Use SVD::solveZ instead.
     *
     * @param src1 input matrix on the left-hand side of the system.
     * @param src2 input matrix on the right-hand side of the system.
     * @param dst output solution.
     * @param flags solution (matrix inversion) method (#DecompTypes)
     * @sa invert, SVD, eigen
     */
    function solve(src1: Mat, src2: Mat, dst: Mat, flags?: int): boolean;

    /**
     * @brief Finds an object pose from 3D-2D point correspondences.
     * This function returns the rotation and the translation vectors that transform a 3D point expressed in the object
     * coordinate frame to the camera coordinate frame, using different methods:
     * - P3P methods (@ref SOLVEPNP_P3P, @ref SOLVEPNP_AP3P): need 4 input points to return a unique solution.
     * - @ref SOLVEPNP_IPPE Input points must be >= 4 and object points must be coplanar.
     * - @ref SOLVEPNP_IPPE_SQUARE Special case suitable for marker pose estimation.
     * Number of input points must be 4. Object points must be defined in the following order:
     * - point 0: [-squareLength / 2,  squareLength / 2, 0]
     * - point 1: [ squareLength / 2,  squareLength / 2, 0]
     * - point 2: [ squareLength / 2, -squareLength / 2, 0]
     * - point 3: [-squareLength / 2, -squareLength / 2, 0]
     * - for all the other flags, number of input points must be >= 4 and object points can be in any configuration.
     *
     * @param objectPoints Array of object points in the object coordinate space, Nx3 1-channel or
     * 1xN/Nx1 3-channel, where N is the number of points. vector\<Point3d\> can be also passed here.
     * @param imagePoints Array of corresponding image points, Nx2 1-channel or 1xN/Nx1 2-channel,
     * where N is the number of points. vector\<Point2d\> can be also passed here.
     * @param cameraMatrix Input camera intrinsic matrix \f$\cameramatrix{A}\f$ .
     * @param distCoeffs Input vector of distortion coefficients
     * \f$\distcoeffs\f$. If the vector is NULL/empty, the zero distortion coefficients are
     * assumed.
     * @param rvec Output rotation vector (see @ref Rodrigues ) that, together with tvec, brings points from
     * the model coordinate system to the camera coordinate system.
     * @param tvec Output translation vector.
     * @param useExtrinsicGuess Parameter used for #SOLVEPNP_ITERATIVE. If true (1), the function uses
     * the provided rvec and tvec values as initial approximations of the rotation and translation
     * vectors, respectively, and further optimizes them.
     * @param flags Method for solving a PnP problem:
     * -   @ref SOLVEPNP_ITERATIVE Iterative method is based on a Levenberg-Marquardt optimization. In
     * this case the function finds such a pose that minimizes reprojection error, that is the sum
     * of squared distances between the observed projections imagePoints and the projected (using
     * @ref projectPoints ) objectPoints .
     * -   @ref SOLVEPNP_P3P Method is based on the paper of X.S. Gao, X.-R. Hou, J. Tang, H.-F. Chang
     * "Complete Solution Classification for the Perspective-Three-Point Problem" (@cite gao2003complete).
     * In this case the function requires exactly four object and image points.
     * -   @ref SOLVEPNP_AP3P Method is based on the paper of T. Ke, S. Roumeliotis
     * "An Efficient Algebraic Solution to the Perspective-Three-Point Problem" (@cite Ke17).
     * In this case the function requires exactly four object and image points.
     * -   @ref SOLVEPNP_EPNP Method has been introduced by F. Moreno-Noguer, V. Lepetit and P. Fua in the
     * paper "EPnP: Efficient Perspective-n-Point Camera Pose Estimation" (@cite lepetit2009epnp).
     * -   @ref SOLVEPNP_DLS **Broken implementation. Using this flag will fallback to EPnP.** \n
     * Method is based on the paper of J. Hesch and S. Roumeliotis.
     * "A Direct Least-Squares (DLS) Method for PnP" (@cite hesch2011direct).
     * -   @ref SOLVEPNP_UPNP **Broken implementation. Using this flag will fallback to EPnP.** \n
     * Method is based on the paper of A. Penate-Sanchez, J. Andrade-Cetto,
     * F. Moreno-Noguer. "Exhaustive Linearization for Robust Camera Pose and Focal Length
     * Estimation" (@cite penate2013exhaustive). In this case the function also estimates the parameters \f$f_x\f$ and \f$f_y\f$
     * assuming that both have the same value. Then the cameraMatrix is updated with the estimated
     * focal length.
     * -   @ref SOLVEPNP_IPPE Method is based on the paper of T. Collins and A. Bartoli.
     * "Infinitesimal Plane-Based Pose Estimation" (@cite Collins14). This method requires coplanar object points.
     * -   @ref SOLVEPNP_IPPE_SQUARE Method is based on the paper of Toby Collins and Adrien Bartoli.
     * "Infinitesimal Plane-Based Pose Estimation" (@cite Collins14). This method is suitable for marker pose estimation.
     * It requires 4 coplanar object points defined in the following order:
     * - point 0: [-squareLength / 2,  squareLength / 2, 0]
     * - point 1: [ squareLength / 2,  squareLength / 2, 0]
     * - point 2: [ squareLength / 2, -squareLength / 2, 0]
     * - point 3: [-squareLength / 2, -squareLength / 2, 0]
     * -   @ref SOLVEPNP_SQPNP Method is based on the paper "A Consistently Fast and Globally Optimal Solution to the
     * Perspective-n-Point Problem" by G. Terzakis and M.Lourakis (@cite Terzakis20). It requires 3 or more points.
     *
     *
     * The function estimates the object pose given a set of object points, their corresponding image
     * projections, as well as the camera intrinsic matrix and the distortion coefficients, see the figure below
     * (more precisely, the X-axis of the camera frame is pointing to the right, the Y-axis downward
     * and the Z-axis forward).
     *
     * ![](pnp.jpg)
     *
     * Points expressed in the world frame \f$ \bf{X}_w \f$ are projected into the image plane \f$ \left[ u, v \right] \f$
     * using the perspective projection model \f$ \Pi \f$ and the camera intrinsic parameters matrix \f$ \bf{A} \f$:
     *
     * \f[
     * \begin{align*}
     * \begin{bmatrix}
     * u \\
     * v \\
     * 1
     * \end{bmatrix} &=
     * \bf{A} \hspace{0.1em} \Pi \hspace{0.2em} ^{c}\bf{T}_w
     * \begin{bmatrix}
     * X_{w} \\
     * Y_{w} \\
     * Z_{w} \\
     * 1
     * \end{bmatrix} \\
     * \begin{bmatrix}
     * u \\
     * v \\
     * 1
     * \end{bmatrix} &=
     * \begin{bmatrix}
     * f_x & 0 & c_x \\
     * 0 & f_y & c_y \\
     * 0 & 0 & 1
     * \end{bmatrix}
     * \begin{bmatrix}
     * 1 & 0 & 0 & 0 \\
     * 0 & 1 & 0 & 0 \\
     * 0 & 0 & 1 & 0
     * \end{bmatrix}
     * \begin{bmatrix}
     * r_{11} & r_{12} & r_{13} & t_x \\
     * r_{21} & r_{22} & r_{23} & t_y \\
     * r_{31} & r_{32} & r_{33} & t_z \\
     * 0 & 0 & 0 & 1
     * \end{bmatrix}
     * \begin{bmatrix}
     * X_{w} \\
     * Y_{w} \\
     * Z_{w} \\
     * 1
     * \end{bmatrix}
     * \end{align*}
     * \f]
     *
     * The estimated pose is thus the rotation (`rvec`) and the translation (`tvec`) vectors that allow transforming
     * a 3D point expressed in the world frame into the camera frame:
     *
     * \f[
     * \begin{align*}
     * \begin{bmatrix}
     * X_c \\
     * Y_c \\
     * Z_c \\
     * 1
     * \end{bmatrix} &=
     * \hspace{0.2em} ^{c}\bf{T}_w
     * \begin{bmatrix}
     * X_{w} \\
     * Y_{w} \\
     * Z_{w} \\
     * 1
     * \end{bmatrix} \\
     * \begin{bmatrix}
     * X_c \\
     * Y_c \\
     * Z_c \\
     * 1
     * \end{bmatrix} &=
     * \begin{bmatrix}
     * r_{11} & r_{12} & r_{13} & t_x \\
     * r_{21} & r_{22} & r_{23} & t_y \\
     * r_{31} & r_{32} & r_{33} & t_z \\
     * 0 & 0 & 0 & 1
     * \end{bmatrix}
     * \begin{bmatrix}
     * X_{w} \\
     * Y_{w} \\
     * Z_{w} \\
     * 1
     * \end{bmatrix}
     * \end{align*}
     * \f]
     *
     * @note
     * -   An example of how to use solvePnP for planar augmented reality can be found at
     * opencv_source_code/samples/python/plane_ar.py
     * -   If you are using Python:
     * - Numpy array slices won't work as input because solvePnP requires contiguous
     * arrays (enforced by the assertion using cv::Mat::checkVector() around line 55 of
     * modules/calib3d/src/solvepnp.cpp version 2.4.9)
     * - The P3P algorithm requires image points to be in an array of shape (N,1,2) due
     * to its calling of cv::undistortPoints (around line 75 of modules/calib3d/src/solvepnp.cpp version 2.4.9)
     * which requires 2-channel information.
     * - Thus, given some data D = np.array(...) where D.shape = (N,M), in order to use a subset of
     * it as, e.g., imagePoints, one must effectively copy it into a new array: imagePoints =
     * np.ascontiguousarray(D[:,:2]).reshape((N,1,2))
     * -   The methods @ref SOLVEPNP_DLS and @ref SOLVEPNP_UPNP cannot be used as the current implementations are
     * unstable and sometimes give completely wrong results. If you pass one of these two
     * flags, @ref SOLVEPNP_EPNP method will be used instead.
     * -   The minimum number of points is 4 in the general case. In the case of @ref SOLVEPNP_P3P and @ref SOLVEPNP_AP3P
     * methods, it is required to use exactly 4 points (the first 3 points are used to estimate all the solutions
     * of the P3P problem, the last one is used to retain the best solution that minimizes the reprojection error).
     * -   With @ref SOLVEPNP_ITERATIVE method and `useExtrinsicGuess=true`, the minimum number of points is 3 (3 points
     * are sufficient to compute a pose but there are up to 4 solutions). The initial solution should be close to the
     * global solution to converge.
     * -   With @ref SOLVEPNP_IPPE input points must be >= 4 and object points must be coplanar.
     * -   With @ref SOLVEPNP_IPPE_SQUARE this is a special case suitable for marker pose estimation.
     * Number of input points must be 4. Object points must be defined in the following order:
     * - point 0: [-squareLength / 2,  squareLength / 2, 0]
     * - point 1: [ squareLength / 2,  squareLength / 2, 0]
     * - point 2: [ squareLength / 2, -squareLength / 2, 0]
     * - point 3: [-squareLength / 2, -squareLength / 2, 0]
     * -  With @ref SOLVEPNP_SQPNP input points must be >= 3
     */
    function solvePnP(
        objectPoints: Mat,
        imagePoints: Mat,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvec: Mat,
        tvec: Mat,
        useExtrinsicGuess?: boolean,
        flags?: int
    ): boolean;

    /**
     * @brief Finds an object pose from 3D-2D point correspondences using the RANSAC scheme.
     *
     * @param objectPoints Array of object points in the object coordinate space, Nx3 1-channel or
     * 1xN/Nx1 3-channel, where N is the number of points. vector\<Point3d\> can be also passed here.
     * @param imagePoints Array of corresponding image points, Nx2 1-channel or 1xN/Nx1 2-channel,
     * where N is the number of points. vector\<Point2d\> can be also passed here.
     * @param cameraMatrix Input camera intrinsic matrix \f$\cameramatrix{A}\f$ .
     * @param distCoeffs Input vector of distortion coefficients
     * \f$\distcoeffs\f$. If the vector is NULL/empty, the zero distortion coefficients are
     * assumed.
     * @param rvec Output rotation vector (see @ref Rodrigues ) that, together with tvec, brings points from
     * the model coordinate system to the camera coordinate system.
     * @param tvec Output translation vector.
     * @param useExtrinsicGuess Parameter used for @ref SOLVEPNP_ITERATIVE. If true (1), the function uses
     * the provided rvec and tvec values as initial approximations of the rotation and translation
     * vectors, respectively, and further optimizes them.
     * @param iterationsCount Number of iterations.
     * @param reprojectionError Inlier threshold value used by the RANSAC procedure. The parameter value
     * is the maximum allowed distance between the observed and computed point projections to consider it
     * an inlier.
     * @param confidence The probability that the algorithm produces a useful result.
     * @param inliers Output vector that contains indices of inliers in objectPoints and imagePoints .
     * @param flags Method for solving a PnP problem (see @ref solvePnP ).
     *
     * The function estimates an object pose given a set of object points, their corresponding image
     * projections, as well as the camera intrinsic matrix and the distortion coefficients. This function finds such
     * a pose that minimizes reprojection error, that is, the sum of squared distances between the observed
     * projections imagePoints and the projected (using @ref projectPoints ) objectPoints. The use of RANSAC
     * makes the function resistant to outliers.
     *
     * @note
     * -   An example of how to use solvePNPRansac for object detection can be found at
     * opencv_source_code/samples/cpp/tutorial_code/calib3d/real_time_pose_estimation/
     * -   The default method used to estimate the camera pose for the Minimal Sample Sets step
     * is #SOLVEPNP_EPNP. Exceptions are:
     * - if you choose #SOLVEPNP_P3P or #SOLVEPNP_AP3P, these methods will be used.
     * - if the number of input points is equal to 4, #SOLVEPNP_P3P is used.
     * -   The method used to estimate the camera pose using all the inliers is defined by the
     * flags parameters unless it is equal to #SOLVEPNP_P3P or #SOLVEPNP_AP3P. In this case,
     * the method #SOLVEPNP_EPNP will be used instead.
     */
    function solvePnPRansac(
        objectPoints: Mat,
        imagePoints: Mat,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvec: Mat,
        tvec: Mat,
        useExtrinsicGuess?: boolean,
        iterationsCount?: int,
        reprojectionError?: float,
        confidence?: double,
        inliers?: Mat,
        flags?: int
    ): boolean;

    /**
     *
     */
    function solvePnPRansac(
        objectPoints: Mat,
        imagePoints: Mat,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvec: Mat,
        tvec: Mat,
        inliers: Mat,
        params?: unknown
    ): boolean;

    /**
     * @brief Refine a pose (the translation and the rotation that transform a 3D point expressed in the object coordinate frame
     * to the camera coordinate frame) from a 3D-2D point correspondences and starting from an initial solution.
     *
     * @param objectPoints Array of object points in the object coordinate space, Nx3 1-channel or 1xN/Nx1 3-channel,
     * where N is the number of points. vector\<Point3d\> can also be passed here.
     * @param imagePoints Array of corresponding image points, Nx2 1-channel or 1xN/Nx1 2-channel,
     * where N is the number of points. vector\<Point2d\> can also be passed here.
     * @param cameraMatrix Input camera intrinsic matrix \f$\cameramatrix{A}\f$ .
     * @param distCoeffs Input vector of distortion coefficients
     * \f$\distcoeffs\f$. If the vector is NULL/empty, the zero distortion coefficients are
     * assumed.
     * @param rvec Input/Output rotation vector (see @ref Rodrigues ) that, together with tvec, brings points from
     * the model coordinate system to the camera coordinate system. Input values are used as an initial solution.
     * @param tvec Input/Output translation vector. Input values are used as an initial solution.
     * @param criteria Criteria when to stop the Levenberg-Marquard iterative algorithm.
     *
     * The function refines the object pose given at least 3 object points, their corresponding image
     * projections, an initial solution for the rotation and translation vector,
     * as well as the camera intrinsic matrix and the distortion coefficients.
     * The function minimizes the projection error with respect to the rotation and the translation vectors, according
     * to a Levenberg-Marquardt iterative minimization @cite Madsen04 @cite Eade13 process.
     */
    function solvePnPRefineLM(
        objectPoints: Mat,
        imagePoints: Mat,
        cameraMatrix: Mat,
        distCoeffs: Mat,
        rvec: Mat,
        tvec: Mat,
        criteria?: TermCriteriaLike
    ): void;

    /**
     * @brief Finds the real or complex roots of a polynomial equation.
     *
     * The function cv::solvePoly finds real and complex roots of a polynomial equation:
     * \f[\texttt{coeffs} [n] x^{n} +  \texttt{coeffs} [n-1] x^{n-1} + ... +  \texttt{coeffs} [1] x +  \texttt{coeffs} [0] = 0\f]
     * @param coeffs array of polynomial coefficients.
     * @param roots output (complex) array of roots.
     * @param maxIters maximum number of iterations the algorithm does.
     */
    function solvePoly(coeffs: Mat, roots: Mat, maxIters?: int): double;

    /**
     * @overload
     * @param m input multi-channel array.
     * @param mv output vector of arrays; the arrays themselves are reallocated, if needed.
     */
    function split(m: Mat, mv: MatVector): void;

    /**
     * @brief Calculates a square root of array elements.
     *
     * The function cv::sqrt calculates a square root of each input array element.
     * In case of multi-channel arrays, each channel is processed
     * independently. The accuracy is approximately the same as of the built-in
     * std::sqrt .
     * @param src input floating-point array.
     * @param dst output array of the same size and type as src.
     */
    function sqrt(src: Mat, dst: Mat): void;

    /**
     * @brief Calculates the per-element difference between two arrays or array and a scalar.
     *
     * The function subtract calculates:
     * - Difference between two arrays, when both input arrays have the same size and the same number of
     * channels:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1}(I) -  \texttt{src2}(I)) \quad \texttt{if mask}(I) \ne0\f]
     * - Difference between an array and a scalar, when src2 is constructed from Scalar or has the same
     * number of elements as `src1.channels()`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1}(I) -  \texttt{src2} ) \quad \texttt{if mask}(I) \ne0\f]
     * - Difference between a scalar and an array, when src1 is constructed from Scalar or has the same
     * number of elements as `src2.channels()`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src1} -  \texttt{src2}(I) ) \quad \texttt{if mask}(I) \ne0\f]
     * - The reverse difference between a scalar and an array in the case of `SubRS`:
     * \f[\texttt{dst}(I) =  \texttt{saturate} ( \texttt{src2} -  \texttt{src1}(I) ) \quad \texttt{if mask}(I) \ne0\f]
     * where I is a multi-dimensional index of array elements. In case of multi-channel arrays, each
     * channel is processed independently.
     *
     * The first function in the list above can be replaced with matrix expressions:
     * @code{.cpp}
     * dst = src1 - src2;
     * dst -= src1; // equivalent to subtract(dst, src1, dst);
     * @endcode
     * The input arrays and the output array can all have the same or different depths. For example, you
     * can subtract to 8-bit unsigned arrays and store the difference in a 16-bit signed array. Depth of
     * the output array is determined by dtype parameter. In the second and third cases above, as well as
     * in the first case, when src1.depth() == src2.depth(), dtype can be set to the default -1. In this
     * case the output array will have the same depth as the input array, be it src1, src2 or both.
     * @note Saturation is not applied when the output array has the depth CV_32S. You may even get
     * result of an incorrect sign in the case of overflow.
     * @param src1 first input array or a scalar.
     * @param src2 second input array or a scalar.
     * @param dst output array of the same size and the same number of channels as the input array.
     * @param mask optional operation mask; this is an 8-bit single channel array that specifies elements
     * of the output array to be changed.
     * @param dtype optional depth of the output array
     * @sa  add, addWeighted, scaleAdd, Mat::convertTo
     */
    function subtract(src1: Mat, src2: Mat, dst: Mat, mask?: Mat, dtype?: int): void;

    /**
     * @brief Applies a fixed-level threshold to each array element.
     *
     * The function applies fixed-level thresholding to a multiple-channel array. The function is typically
     * used to get a bi-level (binary) image out of a grayscale image ( #compare could be also used for
     * this purpose) or for removing a noise, that is, filtering out pixels with too small or too large
     * values. There are several types of thresholding supported by the function. They are determined by
     * type parameter.
     *
     * Also, the special values #THRESH_OTSU or #THRESH_TRIANGLE may be combined with one of the
     * above values. In these cases, the function determines the optimal threshold value using the Otsu's
     * or Triangle algorithm and uses it instead of the specified thresh.
     *
     * @note Currently, the Otsu's and Triangle methods are implemented only for 8-bit single-channel images.
     *
     * @param src input array (multiple-channel, 8-bit or 32-bit floating point).
     * @param dst output array of the same size  and type and the same number of channels as src.
     * @param thresh threshold value.
     * @param maxval maximum value to use with the #THRESH_BINARY and #THRESH_BINARY_INV thresholding
     * types.
     * @param type thresholding type (see #ThresholdTypes).
     * @return the computed threshold value if Otsu's or Triangle methods used.
     *
     * @sa  adaptiveThreshold, findContours, compare, min, max
     */
    function threshold(src: Mat, dst: Mat, thresh: double, maxval: double, type: int): double;

    /**
     * @brief Returns the trace of a matrix.
     *
     * The function cv::trace returns the sum of the diagonal elements of the
     * matrix mtx .
     * \f[\mathrm{tr} ( \texttt{mtx} ) =  \sum _i  \texttt{mtx} (i,i)\f]
     * @param mtx input matrix.
     */
    function trace(mtx: Mat): ScalarLike;

    /**
     * @brief Performs the matrix transformation of every array element.
     *
     * The function cv::transform performs the matrix transformation of every
     * element of the array src and stores the results in dst :
     * \f[\texttt{dst} (I) =  \texttt{m} \cdot \texttt{src} (I)\f]
     * (when m.cols=src.channels() ), or
     * \f[\texttt{dst} (I) =  \texttt{m} \cdot [ \texttt{src} (I); 1]\f]
     * (when m.cols=src.channels()+1 )
     *
     * Every element of the N -channel array src is interpreted as N -element
     * vector that is transformed using the M x N or M x (N+1) matrix m to
     * M-element vector - the corresponding element of the output array dst .
     *
     * The function may be used for geometrical transformation of
     * N -dimensional points, arbitrary linear color space transformation (such
     * as various kinds of RGB to YUV transforms), shuffling the image
     * channels, and so forth.
     * @param src input array that must have as many channels (1 to 4) as
     * m.cols or m.cols-1.
     * @param dst output array of the same size and depth as src; it has as
     * many channels as m.rows.
     * @param m transformation 2x2 or 2x3 floating-point matrix.
     * @sa perspectiveTransform, getAffineTransform, estimateAffine2D, warpAffine, warpPerspective
     */
    function transform(src: Mat, dst: Mat, m: Mat): void;

    /**
     * @brief Transposes a matrix.
     *
     * The function cv::transpose transposes the matrix src :
     * \f[\texttt{dst} (i,j) =  \texttt{src} (j,i)\f]
     * @note No complex conjugation is done in case of a complex matrix. It
     * should be done separately if needed.
     * @param src input array.
     * @param dst output array of the same type as src.
     */
    function transpose(src: Mat, dst: Mat): void;

    /**
     * @brief Transforms an image to compensate for lens distortion.
     *
     * The function transforms an image to compensate radial and tangential lens distortion.
     *
     * The function is simply a combination of #initUndistortRectifyMap (with unity R ) and #remap
     * (with bilinear interpolation). See the former function for details of the transformation being
     * performed.
     *
     * Those pixels in the destination image, for which there is no correspondent pixels in the source
     * image, are filled with zeros (black color).
     *
     * A particular subset of the source image that will be visible in the corrected image can be regulated
     * by newCameraMatrix. You can use #getOptimalNewCameraMatrix to compute the appropriate
     * newCameraMatrix depending on your requirements.
     *
     * The camera matrix and the distortion parameters can be determined using #calibrateCamera. If
     * the resolution of images is different from the resolution used at the calibration stage, \f$f_x,
     * f_y, c_x\f$ and \f$c_y\f$ need to be scaled accordingly, while the distortion coefficients remain
     * the same.
     *
     * @param src Input (distorted) image.
     * @param dst Output (corrected) image that has the same size and type as src .
     * @param cameraMatrix Input camera matrix \f$A = \vecthreethree{f_x}{0}{c_x}{0}{f_y}{c_y}{0}{0}{1}\f$ .
     * @param distCoeffs Input vector of distortion coefficients
     * \f$(k_1, k_2, p_1, p_2[, k_3[, k_4, k_5, k_6[, s_1, s_2, s_3, s_4[, \tau_x, \tau_y]]]])\f$
     * of 4, 5, 8, 12 or 14 elements. If the vector is NULL/empty, the zero distortion coefficients are assumed.
     * @param newCameraMatrix Camera matrix of the distorted image. By default, it is the same as
     * cameraMatrix but you may additionally scale and shift the result by using a different matrix.
     */
    function undistort(src: Mat, dst: Mat, cameraMatrix: Mat, distCoeffs: Mat, newCameraMatrix?: Mat): void;

    /**
     * @overload
     * @code{.cpp}
     * std::vector<cv::Mat> matrices = { cv::Mat(1, 4, CV_8UC1, cv::Scalar(1)),
     * cv::Mat(1, 4, CV_8UC1, cv::Scalar(2)),
     * cv::Mat(1, 4, CV_8UC1, cv::Scalar(3)),};
     *
     * cv::Mat out;
     * cv::vconcat( matrices, out );
     * //out:
     * //[1,   1,   1,   1;
     * // 2,   2,   2,   2;
     * // 3,   3,   3,   3]
     * @endcode
     * @param src input array or vector of matrices. all of the matrices must have the same number of cols and the same depth
     * @param dst output array. It has the same number of cols and depth as the src, and the sum of rows of the src.
     * same depth.
     */
    function vconcat(src: MatVector, dst: Mat): void;

    /**
     * @brief Applies an affine transformation to an image.
     *
     * The function warpAffine transforms the source image using the specified matrix:
     *
     * \f[\texttt{dst} (x,y) =  \texttt{src} ( \texttt{M} _{11} x +  \texttt{M} _{12} y +  \texttt{M} _{13}, \texttt{M} _{21} x +  \texttt{M} _{22} y +  \texttt{M} _{23})\f]
     *
     * when the flag #WARP_INVERSE_MAP is set. Otherwise, the transformation is first inverted
     * with #invertAffineTransform and then put in the formula above instead of M. The function cannot
     * operate in-place.
     *
     * @param src input image.
     * @param dst output image that has the size dsize and the same type as src .
     * @param M \f$2\times 3\f$ transformation matrix.
     * @param dsize size of the output image.
     * @param flags combination of interpolation methods (see #InterpolationFlags) and the optional
     * flag #WARP_INVERSE_MAP that means that M is the inverse transformation (
     * \f$\texttt{dst}\rightarrow\texttt{src}\f$ ).
     * @param borderMode pixel extrapolation method (see #BorderTypes); when
     * borderMode=#BORDER_TRANSPARENT, it means that the pixels in the destination image corresponding to
     * the "outliers" in the source image are not modified by the function.
     * @param borderValue value used in case of a constant border; by default, it is 0.
     *
     * @sa  warpPerspective, resize, remap, getRectSubPix, transform
     */
    function warpAffine(
        src: Mat,
        dst: Mat,
        M: Mat,
        dsize: SizeLike,
        flags?: int,
        borderMode?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * @brief Applies a perspective transformation to an image.
     *
     * The function warpPerspective transforms the source image using the specified matrix:
     *
     * \f[\texttt{dst} (x,y) =  \texttt{src} \left ( \frac{M_{11} x + M_{12} y + M_{13}}{M_{31} x + M_{32} y + M_{33}} ,
     * \frac{M_{21} x + M_{22} y + M_{23}}{M_{31} x + M_{32} y + M_{33}} \right )\f]
     *
     * when the flag #WARP_INVERSE_MAP is set. Otherwise, the transformation is first inverted with invert
     * and then put in the formula above instead of M. The function cannot operate in-place.
     *
     * @param src input image.
     * @param dst output image that has the size dsize and the same type as src .
     * @param M \f$3\times 3\f$ transformation matrix.
     * @param dsize size of the output image.
     * @param flags combination of interpolation methods (#INTER_LINEAR or #INTER_NEAREST) and the
     * optional flag #WARP_INVERSE_MAP, that sets M as the inverse transformation (
     * \f$\texttt{dst}\rightarrow\texttt{src}\f$ ).
     * @param borderMode pixel extrapolation method (#BORDER_CONSTANT or #BORDER_REPLICATE).
     * @param borderValue value used in case of a constant border; by default, it equals 0.
     *
     * @sa  warpAffine, resize, remap, getRectSubPix, perspectiveTransform
     */
    function warpPerspective(
        src: Mat,
        dst: Mat,
        M: Mat,
        dsize: SizeLike,
        flags?: int,
        borderMode?: int,
        borderValue?: ScalarLike
    ): void;

    /**
     * \brief Remaps an image to polar or semilog-polar coordinates space
     *
     * @anchor polar_remaps_reference_image
     * ![Polar remaps reference](pics/polar_remap_doc.png)
     *
     * Transform the source image using the following transformation:
     * \f[
     * dst(\rho , \phi ) = src(x,y)
     * \f]
     *
     * where
     * \f[
     * \begin{array}{l}
     * \vec{I} = (x - center.x, \;y - center.y) \\
     * \phi = Kangle \cdot \texttt{angle} (\vec{I}) \\
     * \rho = \left\{\begin{matrix}
     * Klin \cdot \texttt{magnitude} (\vec{I}) & default \\
     * Klog \cdot log_e(\texttt{magnitude} (\vec{I})) & if \; semilog \\
     * \end{matrix}\right.
     * \end{array}
     * \f]
     *
     * and
     * \f[
     * \begin{array}{l}
     * Kangle = dsize.height / 2\Pi \\
     * Klin = dsize.width / maxRadius \\
     * Klog = dsize.width / log_e(maxRadius) \\
     * \end{array}
     * \f]
     *
     *
     * \par Linear vs semilog mapping
     *
     * Polar mapping can be linear or semi-log. Add one of #WarpPolarMode to `flags` to specify the polar mapping mode.
     *
     * Linear is the default mode.
     *
     * The semilog mapping emulates the human "foveal" vision that permit very high acuity on the line of sight (central vision)
     * in contrast to peripheral vision where acuity is minor.
     *
     * \par Option on `dsize`:
     *
     * - if both values in `dsize <=0 ` (default),
     * the destination image will have (almost) same area of source bounding circle:
     * \f[\begin{array}{l}
     * dsize.area  \leftarrow (maxRadius^2 \cdot \Pi) \\
     * dsize.width = \texttt{cvRound}(maxRadius) \\
     * dsize.height = \texttt{cvRound}(maxRadius \cdot \Pi) \\
     * \end{array}\f]
     *
     *
     * - if only `dsize.height <= 0`,
     * the destination image area will be proportional to the bounding circle area but scaled by `Kx * Kx`:
     * \f[\begin{array}{l}
     * dsize.height = \texttt{cvRound}(dsize.width \cdot \Pi) \\
     * \end{array}
     * \f]
     *
     * - if both values in `dsize > 0 `,
     * the destination image will have the given size therefore the area of the bounding circle will be scaled to `dsize`.
     *
     *
     * \par Reverse mapping
     *
     * You can get reverse mapping adding #WARP_INVERSE_MAP to `flags`
     * \snippet polar_transforms.cpp InverseMap
     *
     * In addiction, to calculate the original coordinate from a polar mapped coordinate \f$(rho, phi)->(x, y)\f$:
     * \snippet polar_transforms.cpp InverseCoordinate
     *
     * @param src Source image.
     * @param dst Destination image. It will have same type as src.
     * @param dsize The destination image size (see description for valid options).
     * @param center The transformation center.
     * @param maxRadius The radius of the bounding circle to transform. It determines the inverse magnitude scale parameter too.
     * @param flags A combination of interpolation methods, #InterpolationFlags + #WarpPolarMode.
     * - Add #WARP_POLAR_LINEAR to select linear polar mapping (default)
     * - Add #WARP_POLAR_LOG to select semilog polar mapping
     * - Add #WARP_INVERSE_MAP for reverse mapping.
     * @note
     * -  The function can not operate in-place.
     * -  To calculate magnitude and angle in degrees #cartToPolar is used internally thus angles are measured from 0 to 360 with accuracy about 0.3 degrees.
     * -  This function uses #remap. Due to current implementation limitations the size of an input and output images should be less than 32767x32767.
     *
     * @sa cv::remap
     */
    function warpPolar(src: Mat, dst: Mat, dsize: SizeLike, center: Point2fLike, maxRadius: double, flags: int): void;

    /**
     * @brief Performs a marker-based image segmentation using the watershed algorithm.
     *
     * The function implements one of the variants of watershed, non-parametric marker-based segmentation
     * algorithm, described in @cite Meyer92 .
     *
     * Before passing the image to the function, you have to roughly outline the desired regions in the
     * image markers with positive (\>0) indices. So, every region is represented as one or more connected
     * components with the pixel values 1, 2, 3, and so on. Such markers can be retrieved from a binary
     * mask using #findContours and #drawContours (see the watershed.cpp demo). The markers are "seeds" of
     * the future image regions. All the other pixels in markers , whose relation to the outlined regions
     * is not known and should be defined by the algorithm, should be set to 0's. In the function output,
     * each pixel in markers is set to a value of the "seed" components or to -1 at boundaries between the
     * regions.
     *
     * @note Any two neighbor connected components are not necessarily separated by a watershed boundary
     * (-1's pixels); for example, they can touch each other in the initial marker image passed to the
     * function.
     *
     * @param image Input 8-bit 3-channel image.
     * @param markers Input/output 32-bit single-channel image (map) of markers. It should have the same
     * size as image .
     *
     * @sa findContours
     */
    function watershed(image: Mat, markers: Mat): void;

    /**
     * @brief Creates 4-dimensional blob from image. Optionally resizes and crops @p image from center,
     * subtract @p mean values, scales values by @p scalefactor, swap Blue and Red channels.
     * @param image input image (with 1-, 3- or 4-channels).
     * @param size spatial size for output image
     * @param mean scalar with mean values which are subtracted from channels. Values are intended
     * to be in (mean-R, mean-G, mean-B) order if @p image has BGR ordering and @p swapRB is true.
     * @param scalefactor multiplier for @p image values.
     * @param swapRB flag which indicates that swap first and last channels
     * in 3-channel image is necessary.
     * @param crop flag which indicates whether image will be cropped after resize or not
     * @param ddepth Depth of output blob. Choose CV_32F or CV_8U.
     * @details if @p crop is true, input image is resized so one side after resize is equal to corresponding
     * dimension in @p size and another one is equal or larger. Then, crop from the center is performed.
     * If @p crop is false, direct resize without cropping and preserving aspect ratio is performed.
     * @returns 4-dimensional Mat with NCHW dimensions order.
     */
    function blobFromImage(
        image: Mat,
        scalefactor?: double,
        size?: SizeLike,
        mean?: ScalarLike,
        swapRB?: boolean,
        crop?: boolean,
        ddepth?: int
    ): Mat;

    /**
     * @brief Read deep learning network represented in one of the supported formats.
     * @param[in] model Binary file contains trained weights. The following file
     * extensions are expected for models from different frameworks:
     * `*.caffemodel` (Caffe, http://caffe.berkeleyvision.org/)
     * `*.pb` (TensorFlow, https://www.tensorflow.org/)
     * `*.t7` | `*.net` (Torch, http://torch.ch/)
     * `*.weights` (Darknet, https://pjreddie.com/darknet/)
     * `*.bin` (DLDT, https://software.intel.com/openvino-toolkit)
     * `*.onnx` (ONNX, https://onnx.ai/)
     * @param[in] config Text file contains network configuration. It could be a
     * file with the following extensions:
     * `*.prototxt` (Caffe, http://caffe.berkeleyvision.org/)
     * `*.pbtxt` (TensorFlow, https://www.tensorflow.org/)
     * `*.cfg` (Darknet, https://pjreddie.com/darknet/)
     * `*.xml` (DLDT, https://software.intel.com/openvino-toolkit)
     * @param[in] framework Explicit framework name tag to determine a format.
     * @returns Net object.
     *
     * This function automatically detects an origin framework of trained model
     * and calls an appropriate function such @ref readNetFromCaffe, @ref readNetFromTensorflow,
     * @ref readNetFromTorch or @ref readNetFromDarknet. An order of @p model and @p config
     * arguments does not matter.
     */
    function readNet(model: string, config?: string, framework?: string): unknown;

    /**
     * @brief Read deep learning network represented in one of the supported formats.
     * @details This is an overloaded member function, provided for convenience.
     * It differs from the above function only in what argument(s) it accepts.
     * @param[in] framework    Name of origin framework.
     * @param[in] bufferModel  A buffer with a content of binary file with weights
     * @param[in] bufferConfig A buffer with a content of text file contains network configuration.
     * @returns Net object.
     */
    function readNet(framework: string, bufferModel: unknown, bufferConfig?: unknown): unknown;

    /**
     * @brief Reads a network model stored in <a href="http://caffe.berkeleyvision.org">Caffe</a> framework's format.
     * @param prototxt   path to the .prototxt file with text description of the network architecture.
     * @param caffeModel path to the .caffemodel file with learned network.
     * @returns Net object.
     */
    function readNetFromCaffe(prototxt: string, caffeModel?: string): unknown;

    /**
     * @brief Reads a network model stored in Caffe model in memory.
     * @param bufferProto buffer containing the content of the .prototxt file
     * @param bufferModel buffer containing the content of the .caffemodel file
     * @returns Net object.
     */
    function readNetFromCaffe(bufferProto: unknown, bufferModel?: unknown): unknown;

    /**
     * @brief Reads a network model stored in <a href="https://pjreddie.com/darknet/">Darknet</a> model files.
     * @param cfgFile      path to the .cfg file with text description of the network architecture.
     * @param darknetModel path to the .weights file with learned network.
     * @returns Network object that ready to do forward, throw an exception in failure cases.
     * @returns Net object.
     */
    function readNetFromDarknet(cfgFile: string, darknetModel?: string): unknown;

    /**
     * @brief Reads a network model stored in <a href="https://pjreddie.com/darknet/">Darknet</a> model files.
     * @param bufferCfg   A buffer contains a content of .cfg file with text description of the network architecture.
     * @param bufferModel A buffer contains a content of .weights file with learned network.
     * @returns Net object.
     */
    function readNetFromDarknet(bufferCfg: unknown, bufferModel?: unknown): unknown;

    /**
     * @brief Reads a network model <a href="https://onnx.ai/">ONNX</a>.
     * @param onnxFile path to the .onnx file with text description of the network architecture.
     * @returns Network object that ready to do forward, throw an exception in failure cases.
     */
    function readNetFromONNX(onnxFile: string): unknown;

    /**
     * @brief Reads a network model from <a href="https://onnx.ai/">ONNX</a>
     * in-memory buffer.
     * @param buffer in-memory buffer that stores the ONNX model bytes.
     * @returns Network object that ready to do forward, throw an exception
     * in failure cases.
     */
    function readNetFromONNX(buffer: unknown): unknown;

    /**
     * @brief Reads a network model stored in <a href="https://www.tensorflow.org/">TensorFlow</a> framework's format.
     * @param model  path to the .pb file with binary protobuf description of the network architecture
     * @param config path to the .pbtxt file that contains text graph definition in protobuf format.
     * Resulting Net object is built by text graph using weights from a binary one that
     * let us make it more flexible.
     * @returns Net object.
     */
    function readNetFromTensorflow(model: string, config?: string): unknown;

    /**
     * @brief Reads a network model stored in <a href="https://www.tensorflow.org/">TensorFlow</a> framework's format.
     * @param bufferModel buffer containing the content of the pb file
     * @param bufferConfig buffer containing the content of the pbtxt file
     * @returns Net object.
     */
    function readNetFromTensorflow(bufferModel: unknown, bufferConfig?: unknown): unknown;

    /**
     * @brief Reads a network model stored in <a href="http://torch.ch">Torch7</a> framework's format.
     * @param model    path to the file, dumped from Torch by using torch.save() function.
     * @param isBinary specifies whether the network was serialized in ascii mode or binary.
     * @param evaluate specifies testing phase of network. If true, it's similar to evaluate() method in Torch.
     * @returns Net object.
     *
     * @note Ascii mode of Torch serializer is more preferable, because binary mode extensively use `long` type of C language,
     * which has various bit-length on different systems.
     *
     * The loading file must contain serialized <a href="https://github.com/torch/nn/blob/master/doc/module.md">nn.Module</a> object
     * with importing network. Try to eliminate a custom objects from serialazing data to avoid importing errors.
     *
     * List of supported layers (i.e. object instances derived from Torch nn.Module class):
     * - nn.Sequential
     * - nn.Parallel
     * - nn.Concat
     * - nn.Linear
     * - nn.SpatialConvolution
     * - nn.SpatialMaxPooling, nn.SpatialAveragePooling
     * - nn.ReLU, nn.TanH, nn.Sigmoid
     * - nn.Reshape
     * - nn.SoftMax, nn.LogSoftMax
     *
     * Also some equivalents of these classes from cunn, cudnn, and fbcunn may be successfully imported.
     */
    function readNetFromTorch(model: string, isBinary?: boolean, evaluate?: boolean): unknown;

    /**
     * @brief Computes undistortion and rectification maps for image transform by cv::remap(). If D is empty zero
     * distortion is used, if R or P is empty identity matrixes are used.
     *
     * @param K Camera intrinsic matrix \f$cameramatrix{K}\f$.
     * @param D Input vector of distortion coefficients \f$\distcoeffsfisheye\f$.
     * @param R Rectification transformation in the object space: 3x3 1-channel, or vector: 3x1/1x3
     * 1-channel or 1x1 3-channel
     * @param P New camera intrinsic matrix (3x3) or new projection matrix (3x4)
     * @param size Undistorted image size.
     * @param m1type Type of the first output map that can be CV_32FC1 or CV_16SC2 . See convertMaps()
     * for details.
     * @param map1 The first output map.
     * @param map2 The second output map.
     */
    function initUndistortRectifyMap(
        K: Mat,
        D: Mat,
        R: Mat,
        P: Mat,
        size: SizeLike,
        m1type: int,
        map1: Mat,
        map2: Mat
    ): void;
}
