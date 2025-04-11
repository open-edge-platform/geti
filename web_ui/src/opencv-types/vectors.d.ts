// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0
declare module 'vectors' {
    import { EmVector } from 'emscripten';
    import { Mat } from 'mat';
    import { double, float, int } from 'scalars';
    import { DMatchLike, KeyPointLike, PointLike, RectLike } from 'valueObjects';

    // register_vector<int>("IntVector");
    class IntVector extends EmVector<int> {}

    // register_vector<float>("FloatVector");
    class FloatVector extends EmVector<float> {}

    // register_vector<double>("DoubleVector");
    class DoubleVector extends EmVector<double> {}

    // register_vector<cv::Point>("PointVector");
    class PointVector extends EmVector<PointLike> {}

    // register_vector<cv::Mat>("MatVector");
    class MatVector extends EmVector<Mat> {}

    // register_vector<cv::Rect>("RectVector");
    class RectVector extends EmVector<RectLike> {}

    // register_vector<cv::KeyPoint>("KeyPointVector");
    class KeyPointVector extends EmVector<KeyPointLike> {}

    // register_vector<cv::DMatch>("DMatchVector");
    class DMatchVector extends EmVector<DMatchLike> {}

    // register_vector<std::vector<cv::DMatch>>("DMatchVectorVector");
    class DMatchVectorVector extends EmVector<DMatchVector> {}
}
