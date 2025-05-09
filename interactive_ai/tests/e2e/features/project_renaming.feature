# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

Feature: project renaming
  The user can rename a project

  Background: Geti platform with a workspace
    Given a workspace

  Scenario Outline: renaming a project
    Given a project of type 'detection'
      When the user renames the project to '<new_name>'
      Then the project name is '<new_name>'

    Examples:
      | new_name |
      | n+OAgA== |
      | 노인은 썰매를 타고 있습니다 |
      | 莫利塞不存在。|
      |        موليز لا وجود له. |
      | </textarea><script>alert(123)</script> |