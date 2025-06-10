// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0
declare module 'enums' {
    enum AKAZE_DescriptorType {
        DESCRIPTOR_KAZE_UPRIGHT = 2,
        DESCRIPTOR_KAZE = 3,
        DESCRIPTOR_MLDB_UPRIGHT = 4,
        DESCRIPTOR_MLDB = 5,
    }

    enum AccessFlag {
        ACCESS_READ = 1 << 24,
        ACCESS_WRITE = 1 << 25,
        ACCESS_RW = 3 << 24,
        ACCESS_MASK = ACCESS_RW,
        ACCESS_FAST = 1 << 26,
    }

    enum AdaptiveThresholdTypes {
        ADAPTIVE_THRESH_MEAN_C = 0,
        ADAPTIVE_THRESH_GAUSSIAN_C = 1,
    }

    enum AgastFeatureDetector_DetectorType {
        AGAST_5_8 = 0,
        AGAST_7_12d = 1,
        AGAST_7_12s = 2,
        OAST_9_16 = 3,
    }

    enum BorderTypes {
        BORDER_CONSTANT = 0,
        BORDER_REPLICATE = 1,
        BORDER_REFLECT = 2,
        BORDER_WRAP = 3,
        BORDER_REFLECT_101 = 4,
        BORDER_TRANSPARENT = 5,
        BORDER_REFLECT101 = BORDER_REFLECT_101,
        BORDER_DEFAULT = BORDER_REFLECT_101,
        BORDER_ISOLATED = 16,
    }

    enum CirclesGridFinderParameters_GridType {
        SYMMETRIC_GRID = 0,
        ASYMMETRIC_GRID = 1,
    }

    enum CmpTypes {
        CMP_EQ = 0,
        CMP_GT = 1,
        CMP_GE = 2,
        CMP_LT = 3,
        CMP_LE = 4,
        CMP_NE = 5,
    }

    enum ColorConversionCodes {
        COLOR_BGR2BGRA = 0,
        COLOR_RGB2RGBA = COLOR_BGR2BGRA,
        COLOR_BGRA2BGR = 1,
        COLOR_RGBA2RGB = COLOR_BGRA2BGR,
        COLOR_BGR2RGBA = 2,
        COLOR_RGB2BGRA = COLOR_BGR2RGBA,
        COLOR_RGBA2BGR = 3,
        COLOR_BGRA2RGB = COLOR_RGBA2BGR,
        COLOR_BGR2RGB = 4,
        COLOR_RGB2BGR = COLOR_BGR2RGB,
        COLOR_BGRA2RGBA = 5,
        COLOR_RGBA2BGRA = COLOR_BGRA2RGBA,
        COLOR_BGR2GRAY = 6,
        COLOR_RGB2GRAY = 7,
        COLOR_GRAY2BGR = 8,
        COLOR_GRAY2RGB = COLOR_GRAY2BGR,
        COLOR_GRAY2BGRA = 9,
        COLOR_GRAY2RGBA = COLOR_GRAY2BGRA,
        COLOR_BGRA2GRAY = 10,
        COLOR_RGBA2GRAY = 11,
        COLOR_BGR2BGR565 = 12,
        COLOR_RGB2BGR565 = 13,
        COLOR_BGR5652BGR = 14,
        COLOR_BGR5652RGB = 15,
        COLOR_BGRA2BGR565 = 16,
        COLOR_RGBA2BGR565 = 17,
        COLOR_BGR5652BGRA = 18,
        COLOR_BGR5652RGBA = 19,
        COLOR_GRAY2BGR565 = 20,
        COLOR_BGR5652GRAY = 21,
        COLOR_BGR2BGR555 = 22,
        COLOR_RGB2BGR555 = 23,
        COLOR_BGR5552BGR = 24,
        COLOR_BGR5552RGB = 25,
        COLOR_BGRA2BGR555 = 26,
        COLOR_RGBA2BGR555 = 27,
        COLOR_BGR5552BGRA = 28,
        COLOR_BGR5552RGBA = 29,
        COLOR_GRAY2BGR555 = 30,
        COLOR_BGR5552GRAY = 31,
        COLOR_BGR2XYZ = 32,
        COLOR_RGB2XYZ = 33,
        COLOR_XYZ2BGR = 34,
        COLOR_XYZ2RGB = 35,
        COLOR_BGR2YCrCb = 36,
        COLOR_RGB2YCrCb = 37,
        COLOR_YCrCb2BGR = 38,
        COLOR_YCrCb2RGB = 39,
        COLOR_BGR2HSV = 40,
        COLOR_RGB2HSV = 41,
        COLOR_BGR2Lab = 44,
        COLOR_RGB2Lab = 45,
        COLOR_BGR2Luv = 50,
        COLOR_RGB2Luv = 51,
        COLOR_BGR2HLS = 52,
        COLOR_RGB2HLS = 53,
        COLOR_HSV2BGR = 54,
        COLOR_HSV2RGB = 55,
        COLOR_Lab2BGR = 56,
        COLOR_Lab2RGB = 57,
        COLOR_Luv2BGR = 58,
        COLOR_Luv2RGB = 59,
        COLOR_HLS2BGR = 60,
        COLOR_HLS2RGB = 61,
        COLOR_BGR2HSV_FULL = 66,
        COLOR_RGB2HSV_FULL = 67,
        COLOR_BGR2HLS_FULL = 68,
        COLOR_RGB2HLS_FULL = 69,
        COLOR_HSV2BGR_FULL = 70,
        COLOR_HSV2RGB_FULL = 71,
        COLOR_HLS2BGR_FULL = 72,
        COLOR_HLS2RGB_FULL = 73,
        COLOR_LBGR2Lab = 74,
        COLOR_LRGB2Lab = 75,
        COLOR_LBGR2Luv = 76,
        COLOR_LRGB2Luv = 77,
        COLOR_Lab2LBGR = 78,
        COLOR_Lab2LRGB = 79,
        COLOR_Luv2LBGR = 80,
        COLOR_Luv2LRGB = 81,
        COLOR_BGR2YUV = 82,
        COLOR_RGB2YUV = 83,
        COLOR_YUV2BGR = 84,
        COLOR_YUV2RGB = 85,
        COLOR_YUV2RGB_NV12 = 90,
        COLOR_YUV2BGR_NV12 = 91,
        COLOR_YUV2RGB_NV21 = 92,
        COLOR_YUV2BGR_NV21 = 93,
        COLOR_YUV420sp2RGB = COLOR_YUV2RGB_NV21,
        COLOR_YUV420sp2BGR = COLOR_YUV2BGR_NV21,
        COLOR_YUV2RGBA_NV12 = 94,
        COLOR_YUV2BGRA_NV12 = 95,
        COLOR_YUV2RGBA_NV21 = 96,
        COLOR_YUV2BGRA_NV21 = 97,
        COLOR_YUV420sp2RGBA = COLOR_YUV2RGBA_NV21,
        COLOR_YUV420sp2BGRA = COLOR_YUV2BGRA_NV21,
        COLOR_YUV2RGB_YV12 = 98,
        COLOR_YUV2BGR_YV12 = 99,
        COLOR_YUV2RGB_IYUV = 100,
        COLOR_YUV2BGR_IYUV = 101,
        COLOR_YUV2RGB_I420 = COLOR_YUV2RGB_IYUV,
        COLOR_YUV2BGR_I420 = COLOR_YUV2BGR_IYUV,
        COLOR_YUV420p2RGB = COLOR_YUV2RGB_YV12,
        COLOR_YUV420p2BGR = COLOR_YUV2BGR_YV12,
        COLOR_YUV2RGBA_YV12 = 102,
        COLOR_YUV2BGRA_YV12 = 103,
        COLOR_YUV2RGBA_IYUV = 104,
        COLOR_YUV2BGRA_IYUV = 105,
        COLOR_YUV2RGBA_I420 = COLOR_YUV2RGBA_IYUV,
        COLOR_YUV2BGRA_I420 = COLOR_YUV2BGRA_IYUV,
        COLOR_YUV420p2RGBA = COLOR_YUV2RGBA_YV12,
        COLOR_YUV420p2BGRA = COLOR_YUV2BGRA_YV12,
        COLOR_YUV2GRAY_420 = 106,
        COLOR_YUV2GRAY_NV21 = COLOR_YUV2GRAY_420,
        COLOR_YUV2GRAY_NV12 = COLOR_YUV2GRAY_420,
        COLOR_YUV2GRAY_YV12 = COLOR_YUV2GRAY_420,
        COLOR_YUV2GRAY_IYUV = COLOR_YUV2GRAY_420,
        COLOR_YUV2GRAY_I420 = COLOR_YUV2GRAY_420,
        COLOR_YUV420sp2GRAY = COLOR_YUV2GRAY_420,
        COLOR_YUV420p2GRAY = COLOR_YUV2GRAY_420,
        COLOR_YUV2RGB_UYVY = 107,
        COLOR_YUV2BGR_UYVY = 108,
        COLOR_YUV2RGB_Y422 = COLOR_YUV2RGB_UYVY,
        COLOR_YUV2BGR_Y422 = COLOR_YUV2BGR_UYVY,
        COLOR_YUV2RGB_UYNV = COLOR_YUV2RGB_UYVY,
        COLOR_YUV2BGR_UYNV = COLOR_YUV2BGR_UYVY,
        COLOR_YUV2RGBA_UYVY = 111,
        COLOR_YUV2BGRA_UYVY = 112,
        COLOR_YUV2RGBA_Y422 = COLOR_YUV2RGBA_UYVY,
        COLOR_YUV2BGRA_Y422 = COLOR_YUV2BGRA_UYVY,
        COLOR_YUV2RGBA_UYNV = COLOR_YUV2RGBA_UYVY,
        COLOR_YUV2BGRA_UYNV = COLOR_YUV2BGRA_UYVY,
        COLOR_YUV2RGB_YUY2 = 115,
        COLOR_YUV2BGR_YUY2 = 116,
        COLOR_YUV2RGB_YVYU = 117,
        COLOR_YUV2BGR_YVYU = 118,
        COLOR_YUV2RGB_YUYV = COLOR_YUV2RGB_YUY2,
        COLOR_YUV2BGR_YUYV = COLOR_YUV2BGR_YUY2,
        COLOR_YUV2RGB_YUNV = COLOR_YUV2RGB_YUY2,
        COLOR_YUV2BGR_YUNV = COLOR_YUV2BGR_YUY2,
        COLOR_YUV2RGBA_YUY2 = 119,
        COLOR_YUV2BGRA_YUY2 = 120,
        COLOR_YUV2RGBA_YVYU = 121,
        COLOR_YUV2BGRA_YVYU = 122,
        COLOR_YUV2RGBA_YUYV = COLOR_YUV2RGBA_YUY2,
        COLOR_YUV2BGRA_YUYV = COLOR_YUV2BGRA_YUY2,
        COLOR_YUV2RGBA_YUNV = COLOR_YUV2RGBA_YUY2,
        COLOR_YUV2BGRA_YUNV = COLOR_YUV2BGRA_YUY2,
        COLOR_YUV2GRAY_UYVY = 123,
        COLOR_YUV2GRAY_YUY2 = 124,
        COLOR_YUV2GRAY_Y422 = COLOR_YUV2GRAY_UYVY,
        COLOR_YUV2GRAY_UYNV = COLOR_YUV2GRAY_UYVY,
        COLOR_YUV2GRAY_YVYU = COLOR_YUV2GRAY_YUY2,
        COLOR_YUV2GRAY_YUYV = COLOR_YUV2GRAY_YUY2,
        COLOR_YUV2GRAY_YUNV = COLOR_YUV2GRAY_YUY2,
        COLOR_RGBA2mRGBA = 125,
        COLOR_mRGBA2RGBA = 126,
        COLOR_RGB2YUV_I420 = 127,
        COLOR_BGR2YUV_I420 = 128,
        COLOR_RGB2YUV_IYUV = COLOR_RGB2YUV_I420,
        COLOR_BGR2YUV_IYUV = COLOR_BGR2YUV_I420,
        COLOR_RGBA2YUV_I420 = 129,
        COLOR_BGRA2YUV_I420 = 130,
        COLOR_RGBA2YUV_IYUV = COLOR_RGBA2YUV_I420,
        COLOR_BGRA2YUV_IYUV = COLOR_BGRA2YUV_I420,
        COLOR_RGB2YUV_YV12 = 131,
        COLOR_BGR2YUV_YV12 = 132,
        COLOR_RGBA2YUV_YV12 = 133,
        COLOR_BGRA2YUV_YV12 = 134,
        COLOR_BayerBG2BGR = 46,
        COLOR_BayerGB2BGR = 47,
        COLOR_BayerRG2BGR = 48,
        COLOR_BayerGR2BGR = 49,
        COLOR_BayerBG2RGB = COLOR_BayerRG2BGR,
        COLOR_BayerGB2RGB = COLOR_BayerGR2BGR,
        COLOR_BayerRG2RGB = COLOR_BayerBG2BGR,
        COLOR_BayerGR2RGB = COLOR_BayerGB2BGR,
        COLOR_BayerBG2GRAY = 86,
        COLOR_BayerGB2GRAY = 87,
        COLOR_BayerRG2GRAY = 88,
        COLOR_BayerGR2GRAY = 89,
        COLOR_BayerBG2BGR_VNG = 62,
        COLOR_BayerGB2BGR_VNG = 63,
        COLOR_BayerRG2BGR_VNG = 64,
        COLOR_BayerGR2BGR_VNG = 65,
        COLOR_BayerBG2RGB_VNG = COLOR_BayerRG2BGR_VNG,
        COLOR_BayerGB2RGB_VNG = COLOR_BayerGR2BGR_VNG,
        COLOR_BayerRG2RGB_VNG = COLOR_BayerBG2BGR_VNG,
        COLOR_BayerGR2RGB_VNG = COLOR_BayerGB2BGR_VNG,
        COLOR_BayerBG2BGR_EA = 135,
        COLOR_BayerGB2BGR_EA = 136,
        COLOR_BayerRG2BGR_EA = 137,
        COLOR_BayerGR2BGR_EA = 138,
        COLOR_BayerBG2RGB_EA = COLOR_BayerRG2BGR_EA,
        COLOR_BayerGB2RGB_EA = COLOR_BayerGR2BGR_EA,
        COLOR_BayerRG2RGB_EA = COLOR_BayerBG2BGR_EA,
        COLOR_BayerGR2RGB_EA = COLOR_BayerGB2BGR_EA,
        COLOR_BayerBG2BGRA = 139,
        COLOR_BayerGB2BGRA = 140,
        COLOR_BayerRG2BGRA = 141,
        COLOR_BayerGR2BGRA = 142,
        COLOR_BayerBG2RGBA = COLOR_BayerRG2BGRA,
        COLOR_BayerGB2RGBA = COLOR_BayerGR2BGRA,
        COLOR_BayerRG2RGBA = COLOR_BayerBG2BGRA,
        COLOR_BayerGR2RGBA = COLOR_BayerGB2BGRA,
        COLOR_COLORCVT_MAX = 143,
    }

    enum ColormapTypes {
        COLORMAP_AUTUMN = 0,
        COLORMAP_BONE = 1,
        COLORMAP_JET = 2,
        COLORMAP_WINTER = 3,
        COLORMAP_RAINBOW = 4,
        COLORMAP_OCEAN = 5,
        COLORMAP_SUMMER = 6,
        COLORMAP_SPRING = 7,
        COLORMAP_COOL = 8,
        COLORMAP_HSV = 9,
        COLORMAP_PINK = 10,
        COLORMAP_HOT = 11,
        COLORMAP_PARULA = 12,
        COLORMAP_MAGMA = 13,
        COLORMAP_INFERNO = 14,
        COLORMAP_PLASMA = 15,
        COLORMAP_VIRIDIS = 16,
        COLORMAP_CIVIDIS = 17,
        COLORMAP_TWILIGHT = 18,
        COLORMAP_TWILIGHT_SHIFTED = 19,
        COLORMAP_TURBO = 20,
        COLORMAP_DEEPGREEN = 21,
    }

    enum ConnectedComponentsAlgorithmsTypes {
        CCL_WU = 0,
        CCL_DEFAULT = -1,
        CCL_GRANA = 1,
    }

    enum ConnectedComponentsTypes {
        CC_STAT_LEFT = 0,
        CC_STAT_TOP = 1,
        CC_STAT_WIDTH = 2,
        CC_STAT_HEIGHT = 3,
        CC_STAT_AREA = 4,
        CC_STAT_MAX = 5,
    }

    enum ContourApproximationModes {
        CHAIN_APPROX_NONE = 1,
        CHAIN_APPROX_SIMPLE = 2,
        CHAIN_APPROX_TC89_L1 = 3,
        CHAIN_APPROX_TC89_KCOS = 4,
    }

    enum CovarFlags {
        COVAR_SCRAMBLED = 0,
        COVAR_NORMAL = 1,
        COVAR_USE_AVG = 2,
        COVAR_SCALE = 4,
        COVAR_ROWS = 8,
        COVAR_COLS = 16,
    }

    enum DecompTypes {
        DECOMP_LU = 0,
        DECOMP_SVD = 1,
        DECOMP_EIG = 2,
        DECOMP_CHOLESKY = 3,
        DECOMP_QR = 4,
        DECOMP_NORMAL = 16,
    }

    enum DescriptorMatcher_MatcherType {
        FLANNBASED = 1,
        BRUTEFORCE = 2,
        BRUTEFORCE_L1 = 3,
        BRUTEFORCE_HAMMING = 4,
        BRUTEFORCE_HAMMINGLUT = 5,
        BRUTEFORCE_SL2 = 6,
    }

    enum DftFlags {
        DFT_INVERSE = 1,
        DFT_SCALE = 2,
        DFT_ROWS = 4,
        DFT_COMPLEX_OUTPUT = 16,
        DFT_REAL_OUTPUT = 32,
        DFT_COMPLEX_INPUT = 64,
        DCT_INVERSE = DFT_INVERSE,
        DCT_ROWS = DFT_ROWS,
    }

    enum DistanceTransformLabelTypes {
        DIST_LABEL_CCOMP = 0,
        DIST_LABEL_PIXEL = 1,
    }

    enum DistanceTransformMasks {
        DIST_MASK_3 = 3,
        DIST_MASK_5 = 5,
        DIST_MASK_PRECISE = 0,
    }

    enum DistanceTypes {
        DIST_USER = -1,
        DIST_L1 = 1,
        DIST_L2 = 2,
        DIST_C = 3,
        DIST_L12 = 4,
        DIST_FAIR = 5,
        DIST_WELSCH = 6,
        DIST_HUBER = 7,
    }

    enum DrawMatchesFlags {
        DEFAULT = 0,
        DRAW_OVER_OUTIMG = 1,
        NOT_DRAW_SINGLE_POINTS = 2,
        DRAW_RICH_KEYPOINTS = 4,
    }

    enum FastFeatureDetector_DetectorType {
        TYPE_5_8 = 0,
        TYPE_7_12 = 1,
        TYPE_9_16 = 2,
    }

    enum FileStorage_Mode {
        READ = 0,
        WRITE = 1,
        APPEND = 2,
        MEMORY = 4,
        FORMAT_MASK = 7 << 3,
        FORMAT_AUTO = 0,
        FORMAT_XML = 1 << 3,
        FORMAT_YAML = 2 << 3,
        FORMAT_JSON = 3 << 3,
        BASE64 = 64,
        WRITE_BASE64 = BASE64 | WRITE,
    }

    enum FileStorage_State {
        UNDEFINED = 0,
        VALUE_EXPECTED = 1,
        NAME_EXPECTED = 2,
        INSIDE_MAP = 4,
    }

    enum FloodFillFlags {
        FLOODFILL_FIXED_RANGE = 1 << 16,
        FLOODFILL_MASK_ONLY = 1 << 17,
    }

    enum Formatter_FormatType {
        FMT_DEFAULT = 0,
        FMT_MATLAB = 1,
        FMT_CSV = 2,
        FMT_PYTHON = 3,
        FMT_NUMPY = 4,
        FMT_C = 5,
    }

    enum GemmFlags {
        GEMM_1_T = 1,
        GEMM_2_T = 2,
        GEMM_3_T = 4,
    }

    enum GrabCutClasses {
        GC_BGD = 0,
        GC_FGD = 1,
        GC_PR_BGD = 2,
        GC_PR_FGD = 3,
    }

    enum GrabCutModes {
        GC_INIT_WITH_RECT = 0,
        GC_INIT_WITH_MASK = 1,
        GC_EVAL = 2,
        GC_EVAL_FREEZE_MODEL = 3,
    }

    enum HOGDescriptor_DescriptorStorageFormat {
        DESCR_FORMAT_COL_BY_COL = 0,
        DESCR_FORMAT_ROW_BY_ROW = 1,
    }

    enum HOGDescriptor_HistogramNormType {
        L2Hys = 0,
    }

    enum HandEyeCalibrationMethod {
        CALIB_HAND_EYE_TSAI = 0,
        CALIB_HAND_EYE_PARK = 1,
        CALIB_HAND_EYE_HORAUD = 2,
        CALIB_HAND_EYE_ANDREFF = 3,
        CALIB_HAND_EYE_DANIILIDIS = 4,
    }

    enum HersheyFonts {
        FONT_HERSHEY_SIMPLEX = 0,
        FONT_HERSHEY_PLAIN = 1,
        FONT_HERSHEY_DUPLEX = 2,
        FONT_HERSHEY_COMPLEX = 3,
        FONT_HERSHEY_TRIPLEX = 4,
        FONT_HERSHEY_COMPLEX_SMALL = 5,
        FONT_HERSHEY_SCRIPT_SIMPLEX = 6,
        FONT_HERSHEY_SCRIPT_COMPLEX = 7,
        FONT_ITALIC = 16,
    }

    enum HistCompMethods {
        HISTCMP_CORREL = 0,
        HISTCMP_CHISQR = 1,
        HISTCMP_INTERSECT = 2,
        HISTCMP_BHATTACHARYYA = 3,
        HISTCMP_HELLINGER = HISTCMP_BHATTACHARYYA,
        HISTCMP_CHISQR_ALT = 4,
        HISTCMP_KL_DIV = 5,
    }

    enum HoughModes {
        HOUGH_STANDARD = 0,
        HOUGH_PROBABILISTIC = 1,
        HOUGH_MULTI_SCALE = 2,
        HOUGH_GRADIENT = 3,
        HOUGH_GRADIENT_ALT = 4,
    }

    enum InterpolationFlags {
        INTER_NEAREST = 0,
        INTER_LINEAR = 1,
        INTER_CUBIC = 2,
        INTER_AREA = 3,
        INTER_LANCZOS4 = 4,
        INTER_LINEAR_EXACT = 5,
        INTER_NEAREST_EXACT = 6,
        INTER_MAX = 7,
        WARP_FILL_OUTLIERS = 8,
        WARP_INVERSE_MAP = 16,
    }

    enum InterpolationMasks {
        INTER_BITS = 5,
        INTER_BITS2 = INTER_BITS * 2,
        INTER_TAB_SIZE = 1 << INTER_BITS,
        INTER_TAB_SIZE2 = INTER_TAB_SIZE * INTER_TAB_SIZE,
    }

    enum KAZE_DiffusivityType {
        DIFF_PM_G1 = 0,
        DIFF_PM_G2 = 1,
        DIFF_WEICKERT = 2,
        DIFF_CHARBONNIER = 3,
    }

    enum KmeansFlags {
        KMEANS_RANDOM_CENTERS = 0,
        KMEANS_PP_CENTERS = 2,
        KMEANS_USE_INITIAL_LABELS = 1,
    }

    enum LineSegmentDetectorModes {
        LSD_REFINE_NONE = 0,
        LSD_REFINE_STD = 1,
        LSD_REFINE_ADV = 2,
    }

    enum LineTypes {
        FILLED = -1,
        LINE_4 = 4,
        LINE_8 = 8,
        LINE_AA = 16,
    }

    enum LocalOptimMethod {
        LOCAL_OPTIM_NULL = 0,
        LOCAL_OPTIM_INNER_LO = 1,
        LOCAL_OPTIM_INNER_AND_ITER_LO = 2,
        LOCAL_OPTIM_GC = 3,
        LOCAL_OPTIM_SIGMA = 4,
    }

    enum MarkerTypes {
        MARKER_CROSS = 0,
        MARKER_TILTED_CROSS = 1,
        MARKER_STAR = 2,
        MARKER_DIAMOND = 3,
        MARKER_SQUARE = 4,
        MARKER_TRIANGLE_UP = 5,
        MARKER_TRIANGLE_DOWN = 6,
    }

    enum MorphShapes {
        MORPH_RECT = 0,
        MORPH_CROSS = 1,
        MORPH_ELLIPSE = 2,
    }

    enum MorphTypes {
        MORPH_ERODE = 0,
        MORPH_DILATE = 1,
        MORPH_OPEN = 2,
        MORPH_CLOSE = 3,
        MORPH_GRADIENT = 4,
        MORPH_TOPHAT = 5,
        MORPH_BLACKHAT = 6,
        MORPH_HITMISS = 7,
    }

    enum NeighborSearchMethod {
        NEIGH_FLANN_KNN = 0,
        NEIGH_GRID = 1,
        NEIGH_FLANN_RADIUS = 2,
    }

    enum NormTypes {
        NORM_INF = 1,
        NORM_L1 = 2,
        NORM_L2 = 4,
        NORM_L2SQR = 5,
        NORM_HAMMING = 6,
        NORM_HAMMING2 = 7,
        NORM_TYPE_MASK = 7,
        NORM_RELATIVE = 8,
        NORM_MINMAX = 32,
    }

    enum ORB_ScoreType {
        HARRIS_SCORE = 0,
        FAST_SCORE = 1,
    }

    enum PCA_Flags {
        DATA_AS_ROW = 0,
        DATA_AS_COL = 1,
        USE_AVG = 2,
    }

    enum Param {
        INT = 0,
        BOOLEAN = 1,
        REAL = 2,
        STRING = 3,
        MAT = 4,
        MAT_VECTOR = 5,
        ALGORITHM = 6,
        FLOAT = 7,
        UNSIGNED_INT = 8,
        UINT64 = 9,
        UCHAR = 11,
        SCALAR = 12,
    }

    enum QuatAssumeType {
        QUAT_ASSUME_NOT_UNIT = 0,
        QUAT_ASSUME_UNIT = 1,
    }

    enum QuatEnum_EulerAnglesType {
        INT_XYZ = 0,
        INT_XZY = 1,
        INT_YXZ = 2,
        INT_YZX = 3,
        INT_ZXY = 4,
        INT_ZYX = 5,
        INT_XYX = 6,
        INT_XZX = 7,
        INT_YXY = 8,
        INT_YZY = 9,
        INT_ZXZ = 10,
        INT_ZYZ = 11,
        EXT_XYZ = 12,
        EXT_XZY = 13,
        EXT_YXZ = 14,
        EXT_YZX = 15,
        EXT_ZXY = 16,
        EXT_ZYX = 17,
        EXT_XYX = 18,
        EXT_XZX = 19,
        EXT_YXY = 20,
        EXT_YZY = 21,
        EXT_ZXZ = 22,
        EXT_ZYZ = 23,
        EULER_ANGLES_MAX_VALUE = 24,
    }

    enum RectanglesIntersectTypes {
        INTERSECT_NONE = 0,
        INTERSECT_PARTIAL = 1,
        INTERSECT_FULL = 2,
    }

    enum ReduceTypes {
        REDUCE_SUM = 0,
        REDUCE_AVG = 1,
        REDUCE_MAX = 2,
        REDUCE_MIN = 3,
    }

    enum RetrievalModes {
        RETR_EXTERNAL = 0,
        RETR_LIST = 1,
        RETR_CCOMP = 2,
        RETR_TREE = 3,
        RETR_FLOODFILL = 4,
    }

    enum RobotWorldHandEyeCalibrationMethod {
        CALIB_ROBOT_WORLD_HAND_EYE_SHAH = 0,
        CALIB_ROBOT_WORLD_HAND_EYE_LI = 1,
    }

    enum RotateFlags {
        ROTATE_90_CLOCKWISE = 0,
        ROTATE_180 = 1,
        ROTATE_90_COUNTERCLOCKWISE = 2,
    }

    enum SVD_Flags {
        MODIFY_A = 1,
        NO_UV = 2,
        FULL_UV = 4,
    }

    enum SamplingMethod {
        SAMPLING_UNIFORM = 0,
        SAMPLING_PROGRESSIVE_NAPSAC = 1,
        SAMPLING_NAPSAC = 2,
        SAMPLING_PROSAC = 3,
    }

    enum ScoreMethod {
        SCORE_METHOD_RANSAC = 0,
        SCORE_METHOD_MSAC = 1,
        SCORE_METHOD_MAGSAC = 2,
        SCORE_METHOD_LMEDS = 3,
    }

    enum ShapeMatchModes {
        CONTOURS_MATCH_I1 = 1,
        CONTOURS_MATCH_I2 = 2,
        CONTOURS_MATCH_I3 = 3,
    }

    enum SolveLPResult {
        SOLVELP_UNBOUNDED = -2,
        SOLVELP_UNFEASIBLE = -1,
        SOLVELP_SINGLE = 0,
        SOLVELP_MULTI = 1,
    }

    enum SolvePnPMethod {
        SOLVEPNP_ITERATIVE = 0,
        SOLVEPNP_EPNP = 1,
        SOLVEPNP_P3P = 2,
        SOLVEPNP_DLS = 3,
        SOLVEPNP_UPNP = 4,
        SOLVEPNP_AP3P = 5,
        SOLVEPNP_IPPE = 6,
        SOLVEPNP_IPPE_SQUARE = 7,
        SOLVEPNP_SQPNP = 8,
        SOLVEPNP_MAX_COUNT = 8 + 1,
    }

    enum SortFlags {
        SORT_EVERY_ROW = 0,
        SORT_EVERY_COLUMN = 1,
        SORT_ASCENDING = 0,
        SORT_DESCENDING = 16,
    }

    enum SpecialFilter {
        FILTER_SCHARR = -1,
    }

    enum TemplateMatchModes {
        TM_SQDIFF = 0,
        TM_SQDIFF_NORMED = 1,
        TM_CCORR = 2,
        TM_CCORR_NORMED = 3,
        TM_CCOEFF = 4,
        TM_CCOEFF_NORMED = 5,
    }

    enum TermCriteria_Type {
        COUNT = 1,
        MAX_ITER = COUNT,
        EPS = 2,
    }

    enum ThresholdTypes {
        THRESH_BINARY = 0,
        THRESH_BINARY_INV = 1,
        THRESH_TRUNC = 2,
        THRESH_TOZERO = 3,
        THRESH_TOZERO_INV = 4,
        THRESH_MASK = 7,
        THRESH_OTSU = 8,
        THRESH_TRIANGLE = 16,
    }

    enum UMatData_MemoryFlag {
        COPY_ON_MAP = 1,
        HOST_COPY_OBSOLETE = 2,
        DEVICE_COPY_OBSOLETE = 4,
        TEMP_UMAT = 8,
        TEMP_COPIED_UMAT = 24,
        USER_ALLOCATED = 32,
        DEVICE_MEM_MAPPED = 64,
        ASYNC_CLEANUP = 128,
    }

    enum UMatUsageFlags {
        USAGE_DEFAULT = 0,
        USAGE_ALLOCATE_HOST_MEMORY = 1 << 0,
        USAGE_ALLOCATE_DEVICE_MEMORY = 1 << 1,
        USAGE_ALLOCATE_SHARED_MEMORY = 1 << 2,
        __UMAT_USAGE_FLAGS_32BIT = 0x7fffffff,
    }

    enum UndistortTypes {
        PROJ_SPHERICAL_ORTHO = 0,
        PROJ_SPHERICAL_EQRECT = 1,
    }

    enum WarpPolarMode {
        WARP_POLAR_LINEAR = 0,
        WARP_POLAR_LOG = 256,
    }

    enum _InputArray_KindFlag {
        KIND_SHIFT = 16,
        FIXED_TYPE = 0x8000 << KIND_SHIFT,
        FIXED_SIZE = 0x4000 << KIND_SHIFT,
        KIND_MASK = 31 << KIND_SHIFT,
        NONE = 0 << KIND_SHIFT,
        MAT = 1 << KIND_SHIFT,
        MATX = 2 << KIND_SHIFT,
        STD_VECTOR = 3 << KIND_SHIFT,
        STD_VECTOR_VECTOR = 4 << KIND_SHIFT,
        STD_VECTOR_MAT = 5 << KIND_SHIFT,
        EXPR = 6 << KIND_SHIFT,
        OPENGL_BUFFER = 7 << KIND_SHIFT,
        CUDA_HOST_MEM = 8 << KIND_SHIFT,
        CUDA_GPU_MAT = 9 << KIND_SHIFT,
        UMAT = 10 << KIND_SHIFT,
        STD_VECTOR_UMAT = 11 << KIND_SHIFT,
        STD_BOOL_VECTOR = 12 << KIND_SHIFT,
        STD_VECTOR_CUDA_GPU_MAT = 13 << KIND_SHIFT,
        STD_ARRAY = 14 << KIND_SHIFT,
        STD_ARRAY_MAT = 15 << KIND_SHIFT,
    }

    enum Error_Code {
        StsOk = 0,
        StsBackTrace = -1,
        StsError = -2,
        StsInternal = -3,
        StsNoMem = -4,
        StsBadArg = -5,
        StsBadFunc = -6,
        StsNoConv = -7,
        StsAutoTrace = -8,
        HeaderIsNull = -9,
        BadImageSize = -10,
        BadOffset = -11,
        BadDataPtr = -12,
        BadStep = -13,
        BadModelOrChSeq = -14,
        BadNumChannels = -15,
        BadNumChannel1U = -16,
        BadDepth = -17,
        BadAlphaChannel = -18,
        BadOrder = -19,
        BadOrigin = -20,
        BadAlign = -21,
        BadCallBack = -22,
        BadTileSize = -23,
        BadCOI = -24,
        BadROISize = -25,
        MaskIsTiled = -26,
        StsNullPtr = -27,
        StsVecLengthErr = -28,
        StsFilterStructContentErr = -29,
        StsKernelStructContentErr = -30,
        StsFilterOffsetErr = -31,
        StsBadSize = -201,
        StsDivByZero = -202,
        StsInplaceNotSupported = -203,
        StsObjectNotFound = -204,
        StsUnmatchedFormats = -205,
        StsBadFlag = -206,
        StsBadPoint = -207,
        StsBadMask = -208,
        StsUnmatchedSizes = -209,
        StsUnsupportedFormat = -210,
        StsOutOfRange = -211,
        StsParseError = -212,
        StsNotImplemented = -213,
        StsBadMemBlock = -214,
        StsAssert = -215,
        GpuNotSupported = -216,
        GpuApiCallError = -217,
        OpenGlNotSupported = -218,
        OpenGlApiCallError = -219,
        OpenCLApiCallError = -220,
        OpenCLDoubleNotSupported = -221,
        OpenCLInitError = -222,
        OpenCLNoAMDBlasFft = -223,
    }

    enum detail_CvFeatureParams_FeatureType {
        HAAR = 0,
        LBP = 1,
        HOG = 2,
    }

    enum detail_TestOp {
        TEST_CUSTOM = 0,
        TEST_EQ = 1,
        TEST_NE = 2,
        TEST_LE = 3,
        TEST_LT = 4,
        TEST_GE = 5,
        TEST_GT = 6,
    }

    enum detail_TrackerSamplerCSC_MODE {
        MODE_INIT_POS = 1,
        MODE_INIT_NEG = 2,
        MODE_TRACK_POS = 3,
        MODE_TRACK_NEG = 4,
        MODE_DETECT = 5,
    }

    enum dnn_Backend {
        DNN_BACKEND_DEFAULT = 0,
        DNN_BACKEND_HALIDE = 0 + 1,
        DNN_BACKEND_INFERENCE_ENGINE = 0 + 2,
        DNN_BACKEND_OPENCV = 0 + 3,
        DNN_BACKEND_VKCOM = 0 + 4,
        DNN_BACKEND_CUDA = 0 + 5,
    }

    enum dnn_Target {
        DNN_TARGET_CPU = 0,
        DNN_TARGET_OPENCL = 0 + 1,
        DNN_TARGET_OPENCL_FP16 = 0 + 2,
        DNN_TARGET_MYRIAD = 0 + 3,
        DNN_TARGET_VULKAN = 0 + 4,
        DNN_TARGET_FPGA = 0 + 5,
        DNN_TARGET_CUDA = 0 + 6,
        DNN_TARGET_CUDA_FP16 = 0 + 7,
        DNN_TARGET_HDDL = 0 + 8,
    }
}
