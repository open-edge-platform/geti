include(CMakeFindDependencyMacro)
find_dependency(OpenCV COMPONENTS core imgproc)
find_dependency(OpenVINO COMPONENTS Runtime)

include("${CMAKE_CURRENT_LIST_DIR}/model_apiTargets.cmake")
