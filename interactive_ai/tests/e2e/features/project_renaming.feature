# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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