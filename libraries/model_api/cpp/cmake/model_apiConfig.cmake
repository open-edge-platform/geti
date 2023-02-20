include(CMakeFindDependencyMacro)
find_dependency(OpenCV)
find_dependency(OpenVINO)

include("${CMAKE_CURRENT_LIST_DIR}/model_apiTargets.cmake")
